"""SIGIL lowering: parsed units -> dependency-ordered symbolic IR.

IR op: {"op", "args", "out", "deps", "file", "line"} — args may contain "$sym"
references bound by earlier ops (cells, ledgers, broods, picks, ...).
"""

import fnmatch

from .sigil_lang import (ASPECTS, AIMS, DIRS, FORMS, Fault, HEADINGS, HUES,
                         LAWS, PALETTES, SIDES, TRAITS, parse_unit)

ASPECT_STMTS = {
    "data": {"ledger"},
    "ground": {"lattice", "cleave", "split", "hoop", "law", "invert",
               "breathe", "align", "abut", "palette", "arena"},
    "marks": {"arena", "brood", "route", "commit", "gauge", "calibrate",
              "over", "pick", "spawn", "cord", "pipe", "thread", "flood",
              "loosen", "corral", "kindle", "hush", "lift", "sink", "paint",
              "veil", "outline", "heft", "prop", "label"},
    "script": {"rim", "weft", "key", "entitle", "note", "inscribe", "flag"},
    "compose": {"use", "settle"},
}

# emission phase per op kind (Kahn tie-break; topo edges still dominate)
PHASE = {"_load": 0, "_alias": 0, "sift": 0, "distill": 0, "derive": 0,
         "bin": 0, "marshal": 0, "crop": 0,
         "carve": 2, "split": 2, "hoop": 2, "invert": 2,
         "breathe": 2, "palette": 2,
         "settle": 6.5,  # laws validate against meterings (strew)
         "cell": 3, "nest": 4,
         "place": 5, "sow": 5,
         "meter": 6, "loosen": 6, "rebase": 6, "share": 6, "abut": 6,
         "tether": 7, "pipe": 7, "thread": 7, "flood": 7, "barb": 7,
         "sweep": 7, "crook": 7, "heft": 7,
         "pick": 8, "flock": 8, "corral": 8, "kindle": 8, "hush": 8,
         "tint": 8, "veil": 8, "outline": 8, "lift": 8, "sink": 8,
         "badge": 9, "inscribe": 9, "flag": 9, "entitle": 9, "note": 9,
         "rim": 9, "weft": 9, "key": 9}


class Lowerer:
    def __init__(self):
        self.ops = []
        self.symbols = {}       # name -> declaring info
        self.parcel_struct = {} # parcel-ref-string -> [op indices mutating it]
        self.cell_cache = {}    # (base_ref, at) -> symbol
        self.n = 0

    def fault(self, code, msg, stmt):
        raise Fault(code, msg, stmt.get("file"), stmt.get("line"))

    def emit(self, op, args, stmt, out=None, deps=(), after_struct=None):
        idx = len(self.ops)
        deps = set(d for d in deps if d)
        if after_struct:
            deps |= {("#", i) for i in self.parcel_struct.get(after_struct, [])}
        self.ops.append({"op": op, "args": args, "out": out,
                         "deps": deps, "file": stmt.get("file"),
                         "line": stmt.get("line"),
                         "phase": PHASE.get(op, 9), "idx": idx})
        return idx

    def declare(self, name, kind, stmt, **info):
        if name in self.symbols:
            self.fault("F210", f"'{name}' already declared "
                       f"(as {self.symbols[name]['kind']})", stmt)
        self.symbols[name] = {"kind": kind, **info}

    def sym(self, name, kinds, stmt, what=None):
        s = self.symbols.get(name)
        if not s or s["kind"] not in kinds:
            have = f" ('{name}' is a {s['kind']})" if s else ""
            self.fault("F201", f"unknown {what or '/'.join(kinds)} "
                       f"'{name}'{have}", stmt)
        return s

    # -- parcel expressions ------------------------------------------------
    def parcel_ref(self, p, stmt):
        """Resolve a parcel expr to (arg_value, dep_symbols, ref_string)."""
        base = p["base"]
        if base == "root":
            bref, bdeps = "p0", set()
        else:
            s = self.sym(base, ("arena",), stmt, "arena")
            bref, bdeps = f"${base}", {f"${base}"}
        key = f"{bref}"
        if p["at"] is None:
            return bref, bdeps, key
        ck = (bref, p["at"])
        if ck not in self.cell_cache:
            self.n += 1
            out = f"$cell{self.n}"
            self.emit("cell", {"parcel": bref, "at": p["at"]}, stmt, out=out,
                      deps=bdeps, after_struct=key)
            self.cell_cache[ck] = out
        cref = self.cell_cache[ck]
        return cref, {cref}, cref

    def mark_struct(self, ref_string, idx):
        self.parcel_struct.setdefault(ref_string, []).append(idx)


def _pred_chain(lw, source_sym, pred, stmt, name=None):
    """Lower a conjunction into chained pick ops; return final symbol."""
    cur = source_sym
    for i, (vein, rel, val) in enumerate(pred):
        last = (i == len(pred) - 1)
        lw.n += 1
        out = f"${name}" if (last and name) else f"$sel{lw.n}"
        lw.emit("pick", {"brood": cur, "vein": vein, "relation": rel,
                         "value": val}, stmt, out=out, deps={cur})
        cur = out
    return cur


def lower(units):
    """units: list of (aspect, stmts, path). Returns dependency-sorted IR."""
    lw = Lowerer()
    order = {"data": 0, "ground": 1, "marks": 2, "script": 3, "compose": 4}
    units = sorted(units, key=lambda u: order[u[0]])

    settles = 0
    broods = {}   # name -> {"ledger","route","form","committed","gauges"}
    gauges = {}   # name -> {"gkind","bindings":[(brood,trait)],"calibrated"}
    aspects_present = {a for a, _, _ in units}

    # pre-scan: a brood's form may be declared in an over-block anywhere in
    # the project, including after its commit statement
    forms_pre = {}
    for aspect, stmts, path in units:
        for st in stmts:
            if st["kind"] != "over":
                continue
            for ks in st["body"]:
                if ks["k"] != "form":
                    continue
                prev = forms_pre.get(st["brood"])
                if prev and prev != ks["form"]:
                    raise Fault("F222", f"brood '{st['brood']}' given two "
                                f"forms", st["file"], ks["line"])
                forms_pre[st["brood"]] = ks["form"]

    for aspect, stmts, path in units:
        for st in stmts:
            if st["kind"] not in ASPECT_STMTS[aspect]:
                allowed = next((a for a, ks in ASPECT_STMTS.items()
                                if st["kind"] in ks), "?")
                raise Fault("F312", f"'{st['kind']}' not permitted in unit of "
                            f"aspect '{aspect}' (belongs in '{allowed}')",
                            st["file"], st["line"])
            if aspect == "ground" and st["kind"] == "arena" and st.get("host"):
                raise Fault("F313", "nest under a glyph belongs in a 'marks' "
                            "unit", st["file"], st["line"])
            lower_stmt(lw, st, broods, gauges, forms_pre)
            if st["kind"] == "settle":
                settles += 1

    if "compose" not in aspects_present:
        raise Fault("F251", "no compose unit; add a unit with `settle!;`")
    if settles == 0:
        raise Fault("F251", "missing `settle!;` in the compose unit")
    if settles > 1:
        raise Fault("F251", "more than one `settle!;`")

    # broods that were used but never committed
    for name, b in broods.items():
        if not b["committed"] and b["used"]:
            raise Fault("F223", f"brood '{name}' is bound/used but never "
                        f"committed", b["stmt"]["file"], b["stmt"]["line"])
    # gauge ceremony
    for name, g in gauges.items():
        if g["gkind"] == "counted" and g["bindings"] and not g["calibrated"]:
            b0 = g["bindings"][0]
            raise Fault("F244", f"counted gauge '{name}' is bound "
                        f"(e.g. {b0[0]}.{b0[1]}) but never calibrated",
                        g["stmt"]["file"], g["stmt"]["line"])

    return _toposort(lw)


def _toposort(lw):
    ops = lw.ops
    produced = {}
    for o in ops:
        if o["out"]:
            produced[o["out"]] = o["idx"]
    indeg = {o["idx"]: 0 for o in ops}
    edges = {o["idx"]: [] for o in ops}
    for o in ops:
        for d in o["deps"]:
            src = d[1] if isinstance(d, tuple) else produced.get(d)
            if src is None:
                raise Fault("F201", f"reference to unbound symbol '{d}'",
                            o["file"], o["line"])
            if src != o["idx"]:
                edges[src].append(o["idx"])
                indeg[o["idx"]] += 1
    import heapq
    ready = [(ops[i]["phase"], i) for i in indeg if indeg[i] == 0]
    heapq.heapify(ready)
    out = []
    while ready:
        _, i = heapq.heappop(ready)
        out.append(ops[i])
        for j in edges[i]:
            indeg[j] -= 1
            if indeg[j] == 0:
                heapq.heappush(ready, (ops[j]["phase"], j))
    if len(out) != len(ops):
        raise Fault("F214", "circular dependency between statements")
    return out


def _lower_stage(lw, cur, stage, st):
    """Lower one pipeline stage; returns the new ledger symbol."""
    fake = {"file": st["file"], "line": stage.get("line", st["line"])}
    sg = stage["stage"]

    def emit(op, args):
        lw.n += 1
        out = f"$led{lw.n}"
        lw.emit(op, args, fake, out=out, deps={cur})
        return out

    if sg in ("keep", "drop"):
        inv = {"is": "is_not", "is_not": "is", "above": "at_most",
               "below": "at_least", "at_least": "below", "at_most": "above"}
        for vein, rel, val in stage["pred"]:
            if sg == "drop":
                if rel not in inv:
                    raise Fault("F209", "drop accepts ==, !=, <, >, <=, >=",
                                fake["file"], fake["line"])
                rel = inv[rel]
            cur = emit("sift", {"ledger": cur, "vein": vein,
                                "relation": rel, "value": val})
        return cur
    if sg == "fold":
        by = stage["by"] if len(stage["by"]) > 1 else stage["by"][0]
        if stage["agg"] == "count":
            return emit("distill", {"ledger": cur, "by": by, "mode": "count"})
        return emit("distill", {"ledger": cur, "by": by, "mode": stage["agg"],
                                "take": stage["vein"]})
    if sg == "derive":
        args = {"ledger": cur, "name": stage["name"], "mode": stage["mode"],
                "a": stage["a"]}
        if stage.get("b"):
            args["b"] = stage["b"]
        return emit("derive", args)
    if sg == "rank":
        sense = "waxing" if stage["sense"] == "asc" else "waning"
        return emit("marshal", {"ledger": cur, "vein": stage["vein"],
                                "sense": sense})
    if sg == "first":
        return emit("crop", {"ledger": cur, "first": stage["n"]})
    if sg == "bins":
        return emit("bin", {"ledger": cur, "vein": stage["vein"],
                            "bins": stage["n"]})
    raise Fault("F111", f"unknown stage '{sg}'", fake["file"], fake["line"])


def lower_stmt(lw, st, broods, gauges, forms_pre=None):
    k = st["kind"]
    forms_pre = forms_pre or {}

    if k == "ledger":
        cur = None
        if "open" in st["src"]:
            lw.n += 1
            cur = f"$led{lw.n}"
            lw.emit("_load", {"path": st["src"]["open"],
                              "schema": st["src"]["schema"]}, st, out=cur)
        else:
            lw.sym(st["src"]["ref"], ("ledger",), st, "ledger")
            cur = f"${st['src']['ref']}"
        for stage in st["stages"]:
            cur = _lower_stage(lw, cur, stage, st)
        lw.declare(st["name"], "ledger", st)
        # alias final symbol to the declared name
        lw.emit("_alias", {"of": cur}, st, out=f"${st['name']}", deps={cur})
        return

    if k == "lattice":
        lw.sym(st["ledger"], ("ledger",), st, "ledger")
        lw.declare(st["name"], "lattice", st, ledger=st["ledger"],
                   vein=st["vein"])
        return

    if k == "cleave":
        lat = lw.sym(st["lattice"], ("lattice",), st, "lattice")
        if st["along"] not in DIRS:
            lw.fault("F204", f"direction must be span|rise", st)
        ref, deps, key = lw.parcel_ref(st["parcel"], st)
        args = {"parcel": ref, "along": st["along"],
                "ledger": f"${lat['ledger']}", "by": lat["vein"]}
        if st["gap"] is not None:
            args["gap"] = st["gap"]
        idx = lw.emit("carve", args, st, deps=deps | {f"${lat['ledger']}"})
        lw.mark_struct(key, idx)
        return

    if k == "split":
        ref, deps, key = lw.parcel_ref(st["parcel"], st)
        args = {"parcel": ref, "along": st["along"], "count": st["count"]}
        if st["gap"] is not None:
            args["gap"] = st["gap"]
        idx = lw.emit("split", args, st, deps=deps)
        lw.mark_struct(key, idx)
        return

    if k == "hoop":
        ref, deps, key = lw.parcel_ref(st["parcel"], st)
        args = {"parcel": ref}
        if st["inner"] is not None:
            args["inner"] = st["inner"]
        idx = lw.emit("hoop", args, st, deps=deps)
        lw.mark_struct(key, idx)
        return

    if k == "law":
        if st["law"] not in LAWS:
            lw.fault("F205", f"unknown law '{st['law']}'", st)
        ref, deps, key = lw.parcel_ref(st["parcel"], st)
        args = {"parcel": ref, "law": st["law"]}
        if st["heading"]:
            args["heading"] = st["heading"]
        lw.emit("settle", args, st, deps=deps)  # laws never gate sowing
        return

    if k in ("invert", "breathe", "palette"):
        ref, deps, key = lw.parcel_ref(st["parcel"], st)
        if k == "invert":
            lw.emit("invert", {"parcel": ref, "along": st["along"]},
                    st, deps=deps)
        elif k == "breathe":
            lw.emit("breathe", {"parcel": ref, "amount": st["amount"]},
                    st, deps=deps)
        else:
            lw.emit("palette", {"parcel": ref, "name": st["name"]},
                    st, deps=deps)
        return

    if k in ("align", "abut"):
        ra, da, _ = lw.parcel_ref(st["a"], st)
        rb, db, _ = lw.parcel_ref(st["b"], st)
        if k == "align":
            lw.emit("share", {"parcel_a": ra, "parcel_b": rb,
                              "trait": st["arg"]}, st, deps=da | db)
        else:
            lw.emit("abut", {"parcel_a": ra, "parcel_b": rb,
                             "edge": st["arg"]}, st, deps=da | db)
        return

    if k == "arena":
        args = {}
        deps = set()
        if st["host"]:
            hs = lw.sym(st["host"], ("spawn",), st, "glyph")
            args["host"] = f"${st['host']}"
            deps = {f"${st['host']}"}
        else:
            ref, deps, _ = lw.parcel_ref(st["parcel"], st)
            args["parcel"] = ref
        for f in ("aim", "breadth", "depth"):
            if st.get(f) is not None:
                args[f] = st[f]
        lw.declare(st["name"], "arena", st)
        lw.emit("nest", args, st, out=f"${st['name']}", deps=deps)
        return

    if k == "brood":
        lw.sym(st["ledger"], ("ledger",), st, "ledger")
        lw.declare(st["name"], "brood", st)
        broods[st["name"]] = {"ledger": st["ledger"], "route": None,
                              "form": None, "committed": False,
                              "used": False, "stmt": st}
        return

    if k == "route":
        b = broods.get(st["brood"])
        if not b:
            lw.fault("F201", f"unknown brood '{st['brood']}'", st)
        if b["committed"]:
            lw.fault("F225", f"brood '{st['brood']}' routed after commit", st)
        b["route"] = st
        return

    if k == "commit":
        b = broods.get(st["brood"])
        if not b:
            lw.fault("F201", f"unknown brood '{st['brood']}'", st)
        if b["committed"]:
            lw.fault("F226", f"brood '{st['brood']}' committed twice", st)
        if not b["route"]:
            lw.fault("F224", f"brood '{st['brood']}' committed without a "
                     f"route", st)
        if not b["form"]:
            b["form"] = forms_pre.get(st["brood"])
        if not b["form"]:
            lw.fault("F221", f"brood '{st['brood']}' committed without a "
                     f"form (set g.form in an over-block)", st)
        ref, deps, key = lw.parcel_ref(b["route"]["parcel"], st)
        args = {"parcel": ref, "ledger": f"${b['ledger']}", "form": b["form"]}
        if b["route"]["by"]:
            args["key"] = b["route"]["by"]
        lw.emit("sow", args, st, out=f"${st['brood']}",
                deps=deps | {f"${b['ledger']}"},
                after_struct=key)
        b["committed"] = True
        b["parcel_expr"] = b["route"]["parcel"]
        return

    if k == "gauge":
        lw.declare(st["name"], "gauge", st)
        gauges[st["name"]] = {"gkind": st["gkind"], "bindings": [],
                              "calibrated": False, "stmt": st}
        return

    if k == "calibrate":
        g = gauges.get(st["gauge"])
        if not g:
            lw.fault("F201", f"unknown gauge '{st['gauge']}'", st)
        if not g["bindings"]:
            lw.fault("F245", f"calibrate of unbound gauge '{st['gauge']}'",
                     st)
        g["calibrated"] = True
        if st["floor"] is None and st["ceil"] is None:
            return  # auto calibration — the instrument resolves the domain
        bname, trait = g["bindings"][0]
        b = broods[bname]
        # keyed routes calibrate on the base parcel; direct routes on the cell
        pexpr = dict(b["parcel_expr"])
        if b["route"]["by"]:
            pexpr["at"] = None
        ref, deps, _ = lw.parcel_ref(pexpr, st)
        args = {"parcel": ref, "trait": trait}
        if st["floor"] is not None:
            args["floor"] = st["floor"]
        if st["ceil"] is not None:
            args["ceil"] = st["ceil"]
        lw.emit("rebase", args, st, deps=deps)
        return

    if k == "over":
        b = broods.get(st["brood"])
        if not b:
            lw.fault("F201", f"unknown brood '{st['brood']}'", st)
        bsym = f"${st['brood']}"
        for ks in st["body"]:
            if ks["k"] == "form":
                if ks["form"] not in FORMS:
                    raise Fault("F206", f"unknown form '{ks['form']}'",
                                st["file"], ks["line"])
                if b["form"] and b["form"] != ks["form"]:
                    raise Fault("F222", f"brood '{st['brood']}' given two "
                                f"forms", st["file"], ks["line"])
                b["form"] = ks["form"]
            elif ks["k"] == "bind":
                g = gauges.get(ks["gauge"])
                if not g:
                    raise Fault("F241", f"unknown gauge '{ks['gauge']}'",
                                st["file"], ks["line"])
                g["bindings"].append((st["brood"], ks["trait"]))
                b["used"] = True
                lw.emit("meter", {"brood": bsym, "trait": ks["trait"],
                                  "vein": ks["vein"]},
                        {"file": st["file"], "line": ks["line"]},
                        deps={bsym})
            elif ks["k"] == "badge":
                b["used"] = True
                args = {"target": bsym}
                if ks["vein"]:
                    args["vein"] = ks["vein"]
                else:
                    args["text"] = ks["text"]
                if ks["aim"]:
                    args["aim"] = ks["aim"]
                lw.emit("badge", args,
                        {"file": st["file"], "line": ks["line"]},
                        deps={bsym})
            elif ks["k"] == "if":
                b["used"] = True
                fake = {"file": st["file"], "line": ks["line"]}
                sel = _pred_chain(lw, bsym, ks["pred"], fake)
                for act in ks["actions"]:
                    af = {"file": st["file"], "line": act["line"]}
                    if act["act"] in ("kindle", "hush"):
                        lw.emit(act["act"], {"target": sel}, af, deps={sel})
                    elif act["act"] == "flag":
                        lw.emit("flag", {"target": sel, "text": act["text"]},
                                af, deps={sel})
                    elif act["act"] == "paint":
                        lw.emit("tint", {"target": sel, "hue": act["hue"]},
                                af, deps={sel})
                    elif act["act"] == "inscribe":
                        args = {"text": act["text"], "near": sel}
                        if act.get("aim"):
                            args["aim"] = act["aim"]
                        lw.emit("inscribe", args, af, deps={sel})
        return

    if k == "pick":
        b = broods.get(st["brood"])
        src = f"${st['brood']}"
        if not b:
            s = lw.symbols.get(st["brood"])
            if not s or s["kind"] not in ("brood", "selection"):
                lw.fault("F201", f"unknown brood/selection '{st['brood']}'",
                         st)
        else:
            b["used"] = True
        lw.declare(st["name"], "selection", st)
        _pred_chain(lw, src, st["pred"], st, name=st["name"])
        return

    if k == "spawn":
        if st["form"] not in FORMS:
            lw.fault("F206", f"unknown form '{st['form']}'", st)
        ref, deps, key = lw.parcel_ref(st["parcel"], st)
        lw.declare(st["name"], "spawn", st, label=st["label"])
        lw.emit("place", {"parcel": ref, "form": st["form"],
                          "name": st["label"]}, st, out=f"${st['name']}",
                deps=deps, after_struct=key)
        return

    if k == "cord":
        a = lw.sym(st["a"], ("spawn",), st, "glyph")
        bb = lw.sym(st["b"], ("spawn",), st, "glyph")
        lw.declare(st["name"], "cord", st)
        lw.emit("tether", {"tail": f"${st['a']}", "head": f"${st['b']}"},
                st, out=f"${st['name']}", deps={f"${st['a']}", f"${st['b']}"})
        return

    if k == "pipe":
        lw.sym(st["a"], ("spawn",), st, "glyph")
        lw.sym(st["b"], ("spawn",), st, "glyph")
        out = None
        if st["name"]:
            lw.declare(st["name"], "cord", st)
            out = f"${st['name']}"
        lw.emit("pipe", {"tail": f"${st['a']}", "head": f"${st['b']}",
                         "width": st["width"]}, st, out=out,
                deps={f"${st['a']}", f"${st['b']}"})
        return

    if k == "thread":
        b = broods.get(st["brood"])
        if not b:
            lw.fault("F201", f"unknown brood '{st['brood']}'", st)
        b["used"] = True
        lw.declare(st["name"], "strand", st)
        lw.emit("thread", {"brood": f"${st['brood']}", "by": st["vein"]},
                st, out=f"${st['name']}", deps={f"${st['brood']}"})
        return

    if k == "flood":
        lw.sym(st["strand"], ("strand",), st, "strand")
        lw.emit("flood", {"strand": f"${st['strand']}"}, st,
                deps={f"${st['strand']}"})
        return

    if k == "loosen":
        b = broods.get(st["brood"])
        if not b:
            lw.fault("F201", f"unknown brood '{st['brood']}'", st)
        b["used"] = True
        lw.emit("loosen", {"brood": f"${st['brood']}", "trait": st["trait"]},
                st, deps={f"${st['brood']}"})
        return

    if k == "corral":
        deps = set()
        members = []
        for m in st["members"]:
            lw.sym(m, ("spawn",), st, "glyph")
            members.append(f"${m}")
            deps.add(f"${m}")
        lw.emit("corral", {"members": members, "label": st["label"]}, st,
                deps=deps)
        return

    if k in ("kindle", "hush", "lift", "sink"):
        tsym, deps = _target(lw, st["target"], st, broods)
        lw.emit(k, {"target": tsym}, st, deps=deps)
        return

    if k == "label":
        tsym, deps = _target(lw, st["target"], st, broods)
        args = {"target": tsym, "text": st["text"]}
        if st.get("aim"):
            args["aim"] = st["aim"]
        lw.emit("badge", args, st, deps=deps)
        return

    if k in ("paint", "veil", "outline", "heft"):
        tsym, deps = _target(lw, st["target"], st, broods)
        opname = {"paint": "tint", "veil": "veil", "outline": "outline",
                  "heft": "heft"}[k]
        argname = {"paint": "hue", "veil": "amount", "outline": "weight",
                   "heft": "weight"}[k]
        lw.emit(opname, {"target": tsym, argname: st["value"]}, st, deps=deps)
        return

    if k == "prop":
        s = lw.sym(st["target"], ("cord", "strand"), st, "cord/strand")
        tsym = f"${st['target']}"
        p, v = st["prop"], st["value"]
        table = {"barb": ("barb", "at"), "sweep": ("sweep", "amount"),
                 "crook": ("crook", "style"), "heft": ("heft", "weight"),
                 "badge": ("badge", "text")}
        if p not in table:
            lw.fault("F207", f"unknown property '.{p}' "
                     f"({', '.join(table)})", st)
        opname, argname = table[p]
        args = {("cord" if opname in ("barb", "sweep", "crook") else
                 "target"): tsym, argname: v}
        lw.emit(opname, args, st, deps={tsym})
        return

    if k == "rim":
        ref, deps, _ = lw.parcel_ref(st["parcel"], st)
        lw.emit("rim", {"parcel": ref, "side": st["side"]}, st, deps=deps)
        return
    if k == "weft":
        ref, deps, _ = lw.parcel_ref(st["parcel"], st)
        lw.emit("weft", {"parcel": ref, "along": st["along"]}, st, deps=deps)
        return
    if k == "key":
        b = broods.get(st["brood"])
        if not b:
            lw.fault("F201", f"unknown brood '{st['brood']}'", st)
        b["used"] = True
        ref, deps, _ = lw.parcel_ref(st["parcel"], st)
        lw.emit("key", {"parcel": ref, "brood": f"${st['brood']}",
                        "trait": st["trait"]}, st,
                deps=deps | {f"${st['brood']}"})
        return
    if k in ("entitle", "note"):
        ref, deps, _ = lw.parcel_ref(st["parcel"], st)
        lw.emit(k, {"parcel": ref, "text": st["text"]}, st, deps=deps)
        return
    if k == "inscribe":
        args = {"text": st["text"]}
        deps = set()
        if st["near"]:
            tsym, deps = _target(lw, st["near"], st, broods)
            args["near"] = tsym
        if st["aim"]:
            args["aim"] = st["aim"]
        lw.emit("inscribe", args, st, deps=deps)
        return
    if k == "flag":
        tsym, deps = _target(lw, st["target"], st, broods)
        lw.emit("flag", {"target": tsym, "text": st["text"]}, st, deps=deps)
        return
    if k in ("use", "settle"):
        return

    lw.fault("F208", f"statement '{k}' not lowerable", st)


def _target(lw, name, st, broods):
    s = lw.symbols.get(name)
    if not s:
        lw.fault("F201", f"unknown target '{name}'", st)
    if s["kind"] == "brood":
        broods[name]["used"] = True
    return f"${name}", {f"${name}"}


# ----------------------------------------------------------------------
# project compilation
# ----------------------------------------------------------------------

def compile_project(files):
    """files: {path: source}. Returns (ir, stats). Raises Fault."""
    units = []
    for path in sorted(files):
        aspect, stmts = parse_unit(files[path], path)
        units.append((aspect, stmts, path))
    if not units:
        raise Fault("F001", "no .sgl units found (check sigil.toml)")
    ir = lower(units)
    n_stmts = sum(len(s) for _, s, _ in units)
    return ir, {"units": len(units), "statements": n_stmts,
                "ops": len([o for o in ir if o["op"] != "_alias"])}
