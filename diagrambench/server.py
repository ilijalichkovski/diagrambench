"""Local benchmark viewer server (stdlib only).

Endpoints:
  GET  /                 viewer app
  GET  /api/state        current session state
  GET  /api/events?since=N   incremental event stream (poll)
  POST /api/act          drive the session manually: {"op": ..., "args": {...}}
"""

import json
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .layout import layout_scene
from .sdk import BOOTSTRAP
from .tasks import agent_view, ref_cost

VIEWER_DIR = os.path.join(os.path.dirname(__file__), "..", "viewer")


def _fmt_args(args):
    return ", ".join(f"{k}={v!r}" for k, v in (args or {}).items())


class EventHub:
    """Wraps a Session; records viewer events with display-list snapshots."""

    def __init__(self, session):
        self.session = session
        self.events = []
        self.lock = threading.Lock()
        self._push("task_start", scene=True)

    def _display(self):
        try:
            items, warnings = layout_scene(self.session.env.scene,
                                           self.session.env.ledgers)
            return items, warnings
        except Exception as e:  # never let a layout bug kill the stream
            return [], [f"render error: {e}"]

    def _push(self, kind, log=None, scene=False, verdict=None, summary=None):
        with self.lock:
            ev = {
                "seq": len(self.events),
                "kind": kind,
                "task": agent_view(self.session.task)
                if self.session.task else None,
                "ref_cost": ref_cost(self.session.task)
                if self.session.task else None,
                "counts": dict(self.session.counts),
                "stats": self.session.lifetime_stats(),
                "finished": self.session.finished,
            }
            if log is not None:
                ev["log"] = log
            if scene:
                items, warnings = self._display()
                ev["items"] = items
                ev["warnings"] = warnings
            if verdict is not None:
                ev["verdict"] = {k: verdict[k] for k in
                                 ("success", "semantic_score", "layout_score",
                                  "failed")}
            if summary is not None:
                ev["summary"] = summary
            self.events.append(ev)

    def act(self, op, args=None):
        session = self.session
        before_idx = session.task_idx
        task_before = session.task
        obs = session.act(op, args)
        log = {"call": f"{op}({_fmt_args(args)})",
               "ok": obs.get("ok", False),
               "text": obs.get("text") or obs.get("error") or ""}
        scene_changed = obs.get("mutated") or op in ("undo", "restart")
        advanced = session.task_idx != before_idx
        if "verdict" in obs:
            # present() was judged; the summary event carries the outcome
            self._push("present", log=log, scene=scene_changed,
                       verdict=obs["verdict"])
            if advanced:
                summary = session.results[-1]
                with self.lock:
                    self.events[-1]["summary"] = summary
                self._push("task_start", scene=True)
        else:
            self._push("action", log=log, scene=scene_changed)
            if advanced:  # forced advance on action-cap
                self._push("task_start", scene=True)
        return obs

    def since(self, n):
        with self.lock:
            return self.events[n:]


def make_handler(hub):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def _json(self, obj, code=200):
            body = json.dumps(obj).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _file(self, name, ctype):
            path = os.path.join(VIEWER_DIR, name)
            with open(path, "rb") as f:
                body = f.read()
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            try:
                if self.path in ("/", "/index.html"):
                    self._file("index.html", "text/html; charset=utf-8")
                elif self.path == "/app.js":
                    self._file("app.js", "application/javascript")
                elif self.path == "/style.css":
                    self._file("style.css", "text/css")
                elif self.path.startswith("/api/state"):
                    self._json(hub.session.state_view())
                elif self.path.startswith("/api/bootstrap"):
                    self._json({"bootstrap": BOOTSTRAP,
                                "instruction": hub.session.instruction()})
                elif self.path.startswith("/api/events"):
                    since = 0
                    if "since=" in self.path:
                        since = int(self.path.split("since=")[1].split("&")[0])
                    self._json({"events": hub.since(since)})
                else:
                    self._json({"error": "not found"}, 404)
            except BrokenPipeError:
                pass

        def do_POST(self):
            try:
                if self.path == "/api/act":
                    n = int(self.headers.get("Content-Length", 0))
                    payload = json.loads(self.rfile.read(n) or b"{}")
                    obs = hub.act(payload.get("op", ""),
                                  payload.get("args") or {})
                    safe = {k: v for k, v in obs.items() if k != "verdict"}
                    if "verdict" in obs:
                        safe["verdict"] = {
                            "success": obs["verdict"]["success"],
                            "semantic_score": obs["verdict"]["semantic_score"],
                            "layout_score": obs["verdict"]["layout_score"],
                            "failed": obs["verdict"]["failed"],
                        }
                    self._json(safe)
                else:
                    self._json({"error": "not found"}, 404)
            except BrokenPipeError:
                pass

    return Handler


def serve(hub, port=8321):
    httpd = ThreadingHTTPServer(("127.0.0.1", port), make_handler(hub))
    print(f"DiagramBench viewer at http://127.0.0.1:{port}")
    return httpd
