"""Ledgers: named tables the agent refines through sift/distill/derive/bin/marshal/crop.

Base ledgers come from datasets.py; refinements create derived ledgers (L1, L2, ...)
with recorded provenance. Verification is content-based (row multisets), so any
derivation path that yields the right table is accepted.
"""

from .datasets import DATASETS, RANKED_ORDERS, vein_kind, ranked_sort_key
from .errors import VeldError

RELATIONS = ["is", "is_not", "above", "below", "at_least", "at_most", "among"]
DISTILL_MODES = ["sum", "mean", "median", "min", "max", "count"]
DERIVE_MODES = ["ratio", "diff", "total_share"]
SENSES = ["waxing", "waning"]


class Ledger:
    def __init__(self, ref, rows, provenance=None, local_orders=None):
        self.ref = ref
        self.rows = rows
        self.provenance = provenance or []
        self.local_orders = local_orders or {}

    def vein_names(self):
        return list(self.rows[0].keys()) if self.rows else []

    def veins(self):
        out = {}
        for name in self.vein_names():
            values = [r[name] for r in self.rows]
            if name in self.local_orders:
                out[name] = "ranked"
            else:
                out[name] = vein_kind(name, values)
        return out

    def kind_of(self, vein):
        kinds = self.veins()
        if vein not in kinds:
            raise VeldError(
                f"ledger {self.ref} has no vein '{vein}'. Veins: {', '.join(kinds)}."
            )
        return kinds[vein]

    def values(self, vein):
        self.kind_of(vein)
        return [r[vein] for r in self.rows]

    def sort_key(self, vein):
        if vein in self.local_orders:
            order = self.local_orders[vein]
            return lambda v: order.index(v) if v in order else len(order)
        return lambda v: ranked_sort_key(vein, v)

    def ordered_levels(self, vein):
        """Distinct values of a told/ranked vein, in rank order (ranked) or
        first-appearance order (told)."""
        seen, levels = set(), []
        for r in self.rows:
            v = r[vein]
            if v not in seen:
                seen.add(v)
                levels.append(v)
        if self.kind_of(vein) == "ranked":
            levels.sort(key=self.sort_key(vein))
        return levels


class LedgerSpace:
    """Per-task data environment: all base datasets plus task-local derivations."""

    def __init__(self):
        self.derived = {}
        self._n = 0

    def resolve(self, ref):
        if not isinstance(ref, str):
            raise VeldError(f"expected a ledger name or ref, got {ref!r}.")
        if ref in self.derived:
            return self.derived[ref]
        if ref in DATASETS:
            return Ledger(ref, [dict(r) for r in DATASETS[ref]])
        raise VeldError(
            f"unknown ledger '{ref}'. Use shelf() for base ledgers; "
            f"derived refs look like L1, L2, ..."
        )

    def register(self, rows, provenance, local_orders=None):
        self._n += 1
        ref = f"L{self._n}"
        led = Ledger(ref, rows, provenance, local_orders)
        self.derived[ref] = led
        return led

    # -- refinement operations -----------------------------------------

    def sift(self, ref, vein, relation, value):
        led = self.resolve(ref)
        kind = led.kind_of(vein)
        if relation not in RELATIONS:
            raise VeldError(
                f"sift: unknown relation '{relation}'. Relations: {', '.join(RELATIONS)}."
            )
        if relation in ("above", "below", "at_least", "at_most") and kind != "counted":
            raise VeldError(
                f"sift: relation '{relation}' needs a counted vein; '{vein}' is {kind}."
            )
        if relation == "among" and not isinstance(value, list):
            raise VeldError("sift: relation 'among' needs a list value.")

        def keep(v):
            if relation == "is":
                return v == value
            if relation == "is_not":
                return v != value
            if relation == "above":
                return v > value
            if relation == "below":
                return v < value
            if relation == "at_least":
                return v >= value
            if relation == "at_most":
                return v <= value
            return v in value

        rows = [dict(r) for r in led.rows if keep(r[vein])]
        if not rows:
            raise VeldError(
                f"sift: no rows of {ref} satisfy {vein} {relation} {value!r}."
            )
        prov = led.provenance + [("sift", vein, relation, value)]
        return self.register(rows, prov, dict(led.local_orders))

    def distill(self, ref, by, take, mode):
        led = self.resolve(ref)
        if mode not in DISTILL_MODES:
            raise VeldError(
                f"distill: unknown mode '{mode}'. Modes: {', '.join(DISTILL_MODES)}."
            )
        by_list = by if isinstance(by, list) else [by]
        for b in by_list:
            k = led.kind_of(b)
            if k == "counted":
                raise VeldError(
                    f"distill: 'by' veins must be told or ranked; '{b}' is counted."
                )
        if mode != "count":
            if not take:
                raise VeldError("distill: mode '%s' requires take=." % mode)
            if led.kind_of(take) != "counted":
                raise VeldError(
                    f"distill: take vein must be counted; '{take}' is {led.kind_of(take)}."
                )
        groups = {}
        order = []
        for r in led.rows:
            key = tuple(r[b] for b in by_list)
            if key not in groups:
                groups[key] = []
                order.append(key)
            groups[key].append(r)

        def agg(vals):
            if mode == "sum":
                return round(sum(vals), 6)
            if mode == "mean":
                return round(sum(vals) / len(vals), 4)
            if mode == "median":
                s = sorted(vals)
                m = len(s) // 2
                return s[m] if len(s) % 2 else round((s[m - 1] + s[m]) / 2, 4)
            if mode == "min":
                return min(vals)
            if mode == "max":
                return max(vals)

        out = []
        for key in order:
            row = {b: k for b, k in zip(by_list, key)}
            if mode == "count":
                row["tally"] = len(groups[key])
            else:
                row[take] = agg([r[take] for r in groups[key]])
            out.append(row)
        prov = led.provenance + [("distill", tuple(by_list), take, mode)]
        return self.register(out, prov, dict(led.local_orders))

    def derive(self, ref, name, mode, a, b=None):
        led = self.resolve(ref)
        if mode not in DERIVE_MODES:
            raise VeldError(
                f"derive: unknown mode '{mode}'. Modes: {', '.join(DERIVE_MODES)}."
            )
        if led.kind_of(a) != "counted":
            raise VeldError(f"derive: vein 'a' must be counted; '{a}' is {led.kind_of(a)}.")
        if mode in ("ratio", "diff"):
            if not b:
                raise VeldError(f"derive: mode '{mode}' requires b=.")
            if led.kind_of(b) != "counted":
                raise VeldError(f"derive: vein 'b' must be counted; '{b}' is {led.kind_of(b)}.")
        rows = [dict(r) for r in led.rows]
        if mode == "total_share":
            total = sum(r[a] for r in rows) or 1
            for r in rows:
                r[name] = round(100.0 * r[a] / total, 4)
        else:
            for r in rows:
                r[name] = round(r[a] / r[b], 6) if mode == "ratio" else round(r[a] - r[b], 6)
        prov = led.provenance + [("derive", name, mode, a, b)]
        return self.register(rows, prov, dict(led.local_orders))

    def bin(self, ref, vein, bins=8):
        led = self.resolve(ref)
        if led.kind_of(vein) != "counted":
            raise VeldError(f"bin: vein must be counted; '{vein}' is {led.kind_of(vein)}.")
        if not isinstance(bins, int) or bins < 2 or bins > 40:
            raise VeldError("bin: bins must be an integer between 2 and 40.")
        vals = led.values(vein)
        lo, hi = min(vals), max(vals)
        import math as _m
        raw = (hi - lo) / bins or 1
        exp = _m.floor(_m.log10(raw))
        width = next(n * (10 ** exp) for n in (1, 2, 2.5, 5, 10)
                     if n * (10 ** exp) >= raw - 1e-12)
        start = _m.floor(lo / width) * width
        nb = max(1, _m.ceil((hi - start) / width - 1e-9))
        labels, counts = [], [0] * nb
        for i in range(nb):
            a = start + i * width
            b = start + (i + 1) * width
            labels.append(f"{a:g}–{b:g}")
        for v in vals:
            idx = min(int((v - start) / width), nb - 1)
            counts[idx] += 1
        rows = [{"bin": labels[i], "tally": counts[i]} for i in range(nb)]
        prov = led.provenance + [("bin", vein, bins)]
        orders = dict(led.local_orders)
        orders["bin"] = labels
        return self.register(rows, prov, orders)

    def marshal(self, ref, vein, sense):
        led = self.resolve(ref)
        if sense not in SENSES:
            raise VeldError(f"marshal: sense must be one of: {', '.join(SENSES)}.")
        kind = led.kind_of(vein)
        key = led.sort_key(vein) if kind == "ranked" else (lambda v: v)
        rows = sorted(
            (dict(r) for r in led.rows),
            key=lambda r: key(r[vein]),
            reverse=(sense == "waning"),
        )
        prov = led.provenance + [("marshal", vein, sense)]
        return self.register(rows, prov, dict(led.local_orders))

    def crop(self, ref, first):
        led = self.resolve(ref)
        if not isinstance(first, int) or first < 1:
            raise VeldError("crop: first must be a positive integer.")
        rows = [dict(r) for r in led.rows[:first]]
        prov = led.provenance + [("crop", first)]
        return self.register(rows, prov, dict(led.local_orders))
