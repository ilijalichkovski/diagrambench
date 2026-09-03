"""Semantic verifier.

Each task carries a hidden goal: a list of checks evaluated against the
candidate semantic scene (never pixels). Structural/`brood` checks expand into
micro-checks so partial progress is visible ("right bars, wrong grouping").

Result: {success, semantic_score, layout_score, failed, passed, presentation}
"""

from .errors import VeldError
from .layout import presentation_report
from .ledgers import LedgerSpace


# ----------------------------------------------------------------------
# helpers
# ----------------------------------------------------------------------

def _norm(s):
    return str(s).strip().lower()


def _text_has(text, sub):
    return text is not None and _norm(sub) in _norm(text)


def apply_transform(base, transform):
    """Apply a hidden-goal transform spec to a base dataset; return rows."""
    ls = LedgerSpace()
    ref = base
    for step in transform or []:
        op = step[0]
        if op == "sift":
            ref = ls.sift(ref, step[1], step[2], step[3]).ref
        elif op == "distill":
            ref = ls.distill(ref, step[1], step[2], step[3]).ref
        elif op == "derive":
            ref = ls.derive(ref, step[1], step[2], step[3],
                            step[4] if len(step) > 4 else None).ref
        elif op == "bin":
            ref = ls.bin(ref, step[1], step[2] if len(step) > 2 else 8).ref
        elif op == "marshal":
            ref = ls.marshal(ref, step[1], step[2]).ref
        elif op == "crop":
            ref = ls.crop(ref, step[1]).ref
        else:
            raise ValueError(f"unknown transform step {op}")
    return ls.resolve(ref).rows


def _row_key(row, cols):
    out = []
    for c in cols:
        v = row.get(c)
        if isinstance(v, float):
            v = round(v, 4)
        out.append(v)
    return tuple(out)


def rows_match(expected, actual):
    """Multiset equality on the expected columns (actual may carry extras)."""
    if not expected:
        return not actual
    cols = list(expected[0].keys())
    if actual and any(c not in actual[0] for c in cols):
        return False
    if len(expected) != len(actual):
        return False
    return sorted(map(str, (_row_key(r, cols) for r in expected))) == \
        sorted(map(str, (_row_key(r, cols) for r in actual)))


def _glyph_matches_where(g, where):
    if not g.row:
        return False
    for k, v in where.items():
        if g.row.get(k) != v:
            return False
    return True


def _find_named(scene, name):
    for g in scene.glyphs.values():
        if g.name and _norm(g.name) == _norm(name):
            return g
    return None


def _resolve_target_glyphs(scene, spec):
    """Target spec -> list of glyphs. {'named': n} or {'where': {...}}."""
    if "named" in spec:
        g = _find_named(scene, spec["named"])
        return [g] if g else []
    if "where" in spec:
        return [g for g in scene.glyphs.values()
                if _glyph_matches_where(g, spec["where"])]
    return []


def _parcel_of_brood(scene, b):
    return scene.parcels.get(b.parcel)


def _chart_root_of_brood(scene, b):
    return scene.chart_root(b.parcel)


# ----------------------------------------------------------------------
# brood micro-checks
# ----------------------------------------------------------------------

def _brood_micros(env, want):
    """Expand a brood check into named micro-predicates over a brood."""
    scene = env.scene
    micros = []

    if "form" in want:
        micros.append(("form is " + want["form"],
                       lambda b: b.form == want["form"]))
    if "count" in want:
        micros.append((f"{want['count']} glyphs",
                       lambda b: len(b.glyphs) == want["count"]))
    if "data" in want:
        spec = want["data"]
        try:
            expected = apply_transform(spec["from"], spec.get("transform"))
        except (VeldError, ValueError):
            expected = None

        def data_ok(b):
            if expected is None:
                return False
            led = env.ledgers.resolve(b.ledger_ref)
            return rows_match(expected, led.rows)
        micros.append(("correct data", data_ok))
    if "meter" in want:
        for trait, vein in want["meter"].items():
            micros.append((f"{trait} metered by '{vein}'",
                           lambda b, t=trait, v=vein: b.meterings.get(t) == v))
    if "not_meter" in want:
        for trait in want["not_meter"]:
            micros.append((f"no {trait} metering",
                           lambda b, t=trait: t not in b.meterings))
    if "key_vein" in want:
        micros.append((f"keyed by '{want['key_vein']}'",
                       lambda b: b.key_vein == want["key_vein"]))
    if "loose" in want:
        for trait in want["loose"]:
            micros.append((f"{trait} on its own gauge",
                           lambda b, t=trait: t in b.loose_traits))
    if "threaded_by" in want:
        def threaded(b, v=want["threaded_by"]):
            return b.strand and env.scene.strands[b.strand].by == v
        micros.append((f"threaded by '{want['threaded_by']}'", threaded))
    if "flooded" in want:
        def flooded(b, expect=want["flooded"]):
            has = bool(b.strand and env.scene.strands[b.strand].flooded)
            return has == expect
        micros.append(("flooded" if want["flooded"] else "not flooded", flooded))
    if "badge_vein" in want:
        def badge_v(b, v=want["badge_vein"]):
            if b.badge and b.badge.get("vein") == v:
                return True
            gl = [env.scene.glyphs[g] for g in b.glyphs]
            return gl and all(g.badge and g.badge.get("vein") == v for g in gl)
        micros.append((f"glyphs badged with '{want['badge_vein']}'", badge_v))
    if "in" in want:
        loc = want["in"]
        if "carved_by" in loc:
            def carved(b, v=loc["carved_by"]):
                p = _parcel_of_brood(scene, b)
                return bool(p and p.carve and p.carve["by"] == v)
            micros.append((f"parcel carved by '{loc['carved_by']}'", carved))
        if "carve_along" in loc:
            def along(b, d=loc["carve_along"]):
                p = _parcel_of_brood(scene, b)
                return bool(p and p.carve and p.carve["along"] == d)
            micros.append((f"carved along {loc['carve_along']}", along))
        if "outer_carved_by" in loc:
            def outer(b, v=loc["outer_carved_by"]):
                p = _parcel_of_brood(scene, b)
                while p is not None:
                    if p.carve and p.carve["by"] == v:
                        return True
                    p = scene.parcels.get(p.parent) if p.parent else None
                return False
            micros.append((f"within a carve by '{loc['outer_carved_by']}'", outer))
        if "hooped" in loc:
            def hooped(b, expect=loc["hooped"]):
                p = _chart_root_of_brood(scene, b)
                own = _parcel_of_brood(scene, b)
                has = bool((p and p.hooped) or (own and own.hooped))
                return has == expect
            micros.append(("hooped parcel" if loc["hooped"] else "flat parcel",
                           hooped))
        if "inner_min" in loc:
            def inner(b, lim=loc["inner_min"]):
                p = _chart_root_of_brood(scene, b)
                own = _parcel_of_brood(scene, b)
                h = (p.hooped if p and p.hooped else
                     (own.hooped if own and own.hooped else None))
                return bool(h and h["inner"] >= lim - 1e-9)
            micros.append((f"open middle (inner ≥ {loc['inner_min']})", inner))
        if "law" in loc:
            def law(b, l=loc["law"]):
                own = _parcel_of_brood(scene, b)
                return bool(own and scene.effective_settle(own)["law"] == l)
            micros.append((f"law '{loc['law']}'", law))
        if "nested_under" in loc:
            def nested(b, host=loc["nested_under"]):
                p = _parcel_of_brood(scene, b)
                while p is not None and p.kind == "cell":
                    p = scene.parcels.get(p.parent)
                if not p or p.kind != "nest" or not p.host_glyph:
                    return False
                hg = scene.glyphs.get(p.host_glyph)
                return bool(hg and hg.name and _norm(hg.name) == _norm(host)) \
                    if host != "*" else True
            micros.append(("nested under " + str(loc["nested_under"]), nested))
        if "in_nest" in loc:
            def in_nest(b, expect=loc["in_nest"]):
                p = _parcel_of_brood(scene, b)
                while p is not None:
                    if p.kind == "nest":
                        return expect
                    p = scene.parcels.get(p.parent) if p.parent else None
                return not expect
            micros.append(("in a nested parcel", in_nest))
        if "in_split_panel" in loc:
            def in_panel(b, expect=loc["in_split_panel"]):
                p = _parcel_of_brood(scene, b)
                while p is not None:
                    if p.kind == "split":
                        return expect
                    p = scene.parcels.get(p.parent) if p.parent else None
                return not expect
            micros.append(("in a split panel", in_panel))
    if "order" in want:
        spec = want["order"]

        def ordered(b, vein=spec["vein"], sense=spec.get("sense", "waxing")):
            led = env.ledgers.resolve(b.ledger_ref)
            try:
                vals = led.values(vein)
            except VeldError:
                return False
            s = sorted(vals, reverse=(sense == "waning"))
            return vals == s
        micros.append((f"rows in {spec.get('sense','waxing')} '{spec['vein']}' "
                       f"order", ordered))
    return micros


# ----------------------------------------------------------------------
# individual checks -> (weight, passed, label)
# ----------------------------------------------------------------------

def _eval_check(env, check):
    scene = env.scene
    kind = check["check"]
    w = check.get("weight", 1.0)

    if kind == "brood":
        micros = _brood_micros(env, check.get("where", {}))
        if not micros:
            return []
        best, best_n = None, -1
        for b in scene.broods.values():
            n = sum(1 for _, fn in micros if fn(b))
            if n > best_n:
                best, best_n = b, n
        mw = w / len(micros)
        out = []
        for label, fn in micros:
            ok = bool(best and fn(best))
            out.append((mw, ok, f"brood: {label}"))
        return out

    if kind == "glyph":
        g = _find_named(scene, check["named"])
        ok = g is not None and ("form" not in check or g.form == check["form"])
        label = f"glyph '{check['named']}'" + \
            (f" as {check['form']}" if "form" in check else "")
        return [(w, ok, label)]

    if kind == "glyph_count":
        n = check["n"]
        form = check.get("form")
        placed = check.get("placed")
        gl = list(scene.glyphs.values())
        if form:
            gl = [g for g in gl if g.form == form]
        if placed is True:
            gl = [g for g in gl if g.brood is None]
        ok = len(gl) == n
        return [(w, ok, f"{n} {form or 'any'} glyph(s) present")]

    if kind == "cord":
        a = _find_named(scene, check["from"])
        b = _find_named(scene, check["to"])
        found = None
        if a and b:
            for c in scene.cords.values():
                if c.tail == a.id and c.head == b.id:
                    found = c
                    break
                if check.get("either_way") and c.tail == b.id and c.head == a.id:
                    found = c
                    break
        ok = found is not None
        if ok and check.get("pipe"):
            ok = found.pipe_width is not None
        if ok and "kindled" in check:
            ok = found.kindled == check["kindled"]
        if ok and "badge_has" in check:
            ok = _text_has(found.badge, check["badge_has"])
        return [(w, ok, f"cord {check['from']} → {check['to']}")]

    if kind == "cord_count":
        ok = len(scene.cords) == check["n"]
        return [(w, ok, f"{check['n']} cord(s)")]

    if kind == "pipe_proportional":
        pairs = check["pairs"]
        widths = []
        for frm, to, val in pairs:
            a, b = _find_named(scene, frm), _find_named(scene, to)
            got = None
            if a and b:
                for c in scene.cords.values():
                    if c.tail == a.id and c.head == b.id and c.pipe_width:
                        got = c.pipe_width
            widths.append((got, val))
        ok = all(g is not None for g, _ in widths)
        if ok:
            base = None
            for g, v in widths:
                if v <= 0:
                    continue
                r = g / v
                if base is None:
                    base = r
                elif not (0.8 <= r / base <= 1.25):
                    ok = False
        return [(w, ok, "pipe widths proportional to the given quantities")]

    if kind == "emphasis":
        mode = check.get("mode", "kindle")
        exclusive = check.get("exclusive", False)
        targets = check.get("target", {})
        if "cord_from" in targets:
            a = _find_named(scene, targets["cord_from"])
            b = _find_named(scene, targets["cord_to"])
            ok = False
            if a and b:
                for c in scene.cords.values():
                    if c.tail == a.id and c.head == b.id:
                        ok = c.kindled if mode == "kindle" else c.hushed
            return [(w, ok, f"{mode}d cord {targets['cord_from']} → "
                     f"{targets['cord_to']}")]
        if "strand" in targets:
            ok = any(s.kindled for s in scene.strands.values()) \
                if mode == "kindle" else False
            return [(w, ok, f"{mode}d strand")]
        gl = _resolve_target_glyphs(scene, targets)
        flagname = "kindled" if mode == "kindle" else "hushed"
        ok = any(getattr(g, flagname) for g in gl)
        if ok and exclusive:
            ids = {g.id for g in gl}
            others = [g for g in scene.glyphs.values()
                      if g.id not in ids and g.row is not None]
            ok = not any(getattr(g, flagname) for g in others)
        desc = targets.get("named") or ", ".join(
            f"{k}={v}" for k, v in targets.get("where", {}).items())
        return [(w, ok, f"{flagname}: {desc}")]

    if kind == "annotation":
        want_kind = check.get("kind", "any")
        ok = False
        for a in scene.annotations:
            if want_kind != "any" and a.kind != want_kind:
                continue
            if "text_has" in check and not _text_has(a.text, check["text_has"]):
                continue
            if "near" in check:
                spec = check["near"]
                near_ok = False
                if a.near:
                    tg = None
                    if a.near in scene.glyphs:
                        tg = scene.glyphs[a.near]
                    elif a.near in scene.flocks:
                        cands = [scene.glyphs[m]
                                 for m in scene.flocks[a.near].members
                                 if m in scene.glyphs]
                        if "named" in spec:
                            near_ok = any(
                                g.name and _norm(g.name) == _norm(spec["named"])
                                for g in cands)
                        elif "where" in spec:
                            near_ok = any(_glyph_matches_where(g, spec["where"])
                                          for g in cands)
                    else:
                        g2 = _find_named(scene, a.near)
                        tg = g2
                    if tg is not None:
                        if "named" in spec:
                            near_ok = tg.name and \
                                _norm(tg.name) == _norm(spec["named"])
                        elif "where" in spec:
                            near_ok = _glyph_matches_where(tg, spec["where"])
                    elif a.near in scene.cords and "cord_from" in spec:
                        c = scene.cords[a.near]
                        fa = _find_named(scene, spec["cord_from"])
                        fb = _find_named(scene, spec.get("cord_to", ""))
                        near_ok = bool(fa and fb and c.tail == fa.id and
                                       c.head == fb.id)
                if not near_ok:
                    continue
            ok = True
            break
        bits = []
        if "text_has" in check:
            bits.append(f"saying '{check['text_has']}'")
        if "near" in check:
            bits.append("anchored to the right target")
        return [(w, ok, f"annotation {' '.join(bits) or 'present'}")]

    if kind == "guide":
        g = check.get("kind")
        parcels = list(scene.parcels.values())
        if g == "rim":
            side = check.get("side")
            ok = any(side in p.rims if side else p.rims for p in parcels)
            return [(w, ok, f"rim on the {side or 'any'} side")]
        if g == "weft":
            along = check.get("along")
            ok = any((along in p.wefts if along else p.wefts) for p in parcels)
            return [(w, ok, f"weft along {along or 'any'}")]
        if g == "key":
            trait = check.get("trait", "tint")
            ok = any(k.trait == trait for k in scene.keys)
            return [(w, ok, f"key for a {trait} metering")]
        if g == "entitle":
            ok = any(_text_has(p.entitle, check.get("text_has", ""))
                     for p in parcels if p.entitle)
            if "text_has" not in check:
                ok = any(p.entitle for p in parcels)
            return [(w, ok, "title present")]
        if g == "note":
            ok = any(p.note for p in parcels)
            return [(w, ok, "note present")]

    if kind == "parcel":
        where = check.get("where", {})
        def match(p):
            if "hooped" in where and bool(p.hooped) != where["hooped"]:
                return False
            if "inner_min" in where and not (
                    p.hooped and p.hooped["inner"] >= where["inner_min"] - 1e-9):
                return False
            if "carved_by" in where and not (
                    p.carve and p.carve["by"] == where["carved_by"]):
                return False
            if "carve_along" in where and not (
                    p.carve and p.carve["along"] == where["carve_along"]):
                return False
            if "split_count" in where and not (
                    p.split and p.split["count"] == where["split_count"]):
                return False
            if "split_along" in where and not (
                    p.split and p.split["along"] == where["split_along"]):
                return False
            if "law" in where:
                if scene.effective_settle(p)["law"] != where["law"]:
                    return False
            if "heading" in where:
                s = scene.effective_settle(p)
                if s.get("heading") != where["heading"]:
                    return False
            if "inverted" in where and where["inverted"] not in p.inverted:
                return False
            if "nest_host_named" in where:
                if p.kind != "nest" or not p.host_glyph:
                    return False
                hg = scene.glyphs.get(p.host_glyph)
                if not (hg and hg.name and
                        _norm(hg.name) == _norm(where["nest_host_named"])):
                    return False
            if "is_nest" in where and (p.kind == "nest") != where["is_nest"]:
                return False
            return True
        ok = any(match(p) for p in scene.parcels.values())
        return [(w, ok, check.get("label", f"parcel {where}"))]

    if kind == "corral":
        names = check.get("contains_named", [])
        ok = False
        for k in scene.corrals.values():
            member_names = {_norm(scene.glyphs[m].name)
                            for m in k.members
                            if m in scene.glyphs and scene.glyphs[m].name}
            if all(_norm(n) in member_names for n in names):
                if "label_has" in check and not _text_has(k.label,
                                                          check["label_has"]):
                    continue
                if check.get("exact") and len(member_names) != len(names):
                    continue
                ok = True
        return [(w, ok, f"corral around {', '.join(names)}")]

    if kind == "tint_fixed":
        targets = check.get("target", {})
        gl = _resolve_target_glyphs(scene, targets)
        hue = check.get("hue")

        def has_tint(g):
            t = g.fixed.get("tint")
            if t is None and g.brood:
                t = scene.broods[g.brood].fixed.get("tint")
            return t is not None and (hue is None or t == hue)
        ok = bool(gl) and all(has_tint(g) for g in gl)
        return [(w, ok, "fixed tint applied" + (f" ({hue})" if hue else ""))]

    if kind == "badge_named":
        g = _find_named(scene, check["named"])
        ok = False
        if g:
            for b in (g.badge, g.badge2):
                if b and _text_has(b.get("text"), check.get("text_has", "")):
                    ok = True
        return [(w, ok, f"badge on '{check['named']}'")]

    if kind == "share_or_abut":
        ok = bool(scene.shared) or bool(getattr(scene, "abuts", []))
        return [(w, ok, "panels aligned (share/abut)")]

    if kind == "strand_count":
        ok = len(scene.strands) == check["n"]
        return [(w, ok, f"{check['n']} strand(s)")]

    raise ValueError(f"unknown check kind '{kind}'")


# ----------------------------------------------------------------------
# main entry
# ----------------------------------------------------------------------

def verify(env, hidden_goal):
    checks = hidden_goal["checks"]
    min_semantic = hidden_goal.get("min_semantic", 1.0)
    results = []
    for c in checks:
        results.extend(_eval_check(env, c))
    total = sum(r[0] for r in results) or 1.0
    got = sum(r[0] for r in results if r[1])
    semantic = got / total

    pres = presentation_report(env.scene, env.ledgers)
    layout_score = 1.0
    layout_score -= min(0.4, 0.08 * pres["label_overlaps"])
    layout_score -= min(0.45, 0.15 * pres["out_of_bounds"])
    layout_score -= min(0.3, 0.1 * pres["glyph_collisions"])
    layout_score -= min(0.2, 0.05 * pres["cord_crossings"])
    layout_score = max(0.0, round(layout_score, 4))

    success = semantic >= min_semantic - 1e-9 and layout_score >= 0.7
    return {
        "success": success,
        "semantic_score": round(semantic, 4),
        "layout_score": layout_score,
        "passed": [lbl for _, ok, lbl in results if ok],
        "failed": [lbl for _, ok, lbl in results if not ok],
        "presentation": pres,
    }
