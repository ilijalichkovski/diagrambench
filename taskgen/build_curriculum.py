"""Assemble the 200-task curriculum and write diagrambench/curriculum/curriculum.json.

Run:  python3 -m taskgen.build_curriculum
"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from taskgen import stage1, stage2, stage3, stage4, stage5
from taskgen.builders import concepts_of

OUT = os.path.join(os.path.dirname(__file__), "..", "diagrambench",
                   "curriculum", "curriculum.json")

STAGES = [(1, stage1), (2, stage2), (3, stage3), (4, stage4), (5, stage5)]


def assemble():
    tasks = []
    seen_concepts = set()
    index = 0
    for stage_no, mod in STAGES:
        for t in mod.build():
            index += 1
            concepts = concepts_of(t["reference_program"])
            new = sorted(set(concepts) - seen_concepts)
            seen_concepts.update(concepts)
            tasks.append({
                "id": f"s{stage_no}-t{index:03d}",
                "stage": stage_no,
                "index": index,
                "instruction": t["instruction"],
                "datasets": t["datasets"],
                "hidden_goal": t["hidden_goal"],
                "reference_program": t["reference_program"],
                "required_concepts": concepts,
                "new_concepts": new,
                "difficulty": {
                    "concepts": len(concepts),
                    "ref_actions": len(t["reference_program"]),
                },
            })
    assert len(tasks) == 200, f"expected 200 tasks, got {len(tasks)}"
    return tasks


def main():
    tasks = assemble()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump({"version": 1, "tasks": tasks}, f, indent=1)
    n_new = sum(len(t["new_concepts"]) for t in tasks)
    print(f"wrote {len(tasks)} tasks ({n_new} concept introductions) to {OUT}")
    for s in range(1, 6):
        st = [t for t in tasks if t["stage"] == s]
        depths = [t["difficulty"]["concepts"] for t in st]
        print(f"  stage {s}: {len(st)} tasks, "
              f"concept depth {min(depths)}–{max(depths)}, "
              f"ref actions {min(t['difficulty']['ref_actions'] for t in st)}–"
              f"{max(t['difficulty']['ref_actions'] for t in st)}")


if __name__ == "__main__":
    main()
