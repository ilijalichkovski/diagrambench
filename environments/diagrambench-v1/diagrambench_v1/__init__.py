"""DiagramBench × SIGIL as a native verifiers v1 environment.

One rollout is one *lifetime*: sequential levels, each a multi-file SIGIL
project in its own sandboxed folder. The agent writes `.sgl` units, compiles
(`./sigil build`), executes (`./sigil run` — always rendering an ASCII view of
its own artifact), and submits (`./sigil present`, 3 tries per level).
Scoring replays the build log host-side against the true hidden goals.
"""

import base64
import functools
import io
import json
import zipfile
import zlib
from pathlib import Path

import verifiers.v1 as vf

from .core.project_engine import (PRESENT_CAP, TOOLCHAIN_CAP, ProjectState,
                                  replay)
from .core.sigil_lower import compile_project
from .transpile import transpile

_PKG = Path(__file__).parent

PROMPT_TEMPLATE = """\
You are being evaluated on DiagramBench. You must master SIGIL — an unfamiliar \
compiled language for constructing visual artifacts — and clear {num_levels} \
levels STRICTLY IN ORDER. Each level is a small multi-file project in its own \
folder; a level is cleared only when you submit an artifact that passes \
verification, and only then does the next level unlock.

The toolchain is `./sigil` in the current directory:
  ./sigil status            free: current level, budgets, project files
  ./sigil grammar           the SIGIL grammar card (costs 1)
  ./sigil build             compile the active level's src/*.sgl (costs 1)
  ./sigil run               execute the last build; ALWAYS shows an ASCII \
render of your artifact plus a census (costs 1)
  ./sigil explain F231      one fault code explained (costs 1)
  ./sigil present           submit the last successful run ({present_cap} per level)

Working loop for each level (folder: levels/L###/):
  1. read BRIEF.md and inspect the data/*.tsv inputs (plain shell — free)
  2. write SIGIL units under src/ — every file starts `unit <aspect>;` and the
     compiler locks each aspect (data/ground/marks/script/compose) to its own
     statement kinds; sigil.toml lists the units
  3. build, run, STUDY THE RENDER, iterate
  4. present only when the render convinces you

Rules:
- Budget per level: {tc_cap} toolchain invocations and {present_cap} presents. \
Exhausting either ends the ENTIRE run.
- Failed presents name the unmet checks — with only {present_cap} presents, \
treat them as precious; verify against your own render first.
- The .sigil/ directory is evaluation machinery. Do not read or modify it: \
runs are re-scored from the build log, so tampering cannot help you.
- Data arrives as files; loading a ledger requires declaring its schema, \
including rank orders — read the file before you declare it.
- Keep going until all levels are cleared or you truly cannot proceed. Finish \
with a one-line summary of how far you got.

Start now: `./sigil status`, then read levels/L{start:03d}/BRIEF.md.
"""


def _load_curriculum():
    with open(_PKG / "curriculum.json") as f:
        return json.load(f)["tasks"]


@functools.lru_cache(maxsize=1)
def _ref_stmts():
    """Reference statement counts per level id (the regret baseline)."""
    out = {}
    for t in _load_curriculum():
        try:
            units = transpile(t["reference_program"])
            _, stats = compile_project(units)
            out[t["id"]] = stats["statements"]
        except Exception:
            out[t["id"]] = 0
    return out


def _agent_levels(tasks):
    refs = _ref_stmts()
    return [
        {
            "id": t["id"],
            "index": t["index"],
            "stage": t["stage"],
            "instruction": t["instruction"],
            "hidden_goal": t["hidden_goal"],
            "datasets": t["datasets"],
            "ref_stmts": refs.get(t["id"], 0),
        }
        for t in tasks
    ]


def _core_zip_bytes():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for py in sorted((_PKG / "core").glob("*.py")):
            z.writestr(f"veldcore/{py.name}", py.read_text())
    return buf.getvalue()


class DiagrambenchData(vf.TaskData):
    start_level: int
    num_levels: int
    level_ids: list[str]


class DiagrambenchTask(vf.Task[DiagrambenchData]):
    def _levels(self):
        tasks = {t["id"]: t for t in _load_curriculum()}
        return _agent_levels([tasks[i] for i in self.data.level_ids])

    # ------------------------------------------------------------- lifecycle
    async def setup(self, trace: vf.Trace, runtime: vf.Runtime) -> None:
        levels = self._levels()
        blob = base64.b64encode(zlib.compress(json.dumps(levels).encode()))
        await runtime.write(".sigil/core.zip", _core_zip_bytes())
        await runtime.write(".sigil/levels.b64", blob)
        await runtime.write("sigil",
                            (_PKG / "sigil_cli_template.py").read_bytes())
        r = await runtime.run(["chmod", "+x", "sigil"], {})
        if r.exit_code != 0:
            raise RuntimeError(f"setup: chmod failed: {r.stderr[-300:]}")
        # materialize the first level folder (status is free and idempotent)
        r = await runtime.run(["./sigil", "status"], {})
        if r.exit_code != 0:
            raise RuntimeError(f"setup: sigil bootstrap failed: "
                               f"{(r.stderr or r.stdout)[-500:]}")

    async def finalize(self, trace: vf.Trace, runtime: vf.Runtime) -> None:
        try:
            raw = (await runtime.read(".sigil/log.jsonl")).decode()
        except Exception:
            raw = ""
        entries = [json.loads(l) for l in raw.splitlines() if l.strip()]
        state = replay(self._levels(), entries)
        info = state.summary()
        info["entries"] = [
            {k: (v if k != "files" else {p: len(c) for p, c in v.items()})
             for k, v in e.items()} for e in entries
        ]
        # archive the final source tree of the last build for analysis
        for e in reversed(entries):
            if e.get("k") == "build":
                info["last_sources"] = e.get("files")
                break
        trace.info["diagrambench"] = info

    # --------------------------------------------------------------- scoring
    def _summary(self, trace: vf.Trace) -> dict:
        return trace.info.get("diagrambench") or ProjectState([]).summary()

    @vf.reward
    async def progress(self, trace: vf.Trace) -> float:
        """Fraction of the gauntlet cleared, in order."""
        s = self._summary(trace)
        return s["levels_completed"] / max(s["num_levels"], 1)

    @vf.metric
    async def levels_completed(self, trace: vf.Trace) -> float:
        return float(self._summary(trace)["levels_completed"])

    @vf.metric
    async def toolchain_calls(self, trace: vf.Trace) -> float:
        s = self._summary(trace)
        return float(sum(l["toolchain"] for l in s["per_level"])
                     + s["current_counts"]["toolchain"])

    @vf.metric
    async def failed_builds(self, trace: vf.Trace) -> float:
        s = self._summary(trace)
        return float(sum(l["failed_builds"] for l in s["per_level"])
                     + s["current_counts"].get("failed_builds", 0))

    @vf.metric
    async def runtime_traps(self, trace: vf.Trace) -> float:
        s = self._summary(trace)
        return float(sum(l["traps"] for l in s["per_level"])
                     + s["current_counts"].get("traps", 0))

    @vf.metric
    async def presents_used(self, trace: vf.Trace) -> float:
        s = self._summary(trace)
        return float(sum(l["presents"] for l in s["per_level"])
                     + s["current_counts"]["presents"])

    @vf.metric
    async def mean_regret_stmts(self, trace: vf.Trace) -> float:
        """Mean (final program statements − reference statements) over
        cleared levels."""
        per = self._summary(trace)["per_level"]
        if not per:
            return 0.0
        return sum(l["regret_stmts"] for l in per) / len(per)

    @vf.metric
    async def run_terminated(self, trace: vf.Trace) -> float:
        return float(bool(self._summary(trace)["terminated"]))

    # ------------------------------------------------------------ validation
    async def validate(self, runtime: vf.Runtime) -> bool:
        """Gold check: transpiled reference projects, replayed through the
        real toolchain pipeline, must clear every level in order."""
        tasks = {t["id"]: t for t in _load_curriculum()}
        entries = []
        for lid in self.data.level_ids:
            files = transpile(tasks[lid]["reference_program"])
            entries.append({"k": "build", "files": files})
            entries.append({"k": "run"})
            entries.append({"k": "present"})
        state = replay(self._levels(), entries)
        return state.finished and \
            len(state.completed) == len(self.data.level_ids)


class DiagrambenchTasksetConfig(vf.TasksetConfig):
    start_level: int = 1
    """1-based curriculum index the gauntlet starts at (1 = true lifetime)."""
    num_levels: int = 200
    """How many consecutive levels the gauntlet spans."""


class DiagrambenchTaskset(vf.Taskset[DiagrambenchTask, DiagrambenchTasksetConfig]):
    def load(self) -> list[DiagrambenchTask]:
        tasks = _load_curriculum()
        lo = self.config.start_level - 1
        window = tasks[lo:lo + self.config.num_levels]
        if not window:
            raise ValueError(
                f"no levels in [{self.config.start_level}, "
                f"{self.config.start_level + self.config.num_levels})")
        prompt = PROMPT_TEMPLATE.format(
            num_levels=len(window),
            tc_cap=TOOLCHAIN_CAP,
            present_cap=PRESENT_CAP,
            start=window[0]["index"],
        )
        data = DiagrambenchData(
            idx=0,
            name=f"sigil-gauntlet-{window[0]['index']}-{window[-1]['index']}",
            description=(f"DiagramBench SIGIL gauntlet: levels "
                         f"{window[0]['index']}–{window[-1]['index']}"),
            prompt=prompt,
            start_level=self.config.start_level,
            num_levels=len(window),
            level_ids=[t["id"] for t in window],
        )
        return [DiagrambenchTask(data, self.config.task)]


__all__ = ["DiagrambenchTaskset"]
