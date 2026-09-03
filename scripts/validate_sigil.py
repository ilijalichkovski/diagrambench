"""Gold-validate the SIGIL port: transpile each reference program, compile,
execute, verify — sequentially, like a real lifetime.

Run:  .venv/bin/python scripts/validate_sigil.py [N | all] [--show K]
"""

import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..",
                                "environments", "diagrambench-v1"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from diagrambench.tasks import load_curriculum
from diagrambench_v1.core.project_engine import dataset_tsv
from diagrambench_v1.core.sigil_exec import execute
from diagrambench_v1.core.sigil_lower import compile_project
from diagrambench_v1.core.verify import verify
from diagrambench_v1.transpile import transpile


def datadir(task):
    d = tempfile.mkdtemp(prefix="sigil-gold-")
    os.makedirs(os.path.join(d, "data"), exist_ok=True)
    for name in task["datasets"]:
        with open(os.path.join(d, "data", f"{name}.tsv"), "w") as f:
            f.write(dataset_tsv(name))
    return d


def main():
    arg = sys.argv[1] if len(sys.argv) > 1 else "10"
    n = 200 if arg == "all" else int(arg)
    show = None
    if "--show" in sys.argv:
        show = int(sys.argv[sys.argv.index("--show") + 1])
    tasks = load_curriculum()[:n]
    bad = 0
    stmt_total = 0
    for t in tasks:
        try:
            units = transpile(t["reference_program"])
        except Exception as e:
            bad += 1
            print(f"FAIL {t['id']}  transpile: {type(e).__name__}: {e}")
            continue
        if show == t["index"]:
            for path, src in sorted(units.items()):
                print(f"───── {path} ─────")
                print(src)
        try:
            ir, stats = compile_project(units)
        except Exception as e:
            bad += 1
            print(f"FAIL {t['id']}  compile: {e}")
            continue
        try:
            env, _ = execute(ir, datadir(t))
        except Exception as e:
            bad += 1
            print(f"FAIL {t['id']}  execute: {e}")
            continue
        r = verify(env, t["hidden_goal"])
        if not r["success"]:
            bad += 1
            print(f"FAIL {t['id']}  verify sem={r['semantic_score']} "
                  f"lay={r['layout_score']}: {r['failed'][:3]}")
            continue
        stmt_total += stats["statements"]
    ok = len(tasks) - bad
    print(f"\n{ok}/{len(tasks)} transpiled SIGIL projects verify "
          f"(mean {stmt_total / max(ok, 1):.1f} statements each).")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
