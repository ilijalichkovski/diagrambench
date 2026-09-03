"""VELD operations: registry, dispatcher, and every op implementation.

The dispatcher enforces syntax (arg names, required args, enums) with
instructive-but-semantics-free errors; each op enforces its own state
constraints the same way.
"""

from .datasets import DATASETS
from .errors import VeldError
from .gauges import GaugeSet
from .ledgers import (DERIVE_MODES, DISTILL_MODES, RELATIONS, SENSES, LedgerSpace)
from .scene import (AIMS, FORMS, HEADINGS, HUES, LAWS, PALETTES, SIDES, TRAITS,
                    Annotation, Brood, Cord, Corral, Flock, Glyph, Key, Parcel,
                    Scene, Strand)

FORM_GLOSS = {
    "slab": "rectangular block",
    "disc": "filled round",
    "wisp": "small point",
    "ring": "open round",
    "capsule": "rounded vessel",
    "rhomb": "tilted quad",
    "drum": "cylinder",
    "plaque": "text card",
}

FAMILY_ORDER = [
    "ledgers", "ground", "sowing", "metering", "settling", "cords", "bands",
    "script", "guides", "emphasis", "layers", "patina", "oracle", "helm",
]


class Param:
    def __init__(self, name, wtype, required=True, enum=None):
        self.name = name
        self.wtype = wtype
        self.required = required
        self.enum = enum


class OpDef:
    def __init__(self, name, family, params, fn, mutates=True, returns=None):
        self.name = name
        self.family = family
        self.params = params
        self.fn = fn
        self.mutates = mutates
        self.returns = returns

    def signature(self):
        parts = [p.name if p.required else p.name + "?" for p in self.params]
        return f"{self.name}({', '.join(parts)})"


OPS = {}


def op(family, params, mutates=True, returns=None):
    def deco(fn):
        name = fn.__name__.rstrip("_")
        OPS[name] = OpDef(name, family, params, fn, mutates, returns)
        return fn
    return deco


# ======================================================================
# Task environment
# ======================================================================

class TaskEnv:
    """One task's live state: scene + ledgers + undo stack + trace."""

    def __init__(self):
        self.scene = Scene()
        self.ledgers = LedgerSpace()
        self._undo = []
        self.trace_log = []  # successful mutating calls

    def snapshot(self):
        import copy
        self._undo.append((self.scene.snapshot(), copy.deepcopy(self.ledgers),
                           list(self.trace_log)))
        if len(self._undo) > 60:
            self._undo.pop(0)

    def act(self, opname, args=None):
        """Dispatch one op call. Returns an observation dict."""
        args = dict(args or {})
        base = {"op": opname, "args": args}
        if opname not in OPS:
            close = ", ".join(sorted(OPS)) if len(OPS) < 8 else \
                "use families() then ops(family) to browse"
            return {**base, "ok": False, "mutated": False,
                    "error": f"unknown op '{opname}' ({close})."}
        od = OPS[opname]
        accepted = [p.name for p in od.params]
        for a in args:
            if a not in accepted:
                return {**base, "ok": False, "mutated": False, "error":
                        f"{opname}: unknown argument '{a}'. Accepted: "
                        f"{', '.join(accepted) or '(none)'}."}
        for p in od.params:
            if p.required and p.name not in args:
                return {**base, "ok": False, "mutated": False, "error":
                        f"{opname}: missing required argument '{p.name}' ({p.wtype})."}
            if p.name in args and p.enum is not None:
                v = args[p.name]
                if v not in p.enum:
                    return {**base, "ok": False, "mutated": False, "error":
                            f"{opname}: '{v}' is not a valid {p.name}. "
                            f"Options: {', '.join(str(e) for e in p.enum)}."}
        if od.mutates:
            self.snapshot()
        try:
            out = od.fn(self, **args)
        except VeldError as e:
            if od.mutates:  # restore pre-call state (op may have half-mutated)
                self.scene, self.ledgers, self.trace_log = self._undo.pop()
            return {**base, "ok": False, "mutated": False, "error": f"{opname}: {e}"
                    if not str(e).startswith(opname) else str(e)}
        except Exception as e:
            if od.mutates:
                self.scene, self.ledgers, self.trace_log = self._undo.pop()
            return {**base, "ok": False, "mutated": False,
                    "error": f"{opname}: refused — arguments do not fit "
                             f"({type(e).__name__})."}
        if od.mutates:
            self.trace_log.append((opname, args))
        if isinstance(out, tuple):
            text, ref = out
        else:
            text, ref = out, None
        obs = {**base, "ok": True, "mutated": od.mutates, "text": text}
        if ref:
            obs["ref"] = ref
        if opname == "present":
            obs["present"] = True
        return obs

    def gauges(self):
        return GaugeSet(self.scene, self.ledgers)


# ======================================================================
# family: ledgers
# ======================================================================

@op("ledgers", [], mutates=False)
def shelf(env):
    lines = ["base ledgers:"]
    for name, rows in DATASETS.items():
        lines.append(f"  {name}  ({len(rows)} rows: {', '.join(rows[0].keys())})")
    if env.ledgers.derived:
        lines.append("derived:")
        for ref, led in env.ledgers.derived.items():
            lines.append(f"  {ref}  ({len(led.rows)} rows: {', '.join(led.vein_names())})")
    return "\n".join(lines)


@op("ledgers", [Param("ledger", "ledger name|ref"),
                Param("rows", "number", required=False)], mutates=False)
def peek(env, ledger, rows=6):
    led = env.ledgers.resolve(ledger)
    if not isinstance(rows, int) or rows < 1:
        raise VeldError("rows must be a positive integer.")
    names = led.vein_names()
    lines = ["  ".join(names)]
    for r in led.rows[:rows]:
        lines.append("  ".join(str(r[n]) for n in names))
    if len(led.rows) > rows:
        lines.append(f"… {len(led.rows) - rows} more rows")
    return "\n".join(lines)


@op("ledgers", [Param("ledger", "ledger name|ref")], mutates=False)
def veins(env, ledger):
    led = env.ledgers.resolve(ledger)
    lines = []
    for name, kind in led.veins().items():
        vals = led.values(name)
        if kind == "counted":
            lines.append(f"  {name}: counted [{min(vals):g} … {max(vals):g}]")
        else:
            lv = led.ordered_levels(name)
            shown = ", ".join(str(v) for v in lv[:6]) + ("…" if len(lv) > 6 else "")
            lines.append(f"  {name}: {kind} ({len(lv)} levels: {shown})")
    return "\n".join(lines)


@op("ledgers", [Param("ledger", "ledger name|ref"), Param("vein", "vein name"),
                Param("relation", "enum", enum=RELATIONS), Param("value", "value")])
def sift(env, ledger, vein, relation, value):
    led = env.ledgers.sift(ledger, vein, relation, value)
    return (f"{led.ref}: {len(led.rows)} rows kept where {vein} {relation} {value!r}.",
            led.ref)


@op("ledgers", [Param("ledger", "ledger name|ref"), Param("by", "vein name|list"),
                Param("mode", "enum", enum=DISTILL_MODES),
                Param("take", "vein name", required=False)])
def distill(env, ledger, by, mode, take=None):
    led = env.ledgers.distill(ledger, by, take, mode)
    return (f"{led.ref}: {len(led.rows)} rows — {mode} of "
            f"{take or 'rows'} by {by}.", led.ref)


@op("ledgers", [Param("ledger", "ledger name|ref"), Param("name", "text"),
                Param("mode", "enum", enum=DERIVE_MODES), Param("a", "vein name"),
                Param("b", "vein name", required=False)])
def derive(env, ledger, name, mode, a, b=None):
    led = env.ledgers.derive(ledger, name, mode, a, b)
    return (f"{led.ref}: new counted vein '{name}' ({mode}).", led.ref)


@op("ledgers", [Param("ledger", "ledger name|ref"), Param("vein", "vein name"),
                Param("bins", "number", required=False)])
def bin_(env, ledger, vein, bins=8):
    led = env.ledgers.bin(ledger, vein, bins)
    return (f"{led.ref}: {len(led.rows)} bins of '{vein}' with veins bin, tally.",
            led.ref)


@op("ledgers", [Param("ledger", "ledger name|ref"), Param("vein", "vein name"),
                Param("sense", "enum", enum=SENSES)])
def marshal(env, ledger, vein, sense):
    led = env.ledgers.marshal(ledger, vein, sense)
    return (f"{led.ref}: rows marshaled by '{vein}' ({sense}).", led.ref)


@op("ledgers", [Param("ledger", "ledger name|ref"), Param("first", "number")])
def crop(env, ledger, first):
    led = env.ledgers.crop(ledger, first)
    return (f"{led.ref}: first {len(led.rows)} rows kept.", led.ref)


# ======================================================================
# family: ground
# ======================================================================

def _fresh_for_structure(env, p, what):
    if p.carve:
        raise VeldError(f"parcel {p.id} is already carved by '{p.carve['by']}'.")
    if p.split:
        raise VeldError(f"parcel {p.id} is already split.")
    direct = [g for g in env.scene.glyphs.values() if g.parcel == p.id]
    if direct:
        raise VeldError(
            f"parcel {p.id} already hosts {len(direct)} glyphs; {what} must "
            f"come before sowing/placing (undo, or nest a fresh parcel).")


@op("ground", [Param("parcel", "parcel ref"),
               Param("along", "enum", enum=["span", "rise"]),
               Param("ledger", "ledger name|ref"), Param("by", "vein name"),
               Param("gap", "number 0..1", required=False)])
def carve(env, parcel, along, ledger, by, gap=None):
    scene = env.scene
    p = scene.parcel(parcel)
    if p.hooped:
        raise VeldError(f"parcel {p.id} is hooped; hooped parcels cannot be carved.")
    _fresh_for_structure(env, p, "carving")
    led = env.ledgers.resolve(ledger)
    kind = led.kind_of(by)
    if kind == "counted":
        raise VeldError(f"'by' must be a told or ranked vein; '{by}' is counted.")
    levels = led.ordered_levels(by)
    if len(levels) > 30:
        raise VeldError(f"'{by}' has {len(levels)} levels; carve accepts at most 30.")
    cells = {}
    ids = []
    for lv in levels:
        cid = scene.next_id("p")
        cells[lv] = cid
        ids.append(cid)
        scene.parcels[cid] = Parcel(cid, parent=p.id, cell_key=lv, kind="cell")
    p.carve = {"along": along, "ledger": led.ref, "by": by,
               "gap": gap if gap is not None else 0.18,
               "cells": cells, "order": levels}
    return (f"{p.id} carved along {along} into {len(levels)} cells by '{by}': "
            f"{', '.join(str(l) for l in levels)} (cells {ids[0]}–{ids[-1]}).", None)


@op("ground", [Param("parcel", "parcel ref"),
               Param("along", "enum", enum=["span", "rise"]),
               Param("count", "number"),
               Param("gap", "number 0..1", required=False)])
def split(env, parcel, along, count, gap=None):
    scene = env.scene
    p = scene.parcel(parcel)
    if p.hooped:
        raise VeldError(f"parcel {p.id} is hooped and cannot be split.")
    _fresh_for_structure(env, p, "splitting")
    if not isinstance(count, int) or not (2 <= count <= 8):
        raise VeldError("count must be an integer between 2 and 8.")
    ids = []
    for _ in range(count):
        cid = scene.next_id("p")
        ids.append(cid)
        scene.parcels[cid] = Parcel(cid, parent=p.id, kind="split")
    p.split = {"along": along, "count": count,
               "gap": gap if gap is not None else 0.08, "cells": ids}
    return (f"{p.id} split along {along} into {count} panels: {', '.join(ids)}.",
            ids[0])


@op("ground", [Param("parcel", "parcel ref"), Param("at", "cell key|index")],
    mutates=False)
def cell(env, parcel, at):
    p = env.scene.parcel(parcel)
    if p.carve:
        if at in p.carve["cells"]:
            return (f"{p.carve['cells'][at]} (cell '{at}' of {p.id}).",
                    p.carve["cells"][at])
        raise VeldError(f"{p.id} has no cell '{at}'. Cells: "
                        f"{', '.join(str(k) for k in p.carve['order'])}.")
    if p.split:
        if isinstance(at, int) and 1 <= at <= len(p.split["cells"]):
            return (f"{p.split['cells'][at-1]} (panel {at} of {p.id}).",
                    p.split["cells"][at - 1])
        raise VeldError(f"{p.id} has {len(p.split['cells'])} panels; "
                        f"at must be 1..{len(p.split['cells'])}.")
    raise VeldError(f"parcel {p.id} is neither carved nor split.")


@op("ground", [Param("parcel", "parcel ref", required=False),
               Param("host", "glyph ref|name", required=False),
               Param("aim", "enum", required=False,
                     enum=["north", "south", "east", "west", "center"]),
               Param("breadth", "number 0..1", required=False),
               Param("depth", "number 0..1", required=False)])
def nest(env, parcel=None, host=None, aim=None, breadth=None, depth=None):
    scene = env.scene
    if (parcel is None) == (host is None):
        raise VeldError("provide exactly one of parcel= or host=.")
    nid = scene.next_id("p")
    np = Parcel(nid, kind="nest")
    if host is not None:
        g = scene.glyph(host)
        np.host_glyph = g.id
        np.parent = g.parcel
        np.nest_aim = aim or "south"
        np.nest_breadth = breadth if breadth is not None else 1.0
        np.nest_depth = depth if depth is not None else 0.45
        where = f"under glyph {g.id}" + (f" ('{g.name}')" if g.name else "")
    else:
        pp = scene.parcel(parcel)
        np.parent = pp.id
        np.nest_aim = aim or "center"
        np.nest_breadth = breadth if breadth is not None else 0.5
        np.nest_depth = depth if depth is not None else 0.4
        where = f"inside {pp.id} at {np.nest_aim}"
    scene.parcels[nid] = np
    return (f"{nid}: fresh parcel nested {where}.", nid)


@op("ground", [Param("parcel", "parcel ref"),
               Param("inner", "number 0..1", required=False)])
def hoop(env, parcel, inner=None):
    p = env.scene.parcel(parcel)
    _fresh_for_structure(env, p, "hooping")
    if inner is not None and not (0 <= inner < 0.95):
        raise VeldError("inner must be between 0 and 0.95.")
    p.hooped = {"inner": inner or 0.0}
    extra = f" with inner {inner:g}" if inner else ""
    return (f"{p.id} hooped{extra}: its span is now angular sweep, "
            f"its rise is now radius.", None)


@op("ground", [Param("parcel", "parcel ref"), Param("amount", "number 0..1")])
def breathe(env, parcel, amount):
    p = env.scene.parcel(parcel)
    if not (0 <= amount <= 0.45):
        raise VeldError("amount must be between 0 and 0.45.")
    p.breathe = amount
    return f"{p.id} now breathes {amount:g}."


@op("ground", [Param("parcel", "parcel ref"),
               Param("along", "enum", enum=["span", "rise"])])
def invert(env, parcel, along):
    p = env.scene.parcel(parcel)
    if along in p.inverted:
        p.inverted.remove(along)
        return f"{p.id}: {along} restored to its usual sense."
    p.inverted.append(along)
    return f"{p.id}: {along} inverted."


@op("ground", [Param("parcel_a", "parcel ref"), Param("parcel_b", "parcel ref"),
               Param("edge", "enum", enum=SIDES)])
def abut(env, parcel_a, parcel_b, edge):
    a = env.scene.parcel(parcel_a)
    b = env.scene.parcel(parcel_b)
    if not hasattr(env.scene, "abuts"):
        env.scene.abuts = []
    env.scene.abuts.append((a.id, b.id, edge))
    return f"{a.id} and {b.id} now abut along their {edge} edges."


# ======================================================================
# family: sowing
# ======================================================================

@op("sowing", [Param("parcel", "parcel ref"), Param("ledger", "ledger name|ref"),
               Param("form", "enum", enum=FORMS),
               Param("key", "vein name", required=False)])
def sow(env, parcel, ledger, form, key=None):
    scene = env.scene
    p = scene.parcel(parcel)
    led = env.ledgers.resolve(ledger)
    if len(led.rows) > 60:
        raise VeldError(f"ledger {led.ref} has {len(led.rows)} rows; sow accepts "
                        f"at most 60 (distill or crop first).")
    if p.split:
        raise VeldError(f"parcel {p.id} is split into panels; sow into one panel "
                        f"(see cell()).")
    if p.carve:
        if not key:
            raise VeldError(f"parcel {p.id} is carved by '{p.carve['by']}'; "
                            f"provide key= to route glyphs to cells.")
        led.kind_of(key)
        unmatched = sorted({str(r[key]) for r in led.rows
                            if r[key] not in p.carve["cells"]})
        if unmatched:
            raise VeldError(
                f"key '{key}' values {', '.join(unmatched[:4])} match no cell of "
                f"{p.id} (cells: {', '.join(str(k) for k in p.carve['order'])}).")
    bid = scene.next_id("b")
    brood = Brood(bid, p.id, led.ref, form, key_vein=key)
    per_cell = {}
    for row in led.rows:
        target = p.carve["cells"][row[key]] if p.carve else p.id
        gid = scene.next_id("g")
        scene.glyphs[gid] = Glyph(gid, target, form, brood=bid, row=dict(row))
        brood.glyphs.append(gid)
        per_cell[target] = per_cell.get(target, 0) + 1
    scene.broods[bid] = brood
    if p.carve:
        counts = sorted(set(per_cell.values()))
        per = (f"{counts[0]}" if len(counts) == 1 else
               f"{counts[0]}–{counts[-1]}")
        return (f"{bid}: {len(brood.glyphs)} {form} glyphs sown into {p.id} "
                f"({len(p.carve['cells'])} cells by '{p.carve['by']}', "
                f"{per} per cell).", bid)
    return (f"{bid}: {len(brood.glyphs)} {form} glyphs sown into {p.id}.", bid)


@op("sowing", [Param("parcel", "parcel ref"), Param("form", "enum", enum=FORMS),
               Param("name", "text", required=False)])
def place(env, parcel, form, name=None):
    scene = env.scene
    p = scene.parcel(parcel)
    if p.carve or p.split:
        raise VeldError(f"parcel {p.id} is partitioned; place into a specific cell.")
    if name:
        for g in scene.glyphs.values():
            if g.name == name:
                raise VeldError(f"a glyph named '{name}' already exists ({g.id}).")
    gid = scene.next_id("g")
    g = Glyph(gid, p.id, form, name=name)
    if name and form in ("capsule", "rhomb", "drum", "plaque", "slab"):
        g.badge = {"text": name, "aim": "center"}
    scene.glyphs[gid] = g
    label = f" named '{name}'" if name else ""
    return (f"{gid}: {form} placed in {p.id}{label}.", gid)


# ======================================================================
# family: metering
# ======================================================================

@op("metering", [Param("brood", "brood ref"),
                 Param("trait", "enum", enum=TRAITS), Param("vein", "vein name")])
def meter(env, brood, trait, vein):
    b = env.scene.brood(brood)
    led = env.ledgers.resolve(b.ledger_ref)
    kind = led.kind_of(vein)
    if trait in ("stature", "girth", "bulk", "veil", "heft") and kind != "counted":
        raise VeldError(f"trait '{trait}' requires a counted vein; "
                        f"'{vein}' is {kind}.")
    b.meterings[trait] = vein
    g = env.gauges().for_brood(b, trait)
    cal = f" Gauge: {g.describe()}." if g else ""
    return f"{b.id}: {trait} now metered by '{vein}' ({kind}).{cal}"


@op("metering", [Param("parcel", "parcel ref"),
                 Param("trait", "enum", enum=TRAITS),
                 Param("floor", "number", required=False),
                 Param("ceil", "number", required=False)])
def rebase(env, parcel, trait, floor=None, ceil=None):
    p = env.scene.parcel(parcel)
    for v, nm in ((floor, "floor"), (ceil, "ceil")):
        if v is not None and (isinstance(v, bool) or
                              not isinstance(v, (int, float))):
            raise VeldError(f"{nm} must be a number.")
    if floor is None and ceil is None:
        if trait in p.gauge_overrides:
            del p.gauge_overrides[trait]
            return f"{p.id}: {trait} gauge restored to automatic calibration."
        raise VeldError("provide floor= and/or ceil=.")
    p.gauge_overrides[trait] = (floor, ceil)
    lo = "auto" if floor is None else f"{floor:g}"
    hi = "auto" if ceil is None else f"{ceil:g}"
    return f"{p.id}: {trait} gauge rebased to [{lo} … {hi}]."


@op("metering", [Param("brood", "brood ref"),
                 Param("trait", "enum", enum=TRAITS)])
def loosen(env, brood, trait):
    b = env.scene.brood(brood)
    if trait not in b.meterings:
        raise VeldError(f"brood {b.id} has no {trait} metering to loosen.")
    if trait not in b.loose_traits:
        b.loose_traits.append(trait)
    g = env.gauges().for_brood(b, trait)
    return (f"{b.id}: {trait} loosened onto a private gauge ({g.describe()}); "
            f"it no longer shares the parcel gauge.")


@op("metering", [Param("parcel_a", "parcel ref"), Param("parcel_b", "parcel ref"),
                 Param("trait", "enum", enum=TRAITS)])
def share(env, parcel_a, parcel_b, trait):
    a = env.scene.parcel(parcel_a)
    b = env.scene.parcel(parcel_b)
    env.scene.shared.append((a.id, b.id, trait))
    return f"{a.id} and {b.id} now share one {trait} gauge."


@op("metering", [Param("brood", "brood ref"),
                 Param("trait", "enum", enum=TRAITS)])
def unmeter(env, brood, trait):
    b = env.scene.brood(brood)
    if trait not in b.meterings:
        raise VeldError(f"brood {b.id} has no {trait} metering.")
    del b.meterings[trait]
    if trait in b.loose_traits:
        b.loose_traits.remove(trait)
    return f"{b.id}: {trait} metering removed."


# ======================================================================
# family: settling
# ======================================================================

@op("settling", [Param("parcel", "parcel ref"),
                 Param("law", "enum", enum=LAWS),
                 Param("heading", "enum", required=False, enum=HEADINGS)])
def settle(env, parcel, law, heading=None):
    scene = env.scene
    p = scene.parcel(parcel)
    if law == "wheel" and not (p.hooped or scene.chart_root(p.id).hooped):
        raise VeldError("law 'wheel' applies only to hooped parcels.")
    if law == "strew":
        broods = scene.broods_in(p.id)
        if not any(t in b.meterings for b in broods for t in ("stance", "perch")):
            raise VeldError(f"law 'strew' needs at least one stance or perch "
                            f"metering among the broods of {p.id}.")
    if law == "current":
        heading = heading or "east"
    p.settle = {"law": law, "heading": heading}
    h = f", heading {heading}" if heading else ""
    return f"{p.id}: glyphs now settle by law '{law}'{h}."


# ======================================================================
# family: cords
# ======================================================================

@op("cords", [Param("tail", "glyph ref|name"), Param("head", "glyph ref|name"),
              Param("sense", "enum", required=False, enum=["forth", "both"])])
def tether(env, tail, head, sense=None):
    scene = env.scene
    a = scene.glyph(tail)
    b = scene.glyph(head)
    if a.id == b.id:
        raise VeldError("tail and head are the same glyph.")
    cid = scene.next_id("c")
    c = Cord(cid, a.id, b.id, sense or "forth")
    if c.sense == "both":
        c.barb = "both"
    scene.cords[cid] = c
    arrow = "↔" if c.sense == "both" else "→"
    na = f"'{a.name}'" if a.name else a.id
    nb = f"'{b.name}'" if b.name else b.id
    return (f"{cid}: cord {na} {arrow} {nb}.", cid)


@op("cords", [Param("brood", "brood ref"), Param("by", "vein name")])
def thread(env, brood, by):
    scene = env.scene
    b = scene.brood(brood)
    if b.strand:
        raise VeldError(f"brood {b.id} already carries strand {b.strand}.")
    led = env.ledgers.resolve(b.ledger_ref)
    led.kind_of(by)
    sid = scene.next_id("s")
    scene.strands[sid] = Strand(sid, b.id, by)
    b.strand = sid
    warn = ""
    if "perch" not in b.meterings and "stature" not in b.meterings:
        warn = " (advisory: no rise metering on this brood — the strand will lie flat)"
    return (f"{sid}: strand threaded through {b.id} in '{by}' order{warn}.", sid)


@op("cords", [Param("strand", "strand ref")])
def flood(env, strand):
    s = env.scene.strand_of(strand)
    s.flooded = True
    return f"{s.id}: the region beneath the strand is now flooded."


@op("cords", [Param("tail", "glyph ref|name"), Param("head", "glyph ref|name"),
              Param("width", "number")])
def pipe(env, tail, head, width):
    scene = env.scene
    a = scene.glyph(tail)
    b = scene.glyph(head)
    if not isinstance(width, (int, float)) or width <= 0:
        raise VeldError("width must be a positive number.")
    cid = scene.next_id("c")
    c = Cord(cid, a.id, b.id, "forth")
    c.pipe_width = float(width)
    c.barb = "none"
    scene.cords[cid] = c
    return (f"{cid}: pipe {a.name or a.id} → {b.name or b.id}, width {width:g} "
            f"(widths normalize against other pipes).", cid)


@op("cords", [Param("cord", "cord ref"),
              Param("at", "enum", enum=["head", "tail", "both", "none"])])
def barb(env, cord, at):
    c = env.scene.cord(cord)
    c.barb = at
    return f"{c.id}: barb at {at}."


@op("cords", [Param("cord", "cord ref"), Param("amount", "number -1..1")])
def sweep(env, cord, amount):
    c = env.scene.cord(cord)
    if not (-1 <= amount <= 1):
        raise VeldError("amount must be between -1 and 1.")
    c.sweep = float(amount)
    return f"{c.id}: sweep {amount:g}."


@op("cords", [Param("cord", "cord ref"),
              Param("style", "enum", enum=["straight", "bend", "arc"])])
def crook(env, cord, style):
    c = env.scene.cord(cord)
    c.crook = style
    return f"{c.id}: routed {style}."


@op("cords", [Param("target", "cord|strand ref"), Param("weight", "number 0..1")])
def heft(env, target, weight):
    scene = env.scene
    if not (0 < weight <= 1):
        raise VeldError("weight must be between 0 and 1.")
    if target in scene.cords:
        scene.cords[target].heft = weight
    elif target in scene.strands:
        scene.strands[target].heft = weight
    else:
        raise VeldError(f"'{target}' is neither a cord nor a strand.")
    return f"{target}: heft {weight:g}."


# ======================================================================
# family: bands
# ======================================================================

def _resolve_members(env, members):
    if not isinstance(members, list) or not members:
        raise VeldError("members must be a non-empty list of glyph refs|names.")
    out = []
    for m in members:
        g = env.scene.glyph(m)
        out.append(g.id)
    return out


@op("bands", [Param("members", "list of glyph refs|names"),
              Param("name", "text", required=False)])
def flock(env, members, name=None):
    ids = _resolve_members(env, members)
    fid = env.scene.next_id("f")
    env.scene.flocks[fid] = Flock(fid, ids, name)
    return (f"{fid}: flock of {len(ids)} glyphs" + (f" named '{name}'." if name else "."),
            fid)


@op("bands", [Param("brood", "brood|flock ref"), Param("vein", "vein name"),
              Param("relation", "enum", enum=RELATIONS), Param("value", "value")])
def pick(env, brood, vein, relation, value):
    scene = env.scene
    glyphs = scene.target_glyphs(brood)
    rows = [g for g in glyphs if g.row and vein in g.row]
    if not rows:
        raise VeldError(f"no glyphs of '{brood}' carry a vein '{vein}'.")

    num = isinstance(value, (int, float)) and not isinstance(value, bool)

    def keep(v):
        ok_n = num and isinstance(v, (int, float))
        return {"is": v == value, "is_not": v != value,
                "above": ok_n and v > value,
                "below": ok_n and v < value,
                "at_least": ok_n and v >= value,
                "at_most": ok_n and v <= value,
                "among": v in value if isinstance(value, list) else False}[relation]

    hits = [g.id for g in rows if keep(g.row[vein])]
    if not hits:
        raise VeldError(f"no glyphs satisfy {vein} {relation} {value!r}.")
    fid = scene.next_id("f")
    scene.flocks[fid] = Flock(fid, hits)
    return (f"{fid}: {len(hits)} glyph(s) picked where {vein} {relation} {value!r}.",
            fid)


@op("bands", [Param("members", "list of glyph refs|names, or a flock ref"),
              Param("label", "text", required=False)])
def corral(env, members, label=None):
    scene = env.scene
    if isinstance(members, str) and members in scene.flocks:
        ids = list(scene.flocks[members].members)
    else:
        ids = _resolve_members(env, members)
    kid = scene.next_id("k")
    scene.corrals[kid] = Corral(kid, ids, label)
    lab = f" labeled '{label}'" if label else ""
    return (f"{kid}: corral around {len(ids)} glyphs{lab}.", kid)


@op("bands", [Param("band", "flock|corral ref")])
def disband(env, band):
    scene = env.scene
    if band in scene.flocks:
        del scene.flocks[band]
    elif band in scene.corrals:
        del scene.corrals[band]
    else:
        raise VeldError(f"'{band}' is neither a flock nor a corral.")
    return f"{band} disbanded."


# ======================================================================
# family: script
# ======================================================================

@op("script", [Param("target", "glyph|brood|flock|cord ref"),
               Param("text", "text", required=False),
               Param("vein", "vein name", required=False),
               Param("aim", "enum", required=False, enum=AIMS)])
def badge(env, target, text=None, vein=None, aim=None):
    scene = env.scene
    if (text is None) == (vein is None):
        raise VeldError("provide exactly one of text= or vein=.")
    kind, obj = scene.resolve_target(target)
    aim = aim or "auto"
    if kind == "cord":
        if vein:
            raise VeldError("cords take text badges only.")
        obj.badge = text
        return f"{obj.id}: badged '{text}'."
    if kind == "brood":
        if vein:
            led = env.ledgers.resolve(obj.ledger_ref)
            led.kind_of(vein)
        obj.badge = {"text": text, "vein": vein, "aim": aim}
        what = f"vein '{vein}'" if vein else f"'{text}'"
        return f"{obj.id}: every glyph badged with {what}."
    if kind in ("glyph", "flock"):
        glyphs = scene.target_glyphs(target)
        for g in glyphs:
            if vein:
                if not g.row or vein not in g.row:
                    raise VeldError(f"glyph {g.id} carries no vein '{vein}'.")
                spec = {"text": str(g.row[vein]), "vein": vein, "aim": aim}
            else:
                spec = {"text": text, "aim": aim}
            if g.badge and g.badge.get("aim") == "center" and g.name and \
                    aim not in ("center", "auto"):
                g.badge2 = spec  # keep the node's name; add a second label
            else:
                g.badge = spec
        n = len(glyphs)
        return f"{n} glyph(s) badged."
    raise VeldError(f"cannot badge a {kind}.")


@op("script", [Param("text", "text"),
               Param("near", "any ref", required=False),
               Param("aim", "enum", required=False, enum=AIMS)])
def inscribe(env, text, near=None, aim=None):
    scene = env.scene
    if near is not None:
        scene.resolve_target(near)
    aid = scene.next_id("a")
    scene.annotations.append(Annotation(aid, "inscribe", text, near, aim or "auto"))
    loc = f" near {near}" if near else ""
    return (f"{aid}: inscription '{text}'{loc}.", aid)


@op("script", [Param("target", "glyph|cord ref"), Param("text", "text")])
def flag(env, target, text):
    scene = env.scene
    kind, obj = scene.resolve_target(target)
    if kind == "flock" and len(obj.members) == 1:
        kind, obj = "glyph", scene.glyphs[obj.members[0]]
    if kind not in ("glyph", "cord"):
        raise VeldError(f"flag points at a single glyph or cord, not a {kind}.")
    aid = scene.next_id("a")
    scene.annotations.append(Annotation(aid, "flag", text, obj.id, "auto"))
    return (f"{aid}: flag '{text}' tied to {obj.id}.", aid)


@op("script", [Param("parcel", "parcel ref"), Param("text", "text")])
def entitle(env, parcel, text):
    p = env.scene.parcel(parcel)
    p.entitle = text
    return f"{p.id} entitled '{text}'."


@op("script", [Param("parcel", "parcel ref"), Param("text", "text")])
def note(env, parcel, text):
    p = env.scene.parcel(parcel)
    p.note = text
    return f"{p.id}: note set."


# ======================================================================
# family: guides
# ======================================================================

@op("guides", [Param("parcel", "parcel ref"),
               Param("side", "enum", enum=SIDES)])
def rim(env, parcel, side):
    p = env.scene.parcel(parcel)
    if p.hooped:
        raise VeldError("hooped parcels have no rims.")
    if side in p.rims:
        raise VeldError(f"{p.id} already has a {side} rim.")
    p.rims.append(side)
    return f"{p.id}: {side} rim raised (calibration will follow its gauge)."


@op("guides", [Param("parcel", "parcel ref"),
               Param("along", "enum", enum=["span", "rise"])])
def weft(env, parcel, along):
    p = env.scene.parcel(parcel)
    if along in p.wefts:
        raise VeldError(f"{p.id} already has a {along} weft.")
    p.wefts.append(along)
    return f"{p.id}: faint weft lines laid along {along}."


@op("guides", [Param("parcel", "parcel ref"), Param("brood", "brood ref"),
               Param("trait", "enum", enum=["tint", "bulk"])])
def key(env, parcel, brood, trait):
    p = env.scene.parcel(parcel)
    b = env.scene.brood(brood)
    if trait not in b.meterings:
        raise VeldError(f"brood {b.id} has no {trait} metering to key.")
    env.scene.keys.append(Key(p.id, b.id, trait))
    return f"key raised on {p.id} for {b.id}'s {trait} metering."


# ======================================================================
# family: emphasis
# ======================================================================

def _emphasis_targets(env, target):
    scene = env.scene
    kind, obj = scene.resolve_target(target)
    if kind in ("glyph", "brood", "flock"):
        return scene.target_glyphs(target), kind
    if kind in ("cord", "strand"):
        return [obj], kind
    raise VeldError(f"cannot emphasize a {kind}.")


@op("emphasis", [Param("target", "glyph|brood|flock|cord|strand ref")])
def kindle(env, target):
    objs, kind = _emphasis_targets(env, target)
    for o in objs:
        o.kindled = True
        o.hushed = False
    return f"{len(objs)} {kind}(s) kindled." if kind == "glyph" else f"{target} kindled."


@op("emphasis", [Param("target", "glyph|brood|flock|cord|strand ref")])
def hush(env, target):
    objs, kind = _emphasis_targets(env, target)
    for o in objs:
        if hasattr(o, "hushed"):
            o.hushed = True
        o.kindled = False
    return f"{len(objs)} {kind}(s) hushed." if kind == "glyph" else f"{target} hushed."


# ======================================================================
# family: layers
# ======================================================================

@op("layers", [Param("target", "glyph|brood|flock|strand ref")])
def lift(env, target):
    glyphs = None
    scene = env.scene
    if target in scene.strands:
        scene.strands[target].__dict__.setdefault("layer", 0)
        scene.strands[target].layer = getattr(scene.strands[target], "layer", 0) + 1
        return f"{target} lifted."
    glyphs = scene.target_glyphs(target)
    for g in glyphs:
        g.layer += 1
    return f"{target} lifted."


@op("layers", [Param("target", "glyph|brood|flock|strand ref")])
def sink(env, target):
    scene = env.scene
    if target in scene.strands:
        scene.strands[target].layer = getattr(scene.strands[target], "layer", 0) - 1
        return f"{target} sunk."
    for g in scene.target_glyphs(target):
        g.layer -= 1
    return f"{target} sunk."


# ======================================================================
# family: patina
# ======================================================================

@op("patina", [Param("target", "glyph|brood|flock|cord|strand|corral ref"),
               Param("hue", "enum", enum=HUES)])
def tint(env, target, hue):
    scene = env.scene
    kind, obj = scene.resolve_target(target)
    if kind in ("cord", "strand", "corral"):
        obj.tint = hue
        return f"{target} tinted {hue}."
    if kind == "brood":
        obj.fixed["tint"] = hue
        for gid in obj.glyphs:
            scene.glyphs[gid].fixed.pop("tint", None)
        return f"{target} tinted {hue}."
    for g in scene.target_glyphs(target):
        g.fixed["tint"] = hue
    return f"{target} tinted {hue}."


@op("patina", [Param("target", "glyph|brood|flock|cord ref"),
               Param("amount", "number 0..1")])
def veil(env, target, amount):
    scene = env.scene
    if not (0 <= amount <= 1):
        raise VeldError("amount must be between 0 and 1.")
    kind, obj = scene.resolve_target(target)
    if kind in ("cord", "strand"):
        obj.__dict__["veil"] = amount
        return f"{target} veiled to {amount:g}."
    if kind == "brood":
        obj.fixed["veil"] = amount
        return f"{target} veiled to {amount:g}."
    for g in scene.target_glyphs(target):
        g.fixed["veil"] = amount
    return f"{target} veiled to {amount:g}."


@op("patina", [Param("target", "glyph|brood|flock ref"),
               Param("weight", "number 0..3")])
def outline(env, target, weight):
    if not (0 <= weight <= 3):
        raise VeldError("weight must be between 0 and 3.")
    kind, obj = env.scene.resolve_target(target)
    if kind == "brood":
        obj.fixed["outline"] = weight
        return f"{target} outlined at {weight:g}."
    for g in env.scene.target_glyphs(target):
        g.fixed["outline"] = weight
    return f"{target} outlined at {weight:g}."


@op("patina", [Param("parcel", "parcel ref"),
               Param("name", "enum", enum=PALETTES)])
def palette(env, parcel, name):
    p = env.scene.parcel(parcel)
    p.palette = name
    return f"{p.id}: palette '{name}'."


# ======================================================================
# family: oracle (introspection)
# ======================================================================

@op("oracle", [], mutates=False)
def families(env):
    lines = ["op families:"]
    for fam in FAMILY_ORDER:
        n = sum(1 for o in OPS.values() if o.family == fam)
        lines.append(f"  {fam}  ({n} ops)")
    return "\n".join(lines)


@op("oracle", [Param("family", "family name")], mutates=False)
def ops(env, family):
    if family not in FAMILY_ORDER:
        raise VeldError(f"unknown family '{family}'. Families: "
                        f"{', '.join(FAMILY_ORDER)}.")
    names = [o.name for o in OPS.values() if o.family == family]
    return "\n".join(f"  {n}" for n in names)


@op("oracle", [Param("op", "op name")], mutates=False)
def sig(env, op):
    if op not in OPS:
        raise VeldError(f"unknown op '{op}'.")
    od = OPS[op]
    lines = [od.signature()]
    for p in od.params:
        extra = f" — one of: {', '.join(str(e) for e in p.enum)}" if p.enum else ""
        req = "" if p.required else " (optional)"
        lines.append(f"  {p.name}: {p.wtype}{req}{extra}")
    return "\n".join(lines)


@op("oracle", [], mutates=False)
def forms(env):
    return "\n".join(f"  {f} — {FORM_GLOSS[f]}" for f in FORMS)


@op("oracle", [], mutates=False)
def census(env):
    from .observe import census_text
    return census_text(env)


@op("oracle", [Param("ref", "any ref")], mutates=False)
def study(env, ref):
    from .observe import study_text
    return study_text(env, ref)


@op("oracle", [], mutates=False)
def trace(env):
    if not env.trace_log:
        return "no scene-changing ops yet this task."
    return "\n".join(f"{i+1}. {name}({', '.join(f'{k}={v!r}' for k, v in a.items())})"
                     for i, (name, a) in enumerate(env.trace_log))


# ======================================================================
# family: helm (control)
# ======================================================================

@op("helm", [], mutates=False)
def undo(env):
    if not env._undo:
        raise VeldError("nothing to undo.")
    scene, ledgers, tlog = env._undo.pop()
    env.scene = scene
    env.ledgers = ledgers
    undone = env.trace_log[-1][0] if env.trace_log and len(env.trace_log) > len(tlog) \
        else "last op"
    env.trace_log = tlog
    return f"undone: {undone}. Scene restored."


@op("helm", [], mutates=False)
def restart(env):
    env.scene = Scene()
    env.ledgers = LedgerSpace()
    env._undo = []
    env.trace_log = []
    return "task restarted: blank ground with root parcel p0."


@op("helm", [], mutates=False)
def present(env):
    return "artifact presented for judgment."


BOOTSTRAP = (
    "VELD bootstrap — you are facing an unfamiliar visual instrument.\n"
    "Known entry points:\n"
    "  families()            list op families\n"
    "  ops(family)           list ops in a family\n"
    "  sig(op)               an op's signature and argument kinds\n"
    "  forms()               available glyph forms\n"
    "  shelf()               available data ledgers\n"
    "  peek(ledger, rows?)   look at rows\n"
    "  veins(ledger)         a ledger's veins and their kinds\n"
    "  census()              current state of the artifact\n"
    "  study(ref)            detail on any ref (parcel/brood/glyph/…)\n"
    "  trace()               ops applied so far this task\n"
    "  undo()                revert the last scene-changing op\n"
    "  restart()             wipe the task's artifact\n"
    "  present()             submit the artifact for judgment\n"
    "Every task begins with a blank ground holding one root parcel: p0."
)
