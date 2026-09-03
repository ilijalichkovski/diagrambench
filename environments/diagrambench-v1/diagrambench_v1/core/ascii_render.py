"""ASCII view: rasterize the display list onto a character grid.

The render is the agent's primary feedback after every `sigil run` — it must
be legible enough to debug from. Deterministic; default 160x60.
"""

import math

CANVAS_W, CANVAS_H = 960.0, 600.0
PATTERNS = ["█", "▓", "▒", "░", "▤", "▦", "▧", "▨", "◆", "◇"]
NEUTRAL_FILLS = {"#F6F7FA", "#FFFFFF", "#FCFCFA", "#F2F4F8"}


class Grid:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.g = [[" "] * w for _ in range(h)]

    def px(self, x, y):
        return (int(x / CANVAS_W * self.w), int(y / CANVAS_H * self.h))

    def put(self, gx, gy, ch):
        if 0 <= gx < self.w and 0 <= gy < self.h:
            self.g[gy][gx] = ch

    def text(self, x, y, s, anchor="start"):
        gx, gy = self.px(x, y)
        if anchor == "middle":
            gx -= len(s) // 2
        elif anchor == "end":
            gx -= len(s)
        for i, ch in enumerate(s):
            self.put(gx + i, gy, ch)

    def hline(self, x0, x1, y, ch="─"):
        gx0, gy = self.px(min(x0, x1), y)
        gx1, _ = self.px(max(x0, x1), y)
        for gx in range(gx0, gx1 + 1):
            self.put(gx, gy, ch)

    def vline(self, x, y0, y1, ch="│"):
        gx, gy0 = self.px(x, min(y0, y1))
        _, gy1 = self.px(x, max(y0, y1))
        for gy in range(gy0, gy1 + 1):
            self.put(gx, gy, ch)

    def box(self, x, y, w, h, dashed=False):
        gx0, gy0 = self.px(x, y)
        gx1, gy1 = self.px(x + w, y + h)
        gx1, gy1 = max(gx1, gx0 + 1), max(gy1, gy0 + 1)
        hch = "┄" if dashed else "─"
        vch = "┆" if dashed else "│"
        for gx in range(gx0 + 1, gx1):
            self.put(gx, gy0, hch)
            self.put(gx, gy1, hch)
        for gy in range(gy0 + 1, gy1):
            self.put(gx0, gy, vch)
            self.put(gx1, gy, vch)
        self.put(gx0, gy0, "┌")
        self.put(gx1, gy0, "┐")
        self.put(gx0, gy1, "└")
        self.put(gx1, gy1, "┘")

    def fill(self, x, y, w, h, ch):
        gx0, gy0 = self.px(x, y)
        gx1, gy1 = self.px(x + w, y + h)
        gx1, gy1 = max(gx1, gx0), max(gy1, gy0)
        for gy in range(gy0, gy1 + 1):
            for gx in range(gx0, gx1 + 1):
                self.put(gx, gy, ch)

    def line(self, x0, y0, x1, y1, ch=None, dot=False):
        gx0, gy0 = self.px(x0, y0)
        gx1, gy1 = self.px(x1, y1)
        dx, dy = abs(gx1 - gx0), abs(gy1 - gy0)
        steps = max(dx, dy, 1)
        for i in range(steps + 1):
            t = i / steps
            gx = round(gx0 + (gx1 - gx0) * t)
            gy = round(gy0 + (gy1 - gy0) * t)
            if ch:
                c = ch
            elif dot:
                c = "·"
            elif dx >= dy * 2:
                c = "─"
            elif dy >= dx * 2:
                c = "│"
            else:
                c = "\\" if (gx1 - gx0) * (gy1 - gy0) > 0 else "/"
            self.put(gx, gy, c)

    def render(self):
        return "\n".join("".join(row).rstrip() for row in self.g)


def _arrow_char(dx, dy):
    if abs(dx) >= abs(dy):
        return "▶" if dx > 0 else "◀"
    return "▼" if dy > 0 else "▲"


def ascii_view(items, warnings, width=160, height=60):
    grid = Grid(width, height)
    fills = {}  # hex -> pattern char

    def pattern(hexc, kindled=False, hushed=False):
        if hushed:
            return "·"
        if kindled:
            return "◉"
        if hexc not in fills:
            fills[hexc] = PATTERNS[len(fills) % len(PATTERNS)]
        return fills[hexc]

    texts = []
    for it in items:
        a = it["attrs"]
        cls = it.get("cls")
        meta = it.get("meta") or {}
        tag = it["tag"]

        if tag == "text":
            texts.append(it)
            continue

        if cls in ("panel",):
            grid.box(a["x"], a["y"], a["width"], a["height"])
        elif cls == "corral":
            grid.box(a["x"], a["y"], a["width"], a["height"], dashed=True)
        elif cls == "glyph" and tag == "rect":
            kindled = float(a.get("stroke-width") or 0) >= 2 and \
                a.get("stroke") not in (None, "none")
            hushed = float(a.get("opacity", 1)) < 0.3
            if meta.get("node"):
                grid.box(a["x"], a["y"], a["width"], a["height"])
            else:
                grid.fill(a["x"], a["y"], a["width"], a["height"],
                          pattern(a.get("fill", "#000"), kindled, hushed))
        elif cls == "glyph" and tag == "circle":
            hushed = float(a.get("opacity", 1)) < 0.3
            kindled = float(a.get("stroke-width") or 0) >= 2 and \
                a.get("fill") not in ("none",)
            r = a["r"]
            if r <= 6:
                gx, gy = grid.px(a["cx"], a["cy"])
                grid.put(gx, gy, "·" if hushed else
                         ("○" if a.get("fill") == "none" else "•"))
            else:
                ch = pattern(a.get("fill") if a.get("fill") != "none"
                             else a.get("stroke", "#000"), kindled, hushed)
                rx = r
                for ddy in range(-int(r), int(r) + 1, max(int(600 / height), 1)):
                    half = math.sqrt(max(r * r - ddy * ddy, 0))
                    gx0, gy = grid.px(a["cx"] - half, a["cy"] + ddy)
                    gx1, _ = grid.px(a["cx"] + half, a["cy"] + ddy)
                    for gx in range(gx0, gx1 + 1):
                        grid.put(gx, gy, ch)
        elif cls == "glyph" and meta.get("wedge"):
            hx, hy = meta["hub"]
            r0, r1 = meta["r0"], meta["r1"]
            a0, a1 = meta["a0"], meta["a1"]
            ch = pattern(a.get("fill", "#000"),
                         float(a.get("stroke-width") or 0) >= 2)
            cw, chh = CANVAS_W / width, CANVAS_H / height
            gx0, gy0 = grid.px(hx - r1, hy - r1)
            gx1, gy1 = grid.px(hx + r1, hy + r1)
            for gy in range(max(gy0, 0), min(gy1 + 1, height)):
                for gx in range(max(gx0, 0), min(gx1 + 1, width)):
                    px = (gx + 0.5) * cw
                    py = (gy + 0.5) * chh
                    dx, dy = px - hx, py - hy
                    r = math.hypot(dx, dy)
                    if not (r0 <= r <= r1):
                        continue
                    ang = math.degrees(math.atan2(dy, dx))
                    span = (a1 - a0) % 360 or 360
                    rel = (ang - a0) % 360
                    if rel <= span:
                        grid.put(gx, gy, ch)
        elif cls == "glyph" and meta.get("node"):
            grid.box(meta["x"], meta["y"], meta["w"], meta["h"])
        elif cls == "strand" and meta.get("points"):
            pts = meta["points"]
            for i in range(1, len(pts)):
                grid.line(pts[i - 1][0], pts[i - 1][1], pts[i][0], pts[i][1])
        elif cls == "flood" and meta.get("points"):
            pts = meta["points"]
            floor = meta["floor"]
            for i in range(1, len(pts)):
                x0, y0 = pts[i - 1]
                x1, y1 = pts[i]
                steps = max(int(abs(x1 - x0) / (CANVAS_W / width)), 1)
                for s in range(steps + 1):
                    t = s / steps
                    px = x0 + (x1 - x0) * t
                    py = y0 + (y1 - y0) * t
                    gx, gy0 = grid.px(px, py)
                    _, gy1 = grid.px(px, floor)
                    for gy in range(gy0, gy1 + 1):
                        if grid.g[gy][gx] == " ":
                            grid.put(gx, gy, "░")
        elif cls in ("cord", "pipe") and meta.get("cord"):
            ax, ay, bx, by = meta["cord"]
            if cls == "pipe":
                grid.line(ax, ay, bx, by, ch="═" if abs(bx - ax) >=
                          abs(by - ay) else "║")
            else:
                grid.line(ax, ay, bx, by)
            if meta.get("barbed"):
                gx, gy = grid.px(bx, by)
                grid.put(gx, gy, _arrow_char(bx - ax, by - ay))
        elif cls == "flagline" and tag == "path" and meta.get("seg"):
            x0, y0, x1, y1 = meta["seg"]
            grid.line(x0, y0, x1, y1, dot=True)
        elif cls in ("rimline",) and tag == "line":
            if abs(a["y2"] - a["y1"]) < 1:
                grid.hline(a["x1"], a["x2"], a["y1"])
            elif abs(a["x2"] - a["x1"]) < 1:
                grid.vline(a["x1"], a["y1"], a["y2"])
        elif cls == "weft" and tag == "line":
            if abs(a["y2"] - a["y1"]) < 1:
                gx0, gy = grid.px(a["x1"], a["y1"])
                gx1, _ = grid.px(a["x2"], a["y2"])
                for gx in range(gx0, gx1 + 1, 3):
                    if grid.g[gy][gx] == " ":
                        grid.put(gx, gy, "·")
            else:
                gx, gy0 = grid.px(a["x1"], a["y1"])
                _, gy1 = grid.px(a["x2"], a["y2"])
                for gy in range(gy0, gy1 + 1, 2):
                    if grid.g[gy][gx] == " ":
                        grid.put(gx, gy, "·")
        elif cls == "key" and tag == "rect":
            gx, gy = grid.px(a["x"], a["y"])
            grid.put(gx, gy + 1, pattern(a.get("fill", "#000")))
        elif cls == "barb" and tag == "polygon":
            pass  # arrowheads for current-law cords come via meta.barbed

    # text on top
    for it in texts:
        a = it["attrs"]
        grid.text(a["x"], a["y"], it.get("text", ""),
                  a.get("text-anchor", "start"))

    lines = [grid.render()]
    if fills:
        legend = "  ".join(f"{ch}={hexc}" for hexc, ch in fills.items())
        lines.append("fills: " + legend + "   ◉=kindled  ·=hushed/point")
    if warnings:
        lines.append("advisories: " + "; ".join(warnings))
    return "\n".join(lines)
