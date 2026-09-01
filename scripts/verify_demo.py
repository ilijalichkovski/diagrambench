"""Milestone 4 demonstration:
  - the canonical program passes,
  - an alternate valid construction (different order, horizontal bars) passes,
  - semantically wrong but visually similar artifacts fail with named reasons.

Run:  python3 scripts/verify_demo.py
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from glyphbench.sdk import TaskEnv
from glyphbench.verify import verify

GOAL = {"checks": [
    {"check": "brood", "weight": 6, "where": {
        "form": "slab",
        "data": {"from": "quarterly_revenue",
                 "transform": [["sift", "region", "is", "Europe"]]},
        "meter": {"stature": "revenue", "tint": "product"},
        "in": {"carved_by": "quarter", "law": "abreast"}}},
    {"check": "guide", "kind": "key", "trait": "tint"},
    {"check": "emphasis", "mode": "kindle", "exclusive": True,
     "target": {"where": {"quarter": "Q3", "product": "Breeze"}}},
    {"check": "annotation", "text_has": "peak",
     "near": {"where": {"quarter": "Q3", "product": "Breeze"}}},
]}


def build(mutations=()):
    env = TaskEnv()
    prog = [
        ("sift", {"ledger": "quarterly_revenue", "vein": "region",
                  "relation": "is", "value": "Europe"}),
        ("carve", {"parcel": "p0", "along": "span", "ledger": "L1",
                   "by": "quarter"}),
        ("sow", {"parcel": "p0", "ledger": "L1", "form": "slab",
                 "key": "quarter"}),
        ("meter", {"brood": "b1", "trait": "stature", "vein": "revenue"}),
        ("meter", {"brood": "b1", "trait": "tint", "vein": "product"}),
        ("key", {"parcel": "p0", "brood": "b1", "trait": "tint"}),
        ("pick", {"brood": "b1", "vein": "quarter", "relation": "is",
                  "value": "Q3"}),
        ("pick", {"brood": "f1", "vein": "product", "relation": "is",
                  "value": "Breeze"}),
        ("kindle", {"target": "f2"}),
        ("inscribe", {"text": "Peak quarter", "near": "f2"}),
        ("rim", {"parcel": "p0", "side": "south"}),
        ("rim", {"parcel": "p0", "side": "west"}),
    ]
    for m in dict(mutations).items():
        idx, repl = m
        prog[idx] = repl
    for opname, args in prog:
        obs = env.act(opname, args)
        if not obs["ok"]:
            print(f"    (op refused: {obs['error']})")
    return env


def show(name, env):
    r = verify(env, GOAL)
    status = "PASS" if r["success"] else "FAIL"
    print(f"{status}  {name}  semantic={r['semantic_score']:.2f} "
          f"layout={r['layout_score']:.2f}")
    for f in r["failed"]:
        print(f"      failed: {f}")


if __name__ == "__main__":
    show("canonical grouped bars", build())

    # alternate valid: carve along rise (horizontal bars) + sift AFTER carve
    env = TaskEnv()
    for opname, args in [
        ("carve", {"parcel": "p0", "along": "rise",
                   "ledger": "quarterly_revenue", "by": "quarter"}),
        ("sift", {"ledger": "quarterly_revenue", "vein": "region",
                  "relation": "is", "value": "Europe"}),
        ("sow", {"parcel": "p0", "ledger": "L1", "form": "slab",
                 "key": "quarter"}),
        ("meter", {"brood": "b1", "trait": "stature", "vein": "revenue"}),
        ("meter", {"brood": "b1", "trait": "tint", "vein": "product"}),
        ("key", {"parcel": "p0", "brood": "b1", "trait": "tint"}),
        ("pick", {"brood": "b1", "vein": "quarter", "relation": "is",
                  "value": "Q3"}),
        ("pick", {"brood": "f1", "vein": "product", "relation": "is",
                  "value": "Breeze"}),
        ("kindle", {"target": "f2"}),
        ("flag", {"target": "f2", "text": "peak quarter"}),
        ("rim", {"parcel": "p0", "side": "south"}),
        ("rim", {"parcel": "p0", "side": "west"}),
    ]:
        obs = env.act(opname, args)
        if not obs["ok"]:
            print(f"    (op refused: {obs['error']})")
    show("alternate valid (horizontal, flag, different op order)", env)

    show("wrong data (Americas instead of Europe)", build({
        0: ("sift", {"ledger": "quarterly_revenue", "vein": "region",
                     "relation": "is", "value": "Americas"})}))
    show("wrong grouping (carved by product)", build({
        1: ("carve", {"parcel": "p0", "along": "span", "ledger": "L1",
                      "by": "product"}),
        2: ("sow", {"parcel": "p0", "ledger": "L1", "form": "slab",
                    "key": "product"})}))
    show("wrong emphasis (kindled Aria Q3)", build({
        7: ("pick", {"brood": "f1", "vein": "product", "relation": "is",
                     "value": "Aria"})}))
    show("missing annotation", build({
        9: ("inscribe", {"text": "Peak quarter"})}))
