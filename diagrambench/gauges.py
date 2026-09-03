"""Gauge resolution.

Gauges (calibrated mappings from data to visual magnitude) are never stored;
they are derived deterministically from the scene + ledgers, so layout,
introspection and observations always agree.

A chart root parcel owns one gauge per direction (span / rise) plus one per
non-spatial trait (tint / bulk / veil / heft) per brood. Carve cells inherit
their root's gauges; `loosen` gives a brood a private gauge for a trait;
`share` unions two roots' gauges for a trait.
"""

import math

from .errors import SigilError

EXTENT_TRAITS = {"stature": "rise", "girth": "span"}
STATION_TRAITS = {"stance": "span", "perch": "rise"}


def nice_ceil(x):
    if x <= 0:
        return 1
    exp = math.floor(math.log10(x))
    f = x / (10 ** exp)
    for n in (1, 2, 2.5, 5, 10):
        if f <= n + 1e-9:
            return n * (10 ** exp)
    return 10 ** (exp + 1)


def nice_ticks(lo, hi, target=5):
    if hi <= lo:
        hi = lo + 1
    span = hi - lo
    step = nice_ceil(span / max(target, 2))
    first = math.ceil(lo / step) * step
    ticks = []
    t = first
    while t <= hi + 1e-9:
        ticks.append(round(t, 10))
        t += step
    return ticks


class Gauge:
    """kind: 'counted' (continuous) or 'band' (discrete stations)."""

    def __init__(self, kind, domain=None, levels=None, zero=False):
        self.kind = kind
        self.domain = domain  # (lo, hi) for counted
        self.levels = levels or []  # ordered values for band
        self.zero = zero

    def describe(self):
        if self.kind == "band":
            shown = ", ".join(str(v) for v in self.levels[:6])
            more = "" if len(self.levels) <= 6 else f", … ({len(self.levels)} levels)"
            return f"band [{shown}{more}]"
        lo, hi = self.domain
        return f"counted [{lo:g} … {hi:g}]"

    def frac(self, value):
        """Normalize a value to 0..1 along the gauge."""
        if self.kind == "band":
            if value not in self.levels:
                return 0.0
            n = len(self.levels)
            return (self.levels.index(value) + 0.5) / n
        lo, hi = self.domain
        if hi <= lo:
            return 0.0
        v = min(max(value, lo), hi)
        return (v - lo) / (hi - lo)

    def band_span(self):
        return 1.0 / max(len(self.levels), 1) if self.kind == "band" else 0.0

    def ticks(self):
        if self.kind == "band":
            return list(self.levels)
        return nice_ticks(self.domain[0], self.domain[1])


def _counted_domain(values, zero):
    lo, hi = min(values), max(values)
    if zero:
        lo = min(0, lo)
        hi = max(hi, 0)
        step = nice_ceil(hi / 5) if hi > 0 else 1
        return (lo, math.ceil(hi / step - 1e-9) * step)
    if lo == hi:
        pad = abs(lo) * 0.1 or 1
        return (lo - pad, hi + pad)
    pad = (hi - lo) * 0.08
    return (lo - pad if lo - pad > 0 or lo < 0 else 0, hi + pad)


class GaugeSet:
    """All gauges for a scene, resolved once per layout/observation."""

    def __init__(self, scene, ledgers):
        self.scene = scene
        self.ledgers = ledgers
        self._dir = {}  # (root_pid, direction) -> Gauge
        self._trait = {}  # (brood_id, trait) -> Gauge
        self._resolve()

    # -- public ----------------------------------------------------------
    def direction(self, root_pid, direction):
        return self._dir.get((root_pid, direction))

    def trait(self, brood_id, trait):
        return self._trait.get((brood_id, trait))

    def for_brood(self, brood, trait):
        """The gauge governing a brood's trait (private if loosened)."""
        if trait in ("tint", "bulk", "veil", "heft"):
            return self._trait.get((brood.id, trait))
        if trait in EXTENT_TRAITS or trait in STATION_TRAITS:
            if trait in brood.loose_traits:
                return self._trait.get((brood.id, trait))
            d = EXTENT_TRAITS.get(trait) or STATION_TRAITS.get(trait)
            root = self.scene.chart_root(brood.parcel)
            return self._dir.get((root.id, d))
        return None

    # -- resolution --------------------------------------------------------
    def _brood_ledger(self, brood):
        return self.ledgers.resolve(brood.ledger_ref)

    def _resolve(self):
        scene = self.scene
        # group contributions per (root, direction)
        contrib = {}  # key -> {"values": [], "levels": [], "zero": bool}

        def slot(key):
            return contrib.setdefault(key, {"values": [], "levels": [], "zero": False})

        # carve bands claim the carved direction of their root
        for p in scene.parcels.values():
            if p.carve:
                root = scene.chart_root(p.id)
                s = slot((root.id, p.carve["along"]))
                for lv in p.carve["order"]:
                    if lv not in s["levels"]:
                        s["levels"].append(lv)

        for b in scene.broods.values():
            if not b.glyphs:
                continue
            led = self._brood_ledger(b)
            root = scene.chart_root(b.parcel)
            for trait, vein in b.meterings.items():
                kind = led.kind_of(vein)
                vals = [g.row[vein] for gid in b.glyphs
                        for g in [scene.glyphs[gid]] if g.row and vein in g.row]
                if trait in ("tint", "bulk", "veil", "heft") or trait in b.loose_traits:
                    self._trait[(b.id, trait)] = self._make_trait_gauge(
                        trait, kind, vals, led, vein, b)
                    continue
                d = EXTENT_TRAITS.get(trait) or STATION_TRAITS.get(trait)
                if not d:
                    continue
                s = slot((root.id, d))
                if trait in EXTENT_TRAITS:
                    s["zero"] = True
                if kind == "counted":
                    gvals = vals
                    if trait in EXTENT_TRAITS and b.glyphs:
                        g0 = scene.glyphs[b.glyphs[0]]
                        law = scene.effective_settle(
                            scene.parcels[g0.parcel])["law"]
                        if law == "heap":
                            # stacked: the gauge must fit each cell's sum
                            sums = {}
                            for gid in b.glyphs:
                                g = scene.glyphs[gid]
                                if g.row and vein in g.row:
                                    sums[g.parcel] = sums.get(g.parcel, 0) + \
                                        g.row[vein]
                            gvals = list(sums.values()) or vals
                    s["values"].extend(gvals)
                else:
                    for lv in led.ordered_levels(vein):
                        if lv not in s["levels"]:
                            s["levels"].append(lv)

        # apply shares (union domains)
        merged = {}
        for (pa, pb, trait) in scene.shared:
            d = EXTENT_TRAITS.get(trait) or STATION_TRAITS.get(trait)
            if not d:
                continue
            ka, kb = (pa, d), (pb, d)
            if ka in contrib and kb in contrib:
                u = {"values": contrib[ka]["values"] + contrib[kb]["values"],
                     "levels": contrib[ka]["levels"] + [l for l in contrib[kb]["levels"]
                                                        if l not in contrib[ka]["levels"]],
                     "zero": contrib[ka]["zero"] or contrib[kb]["zero"]}
                merged[ka] = u
                merged[kb] = u
        contrib.update(merged)

        for (root_pid, d), s in contrib.items():
            self._dir[(root_pid, d)] = self._finish(root_pid, d, s)

    def _override_for(self, root_pid, direction):
        p = self.scene.parcels.get(root_pid)
        if not p:
            return None
        for trait, dd in list(EXTENT_TRAITS.items()) + list(STATION_TRAITS.items()):
            if dd == direction and trait in p.gauge_overrides:
                return p.gauge_overrides[trait]
        return None

    def _finish(self, root_pid, direction, s):
        if s["levels"]:
            g = Gauge("band", levels=s["levels"])
        elif s["values"]:
            g = Gauge("counted", domain=_counted_domain(s["values"], s["zero"]),
                      zero=s["zero"])
        else:
            g = Gauge("counted", domain=(0, 1))
        ov = self._override_for(root_pid, direction)
        if ov and g.kind == "counted":
            floor, ceil = ov
            lo, hi = g.domain
            g.domain = (lo if floor is None else floor, hi if ceil is None else ceil)
        return g

    def _make_trait_gauge(self, trait, kind, vals, led, vein, brood):
        if trait == "tint":
            if kind == "counted":
                return Gauge("counted", domain=_counted_domain(vals, False))
            return Gauge("band", levels=led.ordered_levels(vein))
        if trait in ("stance", "perch", "stature", "girth"):
            # loosened spatial trait -> private gauge
            if kind == "counted":
                zero = trait in EXTENT_TRAITS
                ov = brood and self.scene.parcels.get(
                    self.scene.chart_root(brood.parcel).id)
                g = Gauge("counted", domain=_counted_domain(vals, zero), zero=zero)
                if ov and trait in ov.gauge_overrides:
                    floor, ceil = ov.gauge_overrides[trait]
                    lo, hi = g.domain
                    g.domain = (lo if floor is None else floor,
                                hi if ceil is None else ceil)
                return g
            return Gauge("band", levels=led.ordered_levels(vein))
        if kind != "counted":
            raise SigilError(f"trait '{trait}' requires a counted vein.")
        return Gauge("counted", domain=(0, nice_ceil(max(vals))) if vals else (0, 1),
                     zero=True)
