"""Lifetime report: turn a run's tasks.jsonl into learning-curve tables.

Run:  python3 scripts/report.py runs/demo
Writes runs/<dir>/lifetime.csv and prints windowed curves.
"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def load(run_dir):
    rows = []
    with open(os.path.join(run_dir, "tasks.jsonl")) as f:
        for line in f:
            rows.append(json.loads(line))
    return rows


def main():
    run_dir = sys.argv[1] if len(sys.argv) > 1 else "runs/demo"
    rows = load(run_dir)
    csv_path = os.path.join(run_dir, "lifetime.csv")
    with open(csv_path, "w") as f:
        f.write("index,stage,success,semantic,layout,actions,ref_cost,"
                "regret,introspection,failed_calls,undo,new_concepts\n")
        for r in rows:
            f.write(f"{r['index']},{r['stage']},{int(r['success'])},"
                    f"{r['semantic_score']},{r['layout_score']},"
                    f"{r['actions']},{r['ref_cost']},{r['regret']},"
                    f"{r['introspection']},{r['failed_calls']},{r['undo']},"
                    f"{len(r['new_concepts'])}\n")

    W = 20
    print(f"{len(rows)} tasks · report written to {csv_path}\n")
    print("window     success   mean regret   introspection   failed calls")
    for i in range(0, len(rows), W):
        w = rows[i:i + W]
        sr = sum(1 for r in w if r["success"]) / len(w)
        mr = sum(r["regret"] for r in w) / len(w)
        mi = sum(r["introspection"] for r in w) / len(w)
        mf = sum(r["failed_calls"] for r in w) / len(w)
        print(f"{i+1:>3}-{i+len(w):<5}  {sr:>6.0%}   {mr:>11.2f}   "
              f"{mi:>13.2f}   {mf:>12.2f}")

    # discovery cost each time a task introduces new concepts
    print("\nconcept introductions (discovery cost = regret on that task):")
    for r in rows:
        if r["new_concepts"]:
            names = ", ".join(r["new_concepts"][:5])
            more = "…" if len(r["new_concepts"]) > 5 else ""
            print(f"  task {r['index']:>3} (stage {r['stage']}): "
                  f"regret {r['regret']:>3}  ← {names}{more}")

    # retention: concepts reused after a ≥50-task gap
    last_seen = {}
    print("\nretention probes (concept reused after a 50+ task gap):")
    for r in rows:
        for c in r["required_concepts"]:
            if c in last_seen and r["index"] - last_seen[c] >= 50:
                print(f"  task {r['index']:>3}: '{c}' after "
                      f"{r['index'] - last_seen[c]}-task gap "
                      f"(regret {r['regret']})")
            last_seen[c] = r["index"]


if __name__ == "__main__":
    main()
