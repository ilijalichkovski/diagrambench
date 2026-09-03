"""Textual observations: census() and study() — the agent's only view of the scene.

Everything needed to solve tasks is available here; the rendered SVG is for
humans only.
"""

from .errors import SigilError


def _parcel_line(scene, p):
    bits = [p.id]
    if p.kind == "cell":
        bits.append(f"cell '{p.cell_key}' of {p.parent}")
    elif p.kind == "split":
        bits.append(f"panel of {p.parent}")
    elif p.kind == "nest":
        host = f"glyph {p.host_glyph}" if p.host_glyph else p.parent
        bits.append(f"nested in {host}")
    if p.carve:
        bits.append(f"carved along {p.carve['along']} by '{p.carve['by']}' "
                    f"({len(p.carve['order'])} cells)")
    if p.split:
        bits.append(f"split along {p.split['along']} into {p.split['count']}")
    if p.hooped:
        inner = p.hooped["inner"]
        bits.append("hooped" + (f" (inner {inner:g})" if inner else ""))
    if p.settle:
        h = f", heading {p.settle['heading']}" if p.settle.get("heading") else ""
        bits.append(f"law '{p.settle['law']}'{h}")
    if p.rims:
        bits.append(f"rims: {', '.join(p.rims)}")
    if p.wefts:
        bits.append(f"weft: {', '.join(p.wefts)}")
    if p.entitle:
        bits.append(f"entitled '{p.entitle}'")
    return "  " + " — ".join(bits)


def census_text(env):
    scene = env.scene
    lines = ["GROUND"]
    interesting = [p for p in scene.parcels.values()
                   if p.id == scene.root or p.carve or p.split or p.hooped
                   or p.settle or p.rims or p.wefts or p.kind == "nest"
                   or p.entitle]
    for p in interesting:
        lines.append(_parcel_line(scene, p))

    sown = sum(len(b.glyphs) for b in scene.broods.values())
    placed = [g for g in scene.glyphs.values() if g.brood is None]
    lines.append("")
    lines.append("POPULATION")
    lines.append(f"  glyphs: {len(scene.glyphs)} ({sown} sown in "
                 f"{len(scene.broods)} brood(s), {len(placed)} placed)")
    for b in scene.broods.values():
        m = ", ".join(f"{t}←'{v}'" + (" (loose)" if t in b.loose_traits else "")
                      for t, v in b.meterings.items()) or "no meterings"
        s = f", strand {b.strand}" + \
            (" (flooded)" if b.strand and scene.strands[b.strand].flooded else "") \
            if b.strand else ""
        lines.append(f"  {b.id}: {len(b.glyphs)} {b.form} from {b.ledger_ref}"
                     f" — {m}{s}")
    for g in placed:
        nm = f" '{g.name}'" if g.name else ""
        lines.append(f"  {g.id}: {g.form}{nm} in {g.parcel}"
                     + (" (kindled)" if g.kindled else "")
                     + (" (hushed)" if g.hushed else ""))

    if scene.cords:
        lines.append("")
        lines.append("CORDS")
        for c in scene.cords.values():
            ta, he = scene.glyphs[c.tail], scene.glyphs[c.head]
            arrow = "↔" if c.sense == "both" else "→"
            extra = f" pipe({c.pipe_width:g})" if c.pipe_width else ""
            extra += " kindled" if c.kindled else ""
            lines.append(f"  {c.id}: {ta.name or ta.id} {arrow} {he.name or he.id}"
                         f"{extra}")

    marks = []
    kindled = [g.id for g in scene.glyphs.values() if g.kindled]
    hushed = [g.id for g in scene.glyphs.values() if g.hushed]
    if kindled:
        marks.append(f"kindled: {', '.join(kindled[:8])}")
    if hushed:
        marks.append(f"hushed: {len(hushed)} glyph(s)")
    if scene.corrals:
        for k in scene.corrals.values():
            marks.append(f"{k.id}: corral of {len(k.members)}"
                         + (f" '{k.label}'" if k.label else ""))
    if scene.annotations:
        marks.append(f"annotations: " + "; ".join(
            f"{a.id} {a.kind} '{a.text}'" + (f" @{a.near}" if a.near else "")
            for a in scene.annotations))
    if scene.keys:
        marks.append("keys: " + ", ".join(f"{k.brood}.{k.trait} on {k.parcel}"
                                          for k in scene.keys))
    if marks:
        lines.append("")
        lines.append("MARKS & SCRIPT")
        lines.extend("  " + m for m in marks)

    # layout-derived advisories
    try:
        from .layout import layout_scene
        _, warnings = layout_scene(scene, env.ledgers)
        if warnings:
            lines.append("")
            lines.append("ADVISORIES")
            lines.extend(f"  - {w}" for w in warnings[:8])
    except SigilError:
        pass
    except Exception:
        pass
    return "\n".join(lines)


def study_text(env, ref):
    scene = env.scene
    # ledgers first (base names or L#)
    try:
        led = env.ledgers.resolve(ref)
    except SigilError:
        led = None
    if led is not None and (ref.startswith("L") or led.ref == ref):
        lines = [f"ledger {led.ref}: {len(led.rows)} rows"]
        if led.provenance:
            lines.append("lineage:")
            for step in led.provenance:
                lines.append(f"  {step[0]}{step[1:]}")
        lines.append("veins:")
        for name, kind in led.veins().items():
            lines.append(f"  {name}: {kind}")
        return "\n".join(lines)

    kind, obj = scene.resolve_target(ref)
    gs = env.gauges()

    if kind == "parcel":
        lines = [_parcel_line(scene, obj).strip()]
        root = scene.chart_root(obj.id)
        for d in ("span", "rise"):
            g = gs.direction(root.id, d)
            if g:
                inv = " (inverted)" if d in root.inverted else ""
                lines.append(f"{d} gauge: {g.describe()}{inv}")
        if obj.carve:
            lines.append("cells: " + ", ".join(
                f"'{k}'→{v}" for k, v in obj.carve["cells"].items()))
        if obj.split:
            lines.append("panels: " + ", ".join(obj.split["cells"]))
        if obj.gauge_overrides:
            for t, (lo, hi) in obj.gauge_overrides.items():
                lines.append(f"rebase {t}: [{lo if lo is not None else 'auto'} … "
                             f"{hi if hi is not None else 'auto'}]")
        glyphs_here = scene.glyphs_in(obj.id)
        lines.append(f"population: {len(glyphs_here)} glyph(s)")
        law = scene.effective_settle(obj)
        lines.append(f"effective law: {law['law']}"
                     + (f" heading {law['heading']}" if law.get("heading") else ""))
        return "\n".join(lines)

    if kind == "brood":
        led = env.ledgers.resolve(obj.ledger_ref)
        lines = [f"brood {obj.id}: {len(obj.glyphs)} {obj.form} glyph(s) "
                 f"from {obj.ledger_ref} in {obj.parcel}"]
        if obj.key_vein:
            lines.append(f"keyed into cells by '{obj.key_vein}'")
        for t, v in obj.meterings.items():
            g = gs.for_brood(obj, t)
            loose = " — loose (private gauge)" if t in obj.loose_traits else ""
            lines.append(f"metering {t} ← '{v}' ({led.kind_of(v)}); "
                         f"gauge {g.describe() if g else '?'}{loose}")
        if obj.strand:
            s = scene.strands[obj.strand]
            lines.append(f"strand {s.id} in '{s.by}' order"
                         + (", flooded" if s.flooded else ""))
        if obj.badge:
            lines.append(f"badges: {obj.badge}")
        lines.append(f"glyphs: {', '.join(obj.glyphs[:10])}"
                     + ("…" if len(obj.glyphs) > 10 else ""))
        return "\n".join(lines)

    if kind == "glyph":
        lines = [f"glyph {obj.id}: {obj.form} in {obj.parcel}"]
        if obj.name:
            lines.append(f"name: '{obj.name}'")
        if obj.brood:
            lines.append(f"of brood {obj.brood}")
        if obj.row:
            lines.append("record: " + ", ".join(f"{k}={v!r}" for k, v in obj.row.items()))
        if obj.badge:
            lines.append(f"badge: '{obj.badge.get('text')}' aim {obj.badge.get('aim')}")
        state = []
        if obj.kindled:
            state.append("kindled")
        if obj.hushed:
            state.append("hushed")
        if obj.fixed:
            state.append(f"patina {obj.fixed}")
        if obj.layer:
            state.append(f"layer {obj.layer}")
        if state:
            lines.append("; ".join(state))
        return "\n".join(lines)

    if kind == "cord":
        ta, he = scene.glyphs[obj.tail], scene.glyphs[obj.head]
        lines = [f"cord {obj.id}: {ta.name or ta.id} → {he.name or he.id} "
                 f"(sense {obj.sense}, barb {obj.barb}, crook {obj.crook})"]
        if obj.pipe_width:
            lines.append(f"pipe width {obj.pipe_width:g}")
        if obj.sweep:
            lines.append(f"sweep {obj.sweep:g}")
        if obj.badge:
            lines.append(f"badge '{obj.badge}'")
        if obj.kindled:
            lines.append("kindled")
        return "\n".join(lines)

    if kind == "strand":
        b = scene.broods[obj.brood]
        return (f"strand {obj.id} through {b.id} in '{obj.by}' order"
                + (", flooded" if obj.flooded else "")
                + (f", heft {obj.heft:g}" if obj.heft else ""))

    if kind == "flock":
        return (f"flock {obj.id}"
                + (f" '{obj.name}'" if obj.name else "")
                + f": {', '.join(obj.members)}")

    if kind == "corral":
        return (f"corral {obj.id}"
                + (f" '{obj.label}'" if obj.label else "")
                + f" around {', '.join(obj.members)}")

    raise SigilError(f"nothing to study for '{ref}'.")
