"""Lifetime session: one agent, one instrument, a sequence of tasks.

Owns per-task environments, verification on present(), and all lifetime
logging (actions, task summaries, per-primitive exposure history).
"""

import json
import os
import time

from .sdk import OPS, TaskEnv, BOOTSTRAP
from .tasks import agent_view, ref_cost
from .verify import verify

INTROSPECTION_OPS = {"families", "ops", "sig", "forms", "shelf", "peek",
                     "veins", "census", "study", "trace"}

MAX_ACTIONS_PER_TASK = 160
MAX_PRESENTS_PER_TASK = 8


class Session:
    def __init__(self, tasks, run_dir=None, agent_name="agent", pace=None,
                 on_event=None):
        self.tasks = tasks
        self.agent_name = agent_name
        self.pace = pace
        self.on_event = on_event
        self.run_dir = run_dir
        self.task_idx = 0  # 0-based into tasks
        self.env = TaskEnv()
        self.counts = self._fresh_counts()
        self.results = []      # per-task summaries
        self.exposures = {}    # concept -> {"first": idx, "seen": n}
        self.finished = False
        if run_dir:
            os.makedirs(run_dir, exist_ok=True)
            self._actions_f = open(os.path.join(run_dir, "actions.jsonl"), "a")
            self._tasks_f = open(os.path.join(run_dir, "tasks.jsonl"), "a")
        else:
            self._actions_f = self._tasks_f = None

    def _fresh_counts(self):
        return {"total": 0, "mutating": 0, "failed": 0, "introspection": 0,
                "undo": 0, "presents": 0}

    # ------------------------------------------------------------------
    @property
    def task(self):
        if self.task_idx < len(self.tasks):
            return self.tasks[self.task_idx]
        return None

    def bootstrap_text(self):
        return BOOTSTRAP

    def instruction(self):
        t = self.task
        return t["instruction"] if t else None

    def _log(self, f, obj):
        if f:
            f.write(json.dumps(obj) + "\n")
            f.flush()

    def _emit(self, kind, payload):
        if self.on_event:
            self.on_event(kind, payload)

    # ------------------------------------------------------------------
    def act(self, opname, args=None):
        """One environment action by the agent. Returns the observation dict;
        on present() it also carries 'verdict' (and advances on success)."""
        if self.finished or self.task is None:
            return {"ok": False, "error": "the lifetime is complete.",
                    "mutated": False}
        t = self.task
        obs = self.env.act(opname, args)
        c = self.counts
        c["total"] += 1
        if not obs["ok"]:
            c["failed"] += 1
        if opname in INTROSPECTION_OPS:
            c["introspection"] += 1
        if opname == "undo":
            c["undo"] += 1
        if obs.get("mutated"):
            c["mutating"] += 1

        self._log(self._actions_f, {
            "task": t["id"], "index": t["index"], "n": c["total"],
            "op": opname, "args": args or {}, "ok": obs["ok"],
            "error": obs.get("error"), "ts": round(time.time(), 3),
        })

        if obs.get("present"):
            c["presents"] += 1
            verdict = self._verify(t)
            obs["verdict"] = verdict
            self._emit("present", {"task": t, "verdict": verdict})
            if verdict["success"]:
                self._finish_task(verdict, forced=False)
            elif c["presents"] >= MAX_PRESENTS_PER_TASK or \
                    c["total"] >= MAX_ACTIONS_PER_TASK:
                self._finish_task(verdict, forced=True)
        elif c["total"] >= MAX_ACTIONS_PER_TASK:
            verdict = self._verify(t)
            obs["verdict"] = verdict
            obs["forced"] = True
            self._finish_task(verdict, forced=True)
        else:
            self._emit("action", {"task": t, "obs": obs})
        return obs

    def _verify(self, t):
        try:
            return verify(self.env, t["hidden_goal"])
        except Exception as e:  # a broken scene is a failed artifact
            return {"success": False, "semantic_score": 0.0,
                    "layout_score": 0.0, "passed": [],
                    "failed": [f"artifact could not be judged "
                               f"({type(e).__name__})"],
                    "presentation": {}}

    # ------------------------------------------------------------------
    def _finish_task(self, verdict, forced):
        t = self.task
        c = self.counts
        ref = ref_cost(t)
        # actions spent constructing (present calls excluded from regret cost)
        spent = c["total"] - c["presents"]
        summary = {
            "id": t["id"], "index": t["index"], "stage": t["stage"],
            "success": verdict["success"] and not forced,
            "forced": forced,
            "semantic_score": verdict["semantic_score"],
            "layout_score": verdict["layout_score"],
            "failed_checks": verdict["failed"],
            "actions": c["total"],
            "construct_actions": spent,
            "mutating": c["mutating"],
            "failed_calls": c["failed"],
            "introspection": c["introspection"],
            "undo": c["undo"],
            "presents": c["presents"],
            "ref_cost": ref,
            "regret": spent - ref,
            "required_concepts": t.get("required_concepts", []),
            "new_concepts": t.get("new_concepts", []),
        }
        for concept in t.get("required_concepts", []):
            e = self.exposures.setdefault(concept,
                                          {"first": t["index"], "seen": 0})
            e["seen"] += 1
        self.results.append(summary)
        self._log(self._tasks_f, summary)
        self._emit("task_done", {"task": t, "summary": summary})
        self.task_idx += 1
        self.env = TaskEnv()
        self.counts = self._fresh_counts()
        if self.task_idx >= len(self.tasks):
            self.finished = True
            self._write_exposures()
            self._emit("lifetime_done", {"results": self.results})
        else:
            self._emit("task_start", {"task": self.task})

    def _write_exposures(self):
        if self.run_dir:
            with open(os.path.join(self.run_dir, "exposures.json"), "w") as f:
                json.dump(self.exposures, f, indent=1, sort_keys=True)

    # ------------------------------------------------------------------
    def lifetime_stats(self):
        done = self.results
        n = len(done)
        succ = sum(1 for r in done if r["success"])
        return {
            "tasks_done": n,
            "tasks_total": len(self.tasks),
            "successes": succ,
            "success_rate": round(succ / n, 3) if n else None,
            "mean_regret": round(sum(r["regret"] for r in done) / n, 2)
            if n else None,
            "recent_regret": round(
                sum(r["regret"] for r in done[-20:]) / min(n, 20), 2)
            if n else None,
        }

    def state_view(self):
        """Everything the viewer needs about 'now'."""
        t = self.task
        return {
            "agent": self.agent_name,
            "task": agent_view(t) if t else None,
            "counts": dict(self.counts),
            "ref_cost": ref_cost(t) if t else None,
            "stats": self.lifetime_stats(),
            "finished": self.finished,
        }

    def close(self):
        for f in (self._actions_f, self._tasks_f):
            if f:
                f.close()
