"""Compare DiagramBench gauntlet runs across harnesses.

Usage: .venv/bin/python scripts/compare_harnesses.py outputs/gauntlet20-codex outputs/gauntlet20-default
"""

import json
import sys
from pathlib import Path


def load_trace(run_dir):
    path = Path(run_dir) / "traces.jsonl"
    with open(path) as f:
        traces = [json.loads(line) for line in f if line.strip()]
    return traces[0] if traces else None


def summarize(run_dir):
    t = load_trace(run_dir)
    if t is None:
        return None
    info = t.get("info") or {}
    gb = info.get("diagrambench") or info.get("glyphbench") or {}
    rewards = t.get("rewards") or {}
    metrics = t.get("metrics") or {}
    usage = t.get("usage") or {}
    return {
        "run": str(run_dir),
        "reward": rewards.get("progress"),
        "levels_completed": gb.get("levels_completed"),
        "num_levels": gb.get("num_levels"),
        "terminated": gb.get("terminated"),
        "per_level": gb.get("per_level") or [],
        "metrics": metrics,
        "rewards": rewards,
        "usage": t.get("extra_usage") or {},
        "error": t.get("errors"),
    }


def main():
    runs = [summarize(d) for d in sys.argv[1:]]
    runs = [r for r in runs if r]
    if not runs:
        print("no traces found")
        return

    print(f"{'':28}" + "".join(f"{Path(r['run']).name:>24}" for r in runs))
    def row(label, fn):
        print(f"{label:28}" + "".join(f"{fn(r)!s:>24}" for r in runs))

    row("levels cleared", lambda r: f"{r['levels_completed']}/{r['num_levels']}")
    row("reward (progress)", lambda r: f"{r['reward']:.2f}" if r['reward'] is not None else "-")
    row("run terminated", lambda r: r["terminated"] or "no")
    row("total operations", lambda r: r["metrics"].get("operations_used"))
    row("failed calls", lambda r: r["metrics"].get("failed_calls"))
    row("mean regret (completed)", lambda r: round(r["metrics"].get("mean_regret_completed", 0), 2))
    row("tokens in/out", lambda r: f"{r['usage'].get('input_tokens','?')}/{r['usage'].get('output_tokens','?')}"
        if r["usage"] else "-")
    row("cost ($)", lambda r: round(r["usage"].get("cost", 0), 4) if r["usage"] else "-")

    print("\nper-level construction actions (ref cost in brackets):")
    max_lv = max(len(r["per_level"]) for r in runs)
    for i in range(max_lv):
        cells = []
        ref = None
        for r in runs:
            if i < len(r["per_level"]):
                l = r["per_level"][i]
                ref = l["ref_cost"]
                cells.append(f"{l['actions'] - l['presents']:>3} ops, {l['presents']}p")
            else:
                cells.append("—")
        lid = next((r["per_level"][i]["id"] for r in runs if i < len(r["per_level"])), "?")
        print(f"  {i+1:>2} {lid:10} [{ref:>2}]  " + "  ".join(f"{c:>14}" for c in cells))


if __name__ == "__main__":
    main()
