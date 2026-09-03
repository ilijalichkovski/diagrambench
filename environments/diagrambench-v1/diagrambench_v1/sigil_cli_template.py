#!/usr/bin/env python3
"""sigil — the SIGIL toolchain.

Usage (from the directory containing this executable):
  ./sigil status            free: current level, budgets, project files
  ./sigil build             compile the active level's project (costs 1)
  ./sigil run               execute the last successful build; shows the view (costs 1)
  ./sigil present           submit the last successful run for judgment (3 per level)
  ./sigil grammar           the SIGIL grammar card (costs 1)
  ./sigil explain F231      one fault code explained (costs 1)

The active level lives at levels/L###/ (see its BRIEF.md). State in .sigil/
is evaluation machinery: runs are re-scored from the build log, so editing it
cannot help you.
"""

import base64
import json
import os
import sys
import zlib

ROOT = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(ROOT, ".sigil")
LOG = os.path.join(STATE, "log.jsonl")

sys.path.insert(0, os.path.join(STATE, "core.zip"))
from veldcore.project_engine import (DEFAULT_MANIFEST, PRESENT_CAP,  # noqa
                                     TOOLCHAIN_CAP, ProjectState, apply_entry,
                                     brief_text, dataset_tsv, replay)


def load_levels():
    with open(os.path.join(STATE, "levels.b64"), "rb") as f:
        return json.loads(zlib.decompress(base64.b64decode(f.read())))


def load_entries():
    if not os.path.exists(LOG):
        return []
    with open(LOG) as f:
        return [json.loads(l) for l in f if l.strip()]


def level_dir(level):
    return os.path.join(ROOT, "levels", f"L{level['index']:03d}")


def materialize(level, num_levels, cleared):
    d = level_dir(level)
    os.makedirs(os.path.join(d, "src"), exist_ok=True)
    os.makedirs(os.path.join(d, "data"), exist_ok=True)
    os.makedirs(os.path.join(d, "out"), exist_ok=True)
    with open(os.path.join(d, "BRIEF.md"), "w") as f:
        f.write(brief_text(level, num_levels, cleared))
    mpath = os.path.join(d, "sigil.toml")
    if not os.path.exists(mpath):
        with open(mpath, "w") as f:
            f.write(DEFAULT_MANIFEST)
    for name in level.get("datasets", []):
        with open(os.path.join(d, "data", f"{name}.tsv"), "w") as f:
            f.write(dataset_tsv(name))
    return d


def collect_project_files(d):
    files = {}
    for base, _, names in os.walk(os.path.join(d, "src")):
        for n in names:
            p = os.path.join(base, n)
            rel = os.path.relpath(p, d)
            try:
                files[rel] = open(p).read()
            except OSError:
                pass
    manifest = DEFAULT_MANIFEST
    mp = os.path.join(d, "sigil.toml")
    if os.path.exists(mp):
        manifest = open(mp).read()
    return files, manifest


def main():
    if len(sys.argv) < 2:
        print(__doc__.strip())
        return
    cmd = sys.argv[1]
    levels = load_levels()
    entries = load_entries()

    def datadir_for(level):
        return materialize(level, len(levels), None) and level_dir(level)

    state = replay(levels, entries, datadir_for=lambda lvl: level_dir(lvl))
    if state.level is not None:
        materialize(state.level, len(levels), len(state.completed))

    if cmd == "status":
        if state.finished:
            print(f"ALL {len(levels)} LEVELS COMPLETE.")
            return
        if state.terminated:
            print(f"RUN OVER — {state.terminated}")
            return
        lvl = state.level
        d = level_dir(lvl)
        files, _ = collect_project_files(d)
        print(f"level {lvl['index']} of {len(levels)} [{lvl['id']}] — "
              f"project at {os.path.relpath(d, ROOT)}/")
        print(f"cleared so far: {len(state.completed)}")
        print(state.budget_line())
        print("source files: " + (", ".join(sorted(files)) or "(none yet)"))
        print(f"read {os.path.relpath(d, ROOT)}/BRIEF.md for the task")
        return

    if state.finished or state.terminated:
        print(state.last_text or "RUN OVER.")
        return

    lvl = state.level
    d = level_dir(lvl)

    if cmd == "build":
        files, manifest = collect_project_files(d)
        entry = {"k": "build", "files": files, "manifest": manifest}
    elif cmd == "run":
        entry = {"k": "run"}
    elif cmd == "present":
        entry = {"k": "present"}
    elif cmd == "grammar":
        entry = {"k": "grammar"}
    elif cmd == "explain":
        if len(sys.argv) < 3:
            print("usage: ./sigil explain F231")
            return
        entry = {"k": "explain", "code": sys.argv[2]}
    else:
        print(f"unknown command '{cmd}'")
        print(__doc__.strip())
        return

    text = apply_entry(state, entry, d)
    os.makedirs(STATE, exist_ok=True)
    with open(LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")

    # persist artifacts of a successful run
    if cmd == "run" and state.env is not None:
        outdir = os.path.join(d, "out")
        os.makedirs(outdir, exist_ok=True)
        try:
            from veldcore.layout import layout_scene
            from veldcore.ascii_render import ascii_view
            from veldcore.render import items_to_svg
            items, warnings = layout_scene(state.env.scene,
                                           state.env.ledgers)
            gw, gh = getattr(state, "view_grid", (160, 60))
            with open(os.path.join(outdir, "render.txt"), "w") as f:
                f.write(ascii_view(items, warnings, gw, gh))
            with open(os.path.join(outdir, "render.svg"), "w") as f:
                f.write(items_to_svg(items))
            if getattr(state, "view_mode", "ascii") in ("image", "both"):
                try:
                    import cairosvg
                    cairosvg.svg2png(
                        url=os.path.join(outdir, "render.svg"),
                        write_to=os.path.join(outdir, "render.png"),
                        output_width=1200)
                except Exception as e:
                    text += f"\n(png unavailable: {type(e).__name__})"
        except Exception:
            pass

    # a cleared level materializes the next project folder
    if cmd == "present" and not state.finished and not state.terminated \
            and state.level is not None and "SUCCESS" in text:
        materialize(state.level, len(levels), len(state.completed))

    print(text)


if __name__ == "__main__":
    main()
