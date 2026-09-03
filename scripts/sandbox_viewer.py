#!/usr/bin/env python3
"""DiagramBench sandbox visualizer.

Watches a live eval sandbox and serves a local dashboard showing the agent's
progress in real time: level/budget status, the source tree as the agent
writes it, the toolchain trajectory (builds, runs, presents), and the rendered
artifact after every run — scrubbable back through time.

How it works: the in-sandbox `.sigil/log.jsonl` embeds the full source tree of
every build, so this server polls the sandbox (via `prime sandbox run`),
replays the log locally through the real project engine, and snapshots the
scene (SVG + ASCII) after each entry. The sandbox is never trusted for
scoring — and this viewer needs nothing from it but the log and the live,
not-yet-built files.

Usage:
  # attach to a running sandbox by id
  .venv/bin/python scripts/sandbox_viewer.py vydmpa04ps6aus1y3reqwhre

  # or point at an eval run dir / log — the sandbox id is found in eval.log
  .venv/bin/python scripts/sandbox_viewer.py outputs/sigil10-codex

  # or watch a local directory laid out like the sandbox /app (dev mode)
  .venv/bin/python scripts/sandbox_viewer.py --local /tmp/sigiltest

Options: --port 8399  --interval 4
"""

import argparse
import base64
import io
import json
import os
import re
import subprocess
import sys
import tarfile
import tempfile
import threading
import time
import webbrowser
import zlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..",
                                "environments", "diagrambench-v1"))

from diagrambench_v1.core.ascii_render import ascii_view  # noqa: E402
from diagrambench_v1.core.layout import layout_scene  # noqa: E402
from diagrambench_v1.core.project_engine import (ProjectState,  # noqa: E402
                                                 apply_entry, brief_text,
                                                 dataset_tsv)
from diagrambench_v1.core.render import items_to_svg  # noqa: E402

VIEWER_DIR = os.path.join(os.path.dirname(__file__), "..", "viewer", "sandbox")

TAR_CMD = ("cd /app && echo __B64__ && "
           "tar --exclude='levels/*/out' -cf - .sigil/log.jsonl "
           ".sigil/levels.b64 levels 2>/dev/null | base64 && echo __END__")

# codex CLI writes its full conversation (reasoning, tool calls, outputs)
# to a rollout jsonl; tail it incrementally by byte offset (1-based tail -c)
TRAJ_CMD = ("f=$(ls -t $HOME/.codex/sessions/*/*/*/rollout-*.jsonl "
            "2>/dev/null | head -1); "
            "if [ -n \"$f\" ]; then echo __B64__; "
            "tail -c +{off} \"$f\" | base64; echo __END__; "
            "else echo __NONE__; fi")


def _between_markers(out):
    lines = out.splitlines()
    try:
        start = max(i for i, l in enumerate(lines) if l.strip() == "__B64__")
        end = min(i for i, l in enumerate(lines)
                  if l.strip() == "__END__" and i > start)
    except ValueError:
        return None
    return base64.b64decode("".join(l.strip() for l in lines[start + 1:end]))


# ----------------------------------------------------------------------
# sources
# ----------------------------------------------------------------------

class SandboxSource:
    """Fetches the watched file tree from a prime sandbox."""

    def __init__(self, sandbox_id):
        self.sandbox_id = sandbox_id
        self.label = f"sandbox {sandbox_id}"

    def fetch(self):
        r = subprocess.run(
            ["prime", "sandbox", "run", self.sandbox_id, "--plain", "--",
             "sh", "-c", TAR_CMD],
            capture_output=True, text=True, timeout=60)
        out = r.stdout or ""
        # the CLI echoes the command (which contains the markers), so match
        # only lines that ARE the marker
        blob = _between_markers(out)
        if blob is None:
            raise ConnectionError(
                (r.stderr or out or "no output").strip()[-300:])
        files = {}
        with tarfile.open(fileobj=io.BytesIO(blob)) as tf:
            for m in tf.getmembers():
                if not m.isfile():
                    continue
                data = tf.extractfile(m).read()
                name = m.name
                if name.startswith("./"):
                    name = name[2:]
                files[name] = data
        return files

    def fetch_traj(self, offset):
        """Bytes of the codex rollout jsonl from `offset` onward."""
        cmd = TRAJ_CMD.replace("{off}", str(offset + 1))
        r = subprocess.run(
            ["prime", "sandbox", "run", self.sandbox_id, "--plain", "--",
             "sh", "-c", cmd],
            capture_output=True, text=True, timeout=60)
        out = r.stdout or ""
        blob = _between_markers(out)
        if blob is not None:
            return blob
        return b""  # no session file yet (or marker not found)


class LocalSource:
    """Watches a local directory laid out like the sandbox /app (dev mode)."""

    def __init__(self, root):
        self.root = root
        self.label = f"local {root}"

    def fetch(self):
        files = {}
        for base in (".sigil", "levels"):
            top = os.path.join(self.root, base)
            for dirpath, dirnames, names in os.walk(top):
                if os.path.basename(dirpath) == "out":
                    dirnames[:] = []
                    continue
                for n in names:
                    p = os.path.join(dirpath, n)
                    rel = os.path.relpath(p, self.root)
                    keep = (rel in (".sigil/log.jsonl", ".sigil/levels.b64")
                            or rel.startswith("levels/"))
                    if keep and not n.endswith(".png"):
                        with open(p, "rb") as f:
                            files[rel] = f.read()
        return files

    def fetch_traj(self, offset):
        p = os.path.join(self.root, "codex-rollout.jsonl")
        if not os.path.exists(p):
            return b""
        with open(p, "rb") as f:
            f.seek(offset)
            return f.read()


# ----------------------------------------------------------------------
# watcher: poll -> incremental replay -> snapshots
# ----------------------------------------------------------------------

class Watcher(threading.Thread):
    def __init__(self, source, interval=4.0):
        super().__init__(daemon=True)
        self.source = source
        self.interval = interval
        self.lock = threading.Lock()
        self.levels = None
        self.state = None
        self.consumed = 0
        self.entries = []      # public timeline
        self.snapshots = {}    # entry idx -> {"svg", "ascii"}
        self.sources_at = {}   # entry idx -> {path: text} (builds only)
        self.manifest_at = {}  # entry idx -> sigil.toml text (builds only)
        self.files = {}        # live sandbox tree (text)
        self.traj = []         # model trajectory events (codex rollout)
        self._traj_offset = 0
        self._traj_buf = b""
        self._sigil_count = 0  # log-appending ./sigil calls seen so far
        self.connected = False
        self.error = None
        self.last_poll = 0.0
        self.seq = 0
        self._datadirs = {}

    # -- level data ------------------------------------------------------
    def _datadir(self, idx):
        if idx not in self._datadirs:
            d = tempfile.mkdtemp(prefix=f"dbviz-L{idx}-")
            os.makedirs(os.path.join(d, "data"), exist_ok=True)
            for name in self.levels[idx].get("datasets", []):
                with open(os.path.join(d, "data", f"{name}.tsv"), "w") as f:
                    f.write(dataset_tsv(name))
            self._datadirs[idx] = d
        return self._datadirs[idx]

    def _snapshot_scene(self):
        env = self.state.env
        if env is None:
            return None
        try:
            items, warnings = layout_scene(env.scene, env.ledgers)
            gw, gh = getattr(self.state, "view_grid", (160, 60))
            return {"svg": items_to_svg(items),
                    "ascii": ascii_view(items, warnings, gw, gh)}
        except Exception as e:
            return {"svg": None, "ascii": f"(render failed: {e})"}

    # -- main loop ---------------------------------------------------------
    def run(self):
        while True:
            try:
                raw = self.source.fetch()
                self._ingest(raw)
                try:
                    chunk = self.source.fetch_traj(self._traj_offset)
                    if chunk:
                        self._traj_offset += len(chunk)
                        self._ingest_traj(chunk)
                except Exception:
                    pass  # trajectory is best-effort (codex-only)
                with self.lock:
                    self.connected = True
                    self.error = None
                    self.last_poll = time.time()
            except Exception as e:
                with self.lock:
                    self.connected = False
                    self.error = f"{type(e).__name__}: {str(e)[-200:]}"
                    self.last_poll = time.time()
                    self.seq += 1
            time.sleep(self.interval)

    def _ingest(self, raw):
        if self.levels is None:
            blob = raw.get(".sigil/levels.b64")
            if not blob:
                raise ConnectionError("no .sigil/levels.b64 in tree (not a "
                                      "DiagramBench sandbox?)")
            levels = json.loads(zlib.decompress(base64.b64decode(blob)))
            with self.lock:
                self.levels = levels
                self.state = ProjectState(levels)

        log = raw.get(".sigil/log.jsonl", b"").decode()
        entries = [json.loads(l) for l in log.splitlines() if l.strip()]

        new_public = []
        new_snaps = {}
        new_sources = {}
        while self.consumed < len(entries):
            i = self.consumed
            e = entries[i]
            st = self.state
            if st.finished or st.terminated:
                break
            lvl = st.level
            before = {"tc": st.tc, "presents": st.presents,
                      "level_idx": st.level_idx}
            text = apply_entry(st, e, self._datadir(before["level_idx"]))
            pub = {
                "i": i,
                "k": e.get("k"),
                "code": e.get("code"),
                "level_index": lvl["index"],
                "level_id": lvl["id"],
                "text": text,
                "tc": st.tc if st.level_idx == before["level_idx"]
                else before["tc"] + 1,
                "presents": st.presents if st.level_idx ==
                before["level_idx"] else before["presents"] + 1,
                "cleared": st.level_idx != before["level_idx"],
                "ts": time.time(),
            }
            if e.get("k") == "build":
                new_sources[i] = {p: c for p, c in
                                  (e.get("files") or {}).items()}
                pub["n_files"] = len(new_sources[i])
                if e.get("manifest"):
                    self.manifest_at[i] = e["manifest"]
            if e.get("k") == "run" and "run: ok" in text:
                snap = self._snapshot_scene()
                if snap:
                    new_snaps[i] = snap
                    pub["has_scene"] = True
            if e.get("k") == "present" and st.env is not None and \
                    not pub["cleared"]:
                pass  # env unchanged; verdict text carries the info
            new_public.append(pub)
            self.consumed += 1

        # live (possibly unbuilt) source tree
        files = {}
        for path, data in raw.items():
            if path.startswith("levels/") and (
                    path.endswith(".sgl") or path.endswith(".toml")
                    or path.endswith(".md") or path.endswith(".tsv")):
                try:
                    files[path] = data.decode()
                except UnicodeDecodeError:
                    pass

        with self.lock:
            self.entries.extend(new_public)
            self.snapshots.update(new_snaps)
            self.sources_at.update(new_sources)
            self.files = files
            if new_public or files != self.files:
                self.seq += 1

    # -- model trajectory (codex rollout jsonl) -----------------------------
    SIGIL_RE = re.compile(r"(?:^|[;&|\s(])\./sigil\s+"
                          r"(build|run|present|grammar|explain)\b")

    def _ingest_traj(self, chunk):
        data = self._traj_buf + chunk
        lines = data.split(b"\n")
        self._traj_buf = lines[-1]  # possibly-partial tail
        events = []
        for raw in lines[:-1]:
            raw = raw.strip()
            if not raw:
                continue
            try:
                rec = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if rec.get("type") != "response_item":
                continue
            p = rec.get("payload") or {}
            pt = p.get("type")
            ev = None
            if pt == "reasoning":
                text = "\n".join(
                    c.get("text", "") for c in (p.get("content") or [])
                    if isinstance(c, dict))
                if text.strip():
                    ev = {"kind": "reasoning", "text": text[:4000]}
            elif pt == "message":
                text = "\n".join(
                    c.get("text", "") for c in (p.get("content") or [])
                    if isinstance(c, dict))
                ev = {"kind": p.get("role", "assistant"),
                      "text": text[:4000]}
            elif pt == "function_call":
                cmd = ""
                try:
                    args = json.loads(p.get("arguments") or "{}")
                    cmd = args.get("cmd") or args.get("command") or ""
                    if isinstance(cmd, list):
                        cmd = " ".join(str(x) for x in cmd)
                except json.JSONDecodeError:
                    cmd = (p.get("arguments") or "")[:400]
                n = len(self.SIGIL_RE.findall(cmd))
                ev = {"kind": "tool_call", "name": p.get("name", "tool"),
                      "text": str(cmd)[:1200]}
                if n:
                    ev["entries"] = list(range(self._sigil_count,
                                               self._sigil_count + n))
                    self._sigil_count += n
            elif pt == "function_call_output":
                out = p.get("output") or ""
                if "\nOutput:\n" in out:  # strip the exec wrapper header
                    out = out.split("\nOutput:\n", 1)[1]
                ev = {"kind": "tool_out", "text": out[:1600]}
            if ev:
                ev["ts"] = rec.get("timestamp")
                events.append(ev)
        if events:
            with self.lock:
                base = len(self.traj)
                for k, ev in enumerate(events):
                    ev["j"] = base + k
                self.traj.extend(events)
                self.seq += 1

    # -- views -------------------------------------------------------------
    def api_state(self):
        with self.lock:
            st = self.state
            levels = self.levels or []
            cur = st.level if st else None
            lvl_dir = f"levels/L{cur['index']:03d}" if cur else None
            live_files = sorted(p for p in self.files
                                if lvl_dir and p.startswith(lvl_dir))
            last_build = None
            for e in reversed(self.entries):
                if e["k"] == "build":
                    last_build = e["i"]
                    break
            dirty = []
            if last_build is not None and cur:
                built = self.sources_at.get(last_build, {})
                for p in live_files:
                    rel = p[len(lvl_dir) + 1:]
                    if rel.endswith(".sgl") and \
                            self.files.get(p) != built.get(rel):
                        dirty.append(p)
            return {
                "seq": self.seq,
                "source": self.source.label,
                "connected": self.connected,
                "error": self.error,
                "last_poll": self.last_poll,
                "num_levels": len(levels),
                "level": {"index": cur["index"], "id": cur["id"],
                          "instruction": cur["instruction"]} if cur else None,
                "cleared": len(st.completed) if st else 0,
                "budget": {"tc": st.tc, "presents": st.presents}
                if st else None,
                "finished": bool(st and st.finished),
                "terminated": st.terminated if st else None,
                "per_level": st.completed if st else [],
                "entries": self.entries,
                "live_files": live_files,
                "dirty": dirty,
            }

    def api_entry(self, i):
        with self.lock:
            entry = next((e for e in self.entries if e["i"] == i), None)
            if entry is None:
                return {"error": f"no entry {i}"}
            # scene + sources only travel backward within the same level
            same_level = [e["i"] for e in self.entries
                          if e["level_id"] == entry["level_id"]
                          and e["i"] <= i]
            snap_i = max((j for j in self.snapshots if j in same_level),
                         default=None)
            src_i = max((j for j in self.sources_at if j in same_level),
                        default=None)
            return {
                "entry": entry,
                "snapshot": self.snapshots.get(snap_i),
                "snapshot_i": snap_i,
                "files": self._project_at(entry, src_i),
                "sources_i": src_i,
            }

    def _project_at(self, entry, src_i):
        """Reconstructed project tree of the entry's level, as of that entry."""
        levels = self.levels or []
        pos, level = next(
            ((p, l) for p, l in enumerate(levels)
             if l["id"] == entry["level_id"]), (None, None))
        if level is None:
            return {}
        files = {"BRIEF.md": brief_text(level, len(levels), pos)}
        files["sigil.toml"] = self.manifest_at.get(src_i) or \
            "(default manifest — no build yet)"
        for name in level.get("datasets", []):
            files[f"data/{name}.tsv"] = dataset_tsv(name)
        for path, content in sorted(
                (self.sources_at.get(src_i) or {}).items()):
            files[path] = content
        return files

    def api_traj(self, since):
        with self.lock:
            return {"events": self.traj[since:], "total": len(self.traj)}

    def api_file(self, path):
        with self.lock:
            if path in self.files:
                return {"path": path, "content": self.files[path]}
            return {"error": f"no file {path}"}


# ----------------------------------------------------------------------
# http server
# ----------------------------------------------------------------------

def make_handler(watcher):
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
            with open(os.path.join(VIEWER_DIR, name), "rb") as f:
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
                    self._json(watcher.api_state())
                elif self.path.startswith("/api/entry/"):
                    self._json(watcher.api_entry(
                        int(self.path.rsplit("/", 1)[1])))
                elif self.path.startswith("/api/traj"):
                    since = 0
                    if "since=" in self.path:
                        since = int(self.path.split("since=")[1]
                                    .split("&")[0])
                    self._json(watcher.api_traj(since))
                elif self.path.startswith("/api/file?p="):
                    from urllib.parse import unquote
                    self._json(watcher.api_file(
                        unquote(self.path.split("p=", 1)[1])))
                else:
                    self._json({"error": "not found"}, 404)
            except BrokenPipeError:
                pass
            except Exception as e:
                try:
                    self._json({"error": f"{type(e).__name__}: {e}"}, 500)
                except Exception:
                    pass

    return Handler


def resolve_target(target):
    """Sandbox id, run dir, or eval log path -> SandboxSource."""
    if os.path.isdir(target):
        target = os.path.join(target, "eval.log")
    if os.path.isfile(target):
        text = open(target, errors="ignore").read()
        m = re.findall(r"sandbox ([a-z0-9]{16,}) up", text)
        if not m:
            sys.exit(f"no sandbox id found in {target}")
        return SandboxSource(m[-1])
    return SandboxSource(target)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("target", nargs="?",
                    help="sandbox id, eval run dir, or eval.log path")
    ap.add_argument("--local", help="watch a local dir laid out like /app")
    ap.add_argument("--port", type=int, default=8399)
    ap.add_argument("--interval", type=float, default=4.0)
    ap.add_argument("--open", action="store_true")
    args = ap.parse_args()

    if args.local:
        source = LocalSource(args.local)
    elif args.target:
        source = resolve_target(args.target)
    else:
        ap.error("give a sandbox id / run dir, or --local DIR")

    watcher = Watcher(source, args.interval)
    watcher.start()
    httpd = ThreadingHTTPServer(("127.0.0.1", args.port),
                                make_handler(watcher))
    url = f"http://127.0.0.1:{args.port}"
    print(f"DiagramBench sandbox viewer · watching {source.label} · {url}")
    if args.open:
        webbrowser.open(url)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
