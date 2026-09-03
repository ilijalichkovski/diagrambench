"""Final comparison for the gpt-5.6 marathon-prompt runs.

Reads each run's traces.jsonl (verifiers 0.3.2 shape) and prints the scoreboard:
levels cleared, stop reason, budget/regret, and — per request — the number of
tokens in the full lifetime trajectory (final context length), plus peak,
output, cumulative input, and cost.

Run: .venv/bin/python scripts/marathon_report.py
Falls back to a salvaged summary.json when a run's wrapper died before it wrote
a trace (host-side log replay).
"""

import glob
import json
import os
import sys

RUNS = [
    ("sol",   "codex",       "outputs/mara-sol-codex"),
    ("luna",  "codex",       "outputs/mara-luna-codex"),
    ("terra", "codex",       "outputs/mara-terra-codex"),
    ("sol",   "prime-agent", "outputs/mara-sol-pa"),
]
BASELINE = {("luna", "codex"): 24, ("terra", "codex"): 23,
            ("sol", "prime-agent"): 38, ("sol", "codex"): None}


def trace_path(run_dir):
    fs = [f for f in glob.glob(f"{run_dir}/*/traces.jsonl")
          if os.path.getsize(f) > 0]
    return fs[0] if fs else None


def read_trace(path):
    t = json.loads(open(path).readline())
    sub = t["traces"][0] if t.get("traces") else t
    gb = sub["info"]["diagrambench"]
    m = sub.get("metrics", {})
    calls = [c for c in (sub.get("calls") or [])
             if isinstance(c, dict) and c.get("usage")]
    ctx = [(c["usage"].get("prompt_tokens") or 0)
           + (c["usage"].get("cached_input_tokens") or 0) for c in calls]
    out = sum(c["usage"].get("completion_tokens") or 0 for c in calls)
    rea = sum(c["usage"].get("reasoning_tokens") or 0 for c in calls)
    cost = sum(c["usage"].get("cost") or 0 for c in calls)
    return {
        "cleared": gb["levels_completed"],
        "stop": sub.get("stop_condition"),
        "terminated": gb.get("terminated"),
        "presents": m.get("presents_used"),
        "toolchain": m.get("toolchain_calls"),
        "regret": m.get("mean_regret_stmts"),
        "traj_final": ctx[-1] if ctx else None,
        "traj_peak": max(ctx) if ctx else None,
        "output": out, "reasoning": rea,
        "cumulative_in": sum(ctx) if ctx else None,
        "calls": len(calls), "cost": cost,
    }


def read_salvage(run_dir):
    p = f"{run_dir}-salvage/summary.json"
    if os.path.exists(p):
        s = json.load(open(p))
        return {"cleared": s["levels_completed"], "stop": "SALVAGED (log replay)",
                "terminated": s.get("terminated"), "presents": None,
                "toolchain": None, "regret": None, "traj_final": None,
                "traj_peak": None, "output": None, "reasoning": None,
                "cumulative_in": None, "calls": None, "cost": None}
    return None


def fmt(v, kind=""):
    if v is None:
        return "—"
    if kind == "tok":
        return f"{v:,}"
    if kind == "cost":
        return "—" if not v else f"${v:.2f}"  # prime-agent leaves cost unset
    if kind == "f":
        return f"{v:.2f}"
    return str(v)


def main():
    rows = []
    for model, harness, run_dir in RUNS:
        p = trace_path(run_dir)
        r = read_trace(p) if p else read_salvage(run_dir)
        rows.append((model, harness, r))

    print(f"\n{'run':22} {'cleared':>9} {'baseline':>9} {'stop':<18} "
          f"{'traj tokens':>12} {'peak':>10} {'output':>9} {'cost':>8}")
    print("-" * 104)
    for model, harness, r in rows:
        name = f"{model} · {harness}"
        base = BASELINE.get((model, harness))
        if r is None:
            print(f"{name:22} {'(running / no result yet)':>40}")
            continue
        print(f"{name:22} {fmt(r['cleared']):>9} {fmt(base):>9} "
              f"{(r['stop'] or '—'):<18} {fmt(r['traj_final'],'tok'):>12} "
              f"{fmt(r['traj_peak'],'tok'):>10} {fmt(r['output'],'tok'):>9} "
              f"{fmt(r['cost'],'cost'):>8}")
    print("\ntraj tokens = full lifetime trajectory (final context length); "
          "peak = max single-call context.")
    print("note: codex grows context monotonically (final == peak = whole "
          "trajectory); prime-agent compacts, so its final < peak.")
    print("presents/toolchain/regret and cumulative-input available per run:")
    for model, harness, r in rows:
        if r and r.get("calls"):
            print(f"  {model} · {harness}: {r['calls']} model calls · "
                  f"{fmt(r['presents'])} presents · {fmt(r['toolchain'])} "
                  f"toolchain · regret {fmt(r['regret'],'f')} stmts · "
                  f"cumulative input {fmt(r['cumulative_in'],'tok')} · "
                  f"reasoning {fmt(r['reasoning'],'tok')} tok")


if __name__ == "__main__":
    main()
