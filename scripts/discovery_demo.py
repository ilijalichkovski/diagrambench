"""Milestone 3: a fresh agent experimentally infers a primitive (`carve`)
using nothing but the bootstrap interface, weak signatures and errors.

The transcript below is exactly what a language-only agent would see.

Run:  python3 scripts/discovery_demo.py
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from diagrambench.sdk import BOOTSTRAP, TaskEnv


def main():
    env = TaskEnv()
    print("=" * 72)
    print(BOOTSTRAP)
    print("=" * 72)
    steps = [
        # 1. what exists?
        ("families", {}),
        ("ops", {"family": "ground"}),
        # 2. what does carve take?
        ("sig", {"op": "carve"}),
        # 3. what data is around?
        ("shelf", {}),
        ("veins", {"ledger": "quarterly_revenue"}),
        # 4. first attempt — wrong enum, the error reveals the options
        ("carve", {"parcel": "p0", "along": "width",
                   "ledger": "quarterly_revenue", "by": "quarter"}),
        # 5. second attempt — counted vein, the error reveals the constraint
        ("carve", {"parcel": "p0", "along": "span",
                   "ledger": "quarterly_revenue", "by": "revenue"}),
        # 6. third attempt — success; the observation reveals the effect
        ("carve", {"parcel": "p0", "along": "span",
                   "ledger": "quarterly_revenue", "by": "quarter"}),
        # 7. inspect the consequence
        ("census", {}),
        ("study", {"ref": "p0"}),
        # 8. hypothesis check: can a carved parcel be carved again?
        ("carve", {"parcel": "p0", "along": "rise",
                   "ledger": "quarterly_revenue", "by": "product"}),
        # 9. ...no, but its cells can. The grammar begins to reveal itself.
        ("carve", {"parcel": "p1", "along": "rise",
                   "ledger": "quarterly_revenue", "by": "product"}),
        ("census", {}),
    ]
    for op, args in steps:
        argstr = ", ".join(f"{k}={v!r}" for k, v in args.items())
        print(f"\nagent> {op}({argstr})")
        obs = env.act(op, args)
        text = obs.get("text") or obs.get("error")
        print("\n".join("  " + line for line in text.split("\n")))
    print("\n--- inference: carve(parcel, along, ledger, by) partitions a "
          "parcel into one cell per level of a discrete vein; cells are "
          "parcels and can be carved again; a parcel carves only once. ---")


if __name__ == "__main__":
    main()
