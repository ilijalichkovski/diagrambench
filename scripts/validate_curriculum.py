"""Execute every task's reference program and require verified success.

Run:  python3 scripts/validate_curriculum.py [--render]
--render also writes each task's final SVG to examples/curriculum/.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from glyphbench.sdk import TaskEnv
from glyphbench.tasks import load_curriculum
from glyphbench.verify import verify


def run_program(program):
    env = TaskEnv()
    errors = []
    for opname, args in program:
        obs = env.act(opname, args)
        if not obs["ok"]:
            errors.append(f"{opname}({args}) -> {obs['error']}")
    return env, errors


def main():
    render = "--render" in sys.argv
    tasks = load_curriculum()
    bad = 0
    outdir = os.path.join(os.path.dirname(__file__), "..", "examples",
                          "curriculum")
    if render:
        os.makedirs(outdir, exist_ok=True)
    for t in tasks:
        env, errors = run_program(t["reference_program"])
        r = verify(env, t["hidden_goal"])
        ok = r["success"] and not errors
        if not ok:
            bad += 1
            print(f"FAIL {t['id']}  semantic={r['semantic_score']} "
                  f"layout={r['layout_score']}")
            for e in errors:
                print(f"   op error: {e}")
            for fchk in r["failed"]:
                print(f"   failed check: {fchk}")
        if render:
            from glyphbench.render import render_env
            svg, _ = render_env(env)
            with open(os.path.join(outdir, f"{t['id']}.svg"), "w") as f:
                f.write(svg)
    print(f"\n{len(tasks) - bad}/{len(tasks)} reference programs verify "
          f"successfully.")
    if bad:
        sys.exit(1)


if __name__ == "__main__":
    main()
