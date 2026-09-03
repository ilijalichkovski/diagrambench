"""The SIGIL compiler.

SIGIL (Staged Instruction Grammar for Illustrated Layouts) is the agent-facing
language. Source projects are multi-file: every `.sgl` file opens with a
`unit <aspect>;` header (aspects: data, ground, marks, script, compose) and the
compiler rejects statements outside the unit's aspect. Programs lower to a
dependency-ordered IR of symbolic scene ops executed by `sigil_exec`.

Faults are C-style and terse by design: `file:line: fault F231: ...`.
"""

import re

ASPECTS = ("data", "ground", "marks", "script", "compose")
DIRS = ("span", "rise")
SIDES = ("south", "west", "north", "east")
HEADINGS = ("east", "west", "north", "south")
LAWS = ("abreast", "heap", "strew", "wheel", "current")
FORMS = ("slab", "disc", "wisp", "ring", "capsule", "rhomb", "drum", "plaque")
TRAITS = ("stature", "girth", "stance", "perch", "tint", "bulk", "veil", "heft")
AIMS = ("auto", "north", "south", "east", "west", "center", "rim")
HUES = ("ember", "tide", "moss", "plum", "sand", "slate", "rose", "teal",
        "ink", "mist")
PALETTES = ("quill", "dusk", "field", "emberline")
AGGS = ("sum", "mean", "median", "min", "max", "count")
CMP = {"==": "is", "!=": "is_not", "<": "below", ">": "above",
       "<=": "at_most", ">=": "at_least"}


class Fault(Exception):
    def __init__(self, code, msg, file=None, line=None):
        self.code = code
        self.msg = msg
        self.file = file
        self.line = line
        super().__init__(str(self))

    def __str__(self):
        where = f"{self.file}:{self.line}: " if self.file else ""
        return f"{where}fault {self.code}: {self.msg}"


# ----------------------------------------------------------------------
# lexer
# ----------------------------------------------------------------------

TOKEN_RE = re.compile(r"""
    (?P<ws>\s+)
  | (?P<comment>//[^\n]*)
  | (?P<str>"(?:[^"\\]|\\.)*")
  | (?P<num>-?\d+\.?\d*)
  | (?P<arrow>->)
  | (?P<op>==|!=|<=|>=|&&)
  | (?P<ident>[A-Za-z_][A-Za-z0-9_]*)
  | (?P<punc>[{}()\[\];,:@.|=~!<>/-])
""", re.VERBOSE)


def lex(text, file):
    toks = []
    line = 1
    pos = 0
    while pos < len(text):
        m = TOKEN_RE.match(text, pos)
        if not m:
            raise Fault("F101", f"stray character {text[pos]!r}", file, line)
        kind = m.lastgroup
        val = m.group()
        if kind == "ws":
            line += val.count("\n")
        elif kind == "comment":
            pass
        elif kind == "str":
            toks.append(("str", val[1:-1].replace('\\"', '"'), line))
        elif kind == "num":
            toks.append(("num", float(val) if "." in val else int(val), line))
        else:
            toks.append((kind if kind in ("ident",) else "punc", val, line))
        pos = m.end()
    toks.append(("eof", None, line))
    return toks


class TokStream:
    def __init__(self, toks, file):
        self.toks = toks
        self.i = 0
        self.file = file

    def peek(self, k=0):
        return self.toks[min(self.i + k, len(self.toks) - 1)]

    @property
    def line(self):
        return self.peek()[2]

    def at(self, val):
        t = self.peek()
        return (t[0] in ("punc", "ident", "arrow") and t[1] == val)

    def take(self, val=None, kind=None, what=None):
        t = self.peek()
        if val is not None and not (t[1] == val and t[0] != "str"):
            raise Fault("F102", f"expected {what or repr(val)}, got "
                        f"{t[1]!r}", self.file, t[2])
        if kind is not None and t[0] != kind:
            raise Fault("F102", f"expected {what or kind}, got {t[1]!r}",
                        self.file, t[2])
        self.i += 1
        return t

    def ident(self, what="identifier"):
        t = self.peek()
        if t[0] != "ident":
            raise Fault("F102", f"expected {what}, got {t[1]!r}",
                        self.file, t[2])
        self.i += 1
        return t[1]


# ----------------------------------------------------------------------
# parser — produces statement dicts {kind, ..., file, line}
# ----------------------------------------------------------------------

def parse_unit(text, file):
    ts = TokStream(lex(text, file), file)
    if not ts.at("unit"):
        raise Fault("F103", "every .sgl file must open with 'unit <aspect>;'",
                    file, ts.line)
    ts.take("unit")
    aspect = ts.ident("aspect")
    if aspect not in ASPECTS:
        raise Fault("F104", f"unknown aspect '{aspect}' (aspects: "
                    f"{', '.join(ASPECTS)})", file, ts.line)
    ts.take(";")
    stmts = []
    while not ts.at(None) and ts.peek()[0] != "eof":
        stmts.append(_statement(ts))
    return aspect, stmts


def _parcel(ts):
    ts.take("@")
    name = ts.ident("parcel name")
    at = None
    if ts.at("["):
        ts.take("[")
        t = ts.peek()
        if t[0] in ("str", "num"):
            ts.i += 1
            at = t[1]
        else:
            raise Fault("F102", "expected cell key or index", ts.file, t[2])
        ts.take("]")
    return {"base": name, "at": at}


def _veinref(ts):
    ts.take(".")
    return ts.ident("vein name")


def _literal(ts):
    t = ts.peek()
    if t[0] in ("str", "num"):
        ts.i += 1
        return t[1]
    raise Fault("F102", f"expected literal, got {t[1]!r}", ts.file, t[2])


def _clause(ts):
    vein = _veinref(ts)
    t = ts.peek()
    if t[1] in CMP and t[0] != "str":
        ts.i += 1
        return (vein, CMP[t[1]], _literal(ts))
    if t[1] == "in":
        ts.i += 1
        ts.take("[")
        vals = [_literal(ts)]
        while ts.at(","):
            ts.take(",")
            vals.append(_literal(ts))
        ts.take("]")
        return (vein, "among", vals)
    raise Fault("F102", f"expected comparison, got {t[1]!r}", ts.file, t[2])


def _pred(ts):
    clauses = [_clause(ts)]
    while ts.peek()[1] == "&&":
        ts.i += 1
        clauses.append(_clause(ts))
    return clauses


def _opt_num(ts, word):
    if ts.at(","):
        save = ts.i
        ts.take(",")
        if ts.at(word):
            ts.take(word)
            return ts.take(kind="num")[1]
        ts.i = save
    if ts.at(word):
        ts.take(word)
        return ts.take(kind="num")[1]
    return None


def _statement(ts):
    t = ts.peek()
    line = t[2]
    S = lambda **kw: {**kw, "file": ts.file, "line": line}
    w = t[1]

    if w == "ledger":
        ts.take("ledger")
        name = ts.ident()
        ts.take("=")
        if ts.at("open"):
            ts.take("open")
            ts.take("(")
            path = ts.take(kind="str")[1]
            ts.take(")")
            ts.take("schema", what="'schema'")
            ts.take("(")
            schema = []
            while True:
                col = ts.ident("column name")
                ts.take(":")
                if ts.at("rank"):
                    ts.take("rank")
                    ts.take("[")
                    order = [ts.take(kind="str")[1]]
                    while ts.at(","):
                        ts.take(",")
                        order.append(ts.take(kind="str")[1])
                    ts.take("]")
                    schema.append((col, "rank", order))
                else:
                    kind = ts.ident("kind")
                    if kind not in ("told", "counted"):
                        raise Fault("F105", f"unknown kind '{kind}' (told, "
                                    f"counted, rank[...])", ts.file, ts.line)
                    schema.append((col, kind, None))
                if ts.at(")"):
                    break
                ts.take(",")
            ts.take(")")
            src = {"open": path, "schema": schema}
        else:
            src = {"ref": ts.ident("ledger name")}
        stages = []
        while ts.at("|"):
            ts.take("|")
            stages.append(_stage(ts))
        ts.take(";")
        return S(kind="ledger", name=name, src=src, stages=stages)

    if w == "lattice":
        ts.take("lattice")
        name = ts.ident()
        ts.take("=")
        ts.take("lattice")
        ts.take("(")
        led = ts.ident("ledger name")
        vein = _veinref(ts)
        ts.take(")")
        ts.take(";")
        return S(kind="lattice", name=name, ledger=led, vein=vein)

    if w == "cleave":
        ts.take("cleave")
        p = _parcel(ts)
        ts.take(":")
        d = ts.ident("direction")
        ts.take("by")
        lat = ts.ident("lattice name")
        gap = _opt_num(ts, "gap")
        ts.take(";")
        return S(kind="cleave", parcel=p, along=d, lattice=lat, gap=gap)

    if w == "split":
        ts.take("split")
        p = _parcel(ts)
        ts.take(":")
        d = ts.ident("direction")
        ts.take("into")
        n = ts.take(kind="num")[1]
        gap = _opt_num(ts, "gap")
        ts.take(";")
        return S(kind="split", parcel=p, along=d, count=int(n), gap=gap)

    if w == "hoop":
        ts.take("hoop")
        p = _parcel(ts)
        inner = _opt_num(ts, "inner")
        ts.take(";")
        return S(kind="hoop", parcel=p, inner=inner)

    if w == "law":
        ts.take("law")
        p = _parcel(ts)
        ts.take("=")
        law = ts.ident("law")
        heading = None
        if law == "current":
            ts.take("(")
            heading = ts.ident("heading")
            ts.take(")")
        ts.take(";")
        return S(kind="law", parcel=p, law=law, heading=heading)

    if w == "invert":
        ts.take("invert")
        p = _parcel(ts)
        ts.take(":")
        d = ts.ident("direction")
        ts.take(";")
        return S(kind="invert", parcel=p, along=d)

    if w == "breathe":
        ts.take("breathe")
        p = _parcel(ts)
        n = ts.take(kind="num")[1]
        ts.take(";")
        return S(kind="breathe", parcel=p, amount=n)

    if w in ("align", "abut"):
        ts.take(w)
        a = _parcel(ts)
        ts.take("~")
        b = _parcel(ts)
        ts.take(":")
        x = ts.ident()
        ts.take(";")
        return S(kind=w, a=a, b=b, arg=x)

    if w == "palette":
        ts.take("palette")
        p = _parcel(ts)
        name = ts.ident("palette name")
        ts.take(";")
        return S(kind="palette", parcel=p, name=name)

    if w == "arena":
        ts.take("arena")
        name = ts.ident()
        ts.take("=")
        ts.take("nest")
        host = None
        parcel = None
        if ts.at("under"):
            ts.take("under")
            host = ts.ident("glyph name")
        else:
            parcel = _parcel(ts)
        aim = None
        if ts.at("at"):
            ts.take("at")
            aim = ts.ident("aim")
        breadth = _opt_num(ts, "breadth")
        depth = _opt_num(ts, "depth")
        ts.take(";")
        return S(kind="arena", name=name, parcel=parcel, host=host, aim=aim,
                 breadth=breadth, depth=depth)

    if w == "brood":
        ts.take("brood")
        name = ts.ident()
        ts.take("=")
        ts.take("alloc")
        ts.take("brood")
        ts.take("(")
        led = ts.ident("ledger name")
        ts.take(")")
        ts.take(";")
        return S(kind="brood", name=name, ledger=led)

    if w == "route":
        ts.take("route")
        name = ts.ident("brood name")
        ts.take("into")
        p = _parcel(ts)
        by = None
        if ts.at("by"):
            ts.take("by")
            by = _veinref(ts)
        ts.take(";")
        return S(kind="route", brood=name, parcel=p, by=by)

    if w == "commit":
        ts.take("commit")
        name = ts.ident("brood name")
        ts.take(";")
        return S(kind="commit", brood=name)

    if w == "gauge":
        ts.take("gauge")
        name = ts.ident()
        ts.take("=")
        ts.take("gauge")
        if ts.at("counted"):
            ts.take("counted")
            ts.take(";")
            return S(kind="gauge", name=name, gkind="counted",
                     ledger=None, vein=None)
        ts.take("banded", what="'counted' or 'banded'")
        ts.take("(")
        led = ts.ident("ledger name")
        vein = _veinref(ts)
        ts.take(")")
        ts.take(";")
        return S(kind="gauge", name=name, gkind="banded", ledger=led,
                 vein=vein)

    if w == "calibrate":
        ts.take("calibrate")
        name = ts.ident("gauge name")
        floor = _opt_num(ts, "floor")
        ceil = _opt_num(ts, "ceil")
        ts.take(";")
        return S(kind="calibrate", gauge=name, floor=floor, ceil=ceil)

    if w == "over":
        ts.take("over")
        brood = ts.ident("brood name")
        ts.take("as")
        ts.take("g", what="'g'")
        ts.take("{")
        body = []
        while not ts.at("}"):
            body.append(_kernel_stmt(ts))
        ts.take("}")
        return S(kind="over", brood=brood, body=body)

    if w == "pick":
        ts.take("pick")
        brood = ts.ident("brood name")
        ts.take("where")
        ts.take("(")
        pred = _pred(ts)
        ts.take(")")
        ts.take("as")
        name = ts.ident()
        ts.take(";")
        return S(kind="pick", brood=brood, pred=pred, name=name)

    if w == "spawn":
        ts.take("spawn")
        name = ts.ident()
        ts.take("=")
        form = ts.ident("form")
        label = ts.take(kind="str")[1]
        ts.take("in")
        p = _parcel(ts)
        ts.take(";")
        return S(kind="spawn", name=name, form=form, label=label, parcel=p)

    if w == "cord":
        ts.take("cord")
        name = ts.ident()
        ts.take("=")
        ts.take("tether")
        a = ts.ident("glyph var")
        ts.take("->", what="'->'")
        b = ts.ident("glyph var")
        ts.take(";")
        return S(kind="cord", name=name, a=a, b=b)

    if w == "pipe":
        ts.take("pipe")
        a = ts.ident("glyph var")
        ts.take("->", what="'->'")
        b = ts.ident("glyph var")
        ts.take("width")
        wv = ts.take(kind="num")[1]
        name = None
        if ts.at("as"):
            ts.take("as")
            name = ts.ident()
        ts.take(";")
        return S(kind="pipe", a=a, b=b, width=wv, name=name)

    if w == "thread":
        ts.take("thread")
        brood = ts.ident("brood name")
        ts.take("by")
        vein = _veinref(ts)
        ts.take("as")
        name = ts.ident()
        ts.take(";")
        return S(kind="thread", brood=brood, vein=vein, name=name)

    if w == "flood":
        ts.take("flood")
        name = ts.ident("strand name")
        ts.take(";")
        return S(kind="flood", strand=name)

    if w == "loosen":
        ts.take("loosen")
        brood = ts.ident("brood name")
        trait = _veinref(ts)
        ts.take(";")
        return S(kind="loosen", brood=brood, trait=trait)

    if w == "corral":
        ts.take("corral")
        label = ts.take(kind="str")[1]
        ts.take("{")
        members = [ts.ident("member")]
        while ts.at(","):
            ts.take(",")
            members.append(ts.ident("member"))
        ts.take("}")
        ts.take(";")
        return S(kind="corral", label=label, members=members)

    if w in ("kindle", "hush", "lift", "sink"):
        ts.take(w)
        target = ts.ident("target")
        ts.take(";")
        return S(kind=w, target=target)

    if w == "label":
        ts.take("label")
        target = ts.ident("target")
        text = ts.take(kind="str")[1]
        aim = None
        if ts.at("at"):
            ts.take("at")
            aim = ts.ident("aim")
        ts.take(";")
        return S(kind="label", target=target, text=text, aim=aim)

    if w in ("paint", "veil", "outline", "heft"):
        ts.take(w)
        target = ts.ident("target")
        val = ts.ident("hue") if w == "paint" else ts.take(kind="num")[1]
        ts.take(";")
        return S(kind=w, target=target, value=val)

    if w == "raise":
        ts.take("raise")
        what = ts.ident("rim|weft|key")
        p = _parcel(ts)
        if what == "rim":
            ts.take(":")
            side = ts.ident("side")
            if ts.at("from"):
                ts.take("from")
                ts.ident("gauge/lattice")  # decorative provenance
            ts.take(";")
            return S(kind="rim", parcel=p, side=side)
        if what == "weft":
            ts.take(":")
            d = ts.ident("direction")
            ts.take(";")
            return S(kind="weft", parcel=p, along=d)
        if what == "key":
            ts.take("from")
            brood = ts.ident("brood name")
            trait = _veinref(ts)
            ts.take(";")
            return S(kind="key", parcel=p, brood=brood, trait=trait)
        raise Fault("F106", f"cannot raise '{what}' (rim, weft, key)",
                    ts.file, line)

    if w in ("entitle", "note"):
        ts.take(w)
        p = _parcel(ts)
        text = ts.take(kind="str")[1]
        ts.take(";")
        return S(kind=w, parcel=p, text=text)

    if w == "inscribe":
        ts.take("inscribe")
        text = ts.take(kind="str")[1]
        near = None
        aim = None
        if ts.at("near"):
            ts.take("near")
            near = ts.ident("target")
        if ts.at("at"):
            ts.take("at")
            aim = ts.ident("aim")
        ts.take(";")
        return S(kind="inscribe", text=text, near=near, aim=aim)

    if w == "flag":
        ts.take("flag")
        target = ts.ident("target")
        text = ts.take(kind="str")[1]
        ts.take(";")
        return S(kind="flag", target=target, text=text)

    if w == "use":
        ts.take("use")
        ts.ident()
        ts.take(";")
        return S(kind="use")

    if w == "settle":
        ts.take("settle")
        ts.take("!")
        ts.take(";")
        return S(kind="settle")

    # cord/strand property assignment: name.prop = value ;
    if t[0] == "ident" and ts.peek(1)[1] == "." and ts.peek(1)[0] == "punc":
        name = ts.ident()
        ts.take(".")
        prop = ts.ident("property")
        ts.take("=")
        tv = ts.peek()
        if tv[0] in ("str", "num"):
            ts.i += 1
            val = tv[1]
        else:
            val = ts.ident("value")
        ts.take(";")
        return S(kind="prop", target=name, prop=prop, value=val)

    raise Fault("F107", f"unrecognized statement starting at {w!r}",
                ts.file, line)


def _stage(ts):
    line = ts.line
    w = ts.ident("stage")
    ts.take("(")
    if w in ("keep", "drop"):
        pred = _pred(ts)
        ts.take(")")
        return {"stage": w, "pred": pred, "line": line}
    if w == "fold":
        by = [_veinref(ts)]
        while ts.at(","):
            ts.take(",")
            by.append(_veinref(ts))
        ts.take(";")
        out = ts.ident("output name")
        ts.take("=")
        agg = ts.ident("aggregate")
        if agg not in AGGS:
            raise Fault("F108", f"unknown aggregate '{agg}' "
                        f"({', '.join(AGGS)})", ts.file, line)
        vein = None
        ts.take("(")
        if not ts.at(")"):
            vein = _veinref(ts)
        ts.take(")")
        ts.take(")")
        return {"stage": "fold", "by": by, "out": out, "agg": agg,
                "vein": vein, "line": line}
    if w == "derive":
        name = ts.ident("new vein name")
        ts.take("=")
        if ts.at("share"):
            ts.take("share")
            ts.take("(")
            a = _veinref(ts)
            ts.take(")")
            spec = {"mode": "total_share", "a": a, "b": None}
        else:
            a = _veinref(ts)
            opt = ts.peek()
            if opt[1] not in ("/", "-"):
                raise Fault("F109", "derive supports '/', '-', share(.v)",
                            ts.file, line)
            ts.i += 1
            b = _veinref(ts)
            spec = {"mode": "ratio" if opt[1] == "/" else "diff",
                    "a": a, "b": b}
        ts.take(")")
        return {"stage": "derive", "name": name, **spec, "line": line}
    if w == "rank":
        vein = _veinref(ts)
        ts.take(",")
        sense = ts.ident("asc|desc")
        if sense not in ("asc", "desc"):
            raise Fault("F110", "rank sense must be asc or desc",
                        ts.file, line)
        ts.take(")")
        return {"stage": "rank", "vein": vein, "sense": sense, "line": line}
    if w == "first":
        n = ts.take(kind="num")[1]
        ts.take(")")
        return {"stage": "first", "n": int(n), "line": line}
    if w == "bins":
        vein = _veinref(ts)
        ts.take(",")
        n = ts.take(kind="num")[1]
        ts.take(")")
        return {"stage": "bins", "vein": vein, "n": int(n), "line": line}
    raise Fault("F111", f"unknown pipeline stage '{w}'", ts.file, line)


def _kernel_stmt(ts):
    line = ts.line
    if ts.at("if"):
        ts.take("if")
        ts.take("(")
        pred = _pred(ts)
        ts.take(")")
        ts.take("{")
        actions = []
        while not ts.at("}"):
            aline = ts.line
            w = ts.peek()[1]
            if w in ("kindle", "hush"):
                ts.take(w)
                ts.take("g", what="'g'")
                ts.take(";")
                actions.append({"act": w, "line": aline})
            elif w == "flag":
                ts.take("flag")
                ts.take("g", what="'g'")
                text = ts.take(kind="str")[1]
                ts.take(";")
                actions.append({"act": "flag", "text": text, "line": aline})
            elif w == "paint":
                ts.take("paint")
                ts.take("g", what="'g'")
                hue = ts.ident("hue")
                ts.take(";")
                actions.append({"act": "paint", "hue": hue, "line": aline})
            elif w == "inscribe":
                ts.take("inscribe")
                ts.take("g", what="'g'")
                text = ts.take(kind="str")[1]
                aim = None
                if ts.at("at"):
                    ts.take("at")
                    aim = ts.ident("aim")
                ts.take(";")
                actions.append({"act": "inscribe", "text": text, "aim": aim,
                                "line": aline})
            else:
                raise Fault("F112", f"unknown kernel action '{w}'",
                            ts.file, aline)
        ts.take("}")
        return {"k": "if", "pred": pred, "actions": actions, "line": line}
    ts.take("g", what="'g'")
    ts.take(".")
    field = ts.ident("g.<field>")
    ts.take("=")
    if field == "form":
        form = ts.ident("form")
        ts.take(";")
        return {"k": "form", "form": form, "line": line}
    if field == "badge":
        t = ts.peek()
        if t[0] == "str":
            ts.i += 1
            spec = {"text": t[1], "vein": None}
        else:
            ts.take("text")
            ts.take("(")
            vein = _veinref(ts)
            ts.take(")")
            spec = {"text": None, "vein": vein}
        aim = None
        if ts.at("at"):
            ts.take("at")
            aim = ts.ident("aim")
        ts.take(";")
        return {"k": "badge", **spec, "aim": aim, "line": line}
    if field in TRAITS:
        gauge = ts.ident("gauge name")
        ts.take("(")
        vein = _veinref(ts)
        ts.take(")")
        ts.take(";")
        return {"k": "bind", "trait": field, "gauge": gauge, "vein": vein,
                "line": line}
    raise Fault("F113", f"unknown kernel field 'g.{field}'", ts.file, line)
