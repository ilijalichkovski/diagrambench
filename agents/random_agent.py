"""Random baseline agent: samples ops with loosely plausible arguments.

Almost always fails — it exists to calibrate the floor of the benchmark and
to exercise error paths.
"""

import random

from glyphbench.datasets import DATASETS
from glyphbench.scene import FORMS, LAWS, TRAITS
from glyphbench.sdk import OPS


class RandomAgent:
    def __init__(self, seed=11, actions_per_task=30):
        self.rng = random.Random(seed)
        self.actions_per_task = actions_per_task

    def _random_args(self, opdef):
        args = {}
        for prm in opdef.params:
            if not prm.required and self.rng.random() < 0.6:
                continue
            if prm.enum:
                args[prm.name] = self.rng.choice(prm.enum)
            elif "parcel" in prm.wtype:
                args[prm.name] = self.rng.choice(["p0", "p1", "p2"])
            elif "ledger" in prm.wtype:
                args[prm.name] = self.rng.choice(list(DATASETS) + ["L1"])
            elif "vein" in prm.wtype:
                ds = self.rng.choice(list(DATASETS.values()))
                args[prm.name] = self.rng.choice(list(ds[0].keys()))
            elif "brood" in prm.wtype:
                args[prm.name] = "b1"
            elif "glyph" in prm.wtype or "target" in prm.wtype or \
                    "ref" in prm.wtype:
                args[prm.name] = self.rng.choice(["g1", "g2", "b1", "c1"])
            elif "number" in prm.wtype:
                args[prm.name] = round(self.rng.uniform(0, 1), 2)
            elif "text" in prm.wtype:
                args[prm.name] = self.rng.choice(["node", "note", "peak"])
            elif "list" in prm.wtype:
                args[prm.name] = ["g1", "g2"]
            else:
                args[prm.name] = self.rng.choice(FORMS + LAWS + TRAITS)
        return args

    def run(self, session, act):
        names = [n for n in OPS if n not in ("present", "restart")]
        while not session.finished:
            before = session.task_idx
            # keep trying until the session advances the task (success is
            # ~impossible; the per-task action/present caps force it)
            while session.task_idx == before and not session.finished:
                for _ in range(self.actions_per_task):
                    op = self.rng.choice(names)
                    act(op, self._random_args(OPS[op]))
                    if session.task_idx != before or session.finished:
                        break
                if session.task_idx == before and not session.finished:
                    act("present", {})
