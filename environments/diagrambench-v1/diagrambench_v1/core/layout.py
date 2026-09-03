"""Deterministic layout: (scene, ledgers) -> display list of SVG-level items.

Items carry stable ids so the viewer can tween between successive states.
Item: {"id", "tag", "attrs", "layer", "text"?, "cls"?}
"""

import math

from . import theme
from .gauges import GaugeSet
from .theme import (fmt_num, hue_hex, mix, palette_colors, ramp, soften, text_w)

NODE_SIZES = {  # base w, h for placed forms under `current`/free laws
    "capsule": (128, 46), "rhomb": (104, 60), "drum": (92, 66),
    "plaque": (118, 38), "slab": (110, 42), "disc": (56, 56),
    "ring": (52, 52), "wisp": (18, 18),
}

RIM_GUTTER = {"south": 30, "west": 50, "north": 24, "east": 50}


def _rect(x, y, w, h):
    return {"x": x, "y": y, "w": w, "h": h}


class Layout:
    def __init__(self, scene, ledgers):
        self.scene = scene
        self.ledgers = ledgers
        self.gs = GaugeSet(scene, ledgers)
        self.items = []
        self.warnings = []
        self.pos = {}       # glyph id -> dict(cx, cy, w, h, top, kind)
        self.plots = {}     # parcel id -> plot rect
        self.envelopes = {} # parcel id -> outer rect

    # ------------------------------------------------------------------
    def add(self, id, tag, attrs, layer, text=None, cls=None, meta=None):
        it = {"id": id, "tag": tag, "attrs": attrs, "layer": layer}
        if text is not None:
            it["text"] = str(text)
        if cls:
            it["cls"] = cls
        if meta:
            it["meta"] = meta
        self.items.append(it)

    def warn(self, msg):
        if msg not in self.warnings:
            self.warnings.append(msg)

    # -- palettes / fills ------------------------------------------------
    def parcel_palette(self, pid):
        p = self.scene.parcels.get(pid)
        while p is not None:
            if p.palette:
                return p.palette
            p = self.scene.parcels.get(p.parent) if p.parent else None
        return "quill"

    def brood_of(self, g):
        return self.scene.broods.get(g.brood) if g.brood else None

    def fill_for(self, g):
        b = self.brood_of(g)
        colors = palette_colors(self.parcel_palette(g.parcel))
        if "tint" in g.fixed:
            return hue_hex(g.fixed["tint"])
        if b and "tint" in b.fixed:
            return hue_hex(b.fixed["tint"])
        if b and "tint" in b.meterings and g.row:
            vein = b.meterings["tint"]
            gauge = self.gs.for_brood(b, "tint")
            v = g.row.get(vein)
            if gauge and gauge.kind == "band":
                try:
                    i = gauge.levels.index(v)
                except ValueError:
                    i = 0
                return colors[i % len(colors)]
            if gauge:
                return ramp(gauge.frac(v), base=colors[0])
        if b is None:  # placed node
            return theme.NODE_FILL
        return colors[0]

    def styled(self, g, fill):
        """(fill, stroke, stroke_w, opacity) after emphasis/patina."""
        stroke, sw = "none", 0
        if g.brood is None and g.form in ("capsule", "rhomb", "drum", "plaque",
                                          "slab", "disc", "ring"):
            stroke, sw = theme.NODE_EDGE, 1.2
        if "outline" in g.fixed:
            stroke, sw = mix(fill if fill != theme.NODE_FILL else theme.INK,
                             "#000000", 0.25), g.fixed["outline"]
        op = g.fixed.get("veil", 1.0)
        if g.hushed:
            op = min(op, 0.22)
        if g.kindled:
            base = fill if fill != theme.NODE_FILL else theme.HUE_HEX["ember"]
            if fill == theme.NODE_FILL:
                fill = soften(theme.HUE_HEX["ember"], 0.82)
            stroke, sw = mix(base, "#000000", 0.22), 2.2
        return fill, stroke, sw, op

    # ------------------------------------------------------------------
    def run(self):
        scene = self.scene
        root = scene.parcels[scene.root]
        W, H, M = theme.CANVAS_W, theme.CANVAS_H, theme.MARGIN
        top = M
        if root.entitle:
            self.add("title:root", "text",
                     {"x": M + 4, "y": top + 14, "fill": theme.TITLE,
                      "font-size": theme.FS_TITLE, "font-weight": 600,
                      "text-anchor": "start"},
                     8, root.entitle, cls="title")
            top += 34
        bottom = H - M
        if root.note:
            self.add("note:root", "text",
                     {"x": M + 4, "y": H - M + 8, "fill": theme.MUTED,
                      "font-size": theme.FS_NOTE, "text-anchor": "start"},
                     8, root.note, cls="note")
            bottom -= 22
        if any(k.parcel == scene.root for k in scene.keys):
            top += 22
        self.layout_parcel(scene.root, _rect(M, top, W - 2 * M, bottom - top))
        self.draw_strands()
        self.draw_cords()
        self.draw_corrals()
        self.draw_badges()
        self.draw_keys()
        self.draw_annotations()
        self.collect_warnings()
        self.items.sort(key=lambda it: it["layer"])
        return self.items, self.warnings

    # ------------------------------------------------------------------
    def layout_parcel(self, pid, rect):
        scene = self.scene
        p = scene.parcels[pid]
        self.envelopes[pid] = dict(rect)
        r = dict(rect)
        if p.kind == "nest":
            self.add(f"panel:{pid}", "rect",
                     {"x": r["x"], "y": r["y"], "width": r["w"], "height": r["h"],
                      "rx": 8, "fill": "#FFFFFF", "stroke": theme.PANEL_EDGE,
                      "stroke-width": 1}, 1.8 if p.host_glyph else 0.4,
                     cls="panel")
            pad = 8
            r = _rect(r["x"] + pad, r["y"] + pad, r["w"] - 2 * pad, r["h"] - 2 * pad)
        if p.entitle and pid != scene.root:
            self.add(f"title:{pid}", "text",
                     {"x": r["x"] + 2, "y": r["y"] + 11, "fill": theme.LABEL,
                      "font-size": theme.FS_SUBTITLE, "font-weight": 600,
                      "text-anchor": "start"}, 8, p.entitle, cls="title")
            r = _rect(r["x"], r["y"] + 20, r["w"], r["h"] - 20)
        if p.breathe:
            b = p.breathe * min(r["w"], r["h"])
            r = _rect(r["x"] + b, r["y"] + b, r["w"] - 2 * b, r["h"] - 2 * b)

        gutters = {s: RIM_GUTTER[s] for s in p.rims}
        plot = _rect(r["x"] + gutters.get("west", 0),
                     r["y"] + gutters.get("north", 0),
                     r["w"] - gutters.get("west", 0) - gutters.get("east", 0),
                     r["h"] - gutters.get("north", 0) - gutters.get("south", 0))
        self.plots[pid] = plot
        self.draw_wefts(p, plot)
        self.draw_rims(p, plot)

        if p.carve:
            self.layout_carve(p, plot)
        elif p.split:
            self.layout_split(p, plot)
        else:
            self.layout_leaf(p, plot)

        # parcel-nests inside this parcel
        for q in scene.parcels.values():
            if q.kind == "nest" and q.parent == pid and not q.host_glyph:
                self.layout_parcel(q.id, self.nest_rect(q, plot))
        # host-nests under glyphs of this parcel
        for q in scene.parcels.values():
            if q.kind == "nest" and q.host_glyph:
                hg = scene.glyphs.get(q.host_glyph)
                if hg and hg.parcel == pid and hg.id in self.pos:
                    self.layout_parcel(q.id, self.host_rect(q, hg))

    def nest_rect(self, q, plot):
        w = plot["w"] * (q.nest_breadth or 0.5)
        h = plot["h"] * (q.nest_depth or 0.4)
        aim = q.nest_aim or "center"
        x = plot["x"] + (plot["w"] - w) / 2
        y = plot["y"] + (plot["h"] - h) / 2
        if aim == "north":
            y = plot["y"] + 6
        elif aim == "south":
            y = plot["y"] + plot["h"] - h - 6
        if aim == "east":
            x = plot["x"] + plot["w"] - w - 6
            y = plot["y"] + 6
        elif aim == "west":
            x = plot["x"] + 6
            y = plot["y"] + 6
        return _rect(x, y, w, h)

    def host_rect(self, q, hg):
        gp = self.pos[hg.id]
        w = max(gp["w"] * (q.nest_breadth or 1.25), 104.0)
        h = max(66.0, gp["h"] * 1.5 * (q.nest_depth or 0.9))
        aim = q.nest_aim or "south"
        x = gp["cx"] - w / 2
        y = gp["cy"] + gp["h"] / 2 + 8
        if aim == "north":
            y = gp["cy"] - gp["h"] / 2 - 8 - h
        elif aim == "east":
            x, y = gp["cx"] + gp["w"] / 2 + 8, gp["cy"] - h / 2
        elif aim == "west":
            x, y = gp["cx"] - gp["w"] / 2 - 8 - w, gp["cy"] - h / 2
        return _rect(x, y, w, h)

    # ------------------------------------------------------------------
    def layout_carve(self, p, plot):
        order = list(p.carve["order"])
        if p.carve["along"] in p.inverted:
            order = order[::-1]
        n = len(order)
        gap = p.carve["gap"]
        if p.carve["along"] == "span":
            slot = plot["w"] / n
            for i, key in enumerate(order):
                cid = p.carve["cells"][key]
                self.layout_parcel(cid, _rect(plot["x"] + i * slot + slot * gap / 2,
                                              plot["y"], slot * (1 - gap), plot["h"]))
        else:
            slot = plot["h"] / n
            for i, key in enumerate(order):
                cid = p.carve["cells"][key]
                self.layout_parcel(cid, _rect(plot["x"],
                                              plot["y"] + i * slot + slot * gap / 2,
                                              plot["w"], slot * (1 - gap)))

    def layout_split(self, p, plot):
        cells = p.split["cells"]
        n = len(cells)
        gap = p.split["gap"]
        if p.split["along"] == "span":
            slot = plot["w"] / n
            for i, cid in enumerate(cells):
                self.layout_parcel(cid, _rect(plot["x"] + i * slot + slot * gap / 2,
                                              plot["y"], slot * (1 - gap), plot["h"]))
        else:
            slot = plot["h"] / n
            for i, cid in enumerate(cells):
                self.layout_parcel(cid, _rect(plot["x"],
                                              plot["y"] + i * slot + slot * gap / 2,
                                              plot["w"], slot * (1 - gap)))

    # ------------------------------------------------------------------
    def layout_leaf(self, p, plot):
        scene = self.scene
        glyphs = [g for g in scene.glyphs.values() if g.parcel == p.id]
        if not glyphs:
            return
        law = scene.effective_settle(p)
        root = scene.chart_root(p.id)
        if root.hooped or p.hooped:
            self.settle_wheel(p, plot, glyphs)
            return
        if law["law"] == "current":
            self.settle_current(p, plot, glyphs, law.get("heading") or "east")
            return
        if law["law"] == "strew":
            self.settle_strew(p, root, plot, glyphs)
            return
        if law["law"] == "heap":
            self.settle_heap(p, root, plot, glyphs)
            return
        self.settle_abreast(p, root, plot, glyphs)

    # -- laws --------------------------------------------------------------
    def _rise_frac(self, root, b, g, trait):
        gauge = self.gs.for_brood(b, trait)
        vein = b.meterings[trait]
        v = g.row.get(vein) if g.row else None
        if gauge is None or v is None:
            return None
        return gauge.frac(v)

    def _y(self, root, plot, frac):
        if "rise" in root.inverted:
            return plot["y"] + frac * plot["h"]
        return plot["y"] + plot["h"] - frac * plot["h"]

    def _x(self, root, plot, frac):
        if "span" in root.inverted:
            return plot["x"] + (1 - frac) * plot["w"]
        return plot["x"] + frac * plot["w"]

    def settle_abreast(self, p, root, plot, glyphs):
        n = len(glyphs)
        slot = plot["w"] / n
        floor = plot["y"] + plot["h"]
        inv = "rise" in root.inverted
        for i, g in enumerate(glyphs):
            b = self.brood_of(g)
            cx = plot["x"] + (i + 0.5) * slot
            w = slot * 0.78
            girth_only = b and "girth" in b.meterings and \
                "stature" not in b.meterings
            if b and "girth" in b.meterings:
                f = self._rise_frac(root, b, g, "girth")
                w = (plot["w"] if girth_only else slot * 0.9) * \
                    (f if f is not None else 0.5)
            if g.form in ("slab", "capsule", "plaque"):
                if girth_only:
                    # horizontal bar: grow from the west edge, slot the rise
                    h = plot["h"] * 0.78 if len(glyphs) == 1 else slot * 0.78
                    h = min(h, plot["h"] * 0.78)
                    x = plot["x"] + plot["w"] - w if "span" in root.inverted \
                        else plot["x"]
                    self.emit_block(g, x, plot["y"] + plot["h"] / 2 - h / 2, w, h)
                    continue
                if b and "stature" in b.meterings:
                    f = self._rise_frac(root, b, g, "stature") or 0
                    h = f * plot["h"]
                else:
                    h = plot["h"] * 0.55
                y = plot["y"] if inv else floor - h
                self.emit_block(g, cx - w / 2, y, w, h)
            elif g.form in ("disc", "wisp", "ring"):
                r = self.disc_radius(g, b, min(slot, plot["h"]))
                cy = plot["y"] + plot["h"] / 2
                if b and "stature" in b.meterings:
                    f = self._rise_frac(root, b, g, "stature") or 0
                    cy = self._y(root, plot, f)
                self.emit_round(g, cx, cy, r)
            else:
                w0, h0 = NODE_SIZES.get(g.form, (90, 40))
                s = min(1.0, slot * 0.85 / w0, plot["h"] * 0.6 / h0)
                self.emit_node(g, cx, plot["y"] + plot["h"] / 2, w0 * s, h0 * s)
        for g in glyphs:
            b = self.brood_of(g)
            if b and ("stance" in b.meterings or "perch" in b.meterings) \
                    and g.form in ("disc", "wisp", "ring"):
                self.warn("stance/perch meterings are idle under law 'abreast' "
                          "(consider the settling family)")
                break

    def settle_heap(self, p, root, plot, glyphs):
        floor = plot["y"] + plot["h"]
        inv = "rise" in root.inverted
        w = plot["w"] * 0.66
        cx = plot["x"] + plot["w"] / 2
        acc = 0.0
        for g in glyphs:
            b = self.brood_of(g)
            f = self._rise_frac(root, b, g, "stature") if b and "stature" in \
                b.meterings else None
            if f is None:
                f = 1.0 / len(glyphs) * 0.8
            h = f * plot["h"]
            y = (plot["y"] + acc) if inv else (floor - acc - h)
            self.emit_block(g, cx - w / 2, y, w, max(h - 1.2, 0.5), heap=True)
            acc += h
        if acc > plot["h"] + 1:
            self.warn("heap exceeds its cell (rebase the gauge or distill the data)")

    def settle_strew(self, p, root, plot, glyphs):
        for g in glyphs:
            b = self.brood_of(g)
            if not b:
                w0, h0 = NODE_SIZES.get(g.form, (60, 40))
                self.emit_node(g, plot["x"] + plot["w"] / 2,
                               plot["y"] + plot["h"] / 2, w0, h0)
                continue
            fx = self._rise_frac(root, b, g, "stance") if "stance" in b.meterings \
                else None
            fy = self._rise_frac(root, b, g, "perch") if "perch" in b.meterings \
                else None
            cx = self._x(root, plot, fx if fx is not None else 0.5)
            cy = self._y(root, plot, fy if fy is not None else 0.5)
            if g.form in ("slab", "capsule", "plaque"):
                w = h = 12
                stance_gauge = self.gs.for_brood(b, "stance") \
                    if "stance" in b.meterings else None
                if stance_gauge is not None and stance_gauge.kind == "band":
                    w = stance_gauge.band_span() * plot["w"] * 0.62
                if "girth" in b.meterings:
                    w = (self._rise_frac(root, b, g, "girth") or 0) * plot["w"] * 0.2 + 4
                if "stature" in b.meterings:
                    h = (self._rise_frac(root, b, g, "stature") or 0) * plot["h"]
                    cy = self._y(root, plot, 0) - h / 2
                self.emit_block(g, cx - w / 2, cy - h / 2, w, h)
            else:
                r = self.disc_radius(g, b, 220)
                self.emit_round(g, cx, cy, r)

    def disc_radius(self, g, b, ref):
        base = {"wisp": 3.6, "disc": 6.5, "ring": 7.5}.get(g.form, 6.0)
        if b and "bulk" in b.meterings:
            gauge = self.gs.for_brood(b, "bulk")
            v = g.row.get(b.meterings["bulk"]) if g.row else None
            if gauge and v is not None:
                # perceptual: area ~ value
                return 4.0 + math.sqrt(max(gauge.frac(v), 0)) * min(ref * 0.11, 26)
        return base

    def settle_wheel(self, p, plot, glyphs):
        cx = plot["x"] + plot["w"] / 2
        cy = plot["y"] + plot["h"] / 2
        R = min(plot["w"], plot["h"]) / 2 * 0.86
        hooped = p.hooped or self.scene.chart_root(p.id).hooped
        r0 = R * (hooped["inner"] if hooped else 0)
        vals = []
        for g in glyphs:
            b = self.brood_of(g)
            v = 1.0
            if b and "girth" in b.meterings and g.row:
                v = max(float(g.row.get(b.meterings["girth"], 0)), 0)
            vals.append(v)
        total = sum(vals) or 1.0
        a = -90.0
        for g, v in zip(glyphs, vals):
            sweep_deg = 360.0 * v / total
            a1 = a + sweep_deg
            fill = self.fill_for(g)
            fill, stroke, sw, op = self.styled(g, fill)
            d = self.wedge_path(cx, cy, r0, R, a, a1)
            self.add(f"glyph:{g.id}", "path",
                     {"d": d, "fill": fill, "stroke": "#FFFFFF",
                      "stroke-width": max(sw, 1.5), "opacity": op},
                     3 + g.layer, cls="glyph",
                     meta={"wedge": True, "hub": (cx, cy), "r0": r0,
                           "r1": R, "a0": a, "a1": a1})
            mid = math.radians((a + a1) / 2)
            self.pos[g.id] = {"cx": cx + math.cos(mid) * (r0 + R) / 2,
                              "cy": cy + math.sin(mid) * (r0 + R) / 2,
                              "w": R - r0, "h": R - r0, "kind": "wedge",
                              "mid_angle": (a + a1) / 2, "R": R,
                              "hub": (cx, cy), "frac": v / total}
            a = a1

    def wedge_path(self, cx, cy, r0, r1, a0, a1):
        a0r, a1r = math.radians(a0), math.radians(a1)
        large = 1 if (a1 - a0) > 180 else 0
        x0, y0 = cx + r1 * math.cos(a0r), cy + r1 * math.sin(a0r)
        x1, y1 = cx + r1 * math.cos(a1r), cy + r1 * math.sin(a1r)
        if r0 <= 0.5:
            return (f"M{cx:.2f},{cy:.2f} L{x0:.2f},{y0:.2f} "
                    f"A{r1:.2f},{r1:.2f} 0 {large} 1 {x1:.2f},{y1:.2f} Z")
        xi1, yi1 = cx + r0 * math.cos(a1r), cy + r0 * math.sin(a1r)
        xi0, yi0 = cx + r0 * math.cos(a0r), cy + r0 * math.sin(a0r)
        return (f"M{x0:.2f},{y0:.2f} A{r1:.2f},{r1:.2f} 0 {large} 1 "
                f"{x1:.2f},{y1:.2f} L{xi1:.2f},{yi1:.2f} "
                f"A{r0:.2f},{r0:.2f} 0 {large} 0 {xi0:.2f},{yi0:.2f} Z")

    # -- current (flow) -----------------------------------------------------
    def settle_current(self, p, plot, glyphs, heading):
        scene = self.scene
        ids = [g.id for g in glyphs]
        idset = set(ids)
        edges = [(c.tail, c.head) for c in scene.cords.values()
                 if c.tail in idset and c.head in idset]
        succ, pred = {i: [] for i in ids}, {i: [] for i in ids}
        for t, h in edges:
            succ[t].append(h)
            pred[h].append(t)
        layer = {}

        def depth(n, seen):
            if n in layer:
                return layer[n]
            if n in seen:
                return 0
            seen.add(n)
            d = 0 if not pred[n] else max(depth(m, seen) + 1 for m in pred[n])
            layer[n] = d
            return d

        for n in ids:
            depth(n, set())
        nlayers = max(layer.values()) + 1 if layer else 1
        cols = [[] for _ in range(nlayers)]
        for n in ids:
            cols[layer[n]].append(n)
        # barycenter ordering (two passes)
        for _ in range(2):
            for li in range(1, nlayers):
                prev_pos = {n: i for i, n in enumerate(cols[li - 1])}
                cols[li].sort(key=lambda n: (
                    sum(prev_pos.get(m, 0) for m in pred[n]) / len(pred[n])
                    if pred[n] else ids.index(n)))
        maxc = max(len(c) for c in cols)
        horiz = heading in ("east", "west")
        along_len = plot["w"] if horiz else plot["h"]
        cross_len = plot["h"] if horiz else plot["w"]
        pitch_a = along_len / nlayers
        pitch_c = cross_len / maxc
        scale = 1.0
        for g in glyphs:
            w0, h0 = NODE_SIZES.get(g.form, (110, 44))
            if horiz:
                scale = min(scale, pitch_a * 0.72 / w0, pitch_c * 0.8 / h0)
            else:
                scale = min(scale, pitch_a * 0.72 / h0, pitch_c * 0.8 / w0)
        scale = min(scale, 1.0)
        for li, col in enumerate(cols):
            fa = (li + 0.5) / nlayers
            if heading in ("west", "north"):
                fa = 1 - fa
            for ci, n in enumerate(col):
                fc = (ci + 0.5) / len(col)
                if horiz:
                    cx = plot["x"] + fa * plot["w"]
                    cy = plot["y"] + fc * plot["h"]
                else:
                    cx = plot["x"] + fc * plot["w"]
                    cy = plot["y"] + fa * plot["h"]
                g = scene.glyphs[n]
                w0, h0 = NODE_SIZES.get(g.form, (110, 44))
                self.emit_node(g, cx, cy, w0 * scale, h0 * scale)

    # -- emitters -----------------------------------------------------------
    def emit_block(self, g, x, y, w, h, heap=False):
        fill = self.fill_for(g)
        fill, stroke, sw, op = self.styled(g, fill)
        rx = 2.5 if not heap else 1
        if g.form == "capsule":
            rx = min(10, h / 2)
        self.add(f"glyph:{g.id}", "rect",
                 {"x": x, "y": y, "width": max(w, 0.5), "height": max(h, 0.5),
                  "rx": rx, "fill": fill, "stroke": stroke, "stroke-width": sw,
                  "opacity": op}, 3 + g.layer, cls="glyph")
        self.pos[g.id] = {"cx": x + w / 2, "cy": y + h / 2, "w": w, "h": h,
                          "kind": "block", "top": y}

    def emit_round(self, g, cx, cy, r):
        fill = self.fill_for(g)
        fill, stroke, sw, op = self.styled(g, fill)
        attrs = {"cx": cx, "cy": cy, "r": r, "opacity": op}
        if g.form == "ring":
            attrs.update({"fill": "none", "stroke": fill,
                          "stroke-width": max(sw, 2)})
        else:
            attrs.update({"fill": fill, "stroke": stroke, "stroke-width": sw})
        self.add(f"glyph:{g.id}", "circle", attrs, 3 + g.layer, cls="glyph")
        self.pos[g.id] = {"cx": cx, "cy": cy, "w": 2 * r, "h": 2 * r,
                          "kind": "round", "top": cy - r}

    def emit_node(self, g, cx, cy, w, h):
        fill = self.fill_for(g)
        fill, stroke, sw, op = self.styled(g, fill)
        if sw == 0:
            stroke, sw = theme.NODE_EDGE, 1.2
        lid = f"glyph:{g.id}"
        layer = 3 + g.layer
        if g.form == "rhomb":
            pts = f"{cx},{cy-h/2} {cx+w/2},{cy} {cx},{cy+h/2} {cx-w/2},{cy}"
            self.add(lid, "polygon", {"points": pts, "fill": fill,
                                      "stroke": stroke, "stroke-width": sw,
                                      "opacity": op}, layer, cls="glyph",
                     meta={"node": True, "x": cx - w / 2, "y": cy - h / 2,
                           "w": w, "h": h})
        elif g.form == "drum":
            ry = h * 0.14
            x0, x1 = cx - w / 2, cx + w / 2
            y0, y1 = cy - h / 2 + ry, cy + h / 2 - ry
            d = (f"M{x0:.1f},{y0:.1f} A{w/2:.1f},{ry:.1f} 0 0 1 {x1:.1f},{y0:.1f} "
                 f"L{x1:.1f},{y1:.1f} A{w/2:.1f},{ry:.1f} 0 0 1 {x0:.1f},{y1:.1f} Z "
                 f"M{x0:.1f},{y0:.1f} A{w/2:.1f},{ry:.1f} 0 0 0 {x1:.1f},{y0:.1f}")
            self.add(lid, "path", {"d": d, "fill": fill, "stroke": stroke,
                                   "stroke-width": sw, "opacity": op},
                     layer, cls="glyph",
                     meta={"node": True, "x": cx - w / 2, "y": cy - h / 2,
                           "w": w, "h": h})
        elif g.form in ("disc", "ring", "wisp"):
            self.emit_round(g, cx, cy, min(w, h) / 2)
            return
        else:
            rx = h / 2 if g.form == "capsule" else 5
            self.add(lid, "rect", {"x": cx - w / 2, "y": cy - h / 2, "width": w,
                                   "height": h, "rx": rx, "fill": fill,
                                   "stroke": stroke, "stroke-width": sw,
                                   "opacity": op}, layer, cls="glyph",
                     meta={"node": True})
        self.pos[g.id] = {"cx": cx, "cy": cy, "w": w, "h": h, "kind": "node",
                          "top": cy - h / 2}

    # ------------------------------------------------------------------
    def draw_strands(self):
        scene = self.scene
        for s in scene.strands.values():
            b = scene.broods.get(s.brood)
            if not b or not b.glyphs:
                continue
            led = self.ledgers.resolve(b.ledger_ref)
            key = led.sort_key(s.by)
            kind = led.kind_of(s.by)
            if kind == "told":
                levels = led.ordered_levels(s.by)
                order_of = {v: i for i, v in enumerate(levels)}
                sort_val = lambda g: order_of.get(g.row.get(s.by), 0)
            elif kind == "ranked":
                sort_val = lambda g: key(g.row.get(s.by))
            else:
                sort_val = lambda g: g.row.get(s.by, 0)
            gl = [scene.glyphs[i] for i in b.glyphs if i in self.pos]
            gl.sort(key=sort_val)
            pts = []
            for g in gl:
                pp = self.pos[g.id]
                y = pp["top"] if pp["kind"] == "block" else pp["cy"]
                pts.append((pp["cx"], y))
            if len(pts) < 2:
                continue
            color = hue_hex(s.tint) if s.tint else None
            if color is None:
                color = self.fill_for(gl[0])
                if color == theme.NODE_FILL:
                    color = palette_colors("quill")[0]
            width = 2.2 + (s.heft or 0) * 4
            d = self.smooth_path(pts)
            layer = 4 + getattr(s, "layer", 0)
            op = 0.25 if b.hushed else 1.0
            if s.flooded:
                plot = self.plots.get(scene.chart_root(b.parcel).id) or \
                    self.plots.get(b.parcel)
                floor = plot["y"] + plot["h"]
                fd = d + f" L{pts[-1][0]:.1f},{floor:.1f} L{pts[0][0]:.1f},{floor:.1f} Z"
                self.add(f"flood:{s.id}", "path",
                         {"d": fd, "fill": color, "opacity": 0.13 * op,
                          "stroke": "none"}, 2, cls="flood",
                         meta={"points": pts, "floor": floor})
            sw = width + (1.4 if s.kindled else 0)
            self.add(f"strand:{s.id}", "path",
                     {"d": d, "fill": "none", "stroke": color, "stroke-width": sw,
                      "stroke-linecap": "round", "stroke-linejoin": "round",
                      "opacity": op}, layer, cls="strand",
                     meta={"points": pts})

    def smooth_path(self, pts):
        if len(pts) == 2:
            return f"M{pts[0][0]:.1f},{pts[0][1]:.1f} L{pts[1][0]:.1f},{pts[1][1]:.1f}"
        d = f"M{pts[0][0]:.1f},{pts[0][1]:.1f}"
        for i in range(1, len(pts)):
            p0 = pts[max(i - 2, 0)]
            p1 = pts[i - 1]
            p2 = pts[i]
            p3 = pts[min(i + 1, len(pts) - 1)]
            c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
            c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
            d += (f" C{c1[0]:.1f},{c1[1]:.1f} {c2[0]:.1f},{c2[1]:.1f} "
                  f"{p2[0]:.1f},{p2[1]:.1f}")
        return d

    # ------------------------------------------------------------------
    def draw_cords(self):
        scene = self.scene
        pipes = [c for c in scene.cords.values() if c.pipe_width]
        max_pipe = max((c.pipe_width for c in pipes), default=1.0)
        for c in scene.cords.values():
            if c.tail not in self.pos or c.head not in self.pos:
                continue
            a, b = self.pos[c.tail], self.pos[c.head]
            ax, ay, na = self.edge_anchor(a, b)
            bx, by, nb = self.edge_anchor(b, a)
            dx, dy = bx - ax, by - ay
            dist = math.hypot(dx, dy) or 1
            if c.crook == "straight":
                d = f"M{ax:.1f},{ay:.1f} L{bx:.1f},{by:.1f}"
                end_dir = (dx / dist, dy / dist)
            elif c.crook == "bend":
                # orthogonal route whose last leg enters along the face normal
                if nb[0]:
                    mx = (ax + bx) / 2
                    d = (f"M{ax:.1f},{ay:.1f} L{mx:.1f},{ay:.1f} "
                         f"L{mx:.1f},{by:.1f} L{bx:.1f},{by:.1f}")
                else:
                    my = (ay + by) / 2
                    d = (f"M{ax:.1f},{ay:.1f} L{ax:.1f},{my:.1f} "
                         f"L{bx:.1f},{my:.1f} L{bx:.1f},{by:.1f}")
                end_dir = (-nb[0], -nb[1])
            else:
                # bezier that leaves and arrives along the face normals, so
                # barbs sit perpendicular to the edge they plug into
                nx, ny = -dy / dist, dx / dist
                off = c.sweep * dist * 0.35
                reach = max(dist * 0.4, 26.0)
                c1 = (ax + na[0] * reach + nx * off,
                      ay + na[1] * reach + ny * off)
                c2 = (bx + nb[0] * reach + nx * off,
                      by + nb[1] * reach + ny * off)
                d = (f"M{ax:.1f},{ay:.1f} C{c1[0]:.1f},{c1[1]:.1f} "
                     f"{c2[0]:.1f},{c2[1]:.1f} {bx:.1f},{by:.1f}")
                end_dir = (-nb[0], -nb[1])
            if c.pipe_width:
                wpx = 5 + 22 * (c.pipe_width / max_pipe)
                color = hue_hex(c.tint) if c.tint else theme.PIPE
                if c.kindled:
                    color = theme.CORD_KINDLED
                self.add(f"cord:{c.id}", "path",
                         {"d": d, "fill": "none", "stroke": color,
                          "stroke-width": wpx, "opacity": 0.5 if not c.kindled
                          else 0.75, "stroke-linecap": "butt"},
                         2.8, cls="pipe",
                         meta={"cord": [ax, ay, bx, by], "barbed": False})
            else:
                color = hue_hex(c.tint) if c.tint else theme.CORD
                if c.kindled:
                    color = theme.CORD_KINDLED
                w = 1.6 + (c.heft or 0) * 3.5 + (0.8 if c.kindled else 0)
                op = 0.25 if c.hushed else getattr(c, "veil", 0.95)
                self.add(f"cord:{c.id}", "path",
                         {"d": d, "fill": "none", "stroke": color,
                          "stroke-width": w, "opacity": op,
                          "stroke-linecap": "round"}, 3.4, cls="cord",
                         meta={"cord": [ax, ay, bx, by],
                               "barbed": c.barb in ("head", "both")})
                if c.barb in ("head", "both"):
                    self.arrow(f"barb:{c.id}:h", bx, by, end_dir, color, w, op)
                if c.barb in ("tail", "both"):
                    sx, sy = -end_dir[0], -end_dir[1]
                    self.arrow(f"barb:{c.id}:t", ax, ay, (sx, sy), color, w, op)
            if c.badge:
                mx, my = (ax + bx) / 2, (ay + by) / 2
                self.add(f"badge:cord:{c.id}", "text",
                         {"x": mx, "y": my - 7, "fill": theme.MUTED,
                          "font-size": theme.FS_BADGE, "text-anchor": "middle"},
                         6, c.badge, cls="badge")

    def edge_anchor(self, frm, to):
        """Anchor on frm's boundary toward to's center, plus the outward
        normal of the chosen face (so cords can arrive perpendicular)."""
        dx, dy = to["cx"] - frm["cx"], to["cy"] - frm["cy"]
        if abs(dx) * frm["h"] >= abs(dy) * frm["w"]:
            sx = 1 if dx > 0 else -1
            x = frm["cx"] + (frm["w"] / 2) * sx
            y = frm["cy"] + (dy / (abs(dx) or 1)) * frm["w"] / 2 * 0.35
            return (x, y, (sx, 0))
        sy = 1 if dy > 0 else -1
        y = frm["cy"] + (frm["h"] / 2) * sy
        x = frm["cx"] + (dx / (abs(dy) or 1)) * frm["h"] / 2 * 0.35
        return (x, y, (0, sy))

    def arrow(self, id, x, y, dirv, color, w, op=1.0):
        ux, uy = dirv
        size = 4.5 + w
        px, py = -uy, ux
        pts = (f"{x:.1f},{y:.1f} "
               f"{x - ux * size + px * size * 0.55:.1f},"
               f"{y - uy * size + py * size * 0.55:.1f} "
               f"{x - ux * size - px * size * 0.55:.1f},"
               f"{y - uy * size - py * size * 0.55:.1f}")
        self.add(id, "polygon", {"points": pts, "fill": color, "opacity": op},
                 3.45, cls="barb")

    # ------------------------------------------------------------------
    def draw_corrals(self):
        for k in self.scene.corrals.values():
            boxes = [self.pos[m] for m in k.members if m in self.pos]
            if not boxes:
                continue
            x0 = min(b["cx"] - b["w"] / 2 for b in boxes) - 16
            x1 = max(b["cx"] + b["w"] / 2 for b in boxes) + 16
            y0 = min(b["cy"] - b["h"] / 2 for b in boxes) - (26 if k.label else 14)
            y1 = max(b["cy"] + b["h"] / 2 for b in boxes) + 14
            fill = soften(hue_hex(k.tint), 0.88) if k.tint else theme.CORRAL_FILL
            edge = mix(hue_hex(k.tint), "#FFFFFF", 0.55) if k.tint else \
                theme.CORRAL_EDGE
            self.add(f"corral:{k.id}", "rect",
                     {"x": x0, "y": y0, "width": x1 - x0, "height": y1 - y0,
                      "rx": 10, "fill": fill, "stroke": edge, "stroke-width": 1},
                     1.5, cls="corral")
            if k.label:
                self.add(f"corral-label:{k.id}", "text",
                         {"x": x0 + 10, "y": y0 + 15, "fill": theme.MUTED,
                          "font-size": 10.5, "font-weight": 600,
                          "letter-spacing": "0.08em", "text-anchor": "start"},
                         6, k.label.upper(), cls="label")

    # ------------------------------------------------------------------
    def draw_badges(self):
        scene = self.scene
        done = set()
        for b in scene.broods.values():
            spec = b.badge
            for gid in b.glyphs:
                g = scene.glyphs[gid]
                s = g.badge or spec
                if not s or gid not in self.pos:
                    continue
                text = s.get("text")
                if s.get("vein") and g.row:
                    text = fmt_num(g.row.get(s["vein"]))
                if text is None:
                    continue
                self.place_badge(g, str(text), s.get("aim", "auto"))
                done.add(gid)
        for g in scene.glyphs.values():
            if g.id not in self.pos:
                continue
            if g.id not in done and g.badge:
                self.place_badge(g, g.badge.get("text", ""),
                                 g.badge.get("aim", "auto"))
            if g.badge2:
                self.place_badge(g, g.badge2.get("text", ""),
                                 g.badge2.get("aim", "south"), secondary=True)

    def place_badge(self, g, text, aim, secondary=False):
        pp = self.pos[g.id]
        fs = theme.FS_BADGE
        fill = theme.LABEL
        anchor = "middle"
        weight = 500
        if pp["kind"] == "node":
            x, y = pp["cx"], pp["cy"] + fs * 0.36
            fs, fill, weight = theme.FS_NODE, theme.NODE_TEXT, 500
            if secondary:
                fs, fill, weight = theme.FS_BADGE, theme.MUTED, 500
            if aim in ("north",):
                y = pp["cy"] - pp["h"] / 2 - 6
            elif aim in ("south",):
                y = pp["cy"] + pp["h"] / 2 + fs + 2
        elif pp["kind"] == "wedge":
            mid = math.radians(pp["mid_angle"])
            hubx, huby = pp["hub"]
            if aim == "center":
                rr = (pp["R"] - pp["w"] / 2) if pp["w"] < pp["R"] else pp["R"] * 0.6
                x = hubx + math.cos(mid) * rr
                y = huby + math.sin(mid) * rr + fs * 0.35
                fill = "#FFFFFF"
            else:  # rim / auto
                x = hubx + math.cos(mid) * (pp["R"] + 12)
                y = huby + math.sin(mid) * (pp["R"] + 12) + fs * 0.35
                anchor = "start" if math.cos(mid) > 0.25 else \
                    ("end" if math.cos(mid) < -0.25 else "middle")
        else:
            x, y = pp["cx"], pp["top"] - 5
            if aim == "south":
                y = pp["cy"] + pp["h"] / 2 + fs + 3
            elif aim == "center":
                y = pp["cy"] + fs * 0.36
                fill = "#FFFFFF" if pp["kind"] == "block" and pp["h"] > 16 else fill
            elif aim == "east":
                x, y, anchor = pp["cx"] + pp["w"] / 2 + 6, pp["cy"] + fs * 0.36, "start"
            elif aim == "west":
                x, y, anchor = pp["cx"] - pp["w"] / 2 - 6, pp["cy"] + fs * 0.36, "end"
        self.add(f"badge{'2' if secondary else ''}:{g.id}", "text",
                 {"x": x, "y": y, "fill": fill, "font-size": fs,
                  "font-weight": weight, "text-anchor": anchor},
                 6, text, cls="badge")

    # ------------------------------------------------------------------
    def draw_rims(self, p, plot):
        if not p.rims:
            return
        root = self.scene.chart_root(p.id)
        for side in p.rims:
            if side in ("south", "north"):
                gauge = self.gs.direction(root.id, "span")
                y = plot["y"] + plot["h"] if side == "south" else plot["y"]
                self.add(f"rim:{p.id}:{side}", "line",
                         {"x1": plot["x"], "y1": y, "x2": plot["x"] + plot["w"],
                          "y2": y, "stroke": theme.AXIS, "stroke-width": 1}, 5,
                         cls="rimline")
                if not gauge:
                    continue
                ticks = gauge.ticks()
                if gauge.kind == "counted" and len(ticks) > 12:
                    ticks = ticks[::2]
                if gauge.kind == "band" and len(ticks) > 16:
                    step = math.ceil(len(ticks) / 12)
                    ticks = ticks[::step]
                ty = y + 18 if side == "south" else y - 8
                for t in ticks:
                    fx = self._x(root, plot, gauge.frac(t))
                    label = fmt_num(t) if gauge.kind == "counted" else str(t)
                    self.add(f"rimtick:{p.id}:{side}:{t}", "text",
                             {"x": fx, "y": ty, "fill": theme.MUTED,
                              "font-size": theme.FS_TICK, "text-anchor": "middle"},
                             5, label, cls="tick")
                    if gauge.kind == "counted":
                        self.add(f"rimmark:{p.id}:{side}:{t}", "line",
                                 {"x1": fx, "y1": y, "x2": fx,
                                  "y2": y + (4 if side == "south" else -4),
                                  "stroke": theme.AXIS, "stroke-width": 1}, 5,
                                 cls="rimline")
            else:
                gauge = None
                if side == "east":
                    for b in self.scene.broods_in(root.id):
                        for t in ("perch", "stature"):
                            if t in b.loose_traits:
                                gauge = self.gs.for_brood(b, t)
                if gauge is None:
                    gauge = self.gs.direction(root.id, "rise")
                x = plot["x"] if side == "west" else plot["x"] + plot["w"]
                self.add(f"rim:{p.id}:{side}", "line",
                         {"x1": x, "y1": plot["y"], "x2": x,
                          "y2": plot["y"] + plot["h"], "stroke": theme.AXIS,
                          "stroke-width": 1}, 5, cls="rimline")
                if not gauge:
                    continue
                anchor = "end" if side == "west" else "start"
                tx = x - 8 if side == "west" else x + 8
                for t in gauge.ticks():
                    fy = self._y(root, plot, gauge.frac(t))
                    label = fmt_num(t) if gauge.kind == "counted" else str(t)
                    self.add(f"rimtick:{p.id}:{side}:{t}", "text",
                             {"x": tx, "y": fy + 3.5, "fill": theme.MUTED,
                              "font-size": theme.FS_TICK, "text-anchor": anchor},
                             5, label, cls="tick")

    def draw_wefts(self, p, plot):
        if not p.wefts:
            return
        root = self.scene.chart_root(p.id)
        for along in p.wefts:
            if along == "rise":
                gauge = self.gs.direction(root.id, "rise")
                if not gauge or gauge.kind != "counted":
                    continue
                for t in gauge.ticks():
                    fy = self._y(root, plot, gauge.frac(t))
                    self.add(f"weft:{p.id}:rise:{t}", "line",
                             {"x1": plot["x"], "y1": fy,
                              "x2": plot["x"] + plot["w"], "y2": fy,
                              "stroke": theme.GRID, "stroke-width": 1}, 1,
                             cls="weft")
            else:
                gauge = self.gs.direction(root.id, "span")
                if not gauge or gauge.kind != "counted":
                    continue
                for t in gauge.ticks():
                    fx = self._x(root, plot, gauge.frac(t))
                    self.add(f"weft:{p.id}:span:{t}", "line",
                             {"x1": fx, "y1": plot["y"], "x2": fx,
                              "y2": plot["y"] + plot["h"],
                              "stroke": theme.GRID, "stroke-width": 1}, 1,
                             cls="weft")

    # ------------------------------------------------------------------
    def draw_keys(self):
        scene = self.scene
        for i, k in enumerate(scene.keys):
            b = scene.broods.get(k.brood)
            if not b or k.trait not in b.meterings:
                continue
            gauge = self.gs.for_brood(b, k.trait)
            env = self.envelopes.get(k.parcel)
            if not gauge or not env:
                continue
            colors = palette_colors(self.parcel_palette(b.parcel))
            if gauge.kind == "band":
                entries = [(str(lv), colors[j % len(colors)])
                           for j, lv in enumerate(gauge.levels)]
            else:
                lo, hi = gauge.domain
                entries = [(fmt_num(lo), ramp(0, colors[0])),
                           ("", ramp(0.5, colors[0])),
                           (fmt_num(hi), ramp(1, colors[0]))]
            total = sum(text_w(t, theme.FS_TICK) + 26 for t, _ in entries)
            x = env["x"] + env["w"] - total
            y = env["y"] - 12 - i * 18 if k.parcel == scene.root else env["y"] + 6
            for j, (label, color) in enumerate(entries):
                self.add(f"key:{k.brood}:{k.trait}:swatch:{j}", "rect",
                         {"x": x, "y": y - 8, "width": 10, "height": 10,
                          "rx": 3, "fill": color}, 6, cls="key")
                self.add(f"key:{k.brood}:{k.trait}:label:{j}", "text",
                         {"x": x + 14, "y": y + 1, "fill": theme.LABEL,
                          "font-size": theme.FS_TICK, "text-anchor": "start"},
                         6, label, cls="key")
                x += text_w(label, theme.FS_TICK) + 26

    # ------------------------------------------------------------------
    def anchor_of(self, ref):
        scene = self.scene
        if ref in self.pos:
            pp = self.pos[ref]
            return pp["cx"], pp.get("top", pp["cy"] - pp["h"] / 2), pp
        for g in scene.glyphs.values():
            if g.name == ref and g.id in self.pos:
                pp = self.pos[g.id]
                return pp["cx"], pp.get("top", pp["cy"] - pp["h"] / 2), pp
        if ref in scene.cords:
            c = scene.cords[ref]
            if c.tail in self.pos and c.head in self.pos:
                a, b = self.pos[c.tail], self.pos[c.head]
                return (a["cx"] + b["cx"]) / 2, (a["cy"] + b["cy"]) / 2 - 8, None
        if ref in scene.flocks:
            ms = [m for m in scene.flocks[ref].members if m in self.pos]
            if ms:
                xs = [self.pos[m]["cx"] for m in ms]
                ys = [self.pos[m]["cy"] - self.pos[m]["h"] / 2 for m in ms]
                return sum(xs) / len(xs), min(ys), None
        if ref in self.plots:
            pl = self.plots[ref]
            return pl["x"] + 8, pl["y"] + 8, None
        return None

    def draw_annotations(self):
        W = theme.CANVAS_W
        for a in self.scene.annotations:
            fs = theme.FS_ANNOT
            if a.kind == "inscribe":
                if a.near:
                    anc = self.anchor_of(a.near)
                    if not anc:
                        continue
                    x, y, pp = anc
                    aim = a.aim if a.aim != "auto" else "north"
                    if aim == "north":
                        y -= 10
                        anchor = "middle"
                    elif aim == "south":
                        y += (pp["h"] + 24 if pp else 28)
                        anchor = "middle"
                    elif aim == "east":
                        x += (pp["w"] / 2 + 10 if pp else 12)
                        y += 12
                        anchor = "start"
                    elif aim == "west":
                        x -= (pp["w"] / 2 + 10 if pp else 12)
                        y += 12
                        anchor = "end"
                    else:
                        anchor = "middle"
                else:
                    pl = self.plots.get(self.scene.root)
                    x, y, anchor = pl["x"] + 4, pl["y"] + 14, "start"
                x = min(max(x, 30), W - 30)
                self.add(f"annot:{a.id}", "text",
                         {"x": x, "y": y, "fill": theme.INK, "font-size": fs,
                          "font-weight": 500, "text-anchor": anchor},
                         7, a.text, cls="annot")
            else:  # flag
                anc = self.anchor_of(a.near)
                if not anc:
                    continue
                x, y, pp = anc
                tw = text_w(a.text, fs)
                tx = x + 30
                ty = y - 34
                if tx + tw > W - 24:
                    tx = x - 30 - tw
                if ty < 20:
                    ty = y + (pp["h"] + 40 if pp else 46)
                self.add(f"flagline:{a.id}", "path",
                         {"d": f"M{tx + (0 if tx > x else tw):.1f},{ty + 4:.1f} "
                               f"L{x:.1f},{y - 3:.1f}",
                          "stroke": theme.FAINT, "stroke-width": 1,
                          "fill": "none"}, 6.8, cls="flagline",
                         meta={"seg": [tx + (0 if tx > x else tw), ty + 4,
                                       x, y - 3]})
                self.add(f"flagdot:{a.id}", "circle",
                         {"cx": x, "cy": y - 3, "r": 2, "fill": theme.INK}, 6.9,
                         cls="flagline")
                self.add(f"annot:{a.id}", "text",
                         {"x": tx, "y": ty, "fill": theme.INK, "font-size": fs,
                          "font-weight": 600, "text-anchor": "start"},
                         7, a.text, cls="annot")

    # ------------------------------------------------------------------
    def collect_warnings(self):
        texts = []
        for it in self.items:
            if it["tag"] == "text" and it.get("cls") in ("badge", "tick", "annot"):
                at = it["attrs"]
                w = text_w(it.get("text", ""), at.get("font-size", 11))
                x = at["x"]
                if at.get("text-anchor") == "middle":
                    x -= w / 2
                elif at.get("text-anchor") == "end":
                    x -= w
                texts.append((x, at["y"] - at.get("font-size", 11), w,
                              at.get("font-size", 11) * 1.2, it["id"]))
        overlaps = 0
        for i in range(len(texts)):
            for j in range(i + 1, len(texts)):
                a, b = texts[i], texts[j]
                if a[0] < b[0] + b[2] and b[0] < a[0] + a[2] and \
                        a[1] < b[1] + b[3] and b[1] < a[1] + a[3]:
                    overlaps += 1
        if overlaps:
            self.warn(f"{overlaps} label pair(s) overlap")
        out = 0
        for it in self.items:
            at = it["attrs"]
            xs, ys = [], []
            if it["tag"] == "rect":
                xs = [at["x"], at["x"] + at["width"]]
                ys = [at["y"], at["y"] + at["height"]]
            elif it["tag"] == "circle":
                xs = [at["cx"] - at["r"], at["cx"] + at["r"]]
                ys = [at["cy"] - at["r"], at["cy"] + at["r"]]
            if xs and (min(xs) < -1 or max(xs) > theme.CANVAS_W + 1 or
                       min(ys) < -1 or max(ys) > theme.CANVAS_H + 1):
                out += 1
        if out:
            self.warn(f"{out} element(s) fall outside the ground")
        for b in self.scene.broods.values():
            if b.glyphs and not b.meterings:
                g0 = self.scene.glyphs[b.glyphs[0]]
                if g0.row and b.form in ("slab", "disc", "wisp"):
                    self.warn(f"brood {b.id} carries data but has no meterings")


def layout_scene(scene, ledgers):
    return Layout(scene, ledgers).run()


def presentation_report(scene, ledgers):
    """Structured layout-quality metrics for the verifier."""
    ly = Layout(scene, ledgers)
    items, warnings = ly.run()
    report = {"label_overlaps": 0, "out_of_bounds": 0, "glyph_collisions": 0,
              "cord_crossings": 0, "warnings": warnings}
    for w in warnings:
        if "label pair" in w:
            report["label_overlaps"] = int(w.split()[0])
        if "outside the ground" in w:
            report["out_of_bounds"] = int(w.split()[0])
    # glyph collisions: block glyphs in the same parcel overlapping heavily
    by_parcel = {}
    for gid, pp in ly.pos.items():
        g = scene.glyphs.get(gid)
        if not g or pp["kind"] not in ("block", "node"):
            continue
        by_parcel.setdefault(g.parcel, []).append(pp)
    for boxes in by_parcel.values():
        for i in range(len(boxes)):
            for j in range(i + 1, len(boxes)):
                a, b = boxes[i], boxes[j]
                ox = min(a["cx"] + a["w"] / 2, b["cx"] + b["w"] / 2) - \
                    max(a["cx"] - a["w"] / 2, b["cx"] - b["w"] / 2)
                oy = min(a["cy"] + a["h"] / 2, b["cy"] + b["h"] / 2) - \
                    max(a["cy"] - a["h"] / 2, b["cy"] - b["h"] / 2)
                if ox > 0 and oy > 0:
                    inter = ox * oy
                    smaller = min(a["w"] * a["h"], b["w"] * b["h"]) or 1
                    if inter / smaller > 0.4:
                        report["glyph_collisions"] += 1
    # cord crossings (straight midlines)
    segs = []
    for c in scene.cords.values():
        if c.tail in ly.pos and c.head in ly.pos:
            a, b = ly.pos[c.tail], ly.pos[c.head]
            segs.append(((a["cx"], a["cy"]), (b["cx"], b["cy"])))

    def crosses(s1, s2):
        (ax, ay), (bx, by) = s1
        (cx, cy), (dx, dy) = s2

        def ccw(px, py, qx, qy, rx, ry):
            return (ry - py) * (qx - px) - (qy - py) * (rx - px)

        d1 = ccw(cx, cy, dx, dy, ax, ay)
        d2 = ccw(cx, cy, dx, dy, bx, by)
        d3 = ccw(ax, ay, bx, by, cx, cy)
        d4 = ccw(ax, ay, bx, by, dx, dy)
        return d1 * d2 < 0 and d3 * d4 < 0

    for i in range(len(segs)):
        for j in range(i + 1, len(segs)):
            if len({segs[i][0], segs[i][1], segs[j][0], segs[j][1]}) == 4 and \
                    crosses(segs[i], segs[j]):
                report["cord_crossings"] += 1
    return report
