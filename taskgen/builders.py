"""Curriculum authoring toolkit: a reference-program builder with ref
tracking, concept extraction, and chart/diagram archetype builders."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from diagrambench.datasets import DATASETS, RANKED_ORDERS
from diagrambench.verify import apply_transform


def levels_from_rows(rows, vein):
    seen = []
    for r in rows:
        v = r[vein]
        if v not in seen:
            seen.append(v)
    if vein in RANKED_ORDERS:
        seen.sort(key=lambda v: RANKED_ORDERS[vein].index(v)
                  if v in RANKED_ORDERS[vein] else 99)
    return seen


class P:
    """Reference-program builder that mirrors the SDK's ref numbering."""

    def __init__(self):
        self.ops = []
        self.n = {"L": 0, "b": 0, "f": 0, "s": 0, "c": 0, "p": 0, "a": 0, "k": 0}

    def _op(self, _opname, **args):
        self.ops.append([_opname,
                         {k: v for k, v in args.items() if v is not None}])

    def _next(self, key):
        self.n[key] += 1
        return f"{key}{self.n[key]}"

    # data
    def sift(self, ledger, vein, relation, value):
        self._op("sift", ledger=ledger, vein=vein, relation=relation, value=value)
        return self._next("L")

    def distill(self, ledger, by, mode, take=None):
        self._op("distill", ledger=ledger, by=by, mode=mode, take=take)
        return self._next("L")

    def derive(self, ledger, name, mode, a, b=None):
        self._op("derive", ledger=ledger, name=name, mode=mode, a=a, b=b)
        return self._next("L")

    def bin(self, ledger, vein, bins=None):
        self._op("bin", ledger=ledger, vein=vein, bins=bins)
        return self._next("L")

    def marshal(self, ledger, vein, sense):
        self._op("marshal", ledger=ledger, vein=vein, sense=sense)
        return self._next("L")

    def crop(self, ledger, first):
        self._op("crop", ledger=ledger, first=first)
        return self._next("L")

    # ground
    def carve(self, parcel, along, ledger, by, levels, gap=None):
        self._op("carve", parcel=parcel, along=along, ledger=ledger, by=by,
                 gap=gap)
        cells = {}
        for lv in levels:
            cells[lv] = self._next("p")
        return cells

    def split(self, parcel, along, count, gap=None):
        self._op("split", parcel=parcel, along=along, count=count, gap=gap)
        return [self._next("p") for _ in range(count)]

    def nest(self, parcel=None, host=None, aim=None, breadth=None, depth=None):
        self._op("nest", parcel=parcel, host=host, aim=aim, breadth=breadth,
                 depth=depth)
        return self._next("p")

    def hoop(self, parcel, inner=None):
        self._op("hoop", parcel=parcel, inner=inner)

    def invert(self, parcel, along):
        self._op("invert", parcel=parcel, along=along)

    def abut(self, a, b, edge):
        self._op("abut", parcel_a=a, parcel_b=b, edge=edge)

    # sowing
    def sow(self, parcel, ledger, form, key=None):
        self._op("sow", parcel=parcel, ledger=ledger, form=form, key=key)
        return self._next("b")

    def place(self, parcel, form, name):
        self._op("place", parcel=parcel, form=form, name=name)
        return name

    # metering / settling
    def meter(self, brood, trait, vein):
        self._op("meter", brood=brood, trait=trait, vein=vein)

    def rebase(self, parcel, trait, floor=None, ceil=None):
        self._op("rebase", parcel=parcel, trait=trait, floor=floor, ceil=ceil)

    def loosen(self, brood, trait):
        self._op("loosen", brood=brood, trait=trait)

    def share(self, a, b, trait):
        self._op("share", parcel_a=a, parcel_b=b, trait=trait)

    def settle(self, parcel, law, heading=None):
        self._op("settle", parcel=parcel, law=law, heading=heading)

    # cords
    def tether(self, tail, head, sense=None):
        self._op("tether", tail=tail, head=head, sense=sense)
        return self._next("c")

    def thread(self, brood, by):
        self._op("thread", brood=brood, by=by)
        return self._next("s")

    def flood(self, strand):
        self._op("flood", strand=strand)

    def pipe(self, tail, head, width):
        self._op("pipe", tail=tail, head=head, width=width)
        return self._next("c")

    def barb(self, cord, at):
        self._op("barb", cord=cord, at=at)

    def sweep(self, cord, amount):
        self._op("sweep", cord=cord, amount=amount)

    def crook(self, cord, style):
        self._op("crook", cord=cord, style=style)

    def heft(self, target, weight):
        self._op("heft", target=target, weight=weight)

    # bands
    def flock(self, members, name=None):
        self._op("flock", members=members, name=name)
        return self._next("f")

    def pick(self, brood, vein, relation, value):
        self._op("pick", brood=brood, vein=vein, relation=relation, value=value)
        return self._next("f")

    def corral(self, members, label=None):
        self._op("corral", members=members, label=label)
        return self._next("k")

    # script / guides / emphasis / patina
    def badge(self, target, text=None, vein=None, aim=None):
        self._op("badge", target=target, text=text, vein=vein, aim=aim)

    def inscribe(self, text, near=None, aim=None):
        self._op("inscribe", text=text, near=near, aim=aim)
        return self._next("a")

    def flag(self, target, text):
        self._op("flag", target=target, text=text)
        return self._next("a")

    def entitle(self, parcel, text):
        self._op("entitle", parcel=parcel, text=text)

    def note(self, parcel, text):
        self._op("note", parcel=parcel, text=text)

    def rim(self, parcel, side):
        self._op("rim", parcel=parcel, side=side)

    def weft(self, parcel, along):
        self._op("weft", parcel=parcel, along=along)

    def key(self, parcel, brood, trait):
        self._op("key", parcel=parcel, brood=brood, trait=trait)

    def kindle(self, target):
        self._op("kindle", target=target)

    def hush(self, target):
        self._op("hush", target=target)

    def tint(self, target, hue):
        self._op("tint", target=target, hue=hue)

    def veil(self, target, amount):
        self._op("veil", target=target, amount=amount)

    def lift(self, target):
        self._op("lift", target=target)

    def palette(self, parcel, name):
        self._op("palette", parcel=parcel, name=name)


# ----------------------------------------------------------------------
# concept extraction
# ----------------------------------------------------------------------

def concepts_of(program):
    seen = set()
    for op, args in program:
        seen.add(op)
        if op in ("sow", "place"):
            seen.add("form:" + args["form"])
        if op == "meter":
            seen.add("trait:" + args["trait"])
        if op == "settle":
            seen.add("law:" + args["law"])
        if op in ("sift", "pick"):
            seen.add("relation:" + args["relation"])
        if op == "distill":
            seen.add("mode:" + args["mode"])
        if op == "derive":
            seen.add("derive:" + args["mode"])
        if op == "carve":
            seen.add("carve:" + args["along"])
        if op == "hoop" and args.get("inner"):
            seen.add("hoop:inner")
        if op == "nest":
            seen.add("nest:host" if args.get("host") else "nest:parcel")
        if op == "rim":
            seen.add("rim:" + args["side"])
        if op == "badge" and args.get("vein"):
            seen.add("badge:vein")
    return sorted(seen)


# ----------------------------------------------------------------------
# archetype builders — each returns a partial task dict
# ----------------------------------------------------------------------

def task(instruction, p, checks, datasets, min_semantic=1.0):
    return {"instruction": instruction, "reference_program": p.ops,
            "hidden_goal": {"checks": checks, "min_semantic": min_semantic},
            "datasets": sorted(set(datasets))}


def transformed(ds, transform):
    """(final rows, ledger-ref-producing closure over P)."""
    rows = apply_transform(ds, transform or [])

    def build(p):
        ref = ds
        for step in transform or []:
            if step[0] == "sift":
                ref = p.sift(ref, step[1], step[2], step[3])
            elif step[0] == "distill":
                ref = p.distill(ref, step[1], step[3], step[2])
            elif step[0] == "derive":
                ref = p.derive(ref, step[1], step[2], step[3],
                               step[4] if len(step) > 4 else None)
            elif step[0] == "bin":
                ref = p.bin(ref, step[1], step[2] if len(step) > 2 else None)
            elif step[0] == "marshal":
                ref = p.marshal(ref, step[1], step[2])
            elif step[0] == "crop":
                ref = p.crop(ref, step[1])
        return ref
    return rows, build


def bar(instruction, ds, cat, val, transform=None, orient="columns",
        tint_cat=None, legend=False, badge_vein=None, kindle_where=None,
        annotate=None, rims=("south", "west"), weft_rise=False, title=None,
        note=None, sort=None, law_check=True, palette=None, stacked=False,
        stack_tint=None, gap=None):
    """Carved bar chart family: plain, grouped, stacked, sorted, horizontal."""
    p = P()
    rows, build = transformed(ds, transform)
    ref = build(p)
    if sort:
        ref = p.marshal(ref, sort[0], sort[1])
        rows = sorted(rows, key=lambda r: r[sort[0]],
                      reverse=(sort[1] == "waning"))
    along = "span" if orient == "columns" else "rise"
    trait = "stature" if orient == "columns" else "girth"
    cells = p.carve("p0", along, ref, cat, levels_from_rows(rows, cat), gap=gap)
    b = p.sow("p0", ref, "slab", key=cat)
    p.meter(b, trait, val)
    tcat = tint_cat or stack_tint
    if tcat:
        p.meter(b, "tint", tcat)
    if stacked:
        p.settle("p0", "heap")
    if legend and tcat:
        p.key("p0", b, "tint")
    if palette:
        p.palette("p0", palette)
    if badge_vein:
        p.badge(b, vein=badge_vein, aim="north" if orient == "columns" else "east")
    if kindle_where:
        f = None
        for vein, value in kindle_where.items():
            f = p.pick(f or b, vein, "is", value)
        p.kindle(f)
    if annotate:
        text, where, kind = annotate
        f = None
        for vein, value in where.items():
            f = p.pick(f or b, vein, "is", value)
        if kind == "flag":
            p.flag(f, text)
        else:
            p.inscribe(text, near=f)
    if weft_rise:
        p.weft("p0", "rise")
    for side in rims or []:
        p.rim("p0", side)
    if title:
        p.entitle("p0", title)
    if note:
        p.note("p0", note)

    where = {"form": "slab",
             "data": {"from": ds, "transform": transform or []},
             "meter": dict({trait: val}, **({"tint": tcat} if tcat else {})),
             "in": {"carved_by": cat, "carve_along": along}}
    if law_check and (tint_cat or stacked):
        where["in"]["law"] = "heap" if stacked else "abreast"
    if sort:
        where["order"] = {"vein": sort[0], "sense": sort[1]}
    if badge_vein:
        where["badge_vein"] = badge_vein
    checks = [{"check": "brood", "where": where,
               "weight": max(4, len(where) * 2)}]
    if legend and tcat:
        checks.append({"check": "guide", "kind": "key", "trait": "tint"})
    for side in rims or []:
        checks.append({"check": "guide", "kind": "rim", "side": side})
    if weft_rise:
        checks.append({"check": "guide", "kind": "weft", "along": "rise"})
    if title:
        checks.append({"check": "guide", "kind": "entitle",
                       "text_has": title.split()[0]})
    if note:
        checks.append({"check": "guide", "kind": "note"})
    if kindle_where:
        checks.append({"check": "emphasis", "mode": "kindle",
                       "target": {"where": kindle_where}, "exclusive": True})
    if annotate:
        text, wh, kind = annotate
        key_word = max(text.split(), key=len)
        checks.append({"check": "annotation", "text_has": key_word,
                       "near": {"where": wh}})
    return task(instruction, p, checks, [ds])


def pie(instruction, ds, cat, val, transform=None, inner=None,
        badge_cat=True, badge_val=False, legend=False, title=None,
        kindle_where=None, palette=None):
    p = P()
    rows, build = transformed(ds, transform)
    ref = build(p)
    p.hoop("p0", inner=inner)
    b = p.sow("p0", ref, "slab")
    p.meter(b, "girth", val)
    p.meter(b, "tint", cat)
    if palette:
        p.palette("p0", palette)
    if badge_cat:
        p.badge(b, vein=cat, aim="rim")
    elif badge_val:
        p.badge(b, vein=val, aim="center")
    if legend:
        p.key("p0", b, "tint")
    if kindle_where:
        f = None
        for vein, value in kindle_where.items():
            f = p.pick(f or b, vein, "is", value)
        p.kindle(f)
    if title:
        p.entitle("p0", title)
    where = {"form": "slab", "data": {"from": ds, "transform": transform or []},
             "meter": {"girth": val, "tint": cat}, "in": {"hooped": True}}
    if inner:
        where["in"]["inner_min"] = inner * 0.66
    if badge_cat:
        where["badge_vein"] = cat
    elif badge_val:
        where["badge_vein"] = val
    checks = [{"check": "brood", "where": where, "weight": 6}]
    if legend:
        checks.append({"check": "guide", "kind": "key", "trait": "tint"})
    if title:
        checks.append({"check": "guide", "kind": "entitle"})
    if kindle_where:
        checks.append({"check": "emphasis", "mode": "kindle",
                       "target": {"where": kindle_where}, "exclusive": True})
    return task(instruction, p, checks, [ds])


def line(instruction, ds, x, y, transform=None, area=False, form="wisp",
         rims=("south", "west"), weft_rise=True, title=None, annotate=None,
         kindle_strand=False, hue=None, note=None):
    p = P()
    rows, build = transformed(ds, transform)
    ref = build(p)
    b = p.sow("p0", ref, form)
    p.meter(b, "stance", x)
    p.meter(b, "perch", y)
    p.settle("p0", "strew")
    s = p.thread(b, by=x)
    if area:
        p.flood(s)
    if hue:
        p.tint(s, hue)
        p.tint(b, hue)
    if kindle_strand:
        p.kindle(s)
    if annotate:
        text, where, kind = annotate
        f = None
        for vein, value in where.items():
            f = p.pick(f or b, vein, "is", value)
        if kind == "flag":
            p.flag(f, text)
        else:
            p.inscribe(text, near=f)
    if weft_rise:
        p.weft("p0", "rise")
    for side in rims or []:
        p.rim("p0", side)
    if title:
        p.entitle("p0", title)
    if note:
        p.note("p0", note)
    where = {"form": form, "data": {"from": ds, "transform": transform or []},
             "meter": {"stance": x, "perch": y}, "threaded_by": x,
             "in": {"law": "strew"}}
    if area:
        where["flooded"] = True
    checks = [{"check": "brood", "where": where, "weight": 6}]
    for side in rims or []:
        checks.append({"check": "guide", "kind": "rim", "side": side})
    if weft_rise:
        checks.append({"check": "guide", "kind": "weft", "along": "rise"})
    if title:
        checks.append({"check": "guide", "kind": "entitle"})
    if annotate:
        text, wh, kind = annotate
        checks.append({"check": "annotation",
                       "text_has": max(text.split(), key=len),
                       "near": {"where": wh}})
    return task(instruction, p, checks, [ds])


def scatter(instruction, ds, x, y, transform=None, tint_cat=None, bulk=None,
            legend=False, rims=("south", "west"), title=None, annotate=None,
            badge_vein=None, form="disc", kindle_where=None):
    p = P()
    rows, build = transformed(ds, transform)
    ref = build(p)
    b = p.sow("p0", ref, form)
    p.meter(b, "stance", x)
    p.meter(b, "perch", y)
    if bulk:
        p.meter(b, "bulk", bulk)
    if tint_cat:
        p.meter(b, "tint", tint_cat)
    p.settle("p0", "strew")
    if legend and tint_cat:
        p.key("p0", b, "tint")
    if badge_vein:
        p.badge(b, vein=badge_vein, aim="north")
    if kindle_where:
        f = None
        for vein, value in kindle_where.items():
            f = p.pick(f or b, vein, "is", value)
        p.kindle(f)
    if annotate:
        text, where, kind = annotate
        f = None
        for vein, value in where.items():
            f = p.pick(f or b, vein, "is", value)
        if kind == "flag":
            p.flag(f, text)
        else:
            p.inscribe(text, near=f)
    for side in rims or []:
        p.rim("p0", side)
    if title:
        p.entitle("p0", title)
    meters = {"stance": x, "perch": y}
    if bulk:
        meters["bulk"] = bulk
    if tint_cat:
        meters["tint"] = tint_cat
    where = {"form": form, "data": {"from": ds, "transform": transform or []},
             "meter": meters, "in": {"law": "strew"}}
    if badge_vein:
        where["badge_vein"] = badge_vein
    checks = [{"check": "brood", "where": where, "weight": 6}]
    if legend and tint_cat:
        checks.append({"check": "guide", "kind": "key", "trait": "tint"})
    for side in rims or []:
        checks.append({"check": "guide", "kind": "rim", "side": side})
    if title:
        checks.append({"check": "guide", "kind": "entitle"})
    if annotate:
        text, wh, kind = annotate
        checks.append({"check": "annotation",
                       "text_has": max(text.split(), key=len),
                       "near": {"where": wh}})
    if kindle_where:
        checks.append({"check": "emphasis", "mode": "kindle",
                       "target": {"where": kindle_where}, "exclusive": True})
    return task(instruction, p, checks, [ds])


def diagram(instruction, nodes, edges, heading="east", corrals=None,
            kindle_cords=None, kindle_nodes=None, title=None, cord_badges=None,
            flags=None, hush_nodes=None, extra_checks=None, datasets=()):
    """nodes: [(form, name)]; edges: [(tail, head)] or [(tail, head, badge)];
    corrals: [(members, label)]; kindle_cords: [(tail, head)]."""
    p = P()
    p.settle("p0", "current", heading=heading)
    for form, name in nodes:
        p.place("p0", form, name)
    cord_refs = {}
    for e in edges:
        tail, head = e[0], e[1]
        c = p.tether(tail, head)
        cord_refs[(tail, head)] = c
        if len(e) > 2 and e[2]:
            p.badge(c, text=e[2])
    for members, label in corrals or []:
        p.corral(members, label=label)
    for tail, head in kindle_cords or []:
        p.kindle(cord_refs[(tail, head)])
    for name in kindle_nodes or []:
        p.kindle(name)
    for name in hush_nodes or []:
        p.hush(name)
    for target, text in flags or []:
        p.flag(target, text)
    if title:
        p.entitle("p0", title)
    checks = [{"check": "parcel", "label": f"a {heading}ward current",
               "where": {"law": "current", "heading": heading}}]
    for form, name in nodes:
        checks.append({"check": "glyph", "named": name, "form": form})
    for e in edges:
        c = {"check": "cord", "from": e[0], "to": e[1]}
        if len(e) > 2 and e[2]:
            c["badge_has"] = e[2]
        checks.append(c)
    for members, label in corrals or []:
        c = {"check": "corral", "contains_named": members}
        if label:
            c["label_has"] = label
        checks.append(c)
    for tail, head in kindle_cords or []:
        checks.append({"check": "emphasis", "mode": "kindle",
                       "target": {"cord_from": tail, "cord_to": head}})
    for name in kindle_nodes or []:
        checks.append({"check": "emphasis", "mode": "kindle",
                       "target": {"named": name}})
    for name in hush_nodes or []:
        checks.append({"check": "emphasis", "mode": "hush",
                       "target": {"named": name}})
    for target, text in flags or []:
        checks.append({"check": "annotation", "kind": "flag",
                       "text_has": max(text.split(), key=len),
                       "near": {"named": target}})
    if title:
        checks.append({"check": "guide", "kind": "entitle"})
    checks.extend(extra_checks or [])
    return task(instruction, p, checks, list(datasets))


def histogram(instruction, ds, val, bins=8, rims=("south", "west"),
              title=None, weft_rise=True):
    return bar(instruction, ds, "bin", "tally",
               transform=[["bin", val, bins]], rims=rims, title=title,
               weft_rise=weft_rise, law_check=False, gap=0.06)
