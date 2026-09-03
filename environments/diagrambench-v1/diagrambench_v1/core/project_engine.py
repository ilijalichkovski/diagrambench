"""SIGIL project engine: multi-file levels, budgets, and log replay.

The log is the single source of truth: every `build` entry embeds the full
source tree it compiled, so the host replays the identical pipeline against
the true hidden goals. Budgets: 40 toolchain invocations (build/run/grammar/
explain) and 3 presents per level; exhausting either ends the lifetime.
"""

import fnmatch
import os
import tempfile

from .datasets import DATASETS
from .errors import SigilError
from .sigil_exec import GRAMMAR, Trap, execute, explain
from .sigil_lang import Fault
from .sigil_lower import compile_project
from .verify import verify

TOOLCHAIN_CAP = 40
PRESENT_CAP = 3


def dataset_tsv(name):
    rows = DATASETS[name]
    cols = list(rows[0].keys())
    out = ["\t".join(cols)]
    for r in rows:
        out.append("\t".join(str(r[c]) for c in cols))
    return "\n".join(out) + "\n"


def brief_text(level, num_levels, cleared):
    ds = "\n".join(f"  data/{d}.tsv" for d in level.get("datasets", []))
    ds_block = f"\nInputs shipped with this level:\n{ds}\n" if ds else ""
    return f"""# Level {level['index']} of {num_levels} — {level['id']}

{level['instruction']}
{ds_block}
Budget: {TOOLCHAIN_CAP} toolchain invocations (build / run / grammar / explain)
and {PRESENT_CAP} presents. Exhausting either ends the entire run.

Levels cleared so far: {cleared}.
"""


DEFAULT_MANIFEST = """\
[project]
units = ["src/*.sgl"]

[view]
mode = "ascii"      # ascii | image | both | none
grid = "160x60"
"""


def _safe_verify(env, hidden_goal):
    try:
        return verify(env, hidden_goal)
    except Exception as e:
        return {"success": False, "semantic_score": 0.0, "layout_score": 0.0,
                "passed": [], "failed":
                [f"artifact could not be judged ({type(e).__name__})"]}


class ProjectState:
    def __init__(self, levels):
        self.levels = levels
        self.level_idx = 0
        self.tc = 0                 # toolchain invocations this level
        self.presents = 0
        self.builds = 0
        self.failed_builds = 0
        self.runs = 0
        self.traps = 0
        self.ir = None              # last successful build
        self.ir_stats = None
        self.env = None             # last successful run's scene
        self.completed = []
        self.terminated = None
        self.finished = False
        self.entries_consumed = 0
        self.last_text = ""

    @property
    def level(self):
        return self.levels[self.level_idx] \
            if self.level_idx < len(self.levels) else None

    def budget_line(self):
        return (f"budget: {self.tc}/{TOOLCHAIN_CAP} toolchain · "
                f"{self.presents}/{PRESENT_CAP} presents")

    def summary(self):
        return {
            "levels_completed": len(self.completed),
            "num_levels": len(self.levels),
            "finished": self.finished,
            "terminated": self.terminated,
            "entries_consumed": self.entries_consumed,
            "per_level": self.completed,
            "current_level": self.level["id"] if self.level else None,
            "current_counts": {"toolchain": self.tc, "presents": self.presents,
                               "builds": self.builds,
                               "failed_builds": self.failed_builds,
                               "runs": self.runs, "traps": self.traps},
        }

    def _spend(self, kind):
        if kind == "present":
            self.presents += 1
            if self.presents > PRESENT_CAP:  # guarded before call; safety
                self.terminated = (f"present budget exhausted on level "
                                   f"{self.level_idx + 1}.")
        else:
            self.tc += 1
            if self.tc >= TOOLCHAIN_CAP:
                self.terminated = (f"toolchain budget exhausted on level "
                                   f"{self.level_idx + 1}.")

    def _advance(self, verdict):
        lvl = self.level
        self.completed.append({
            "id": lvl["id"], "index": lvl["index"], "stage": lvl.get("stage"),
            "toolchain": self.tc, "builds": self.builds,
            "failed_builds": self.failed_builds, "runs": self.runs,
            "traps": self.traps, "presents": self.presents,
            "statements": (self.ir_stats or {}).get("statements", 0),
            "ref_stmts": lvl.get("ref_stmts", 0),
            "regret_stmts": (self.ir_stats or {}).get("statements", 0)
            - lvl.get("ref_stmts", 0),
            "semantic_score": verdict["semantic_score"],
            "layout_score": verdict["layout_score"],
        })
        self.level_idx += 1
        self.tc = self.presents = 0
        self.builds = self.failed_builds = self.runs = self.traps = 0
        self.ir = self.ir_stats = self.env = None
        if self.level_idx >= len(self.levels):
            self.finished = True


def collect_units(files, manifest_globs):
    """files: {relpath: content} of the project. Selects unit sources."""
    out = {}
    for pattern in manifest_globs:
        for path in sorted(files):
            if fnmatch.fnmatch(path, pattern) and path.endswith(".sgl"):
                out[path] = files[path]
    return out


def _mini_toml(text):
    """Minimal TOML subset parser (sections, strings, string lists)."""
    import re as _re
    out, section = {}, None
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        ms = _re.match(r"^\[([A-Za-z0-9_.-]+)\]$", line)
        if ms:
            section = out.setdefault(ms.group(1), {})
            continue
        mkv = _re.match(r'^([A-Za-z0-9_-]+)\s*=\s*(.+)$', line)
        if not mkv or section is None:
            raise ValueError(f"cannot parse line: {raw!r}")
        key, val = mkv.group(1), mkv.group(2).strip()
        if val.startswith("["):
            section[key] = _re.findall(r'"((?:[^"\\]|\\.)*)"', val)
        elif val.startswith('"'):
            section[key] = val[1:-1]
        else:
            section[key] = val
    return out


def parse_manifest(text):
    try:
        import tomllib
        loads = tomllib.loads
    except ImportError:
        loads = _mini_toml
    try:
        m = loads(text)
    except Exception as e:
        raise Fault("F002", f"sigil.toml does not parse ({e})")
    units = (m.get("project") or {}).get("units") or ["src/*.sgl"]
    view = m.get("view") or {}
    mode = view.get("mode", "ascii")
    grid = view.get("grid", "160x60")
    try:
        gw, gh = (int(x) for x in grid.lower().split("x"))
        gw, gh = max(60, min(gw, 200)), max(24, min(gh, 80))
    except Exception:
        gw, gh = 160, 60
    return units, mode, (gw, gh)


def apply_entry(state, entry, datadir):
    """Advance state by one log entry. Returns agent-facing text."""
    if state.finished:
        state.last_text = "ALL LEVELS COMPLETE."
        return state.last_text
    if state.terminated:
        state.last_text = f"RUN OVER — {state.terminated}"
        return state.last_text

    kind = entry.get("k")
    if kind == "grammar":
        state._spend("tc")
        text = GRAMMAR
    elif kind == "explain":
        state._spend("tc")
        text = f"{entry.get('code')}: {explain(entry.get('code', ''))}"
    elif kind == "build":
        state._spend("tc")
        state.builds += 1
        files = entry.get("files") or {}
        manifest = entry.get("manifest") or DEFAULT_MANIFEST
        try:
            globs, mode, grid = parse_manifest(manifest)
            units = collect_units(files, globs)
            ir, stats = compile_project(units)
            state.ir = ir
            state.ir_stats = stats
            state.view_mode, state.view_grid = mode, grid
            text = (f"build: ok · {stats['statements']} statements across "
                    f"{stats['units']} unit(s) · {stats['ops']} lowered ops")
        except Fault as f:
            state.failed_builds += 1
            text = f"{f}\nbuild: failed"
    elif kind == "run":
        state._spend("tc")
        if state.ir is None:
            text = "run: nothing built yet (or last build failed)"
        else:
            state.runs += 1
            try:
                env, n = execute(state.ir, datadir)
                state.env = env
                text = render_feedback(state, env, n)
            except Trap as t:
                state.traps += 1
                text = f"{t}\nrun: trapped"
    elif kind == "present":
        if state.env is None:
            state._spend("tc")
            text = "present: no successful run to submit"
        else:
            state._spend("present")
            verdict = _safe_verify(state.env, state.level["hidden_goal"])
            if verdict["success"]:
                cleared = state.level_idx + 1
                state._advance(verdict)
                text = (f"SUCCESS — level {cleared} cleared "
                        f"({len(state.completed)}/{len(state.levels)}).")
                if state.finished:
                    text += f"\nALL {len(state.levels)} LEVELS COMPLETE."
                else:
                    text += (f"\nNext level unlocked: levels/"
                             f"L{state.level['index']:03d}/ — read its "
                             f"BRIEF.md")
            else:
                lines = [f"NOT YET — semantic "
                         f"{verdict['semantic_score']:.2f}, layout "
                         f"{verdict['layout_score']:.2f} "
                         f"({state.presents}/{PRESENT_CAP} presents used)"]
                lines += [f"  unmet: {f}" for f in verdict["failed"][:8]]
                if state.presents >= PRESENT_CAP:
                    state.terminated = (f"present budget exhausted on level "
                                        f"{state.level_idx + 1}.")
                    lines.append(f"RUN OVER — {state.terminated}")
                text = "\n".join(lines)
    else:
        text = f"unknown log entry kind {kind!r}"

    if state.terminated and "RUN OVER" not in text:
        text += f"\nRUN OVER — {state.terminated}"
    state.entries_consumed += 1
    state.last_text = text
    return text


def render_feedback(state, env, n_ops):
    from .ascii_render import ascii_view
    from .layout import layout_scene
    from .observe import census_text
    mode = getattr(state, "view_mode", "ascii")
    gw, gh = getattr(state, "view_grid", (160, 60))
    parts = [f"run: ok · {n_ops} ops applied"]
    if mode in ("ascii", "both"):
        try:
            items, warnings = layout_scene(env.scene, env.ledgers)
            view = ascii_view(items, warnings, gw, gh)
            parts.append("─" * 24 + f" view · ascii {gw}x{gh} " + "─" * 24)
            parts.append(view)
            parts.append("─" * 72)
        except Exception as e:
            parts.append(f"(view unavailable: {type(e).__name__}: {e})")
    if mode in ("image", "both"):
        parts.append("(render.svg / render.png written to out/)")
    try:
        parts.append(census_text(env))
    except Exception:
        pass
    parts.append(state.budget_line())
    return "\n".join(parts)


def replay(levels, entries, datadir_for=None):
    """Host-side authoritative replay. `datadir_for(level)` materializes the
    level's data files and returns the directory (defaults to temp dirs)."""
    state = ProjectState(levels)

    def default_datadir(level):
        d = tempfile.mkdtemp(prefix="sigil-replay-")
        os.makedirs(os.path.join(d, "data"), exist_ok=True)
        for name in level.get("datasets", []):
            with open(os.path.join(d, "data", f"{name}.tsv"), "w") as f:
                f.write(dataset_tsv(name))
        return d

    make = datadir_for or default_datadir
    cache = {}
    for entry in entries:
        if state.finished or state.terminated:
            break
        idx = state.level_idx
        if idx not in cache:
            cache[idx] = make(state.level)
        apply_entry(state, entry, cache[idx])
    return state
