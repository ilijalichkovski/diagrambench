"""Sequential-gauntlet engine shared by the in-sandbox `./veld` CLI and the
host-side authoritative rescoring.

The whole run is defined by (levels, ops): `levels` is the ordered curriculum
slice, `ops` the chronological list of every operation the agent issued. State
is always rebuilt by replaying `ops` from scratch, so the operation log is the
single source of truth — the host re-runs the same replay against the true
hidden goals, which makes in-sandbox tampering pointless.
"""

from .errors import VeldError  # noqa: F401  (re-exported for the CLI)
from .sdk import BOOTSTRAP, TaskEnv  # noqa: F401
from .verify import verify

LEVEL_ACTION_CAP = 160
PRESENT_CAP = 8

INTROSPECTION_OPS = {"families", "ops", "sig", "forms", "shelf", "peek",
                     "veins", "census", "study", "trace"}


def _fresh_counts():
    return {"actions": 0, "presents": 0, "failed": 0, "introspection": 0,
            "undo": 0}


def _safe_verify(env, hidden_goal):
    try:
        return verify(env, hidden_goal)
    except Exception as e:  # a broken scene is a failed artifact
        return {"success": False, "semantic_score": 0.0, "layout_score": 0.0,
                "passed": [],
                "failed": [f"artifact could not be judged ({type(e).__name__})"]}


class ReplayState:
    def __init__(self, levels):
        self.levels = levels
        self.level_idx = 0          # 0-based index into levels
        self.env = TaskEnv()
        self.counts = _fresh_counts()
        self.completed = []         # per-level summaries, in order
        self.terminated = None      # reason string once the run is over
        self.finished = False       # all levels cleared
        self.ops_consumed = 0
        self.last_text = ""

    @property
    def level(self):
        if self.level_idx < len(self.levels):
            return self.levels[self.level_idx]
        return None

    def summary(self):
        return {
            "levels_completed": len(self.completed),
            "num_levels": len(self.levels),
            "finished": self.finished,
            "terminated": self.terminated,
            "ops_consumed": self.ops_consumed,
            "per_level": self.completed,
            "current_level": self.level["id"] if self.level else None,
            "current_counts": dict(self.counts),
        }


def format_brief(state):
    if state.finished:
        return (f"ALL {len(state.levels)} LEVELS COMPLETE. "
                f"The instrument rests.")
    if state.terminated:
        return f"RUN OVER — {state.terminated}"
    lvl = state.level
    c = state.counts
    return (
        f"LEVEL {state.level_idx + 1} of {len(state.levels)} "
        f"[{lvl['id']}]\n"
        f"{lvl['instruction']}\n"
        f"budget: {c['actions']}/{LEVEL_ACTION_CAP} operations used, "
        f"{c['presents']}/{PRESENT_CAP} presents used\n"
        f"levels cleared so far: {len(state.completed)}"
    )


def _finish_level(state, verdict):
    lvl = state.level
    c = state.counts
    construct = c["actions"] - c["presents"]
    state.completed.append({
        "id": lvl["id"],
        "index": lvl["index"],
        "stage": lvl.get("stage"),
        "actions": c["actions"],
        "presents": c["presents"],
        "failed_calls": c["failed"],
        "introspection": c["introspection"],
        "undo": c["undo"],
        "ref_cost": lvl.get("ref_cost", 0),
        "regret": construct - lvl.get("ref_cost", 0),
        "semantic_score": verdict["semantic_score"],
        "layout_score": verdict["layout_score"],
    })
    state.level_idx += 1
    state.env = TaskEnv()
    state.counts = _fresh_counts()
    if state.level_idx >= len(state.levels):
        state.finished = True


def step(state, op, args):
    """Apply one operation to the live state. Returns the agent-facing text."""
    if state.finished:
        state.last_text = format_brief(state)
        return state.last_text
    if state.terminated:
        state.last_text = f"RUN OVER — {state.terminated} No further ops accepted."
        return state.last_text

    obs = state.env.act(op, args or {})
    c = state.counts
    c["actions"] += 1
    if not obs.get("ok"):
        c["failed"] += 1
    if op in INTROSPECTION_OPS:
        c["introspection"] += 1
    if op == "undo":
        c["undo"] += 1

    if obs.get("present") and obs.get("ok"):
        c["presents"] += 1
        verdict = _safe_verify(state.env, state.level["hidden_goal"])
        if verdict["success"]:
            cleared = state.level_idx + 1
            _finish_level(state, verdict)
            text = (f"SUCCESS — level {cleared} cleared "
                    f"({len(state.completed)}/{len(state.levels)}).")
            if state.finished:
                text += f"\n\nALL {len(state.levels)} LEVELS COMPLETE."
            else:
                text += "\n\n" + format_brief(state)
            state.last_text = text
            return text
        lines = [
            f"NOT YET — semantic {verdict['semantic_score']:.2f}, "
            f"layout {verdict['layout_score']:.2f} "
            f"(present {c['presents']}/{PRESENT_CAP})",
        ]
        lines += [f"  unmet: {f}" for f in verdict["failed"][:8]]
        if c["presents"] >= PRESENT_CAP:
            state.terminated = (f"present budget exhausted on level "
                                f"{state.level_idx + 1}.")
            lines.append(f"RUN OVER — {state.terminated}")
        state.last_text = "\n".join(lines)
        return state.last_text

    text = obs.get("text") if obs.get("ok") else f"error: {obs.get('error')}"
    if c["actions"] >= LEVEL_ACTION_CAP and not state.finished:
        state.terminated = (f"operation budget exhausted on level "
                            f"{state.level_idx + 1}.")
        text = (text or "") + f"\nRUN OVER — {state.terminated}"
    state.last_text = text or ""
    return state.last_text


def replay(levels, ops):
    """Rebuild run state by replaying `ops` in order. Ops arriving after the
    run is over are not consumed (the CLI uses this to refuse logging them)."""
    state = ReplayState(levels)
    for entry in ops:
        if state.finished or state.terminated:
            break
        step(state, entry.get("op", ""), entry.get("args") or {})
        state.ops_consumed += 1
    return state
