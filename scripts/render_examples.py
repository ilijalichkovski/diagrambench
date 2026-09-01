"""Milestone 2 showcase: build five artifacts through the SDK and render SVGs.

Run:  python3 scripts/render_examples.py
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from glyphbench.sdk import TaskEnv
from glyphbench.render import render_env

OUT = os.path.join(os.path.dirname(__file__), "..", "examples")


def run(name, program):
    env = TaskEnv()
    for opname, args in program:
        obs = env.act(opname, args)
        if not obs["ok"]:
            print(f"  !! {name}: {opname}({args}) -> {obs['error']}")
            return None
    svg, warnings = render_env(env)
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, f"{name}.svg")
    with open(path, "w") as f:
        f.write(svg)
    print(f"  ok {name}.svg" + (f"  [warnings: {'; '.join(warnings)}]" if warnings else ""))
    return env


BAR = [
    ("sift", {"ledger": "quarterly_revenue", "vein": "region", "relation": "is",
              "value": "Europe"}),
    ("distill", {"ledger": "L1", "by": "quarter", "take": "revenue", "mode": "sum"}),
    ("carve", {"parcel": "p0", "along": "span", "ledger": "L2", "by": "quarter"}),
    ("sow", {"parcel": "p0", "ledger": "L2", "form": "slab", "key": "quarter"}),
    ("meter", {"brood": "b1", "trait": "stature", "vein": "revenue"}),
    ("weft", {"parcel": "p0", "along": "rise"}),
    ("rim", {"parcel": "p0", "side": "south"}),
    ("rim", {"parcel": "p0", "side": "west"}),
    ("entitle", {"parcel": "p0", "text": "European revenue by quarter"}),
]

GROUPED_BAR = [
    ("sift", {"ledger": "quarterly_revenue", "vein": "region", "relation": "is",
              "value": "Europe"}),
    ("carve", {"parcel": "p0", "along": "span", "ledger": "L1", "by": "quarter"}),
    ("sow", {"parcel": "p0", "ledger": "L1", "form": "slab", "key": "quarter"}),
    ("meter", {"brood": "b1", "trait": "stature", "vein": "revenue"}),
    ("meter", {"brood": "b1", "trait": "tint", "vein": "product"}),
    ("key", {"parcel": "p0", "brood": "b1", "trait": "tint"}),
    ("weft", {"parcel": "p0", "along": "rise"}),
    ("rim", {"parcel": "p0", "side": "south"}),
    ("rim", {"parcel": "p0", "side": "west"}),
    ("entitle", {"parcel": "p0", "text": "European revenue by quarter and product"}),
]

PIE = [
    ("hoop", {"parcel": "p0", "inner": 0.55}),
    ("sow", {"parcel": "p0", "ledger": "energy_mix", "form": "slab"}),
    ("meter", {"brood": "b1", "trait": "girth", "vein": "share"}),
    ("meter", {"brood": "b1", "trait": "tint", "vein": "source"}),
    ("badge", {"target": "b1", "vein": "source", "aim": "rim"}),
    ("entitle", {"parcel": "p0", "text": "Electricity generation mix"}),
]

LINE = [
    ("sow", {"parcel": "p0", "ledger": "monthly_finance", "form": "wisp"}),
    ("meter", {"brood": "b1", "trait": "stance", "vein": "period"}),
    ("meter", {"brood": "b1", "trait": "perch", "vein": "revenue"}),
    ("settle", {"parcel": "p0", "law": "strew"}),
    ("thread", {"brood": "b1", "by": "period"}),
    ("weft", {"parcel": "p0", "along": "rise"}),
    ("rim", {"parcel": "p0", "side": "south"}),
    ("rim", {"parcel": "p0", "side": "west"}),
    ("entitle", {"parcel": "p0", "text": "Monthly revenue over two years"}),
]

FLOW = [
    ("settle", {"parcel": "p0", "law": "current", "heading": "east"}),
    ("place", {"parcel": "p0", "form": "capsule", "name": "Submit"}),
    ("place", {"parcel": "p0", "form": "capsule", "name": "Validate"}),
    ("place", {"parcel": "p0", "form": "rhomb", "name": "Valid?"}),
    ("place", {"parcel": "p0", "form": "capsule", "name": "Process"}),
    ("place", {"parcel": "p0", "form": "capsule", "name": "Reject"}),
    ("place", {"parcel": "p0", "form": "capsule", "name": "Done"}),
    ("tether", {"tail": "Submit", "head": "Validate"}),
    ("tether", {"tail": "Validate", "head": "Valid?"}),
    ("tether", {"tail": "Valid?", "head": "Process"}),
    ("tether", {"tail": "Valid?", "head": "Reject"}),
    ("tether", {"tail": "Process", "head": "Done"}),
    ("badge", {"target": "c3", "text": "yes"}),
    ("badge", {"target": "c4", "text": "no"}),
    ("entitle", {"parcel": "p0", "text": "Order intake"}),
]

ARCH = [
    ("settle", {"parcel": "p0", "law": "current", "heading": "east"}),
    ("place", {"parcel": "p0", "form": "capsule", "name": "Users"}),
    ("place", {"parcel": "p0", "form": "capsule", "name": "Gateway"}),
    ("place", {"parcel": "p0", "form": "capsule", "name": "Payments"}),
    ("place", {"parcel": "p0", "form": "capsule", "name": "Orders"}),
    ("place", {"parcel": "p0", "form": "capsule", "name": "Search"}),
    ("place", {"parcel": "p0", "form": "drum", "name": "Ledger DB"}),
    ("place", {"parcel": "p0", "form": "drum", "name": "Vector store"}),
    ("tether", {"tail": "Users", "head": "Gateway"}),
    ("tether", {"tail": "Gateway", "head": "Payments"}),
    ("tether", {"tail": "Gateway", "head": "Orders"}),
    ("tether", {"tail": "Gateway", "head": "Search"}),
    ("tether", {"tail": "Payments", "head": "Ledger DB"}),
    ("tether", {"tail": "Orders", "head": "Ledger DB"}),
    ("tether", {"tail": "Search", "head": "Vector store"}),
    ("corral", {"members": ["Payments", "Orders", "Search"], "label": "Core"}),
    ("kindle", {"target": "c2"}),
    ("kindle", {"target": "Payments"}),
    ("entitle", {"parcel": "p0", "text": "Service architecture"}),
]

if __name__ == "__main__":
    print("rendering showcase examples:")
    run("bar", BAR)
    run("grouped_bar", GROUPED_BAR)
    run("pie", PIE)
    run("line", LINE)
    run("flow", FLOW)
    run("arch", ARCH)
