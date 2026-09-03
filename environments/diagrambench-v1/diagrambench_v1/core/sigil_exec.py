"""SIGIL execution: run compiled IR against a fresh scene, plus the grammar
card and fault-explanation texts served by the toolchain."""

import os

from .sdk import TaskEnv


class Trap(Exception):
    def __init__(self, code, msg, file=None, line=None):
        self.code = code
        self.msg = msg
        self.file = file
        self.line = line

    def __str__(self):
        where = f"{self.file}:{self.line}: " if self.file else ""
        return f"{where}trap {self.code}: {self.msg}"


def _load_tsv(workdir, path, schema):
    full = os.path.normpath(os.path.join(workdir, path))
    if not os.path.exists(full):
        raise Trap("T101", f"no such data file '{path}'")
    with open(full) as f:
        lines = [l.rstrip("\n") for l in f if l.strip()]
    header = lines[0].split("\t")
    declared = [c for c, _, _ in schema]
    if sorted(header) != sorted(declared):
        raise Trap("T102", f"schema does not match file columns "
                   f"(file has: {', '.join(header)})")
    kinds = {c: (k, order) for c, k, order in schema}
    rows = []
    for ln in lines[1:]:
        vals = ln.split("\t")
        row = {}
        for col, raw in zip(header, vals):
            kind, order = kinds[col]
            if kind == "counted":
                try:
                    row[col] = int(raw) if "." not in raw else float(raw)
                except ValueError:
                    raise Trap("T103", f"column '{col}' declared counted but "
                               f"holds {raw!r}")
            elif kind == "rank":
                if raw not in order:
                    raise Trap("T104", f"value {raw!r} of '{col}' not in its "
                               f"declared rank order")
                row[col] = raw
            else:
                row[col] = raw
        rows.append(row)
    orders = {c: o for c, k, o in schema if k == "rank"}
    return rows, orders, path


import re as _re

_SYM = _re.compile(r"^\$[A-Za-z_][A-Za-z0-9_]*$")


def _resolve(v, syms):
    if isinstance(v, str) and _SYM.match(v):
        if v not in syms:
            raise Trap("T201", f"unbound symbol {v}")
        return syms[v]
    if isinstance(v, list):
        return [_resolve(x, syms) for x in v]
    return v


def execute(ir, workdir):
    """Run IR. Returns (env, resolved_op_count). Raises Trap on first fault."""
    env = TaskEnv()
    syms = {}
    n = 0
    for o in ir:
        op, args = o["op"], o["args"]
        if op == "_alias":
            syms[o["out"]] = _resolve(args["of"], syms)
            continue
        if op == "_load":
            try:
                rows, orders, path = _load_tsv(workdir, args["path"],
                                               args["schema"])
            except Trap as t:
                t.file, t.line = o["file"], o["line"]
                raise
            led = env.ledgers.register(rows, [("open", path)], orders)
            syms[o["out"]] = led.ref
            n += 1
            continue
        try:
            rargs = {k: _resolve(v, syms) for k, v in args.items()}
        except Trap as t:
            t.file, t.line = o["file"], o["line"]
            raise
        obs = env.act(op, rargs)
        n += 1
        if not obs.get("ok"):
            raise Trap("T200", obs.get("error", "refused"), o["file"],
                       o["line"])
        if obs.get("ref"):
            if o["out"]:
                syms[o["out"]] = obs["ref"]
        elif o["out"]:
            # ops that name things rather than mint refs (place -> glyph name)
            syms[o["out"]] = rargs.get("name") or obs.get("ref")
    return env, n


# ----------------------------------------------------------------------
# grammar card & fault explanations (terse by design)
# ----------------------------------------------------------------------

GRAMMAR = """\
SIGIL GRAMMAR CARD — statement forms only. Semantics are yours to discover.

project: sigil.toml lists units; every .sgl begins `unit <aspect>;`
aspects: data | ground | marks | script | compose

unit data;
  ledger N = open("data/F.tsv") schema (col: told|counted|rank["a","b",...], ...);
  ledger N = M | stage | stage ...;
    stages: keep(.v == lit | != | < | > | <= | >= | in [lit,...] [&& ...])
            drop(...)              fold(.by[,.by2]; out = sum|mean|median|min|max|count(.v))
            derive(name = .a / .b | .a - .b | share(.a))
            rank(.v, asc|desc)     first(n)     bins(.v, n)

unit ground;
  lattice N = lattice(LEDGER.vein);
  cleave @P : span|rise by LATTICE [, gap X];
  split @P : span|rise into N [, gap X];
  hoop @P [inner X];
  law @P = abreast|heap|strew|wheel|current(east|west|north|south);
  invert @P : span|rise;      breathe @P X;      palette @P name;
  align @A ~ @B : trait;      abut @A ~ @B : side;
  arena N = nest @P [at aim] [, breadth X] [, depth Y];
  parcels: @root | @root["key"] | @root[i] | @ARENA

unit marks;
  brood N = alloc brood(LEDGER);
  route N into @P [by .vein];
  commit N;
  gauge N = gauge counted | gauge banded(LEDGER.vein);
  calibrate N [, floor X] [, ceil Y];
  over N as g { g.form = FORM;  g.TRAIT = GAUGE(.vein);
                g.badge = text(.vein)|"txt" [at aim];
                if (.v == lit [&& ...]) { kindle g; hush g; flag g "txt";
                                          paint g HUE; inscribe g "txt" [at aim]; } }
  pick N where (pred) as SEL;
  spawn N = FORM "Label" in @P;
  cord N = tether A -> B;      pipe A -> B width X [as N];
  N.barb = head|tail|both|none;  N.crook = straight|bend|arc;
  N.sweep = X;  N.heft = X;  N.badge = "txt";
  thread BROOD by .vein as S;   flood S;
  loosen BROOD.trait;           corral "Label" { A, B, ... };
  kindle T; hush T; lift T; sink T;
  paint T HUE; veil T X; outline T X;   label T "txt" [at aim];
  arena N = nest under GLYPH [at aim] [, breadth X, depth Y];

unit script;
  raise rim @P:south|west|north|east [from GAUGE];
  raise weft @P : span|rise;
  raise key @P from BROOD.tint|bulk;
  entitle @P "txt";   note @P "txt";
  inscribe "txt" [near T] [at aim];   flag T "txt";

unit compose;
  use NAME; ...
  settle!;                        // required, exactly once

FORMS: slab disc wisp ring capsule rhomb drum plaque
TRAITS: stature girth stance perch tint bulk veil heft
HUES: ember tide moss plum sand slate rose teal ink mist
aims: auto north south east west center rim
"""

EXPLAIN = {
    "F001": "no units compiled; sigil.toml's [project].units must match .sgl files.",
    "F101": "lexical: a character the tokenizer does not accept.",
    "F102": "syntax: the parser expected a different token here.",
    "F103": "every .sgl file must begin with 'unit <aspect>;'.",
    "F104": "aspect must be one of: data, ground, marks, script, compose.",
    "F105": "schema kinds: told, counted, rank[\"a\",\"b\",...].",
    "F201": "a name is referenced that no statement declares.",
    "F210": "the same name is declared twice.",
    "F214": "statements form a dependency cycle.",
    "F221": "a committed brood must have a form; set g.form in an over-block.",
    "F222": "a brood may take exactly one form.",
    "F223": "a brood that is bound or used must be committed.",
    "F224": "route a brood into a parcel before committing it.",
    "F225": "routes are fixed at commit; route before commit.",
    "F226": "commit is once per brood.",
    "F241": "a kernel binding names a gauge that was never declared.",
    "F244": "counted gauges bound to traits must be calibrated "
            "(bare 'calibrate g;' requests automatic calibration).",
    "F245": "calibrate applies to gauges that have at least one binding.",
    "F251": "the compose unit must contain exactly one 'settle!;'.",
    "F312": "each unit aspect admits only its own statement kinds.",
    "F313": "nesting under a glyph is a marks-aspect statement.",
    "T101": "the opened data file does not exist relative to the project.",
    "T102": "declared schema columns must exactly match the file's header.",
    "T103": "a counted column holds a non-numeric value.",
    "T104": "a rank column holds a value missing from its declared order.",
    "T200": "the instrument refused the lowered operation; the message "
            "carries its exact words.",
    "T201": "an internal symbol failed to resolve; report this.",
}


def explain(code):
    return EXPLAIN.get(code, f"no entry for '{code}'.")
