#!/usr/bin/env python3
"""DiagramBench runner.

Examples:
  # watch the demo agent learn the instrument across the whole curriculum
  python3 run_benchmark.py --agent demo --serve --pace 0.35

  # headless full lifetime with logs
  python3 run_benchmark.py --agent demo --run-dir runs/demo --pace 0

  # serve an idle session and drive it yourself via POST /api/act
  python3 run_benchmark.py --agent none --serve

  # random baseline over the first 40 tasks
  python3 run_benchmark.py --agent random --tasks 1-40 --run-dir runs/random
"""

import argparse
import threading
import time
import webbrowser

from diagrambench.session import Session
from diagrambench.tasks import load_curriculum


def parse_range(spec, n):
    if not spec:
        return 0, n
    a, _, b = spec.partition("-")
    return max(int(a) - 1, 0), min(int(b or a), n)


def main():
    ap = argparse.ArgumentParser(description="Run DiagramBench")
    ap.add_argument("--agent", default="none",
                    choices=["demo", "random", "none"])
    ap.add_argument("--tasks", default=None, help="e.g. 1-25")
    ap.add_argument("--serve", action="store_true")
    ap.add_argument("--port", type=int, default=8321)
    ap.add_argument("--pace", type=float, default=0.35,
                    help="seconds between agent actions (0 = flat out)")
    ap.add_argument("--run-dir", default=None)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--noise", default="auto", choices=["auto", "none"])
    ap.add_argument("--open", action="store_true", help="open the browser")
    args = ap.parse_args()

    tasks = load_curriculum()
    lo, hi = parse_range(args.tasks, len(tasks))
    tasks = tasks[lo:hi]
    for i, t in enumerate(tasks):  # reindex the slice as its own lifetime
        t = dict(t)
        t["index"] = i + 1
        tasks[i] = t

    session = Session(tasks, run_dir=args.run_dir,
                      agent_name=args.agent)

    hub = None
    if args.serve:
        from diagrambench.server import EventHub, serve
        hub = EventHub(session)
        httpd = serve(hub, args.port)
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
        if args.open:
            webbrowser.open(f"http://127.0.0.1:{args.port}")

    def act(op, a=None):
        obs = hub.act(op, a) if hub else session.act(op, a)
        if args.pace:
            time.sleep(args.pace)
        return obs

    if args.agent == "demo":
        from agents.demo_agent import DemoAgent
        agent = DemoAgent(seed=args.seed, noise=args.noise)
    elif args.agent == "random":
        from agents.random_agent import RandomAgent
        agent = RandomAgent(seed=args.seed)
    else:
        agent = None

    if agent:
        def run_agent():
            agent.run(session, act)
            stats = session.lifetime_stats()
            print(f"lifetime complete: {stats}")
            session.close()
        if args.serve:
            threading.Thread(target=run_agent, daemon=True).start()
        else:
            run_agent()
            return

    if args.serve:
        print("(ctrl-c to stop)")
        try:
            while True:
                time.sleep(3600)
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
