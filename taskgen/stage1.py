"""Stage 1 (tasks 1-25): primitive discovery. Each task isolates 1-2 concepts."""

from .builders import P, task, bar, pie, line, scatter, histogram


def build():
    T = []

    # 1 — place
    p = P()
    p.place("p0", "slab", "block")
    T.append(task(
        "Bring a single slab into being on the ground.",
        p, [{"check": "glyph_count", "n": 1, "form": "slab", "placed": True}],
        []))

    # 2 — place two discs
    p = P()
    p.place("p0", "disc", "left")
    p.place("p0", "disc", "right")
    T.append(task(
        "Put exactly two discs on the ground, side by side.",
        p, [{"check": "glyph_count", "n": 2, "form": "disc", "placed": True}],
        []))

    # 3 — carve
    p = P()
    p.carve("p0", "span", "quarterly_revenue", "quarter", ["Q1", "Q2", "Q3", "Q4"])
    T.append(task(
        "Divide the ground horizontally into one region per quarter, using the "
        "'quarter' vein of ledger 'quarterly_revenue'.",
        p, [{"check": "parcel", "label": "ground carved by quarter along span",
             "where": {"carved_by": "quarter", "carve_along": "span"}}],
        ["quarterly_revenue"]))

    # 4 — sow
    p = P()
    p.sow("p0", "energy_mix", "slab")
    T.append(task(
        "Give every row of ledger 'energy_mix' a slab of its own on the ground.",
        p, [{"check": "brood", "weight": 3, "where": {
            "form": "slab", "count": 6,
            "data": {"from": "energy_mix", "transform": []}}}],
        ["energy_mix"]))

    # 5 — meter stature
    p = P()
    b = p.sow("p0", "age_distribution", "slab")
    p.meter(b, "stature", "population")
    T.append(task(
        "Sow ledger 'age_distribution' as slabs and let each one's height "
        "express its 'population'.",
        p, [{"check": "brood", "weight": 4, "where": {
            "form": "slab",
            "data": {"from": "age_distribution", "transform": []},
            "meter": {"stature": "population"}}}],
        ["age_distribution"]))

    # 6 — badge
    p = P()
    b = p.sow("p0", "age_distribution", "slab")
    p.meter(b, "stature", "population")
    p.badge(b, vein="age_band", aim="south")
    T.append(task(
        "Sow 'age_distribution' as slabs with height from 'population', and "
        "write each slab's 'age_band' beneath it.",
        p, [{"check": "brood", "weight": 5, "where": {
            "form": "slab",
            "data": {"from": "age_distribution", "transform": []},
            "meter": {"stature": "population"}, "badge_vein": "age_band"}}],
        ["age_distribution"]))

    # 7 — distill
    p = P()
    L = p.distill("quarterly_revenue", "quarter", "sum", "revenue")
    b = p.sow("p0", L, "slab")
    p.meter(b, "stature", "revenue")
    T.append(task(
        "Reduce ledger 'quarterly_revenue' to one row per quarter carrying "
        "total 'revenue', then sow the result as slabs with height from "
        "revenue.",
        p, [{"check": "brood", "weight": 4, "where": {
            "form": "slab",
            "data": {"from": "quarterly_revenue",
                     "transform": [["distill", "quarter", "revenue", "sum"]]},
            "meter": {"stature": "revenue"}}}],
        ["quarterly_revenue"]))

    # 8 — rims
    p = P()
    L = p.distill("quarterly_revenue", "quarter", "sum", "revenue")
    cells = p.carve("p0", "span", L, "quarter", ["Q1", "Q2", "Q3", "Q4"])
    b = p.sow("p0", L, "slab", key="quarter")
    p.meter(b, "stature", "revenue")
    p.rim("p0", "south")
    p.rim("p0", "west")
    T.append(task(
        "Show total 'revenue' per quarter from 'quarterly_revenue': one region "
        "per quarter, a slab in each, height from revenue. Raise calibrated "
        "rims on the south and west.",
        p, [{"check": "brood", "weight": 5, "where": {
            "form": "slab",
            "data": {"from": "quarterly_revenue",
                     "transform": [["distill", "quarter", "revenue", "sum"]]},
            "meter": {"stature": "revenue"},
            "in": {"carved_by": "quarter"}}},
            {"check": "guide", "kind": "rim", "side": "south"},
            {"check": "guide", "kind": "rim", "side": "west"}],
        ["quarterly_revenue"]))

    # 9 — named nodes + tether
    p = P()
    p.place("p0", "capsule", "Alpha")
    p.place("p0", "capsule", "Beta")
    p.tether("Alpha", "Beta")
    T.append(task(
        "Place two capsules named 'Alpha' and 'Beta', and run a cord from "
        "Alpha to Beta.",
        p, [{"check": "glyph", "named": "Alpha", "form": "capsule"},
            {"check": "glyph", "named": "Beta", "form": "capsule"},
            {"check": "cord", "from": "Alpha", "to": "Beta"}],
        []))

    # 10 — current law
    p = P()
    p.settle("p0", "current", heading="east")
    p.place("p0", "capsule", "Start")
    p.place("p0", "capsule", "Middle")
    p.place("p0", "capsule", "End")
    p.tether("Start", "Middle")
    p.tether("Middle", "End")
    T.append(task(
        "Build a chain: capsules 'Start' → 'Middle' → 'End', cords between "
        "them, flowing as an eastward current.",
        p, [{"check": "parcel", "label": "eastward current",
             "where": {"law": "current", "heading": "east"}},
            {"check": "glyph", "named": "Start"},
            {"check": "glyph", "named": "Middle"},
            {"check": "glyph", "named": "End"},
            {"check": "cord", "from": "Start", "to": "Middle"},
            {"check": "cord", "from": "Middle", "to": "End"}],
        []))

    # 11 — tint + kindle
    p = P()
    b = p.sow("p0", "browser_share", "slab")
    p.meter(b, "stature", "share")
    p.tint(b, "slate")
    f = p.pick(b, "browser", "is", "Chrome")
    p.kindle(f)
    T.append(task(
        "Sow 'browser_share' as slabs with height from 'share', tint the whole "
        "brood slate, then kindle only the Chrome slab so it stands out.",
        p, [{"check": "brood", "weight": 4, "where": {
            "form": "slab",
            "data": {"from": "browser_share", "transform": []},
            "meter": {"stature": "share"}}},
            {"check": "tint_fixed", "target": {"where": {"browser": "Safari"}},
             "hue": "slate"},
            {"check": "emphasis", "mode": "kindle", "exclusive": True,
             "target": {"where": {"browser": "Chrome"}}}],
        ["browser_share"]))

    # 12 — sift
    p = P()
    L = p.sift("quarterly_revenue", "region", "is", "Europe")
    b = p.sow("p0", L, "slab")
    p.meter(b, "stature", "revenue")
    T.append(task(
        "From 'quarterly_revenue', keep only the rows where 'region' is "
        "Europe, and sow them as slabs with height from 'revenue'.",
        p, [{"check": "brood", "weight": 4, "where": {
            "form": "slab",
            "data": {"from": "quarterly_revenue",
                     "transform": [["sift", "region", "is", "Europe"]]},
            "meter": {"stature": "revenue"}}}],
        ["quarterly_revenue"]))

    # 13 — stance/perch/strew (scatter)
    T.append(scatter(
        "Scatter the cities of ledger 'city_stats': position each disc by "
        "'growth' across the span and 'transit_share' up the rise.",
        "city_stats", "growth", "transit_share", rims=()))

    # 14 — thread (line)
    T.append(line(
        "Trace 'monthly_finance': sow small points positioned by 'period' "
        "(span) and 'revenue' (rise), then thread one strand through them in "
        "period order.",
        "monthly_finance", "period", "revenue", rims=(), weft_rise=False))

    # 15 — hoop + girth (pie)
    T.append(pie(
        "Hoop the ground and sow ledger 'energy_mix' so each source claims an "
        "angular share proportional to 'share', with a distinct tint per "
        "source.",
        "energy_mix", "source", "share", badge_cat=False))

    # 16 — tint metering + key
    p = P()
    b = p.sow("p0", "browser_share", "slab")
    p.meter(b, "stature", "share")
    p.meter(b, "tint", "browser")
    p.key("p0", b, "tint")
    T.append(task(
        "Sow 'browser_share' slabs with height from 'share' and a distinct "
        "tint per 'browser'; raise a key explaining the tints.",
        p, [{"check": "brood", "weight": 4, "where": {
            "form": "slab",
            "data": {"from": "browser_share", "transform": []},
            "meter": {"stature": "share", "tint": "browser"}}},
            {"check": "guide", "kind": "key", "trait": "tint"}],
        ["browser_share"]))

    # 17 — inscribe near a picked glyph
    p = P()
    b = p.sow("p0", "energy_mix", "slab")
    p.meter(b, "stature", "share")
    f = p.pick(b, "source", "is", "Hydro")
    p.inscribe("Renewables lead", near=f)
    T.append(task(
        "Sow 'energy_mix' slabs with height from 'share', and inscribe the "
        "words 'Renewables lead' next to the Hydro slab.",
        p, [{"check": "brood", "weight": 3, "where": {
            "form": "slab", "data": {"from": "energy_mix", "transform": []},
            "meter": {"stature": "share"}}},
            {"check": "annotation", "text_has": "Renewables",
             "near": {"where": {"source": "Hydro"}}}],
        ["energy_mix"]))

    # 18 — heap
    p = P()
    L = p.sift("survey_results", "topic", "is", "Remote work")
    b = p.sow("p0", L, "slab")
    p.meter(b, "stature", "share")
    p.meter(b, "tint", "response")
    p.settle("p0", "heap")
    T.append(task(
        "Take the 'Remote work' rows of 'survey_results' and pile them into a "
        "single column: each response's 'share' stacked on the previous one, "
        "tinted by 'response'.",
        p, [{"check": "brood", "weight": 5, "where": {
            "form": "slab",
            "data": {"from": "survey_results",
                     "transform": [["sift", "topic", "is", "Remote work"]]},
            "meter": {"stature": "share", "tint": "response"},
            "in": {"law": "heap"}}}],
        ["survey_results"]))

    # 19 — marshal
    p = P()
    L = p.marshal("feature_usage", "users", "waning")
    b = p.sow("p0", L, "slab")
    p.meter(b, "stature", "users")
    p.badge(b, vein="feature", aim="south")
    T.append(task(
        "Sow 'feature_usage' as slabs with height from 'users', arranged from "
        "most-used to least-used, each badged with its 'feature' beneath.",
        p, [{"check": "brood", "weight": 5, "where": {
            "form": "slab",
            "data": {"from": "feature_usage", "transform": []},
            "meter": {"stature": "users"}, "badge_vein": "feature",
            "order": {"vein": "users", "sense": "waning"}}}],
        ["feature_usage"]))

    # 20 — bulk
    T.append(scatter(
        "Scatter 'city_stats' discs by 'growth' (span) and 'transit_share' "
        "(rise), sizing each disc's bulk by 'population'.",
        "city_stats", "growth", "transit_share", bulk="population", rims=()))

    # 21 — bin (histogram)
    T.append(histogram(
        "Distribute the 'hours' of ledger 'ticket_resolution' into about 8 "
        "bins and show the count in each bin as a column. Rims south and "
        "west.",
        "ticket_resolution", "hours", bins=8, weft_rise=False))

    # 22 — flag
    p = P()
    p.place("p0", "capsule", "Gateway")
    p.flag("Gateway", "entry point")
    T.append(task(
        "Place a capsule named 'Gateway' and tie a flag to it reading "
        "'entry point'.",
        p, [{"check": "glyph", "named": "Gateway", "form": "capsule"},
            {"check": "annotation", "kind": "flag", "text_has": "entry",
             "near": {"named": "Gateway"}}],
        []))

    # 23 — entitle + note
    p = P()
    L = p.distill("quarterly_revenue", "quarter", "sum", "revenue")
    cells = p.carve("p0", "span", L, "quarter", ["Q1", "Q2", "Q3", "Q4"])
    b = p.sow("p0", L, "slab", key="quarter")
    p.meter(b, "stature", "revenue")
    p.entitle("p0", "Revenue by quarter")
    p.note("p0", "FY2025, all regions")
    T.append(task(
        "Rebuild the quarterly total-revenue columns from 'quarterly_revenue' "
        "(one region per quarter). Entitle the ground 'Revenue by quarter' "
        "and add the note 'FY2025, all regions'.",
        p, [{"check": "brood", "weight": 4, "where": {
            "form": "slab",
            "data": {"from": "quarterly_revenue",
                     "transform": [["distill", "quarter", "revenue", "sum"]]},
            "meter": {"stature": "revenue"}, "in": {"carved_by": "quarter"}}},
            {"check": "guide", "kind": "entitle", "text_has": "Revenue"},
            {"check": "guide", "kind": "note"}],
        ["quarterly_revenue"]))

    # 24 — weft
    T.append(bar(
        "Chart total weekly 'visits' from 'site_traffic' as columns per "
        "'week', with south and west rims and faint weft lines along the "
        "rise.",
        "site_traffic", "week", "visits",
        transform=[["distill", "week", "visits", "sum"]], weft_rise=True))

    # 25 — barb + sweep + crook
    p = P()
    p.place("p0", "disc", "here")
    p.place("p0", "disc", "there")
    c = p.tether("here", "there")
    p.barb(c, "both")
    p.crook(c, "arc")
    p.sweep(c, 0.5)
    T.append(task(
        "Place two discs named 'here' and 'there'; join them with a single "
        "arcing cord, curved noticeably, barbed at both ends.",
        p, [{"check": "glyph", "named": "here", "form": "disc"},
            {"check": "glyph", "named": "there", "form": "disc"},
            {"check": "cord", "from": "here", "to": "there"},
            {"check": "cord_count", "n": 1}],
        []))

    assert len(T) == 25, len(T)
    return T
