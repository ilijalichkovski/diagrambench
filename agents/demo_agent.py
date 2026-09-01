"""Scripted demo agent.

Replays each task's reference program with exploration noise that decays over
the lifetime and spikes when a task introduces never-seen concepts. This is an
evaluator-side *simulator* of the intended learning trajectory (novice →
expert) used to demo the viewer and exercise the logging — it reads task
metadata a real agent never sees. Deterministic given a seed.
"""

import random

INTROSPECTION_FOR = {
    "carve": [("ops", {"family": "ground"}), ("sig", {"op": "carve"})],
    "sow": [("ops", {"family": "sowing"}), ("sig", {"op": "sow"}),
            ("forms", {})],
    "meter": [("sig", {"op": "meter"})],
    "settle": [("sig", {"op": "settle"})],
    "tether": [("ops", {"family": "cords"}), ("sig", {"op": "tether"})],
    "thread": [("sig", {"op": "thread"})],
    "hoop": [("sig", {"op": "hoop"})],
    "pipe": [("ops", {"family": "cords"}), ("sig", {"op": "pipe"})],
    "nest": [("sig", {"op": "nest"})],
    "loosen": [("sig", {"op": "loosen"})],
    "distill": [("ops", {"family": "ledgers"}), ("sig", {"op": "distill"})],
    "sift": [("sig", {"op": "sift"})],
    "corral": [("sig", {"op": "corral"})],
    "split": [("sig", {"op": "split"})],
}

BOTCHES = {
    "carve": [("carve", lambda a: {**a, "along": "sideways"}),
              ("carve", lambda a: {k: v for k, v in a.items() if k != "by"})],
    "sow": [("sow", lambda a: {k: v for k, v in a.items() if k != "key"})],
    "meter": [("meter", lambda a: {**a, "trait": "height"})],
    "settle": [("settle", lambda a: {**a, "law": "grid"})],
    "sift": [("sift", lambda a: {**a, "relation": "equals"})],
    "distill": [("distill", lambda a: {**a, "mode": "total"})],
    "hoop": [("hoop", lambda a: {**a, "inner": 2})],
    "pipe": [("pipe", lambda a: {k: v for k, v in a.items()
                                 if k != "width"})],
}


class DemoAgent:
    def __init__(self, seed=7, noise="auto"):
        self.rng = random.Random(seed)
        self.noise = noise
        self.seen = set()

    def _explore_prob(self, task):
        if self.noise == "none":
            return 0.0
        idx = task["index"]
        base = max(0.03, 0.85 * (0.93 ** idx))
        new = set(task.get("new_concepts", []))
        if new:
            base = min(0.95, base + 0.18 * len(new))
        return base

    def run_task(self, session, act):
        task = session.task
        if task is None:
            return
        p = self._explore_prob(task)
        first_ops = []
        if self.rng.random() < p:
            act("families", {})
            act("shelf", {})
        for opname, args in task["reference_program"]:
            fresh = opname not in self.seen
            if fresh and opname in INTROSPECTION_FOR and \
                    self.rng.random() < max(p, 0.3 if fresh else 0):
                for iop, iargs in INTROSPECTION_FOR[opname]:
                    act(iop, iargs)
            if self.rng.random() < p * 0.5 and opname in BOTCHES:
                bop, mut = self.rng.choice(BOTCHES[opname])
                act(bop, mut(dict(args)))
            act(opname, args)
            if self.rng.random() < p * 0.12:
                act("census", {})
            self.seen.add(opname)
        act("present", {})

    def run(self, session, act):
        while not session.finished:
            before = session.task_idx
            self.run_task(session, act)
            if session.task_idx == before:
                # present was rejected (shouldn't happen with reference
                # programs) — restart the task once, then replay cleanly
                act("restart", {})
                for opname, args in session.task["reference_program"]:
                    act(opname, args)
                act("present", {})
                if session.task_idx == before:
                    break
