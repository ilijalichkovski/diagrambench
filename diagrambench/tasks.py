"""Task schema and curriculum loading.

A task:
{
  "id": "s1-t003",
  "stage": 1,
  "index": 3,                     # 1-based lifetime position
  "instruction": "...",           # ONLY thing the agent sees (plus bootstrap)
  "datasets": ["quarterly_revenue"],
  "hidden_goal": {"checks": [...], "min_semantic": 1.0},
  "reference_program": [[op, args], ...],   # evaluator metadata
  "required_concepts": [...],
  "new_concepts": [...],
  "difficulty": {"concepts": n, "ref_actions": m}
}

The agent must never see hidden_goal / reference_program / *_concepts.
"""

import json
import os

CURRICULUM_PATH = os.path.join(os.path.dirname(__file__), "curriculum",
                               "curriculum.json")

AGENT_VISIBLE_FIELDS = ("id", "stage", "index", "instruction", "datasets")


def load_curriculum(path=None):
    with open(path or CURRICULUM_PATH) as f:
        data = json.load(f)
    tasks = data["tasks"]
    assert [t["index"] for t in tasks] == list(range(1, len(tasks) + 1))
    return tasks


def agent_view(task):
    return {k: task[k] for k in AGENT_VISIBLE_FIELDS if k in task}


def ref_cost(task):
    return len(task["reference_program"])
