"""DiagramBench test suite (stdlib unittest).

Run:  python3 -m unittest discover tests -v
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from diagrambench.ledgers import LedgerSpace
from diagrambench.render import render_env
from diagrambench.sdk import OPS, TaskEnv
from diagrambench.session import Session
from diagrambench.tasks import agent_view, load_curriculum
from diagrambench.verify import apply_transform, rows_match, verify


def run(env, program):
    out = []
    for op, args in program:
        out.append(env.act(op, args))
    return out


BAR_PROGRAM = [
    ("sift", {"ledger": "quarterly_revenue", "vein": "region",
              "relation": "is", "value": "Europe"}),
    ("carve", {"parcel": "p0", "along": "span", "ledger": "L1",
               "by": "quarter"}),
    ("sow", {"parcel": "p0", "ledger": "L1", "form": "slab",
             "key": "quarter"}),
    ("meter", {"brood": "b1", "trait": "stature", "vein": "revenue"}),
    ("rim", {"parcel": "p0", "side": "south"}),
]


class TestLedgers(unittest.TestCase):
    def test_sift_distill(self):
        ls = LedgerSpace()
        led = ls.sift("quarterly_revenue", "region", "is", "Europe")
        self.assertEqual(len(led.rows), 12)
        agg = ls.distill(led.ref, "quarter", "revenue", "sum")
        self.assertEqual(len(agg.rows), 4)
        q1 = [r for r in agg.rows if r["quarter"] == "Q1"][0]
        self.assertEqual(q1["revenue"], 42 + 30 + 21)

    def test_bin_covers_all_rows(self):
        ls = LedgerSpace()
        led = ls.bin("ticket_resolution", "hours", 8)
        self.assertEqual(sum(r["tally"] for r in led.rows), 40)

    def test_derive_total_share(self):
        ls = LedgerSpace()
        led = ls.derive("browser_share", "pct", "total_share", "share")
        self.assertAlmostEqual(sum(r["pct"] for r in led.rows), 100.0, 3)

    def test_rows_match_is_order_free(self):
        a = apply_transform("energy_mix", [])
        self.assertTrue(rows_match(a, list(reversed(a))))
        self.assertFalse(rows_match(a, a[:-1]))


class TestSDK(unittest.TestCase):
    def test_errors_reveal_constraints_not_purpose(self):
        env = TaskEnv()
        obs = env.act("carve", {"parcel": "p0", "along": "span",
                                "ledger": "quarterly_revenue",
                                "by": "revenue"})
        self.assertFalse(obs["ok"])
        self.assertIn("told or ranked", obs["error"])
        self.assertNotIn("group", obs["error"].lower())
        obs = env.act("settle", {"parcel": "p0", "law": "grid"})
        self.assertIn("abreast", obs["error"])

    def test_keyed_sow_required_on_carved_parcel(self):
        env = TaskEnv()
        env.act("carve", {"parcel": "p0", "along": "span",
                          "ledger": "quarterly_revenue", "by": "quarter"})
        obs = env.act("sow", {"parcel": "p0",
                              "ledger": "quarterly_revenue", "form": "slab"})
        self.assertFalse(obs["ok"])
        self.assertIn("key", obs["error"])

    def test_undo_restores_scene_and_ledgers(self):
        env = TaskEnv()
        run(env, BAR_PROGRAM[:3])
        self.assertEqual(len(env.scene.glyphs), 12)
        env.act("undo", {})
        self.assertEqual(len(env.scene.glyphs), 0)
        self.assertIn("L1", env.ledgers.derived)
        env.act("undo", {})
        env.act("undo", {})
        self.assertNotIn("L1", env.ledgers.derived)

    def test_every_op_has_signature(self):
        env = TaskEnv()
        for name in OPS:
            obs = env.act("sig", {"op": name})
            self.assertTrue(obs["ok"], name)

    def test_deterministic_rendering(self):
        svgs = []
        for _ in range(2):
            env = TaskEnv()
            run(env, BAR_PROGRAM)
            svgs.append(render_env(env)[0])
        self.assertEqual(svgs[0], svgs[1])
        self.assertIn("<svg", svgs[0])


class TestVerifier(unittest.TestCase):
    GOAL = {"checks": [
        {"check": "brood", "weight": 5, "where": {
            "form": "slab",
            "data": {"from": "quarterly_revenue",
                     "transform": [["sift", "region", "is", "Europe"]]},
            "meter": {"stature": "revenue"},
            "in": {"carved_by": "quarter"}}},
        {"check": "guide", "kind": "rim", "side": "south"},
    ]}

    def test_correct_scene_passes(self):
        env = TaskEnv()
        run(env, BAR_PROGRAM)
        r = verify(env, self.GOAL)
        self.assertTrue(r["success"])
        self.assertEqual(r["semantic_score"], 1.0)

    def test_alternate_orientation_passes(self):
        env = TaskEnv()
        prog = [p if p[0] != "carve" else
                ("carve", {**p[1], "along": "rise"}) for p in BAR_PROGRAM]
        run(env, prog)
        self.assertTrue(verify(env, self.GOAL)["success"])

    def test_wrong_data_fails(self):
        env = TaskEnv()
        prog = list(BAR_PROGRAM)
        prog[0] = ("sift", {"ledger": "quarterly_revenue", "vein": "region",
                            "relation": "is", "value": "Asia"})
        run(env, prog)
        r = verify(env, self.GOAL)
        self.assertFalse(r["success"])
        self.assertIn("brood: correct data", r["failed"])


class TestCurriculum(unittest.TestCase):
    def test_loads_200_staged_tasks(self):
        tasks = load_curriculum()
        self.assertEqual(len(tasks), 200)
        stages = [t["stage"] for t in tasks]
        self.assertEqual(stages, sorted(stages))
        self.assertEqual(stages.count(1), 25)

    def test_agent_view_hides_evaluator_metadata(self):
        t = load_curriculum()[0]
        view = agent_view(t)
        for hidden in ("hidden_goal", "reference_program",
                       "required_concepts", "new_concepts"):
            self.assertNotIn(hidden, view)
        self.assertIn("instruction", view)

    def test_concept_introduction_is_staged(self):
        tasks = load_curriculum()
        stage1_new = sum(len(t["new_concepts"]) for t in tasks
                         if t["stage"] == 1)
        self.assertGreater(stage1_new, 30)
        late_new = [t for t in tasks if t["stage"] == 5 and
                    "pipe" in t["new_concepts"]]
        self.assertEqual(len(late_new), 1)  # plasticity probe


class TestSession(unittest.TestCase):
    def test_lifetime_accounting(self):
        tasks = load_curriculum()[:2]
        tasks = [dict(t, index=i + 1) for i, t in enumerate(tasks)]
        s = Session(tasks)
        s.act("census", {})   # exploration
        for op, args in tasks[0]["reference_program"]:
            s.act(op, args)
        obs = s.act("present", {})
        self.assertTrue(obs["verdict"]["success"])
        self.assertEqual(s.task_idx, 1)
        r = s.results[0]
        self.assertEqual(r["regret"], 1)  # one census beyond reference
        self.assertEqual(r["introspection"], 1)
        self.assertTrue(r["success"])


if __name__ == "__main__":
    unittest.main()
