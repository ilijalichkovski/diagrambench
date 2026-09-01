"""Stage 5 (tasks 161-200): mastery compositions + late plasticity probes.
`pipe` (flow magnitude) is deliberately introduced only here, to measure
whether an old agent still learns new primitives efficiently."""

from .builders import P, task, bar, pie, line, scatter, histogram, diagram
from .stage3 import multi_line
from .stage4 import dual_axis


def build():
    T = []

    # 161 — spec Example A
    p = P()
    p.settle("p0", "current", heading="east")
    p.place("p0", "capsule", "Users")
    p.place("p0", "capsule", "Gateway")
    for svc in ("Payments", "Orders", "Search"):
        p.place("p0", "capsule", svc)
    p.place("p0", "drum", "Shared DB")
    p.place("p0", "drum", "Vector store")
    p.tether("Users", "Gateway")
    c_pay = p.tether("Gateway", "Payments")
    p.tether("Gateway", "Orders")
    p.tether("Gateway", "Search")
    c2 = p.tether("Payments", "Shared DB")
    p.tether("Orders", "Shared DB")
    p.tether("Search", "Vector store")
    p.corral(["Payments", "Orders", "Search"], label="Core")
    p.kindle(c_pay)
    p.kindle("Payments")
    for svc in ("Payments", "Orders", "Search"):
        n = p.nest(host=svc, aim="south")
        L = p.sift("latency_profile", "service", "is", svc)
        b = p.sow(n, L, "slab")
        p.meter(b, "stature", "ms")
    p.entitle("p0", "Core platform")
    checks = [
        {"check": "parcel", "where": {"law": "current", "heading": "east"},
         "label": "eastward current"},
        {"check": "glyph", "named": "Users", "form": "capsule"},
        {"check": "glyph", "named": "Gateway", "form": "capsule"},
        {"check": "glyph", "named": "Shared DB", "form": "drum"},
        {"check": "glyph", "named": "Vector store", "form": "drum"},
        {"check": "cord", "from": "Users", "to": "Gateway"},
        {"check": "cord", "from": "Gateway", "to": "Payments"},
        {"check": "cord", "from": "Gateway", "to": "Orders"},
        {"check": "cord", "from": "Gateway", "to": "Search"},
        {"check": "cord", "from": "Payments", "to": "Shared DB"},
        {"check": "cord", "from": "Orders", "to": "Shared DB"},
        {"check": "cord", "from": "Search", "to": "Vector store"},
        {"check": "corral", "contains_named": ["Payments", "Orders",
                                               "Search"],
         "label_has": "Core"},
        {"check": "emphasis", "mode": "kindle",
         "target": {"cord_from": "Gateway", "cord_to": "Payments"}},
        {"check": "emphasis", "mode": "kindle",
         "target": {"named": "Payments"}},
    ]
    for svc in ("Payments", "Orders", "Search"):
        checks.append({"check": "brood", "weight": 4, "where": {
            "form": "slab",
            "data": {"from": "latency_profile",
                     "transform": [["sift", "service", "is", svc]]},
            "meter": {"stature": "ms"}, "in": {"nested_under": svc}}})
    T.append(task(
        "An architecture flowing east: 'Users' → 'Gateway' → the services "
        "'Payments', 'Orders', 'Search' (corralled as 'Core'). Payments and "
        "Orders share drum 'Shared DB'; Search uses drum 'Vector store'. "
        "Kindle the Gateway→Payments cord and the Payments capsule. Beneath "
        "each service, nest its 'latency_profile' rows as mini columns "
        "metered by 'ms'. Entitle it 'Core platform'.",
        p, checks, ["latency_profile"]))

    # 162 — spec Example B
    p = P()
    b1 = p.sow("p0", "monthly_finance", "slab")
    p.meter(b1, "stance", "period")
    p.meter(b1, "stature", "revenue")
    b2 = p.sow("p0", "monthly_finance", "wisp")
    p.meter(b2, "stance", "period")
    p.meter(b2, "perch", "margin")
    p.loosen(b2, "perch")
    p.settle("p0", "strew")
    s = p.thread(b2, by="period")
    p.tint(b2, "ember")
    p.tint(s, "ember")
    f1 = p.pick(b1, "era", "is", "after launch")
    p.kindle(f1)
    f2 = p.pick(b2, "period", "is", "M24")
    p.flag(f2, "highest margin")
    n = p.nest(parcel="p0", aim="west", breadth=0.24, depth=0.34)
    cells = p.carve(n, "span", "final_month_mix", "product",
                    ["Aria", "Breeze", "Cove"])
    b3 = p.sow(n, "final_month_mix", "slab", key="product")
    p.meter(b3, "stature", "revenue")
    p.badge(b3, vein="product", aim="south")
    p.entitle(n, "M24 by product")
    p.rim("p0", "south")
    p.rim("p0", "west")
    p.rim("p0", "east")
    p.weft("p0", "rise")
    p.entitle("p0", "Two years: revenue and margin")
    T.append(task(
        "Show 24 months from 'monthly_finance': 'revenue' as slabs "
        "stationed by 'period' and 'margin' as an ember strand on its own "
        "loosened gauge (east rim). Kindle the after-launch slabs (their "
        "'era'), flag the highest-margin month (M24), and nest a compact "
        "inset toward the west showing 'final_month_mix' revenue per "
        "product as badged mini columns entitled 'M24 by product'. Rims "
        "south/west/east, weft, and a ground title.",
        p, [{"check": "brood", "weight": 5, "where": {
            "form": "slab",
            "data": {"from": "monthly_finance", "transform": []},
            "meter": {"stance": "period", "stature": "revenue"},
            "in": {"law": "strew"}}},
            {"check": "brood", "weight": 5, "where": {
                "form": "wisp", "meter": {"stance": "period",
                                          "perch": "margin"},
                "loose": ["perch"], "threaded_by": "period"}},
            {"check": "emphasis", "mode": "kindle",
             "target": {"where": {"era": "after launch"}}},
            {"check": "annotation", "kind": "flag", "text_has": "margin",
             "near": {"where": {"period": "M24"}}},
            {"check": "brood", "weight": 5, "where": {
                "form": "slab",
                "data": {"from": "final_month_mix", "transform": []},
                "meter": {"stature": "revenue"}, "badge_vein": "product",
                "in": {"carved_by": "product", "in_nest": True}}},
            {"check": "guide", "kind": "rim", "side": "east"},
            {"check": "guide", "kind": "entitle"}],
        ["monthly_finance", "final_month_mix"]))

    # 163 — spec Example C: pipes (NEW primitive, plasticity probe)
    p = P()
    p.settle("p0", "current", heading="east")
    for stage in ("Applicants", "Screen", "Interview", "Offer", "Hired"):
        p.place("p0", "capsule", stage)
    p.pipe("Applicants", "Screen", 420)
    p.pipe("Screen", "Interview", 160)
    p.pipe("Interview", "Offer", 45)
    p.pipe("Offer", "Hired", 32)
    for stage, days in [("Applicants", 2), ("Screen", 5), ("Interview", 12),
                        ("Offer", 4), ("Hired", 3)]:
        p.badge(stage, text=f"{days} days", aim="south")
    p.kindle("Applicants")
    p.flag("Applicants", "largest drop-off")
    p.entitle("p0", "Hiring funnel")
    T.append(task(
        "A hiring-funnel flow east using ledger 'hiring_funnel' for the "
        "numbers: capsules 'Applicants' → 'Screen' → 'Interview' → 'Offer' "
        "→ 'Hired', connected by pipes whose widths are proportional to "
        "the 'candidates' count entering the next stage (420, 160, 45, "
        "32). Badge each stage beneath with its 'median_days' (e.g. "
        "'5 days'). Kindle the stage with the largest loss (Applicants) "
        "and flag it 'largest drop-off'. Entitle 'Hiring funnel'.",
        p, [{"check": "parcel", "where": {"law": "current",
                                          "heading": "east"},
             "label": "eastward current"},
            {"check": "pipe_proportional", "weight": 4, "pairs": [
                ["Applicants", "Screen", 420], ["Screen", "Interview", 160],
                ["Interview", "Offer", 45], ["Offer", "Hired", 32]]},
            {"check": "badge_named", "named": "Screen", "text_has": "5"},
            {"check": "badge_named", "named": "Interview",
             "text_has": "12"},
            {"check": "emphasis", "mode": "kindle",
             "target": {"named": "Applicants"}},
            {"check": "annotation", "kind": "flag", "text_has": "drop",
             "near": {"named": "Applicants"}},
            {"check": "guide", "kind": "entitle"}],
        ["hiring_funnel"]))

    # 164 — pipes again (plasticity reuse, short gap)
    p = P()
    p.settle("p0", "current", heading="east")
    for name in ("Lead", "Qualified", "Proposal", "Negotiation", "Won"):
        p.place("p0", "capsule", name)
    p.pipe("Lead", "Qualified", 186)
    p.pipe("Qualified", "Proposal", 94)
    p.pipe("Proposal", "Negotiation", 41)
    p.pipe("Negotiation", "Won", 27)
    p.badge("Won", text="$1.2M", aim="south")
    p.kindle("Won")
    p.entitle("p0", "Sales funnel")
    T.append(task(
        "Using 'sales_pipeline' deal counts, run pipes east through "
        "capsules 'Lead' → 'Qualified' → 'Proposal' → 'Negotiation' → "
        "'Won' with widths proportional to the 'deals' reaching the next "
        "phase (186, 94, 41, 27). Badge 'Won' beneath with '$1.2M', kindle "
        "it, entitle 'Sales funnel'.",
        p, [{"check": "pipe_proportional", "weight": 4, "pairs": [
            ["Lead", "Qualified", 186], ["Qualified", "Proposal", 94],
            ["Proposal", "Negotiation", 41], ["Negotiation", "Won", 27]]},
            {"check": "badge_named", "named": "Won", "text_has": "1.2"},
            {"check": "emphasis", "mode": "kindle",
             "target": {"named": "Won"}},
            {"check": "guide", "kind": "entitle"}],
        ["sales_pipeline"]))

    # 165 — full report: grouped + inset donut + annotations
    p = P()
    L = p.sift("quarterly_revenue", "region", "is", "Europe")
    cells = p.carve("p0", "span", L, "quarter", ["Q1", "Q2", "Q3", "Q4"])
    b = p.sow("p0", L, "slab", key="quarter")
    p.meter(b, "stature", "revenue")
    p.meter(b, "tint", "product")
    p.key("p0", b, "tint")
    f = p.pick(b, "quarter", "is", "Q3")
    f2 = p.pick(f, "product", "is", "Breeze")
    p.kindle(f2)
    p.flag(f2, "Peak quarter")
    n = p.nest(parcel="p0", aim="east", breadth=0.26, depth=0.38)
    L2 = p.distill(L, "product", "sum", "revenue")
    p.hoop(n, inner=0.5)
    b2 = p.sow(n, L2, "slab")
    p.meter(b2, "girth", "revenue")
    p.meter(b2, "tint", "product")
    p.entitle(n, "Year share")
    p.rim("p0", "south")
    p.rim("p0", "west")
    p.weft("p0", "rise")
    p.entitle("p0", "Europe: quarterly revenue by product")
    p.note("p0", "Breeze spiked in Q3 on the summer campaign")
    T.append(task(
        "A report figure from 'quarterly_revenue' (Europe only): grouped "
        "columns of 'revenue' per 'quarter' tinted by 'product' with key, "
        "rims and weft; kindle and flag Breeze Q3 as 'Peak quarter'; nest "
        "an open ring inset (east) of each product's total-year share "
        "entitled 'Year share'; title and a note.",
        p, [{"check": "brood", "weight": 6, "where": {
            "form": "slab",
            "data": {"from": "quarterly_revenue",
                     "transform": [["sift", "region", "is", "Europe"]]},
            "meter": {"stature": "revenue", "tint": "product"},
            "in": {"carved_by": "quarter", "law": "abreast"}}},
            {"check": "guide", "kind": "key", "trait": "tint"},
            {"check": "emphasis", "mode": "kindle", "exclusive": True,
             "target": {"where": {"quarter": "Q3", "product": "Breeze"}}},
            {"check": "annotation", "kind": "flag", "text_has": "Peak",
             "near": {"where": {"quarter": "Q3", "product": "Breeze"}}},
            {"check": "brood", "weight": 5, "where": {
                "form": "slab",
                "data": {"from": "quarterly_revenue",
                         "transform": [["sift", "region", "is", "Europe"],
                                       ["distill", "product", "revenue",
                                        "sum"]]},
                "meter": {"girth": "revenue", "tint": "product"},
                "in": {"hooped": True, "in_nest": True}}},
            {"check": "guide", "kind": "entitle"},
            {"check": "guide", "kind": "note"}],
        ["quarterly_revenue"]))

    # 166 — service scorecard: nested minis + kindled worst
    p = P()
    p.settle("p0", "current", heading="east")
    p.place("p0", "capsule", "Edge")
    for svc in ("Gateway", "Payments", "Search"):
        p.place("p0", "capsule", svc)
    p.tether("Edge", "Gateway")
    p.tether("Gateway", "Payments")
    p.tether("Gateway", "Search")
    for svc in ("Gateway", "Payments", "Search"):
        n = p.nest(host=svc, aim="south")
        L = p.sift("latency_profile", "service", "is", svc)
        b = p.sow(n, L, "slab")
        p.meter(b, "stature", "ms")
    p.kindle("Search")
    p.flag("Search", "worst p99")
    p.entitle("p0", "Latency scorecard")
    T.append(task(
        "A latency scorecard flowing east: 'Edge' → 'Gateway' → 'Payments' "
        "and 'Search'. Nest each of Gateway/Payments/Search's "
        "'latency_profile' rows beneath it as mini 'ms' columns. Kindle "
        "Search (worst p99) and flag it 'worst p99'. Entitle 'Latency "
        "scorecard'.",
        p, [{"check": "cord", "from": "Edge", "to": "Gateway"},
            {"check": "cord", "from": "Gateway", "to": "Payments"},
            {"check": "cord", "from": "Gateway", "to": "Search"},
            {"check": "brood", "weight": 4, "where": {
                "form": "slab", "meter": {"stature": "ms"},
                "in": {"nested_under": "Gateway"}}},
            {"check": "brood", "weight": 4, "where": {
                "form": "slab", "meter": {"stature": "ms"},
                "in": {"nested_under": "Payments"}}},
            {"check": "brood", "weight": 4, "where": {
                "form": "slab", "meter": {"stature": "ms"},
                "in": {"nested_under": "Search"}}},
            {"check": "emphasis", "mode": "kindle",
             "target": {"named": "Search"}},
            {"check": "annotation", "kind": "flag", "text_has": "p99",
             "near": {"named": "Search"}},
            {"check": "guide", "kind": "entitle"}],
        ["latency_profile"]))

    # 167 — dashboard: dual axis + stacked panel
    p = P()
    panels = p.split("p0", "rise", 2)
    b1 = p.sow(panels[0], "monthly_finance", "slab")
    p.meter(b1, "stance", "period")
    p.meter(b1, "stature", "revenue")
    b2 = p.sow(panels[0], "monthly_finance", "wisp")
    p.meter(b2, "stance", "period")
    p.meter(b2, "perch", "margin")
    p.loosen(b2, "perch")
    p.settle(panels[0], "strew")
    s = p.thread(b2, by="period")
    p.tint(b2, "ember")
    p.tint(s, "ember")
    p.rim(panels[0], "west")
    p.rim(panels[0], "east")
    p.entitle(panels[0], "Revenue and margin")
    L = p.sift("site_traffic", "week", "among",
               ["W09", "W10", "W11", "W12"])
    cells = p.carve(panels[1], "span", L, "week",
                    ["W09", "W10", "W11", "W12"])
    b3 = p.sow(panels[1], L, "slab", key="week")
    p.meter(b3, "stature", "visits")
    p.meter(b3, "tint", "channel")
    p.settle(panels[1], "heap")
    p.key(panels[1], b3, "tint")
    p.rim(panels[1], "west")
    p.entitle(panels[1], "Recent traffic")
    T.append(task(
        "A two-panel executive dashboard: top, 'monthly_finance' revenue "
        "slabs by 'period' with margin threaded on a loosened ember gauge "
        "(west and east rims); bottom, weeks W09–W12 of 'site_traffic' "
        "stacked by channel with key and west rim. Entitle both panels.",
        p, [{"check": "parcel", "where": {"split_count": 2,
                                          "split_along": "rise"},
             "label": "two stacked panels"},
            {"check": "brood", "weight": 4, "where": {
                "form": "slab", "meter": {"stance": "period",
                                          "stature": "revenue"}}},
            {"check": "brood", "weight": 4, "where": {
                "form": "wisp", "loose": ["perch"],
                "threaded_by": "period"}},
            {"check": "brood", "weight": 4, "where": {
                "form": "slab",
                "data": {"from": "site_traffic",
                         "transform": [["sift", "week", "among",
                                        ["W09", "W10", "W11", "W12"]]]},
                "meter": {"stature": "visits", "tint": "channel"},
                "in": {"law": "heap"}}},
            {"check": "guide", "kind": "key", "trait": "tint"}],
        ["monthly_finance", "site_traffic"]))

    # 168 — pipes: traffic flow map (plasticity reuse)
    p = P()
    p.settle("p0", "current", heading="east")
    for form, name in [("capsule", "Campaigns"), ("capsule", "Site"),
                       ("capsule", "Signup"), ("capsule", "Checkout")]:
        p.place("p0", form, name)
    p.pipe("Campaigns", "Site", 1030)
    p.pipe("Site", "Signup", 330)
    p.pipe("Signup", "Checkout", 95)
    p.kindle("Signup")
    p.flag("Signup", "biggest leak")
    T.append(task(
        "A conversion flow east with pipes: 'Campaigns' → 'Site' (width "
        "1030) → 'Signup' (330) → 'Checkout' (95), widths proportional to "
        "those volumes. Kindle 'Signup' and flag it 'biggest leak'.",
        p, [{"check": "pipe_proportional", "weight": 4, "pairs": [
            ["Campaigns", "Site", 1030], ["Site", "Signup", 330],
            ["Signup", "Checkout", 95]]},
            {"check": "emphasis", "mode": "kindle",
             "target": {"named": "Signup"}},
            {"check": "annotation", "kind": "flag", "text_has": "leak",
             "near": {"named": "Signup"}}],
        []))

    # 169 — retention: full grouped bars with everything (long gap from 91)
    T.append(bar(
        "Asia's quarterly story from 'quarterly_revenue': grouped columns "
        "per 'quarter' tinted by 'product' with key, rims, weft; kindle "
        "Aria Q4 and flag it 'new high'; entitle 'Asia by product' and "
        "note 'constant currency'.",
        "quarterly_revenue", "quarter", "revenue",
        transform=[["sift", "region", "is", "Asia"]],
        tint_cat="product", legend=True, weft_rise=True,
        kindle_where={"quarter": "Q4", "product": "Aria"},
        annotate=("new high", {"quarter": "Q4", "product": "Aria"}, "flag"),
        title="Asia by product", note="constant currency"))

    # 170 — mastery multi-line + inset histogram
    p = P()
    for value, hue in [("Control", "slate"), ("Variant B", "ember")]:
        L = p.sift("experiment_results", "variant", "is", value)
        b = p.sow("p0", L, "wisp")
        p.meter(b, "stance", "day")
        p.meter(b, "perch", "conversion")
        s = p.thread(b, by="day")
        p.tint(b, hue)
        p.tint(s, hue)
    p.settle("p0", "strew")
    p.rim("p0", "south")
    p.rim("p0", "west")
    n = p.nest(parcel="p0", aim="west", breadth=0.26, depth=0.36)
    LB = p.sift("experiment_results", "variant", "is", "Variant B")
    BB = p.bin(LB, "conversion", 5)
    from glyphbench.verify import apply_transform
    from .builders import levels_from_rows
    rowsB = apply_transform("experiment_results",
                            [["sift", "variant", "is", "Variant B"],
                             ["bin", "conversion", 5]])
    cells = p.carve(n, "span", BB, "bin", levels_from_rows(rowsB, "bin"),
                    gap=0.06)
    b3 = p.sow(n, BB, "slab", key="bin")
    p.meter(b3, "stature", "tally")
    p.entitle(n, "B distribution")
    p.entitle("p0", "Experiment 42")
    T.append(task(
        "From 'experiment_results': thread Control (slate) and Variant B "
        "(ember) 'conversion' over 'day' with rims; nest a west inset "
        "binning Variant B's conversions (about 5 bins) as mini columns "
        "entitled 'B distribution'; entitle the ground 'Experiment 42'.",
        p, [{"check": "brood", "weight": 4, "where": {
            "form": "wisp",
            "data": {"from": "experiment_results",
                     "transform": [["sift", "variant", "is", "Control"]]},
            "threaded_by": "day"}},
            {"check": "brood", "weight": 4, "where": {
                "form": "wisp",
                "data": {"from": "experiment_results",
                         "transform": [["sift", "variant", "is",
                                        "Variant B"]]},
                "threaded_by": "day"}},
            {"check": "brood", "weight": 5, "where": {
                "form": "slab",
                "data": {"from": "experiment_results",
                         "transform": [["sift", "variant", "is",
                                        "Variant B"],
                                       ["bin", "conversion", 5]]},
                "meter": {"stature": "tally"},
                "in": {"carved_by": "bin", "in_nest": True}}},
            {"check": "guide", "kind": "entitle"}],
        ["experiment_results"]))

    # 171 — three-panel regional report with shared gauges + kindles
    p = P()
    panels = p.split("p0", "span", 3)
    for i, region in enumerate(["Europe", "Americas", "Asia"]):
        L = p.sift("quarterly_revenue", "region", "is", region)
        cells = p.carve(panels[i], "span", L, "quarter",
                        ["Q1", "Q2", "Q3", "Q4"])
        b = p.sow(panels[i], L, "slab", key="quarter")
        p.meter(b, "stature", "revenue")
        p.meter(b, "tint", "product")
        p.settle(panels[i], "heap")
        p.rim(panels[i], "south")
        p.entitle(panels[i], region)
    p.share(panels[0], panels[1], "stature")
    p.share(panels[1], panels[2], "stature")
    p.rim(panels[0], "west")
    p.key("p0", "b1", "tint")
    p.entitle("p0", "Stacked revenue by region")
    T.append(task(
        "Small multiples from 'quarterly_revenue': three panels (Europe, "
        "Americas, Asia), each stacking 'revenue' per 'quarter' by product "
        "(tint), stature gauges shared across panels, south rims, west rim "
        "on the first, one key, panel titles and a ground title.",
        p, [{"check": "parcel", "where": {"split_count": 3},
             "label": "three panels"},
            {"check": "brood", "weight": 4, "where": {
                "form": "slab",
                "data": {"from": "quarterly_revenue",
                         "transform": [["sift", "region", "is", "Europe"]]},
                "meter": {"stature": "revenue", "tint": "product"},
                "in": {"carved_by": "quarter", "law": "heap"}}},
            {"check": "brood", "weight": 4, "where": {
                "form": "slab",
                "data": {"from": "quarterly_revenue",
                         "transform": [["sift", "region", "is", "Asia"]]},
                "meter": {"stature": "revenue", "tint": "product"},
                "in": {"law": "heap"}}},
            {"check": "share_or_abut"},
            {"check": "guide", "kind": "key", "trait": "tint"},
            {"check": "guide", "kind": "entitle"}],
        ["quarterly_revenue"]))

    # 172 — org + allocation mixed grammar
    p = P()
    panels = p.split("p0", "span", 2, gap=0.12)
    p.settle(panels[0], "current", heading="south")
    for name in ("CTO", "Platform", "Product", "Infra"):
        p.place(panels[0], "capsule", name)
    p.tether("CTO", "Platform")
    p.tether("CTO", "Product")
    p.tether("Platform", "Infra")
    p.entitle(panels[0], "Org")
    L = p.distill("team_allocation", "team", "sum", "engineers")
    cells = p.carve(panels[1], "span", L, "team",
                    ["Platform", "Product", "Infra"])
    b = p.sow(panels[1], L, "slab", key="team")
    p.meter(b, "stature", "engineers")
    p.badge(b, vein="engineers", aim="north")
    p.rim(panels[1], "south")
    p.entitle(panels[1], "Headcount")
    T.append(task(
        "Two panels: left, a southward org sketch 'CTO' → 'Platform' and "
        "'Product', with 'Platform' → 'Infra'; right, total 'engineers' "
        "per 'team' from 'team_allocation' as badged columns with a south "
        "rim. Entitle both panels.",
        p, [{"check": "parcel", "where": {"split_count": 2},
             "label": "two panels"},
            {"check": "cord", "from": "CTO", "to": "Platform"},
            {"check": "cord", "from": "Platform", "to": "Infra"},
            {"check": "brood", "weight": 5, "where": {
                "form": "slab",
                "data": {"from": "team_allocation",
                         "transform": [["distill", "team", "engineers",
                                        "sum"]]},
                "meter": {"stature": "engineers"},
                "badge_vein": "engineers",
                "in": {"carved_by": "team", "in_split_panel": True}}}],
        ["team_allocation"]))

    # 173 — leaderboard with hushed laggards
    p = P()
    L = p.distill("model_evals", "model", "mean", "score")
    L2 = p.marshal(L, "score", "waning")
    cells = p.carve("p0", "span", L2, "model",
                    ["Merlin", "Osprey", "Harrier", "Petrel", "Kestrel"])
    b = p.sow("p0", L2, "slab", key="model")
    p.meter(b, "stature", "score")
    p.badge(b, vein="score", aim="north")
    f = p.pick(b, "model", "is", "Merlin")
    p.kindle(f)
    f2 = p.pick(b, "score", "below", 75)
    p.hush(f2)
    p.rim("p0", "south")
    p.rim("p0", "west")
    p.entitle("p0", "Mean score by model")
    T.append(task(
        "A leaderboard from 'model_evals': mean 'score' per 'model', "
        "sorted waning, value badges, rims; kindle the leader (Merlin) and "
        "hush every model whose mean is below 75. Entitle it.",
        p, [{"check": "brood", "weight": 5, "where": {
            "form": "slab",
            "data": {"from": "model_evals",
                     "transform": [["distill", "model", "score", "mean"],
                                   ["marshal", "score", "waning"]]},
            "meter": {"stature": "score"}, "badge_vein": "score",
            "order": {"vein": "score", "sense": "waning"},
            "in": {"carved_by": "model"}}},
            {"check": "emphasis", "mode": "kindle",
             "target": {"where": {"model": "Merlin"}}},
            {"check": "emphasis", "mode": "hush",
             "target": {"where": {"model": "Kestrel"}}},
            {"check": "guide", "kind": "entitle"}],
        ["model_evals"]))

    # 174 — pipes into a drum (plasticity, new topology)
    p = P()
    p.settle("p0", "current", heading="east")
    p.place("p0", "capsule", "Mobile")
    p.place("p0", "capsule", "Web")
    p.place("p0", "capsule", "Collector")
    p.place("p0", "drum", "Lake")
    p.pipe("Mobile", "Collector", 640)
    p.pipe("Web", "Collector", 380)
    p.pipe("Collector", "Lake", 1020)
    p.badge("Collector", text="1.02M events/day", aim="south")
    T.append(task(
        "An event-volume map east: 'Mobile' (640) and 'Web' (380) pipe "
        "into 'Collector', which pipes 1020 onward into drum 'Lake' — "
        "widths proportional to volumes. Badge Collector beneath with "
        "'1.02M events/day'.",
        p, [{"check": "pipe_proportional", "weight": 4, "pairs": [
            ["Mobile", "Collector", 640], ["Web", "Collector", 380],
            ["Collector", "Lake", 1020]]},
            {"check": "glyph", "named": "Lake", "form": "drum"},
            {"check": "badge_named", "named": "Collector",
             "text_has": "events"}],
        []))

    # 175 — annotated area with era shading story
    T.append(line(
        "The launch story from 'monthly_finance': flood 'revenue' over "
        "'period' with rims and weft; flag M13 'launch' and M24 'today'; "
        "entitle 'Revenue since inception' and note 'flooded region shows "
        "cumulative reach'.",
        "monthly_finance", "period", "revenue", area=True,
        annotate=("launch", {"period": "M13"}, "flag"),
        title="Revenue since inception",
        note="flooded region shows cumulative reach"))
    T[-1]["reference_program"].insert(-4, ["pick", {
        "brood": "b1", "vein": "period", "relation": "is", "value": "M24"}])
    T[-1]["reference_program"].insert(-4, ["flag", {
        "target": "f2", "text": "today"}])
    T[-1]["hidden_goal"]["checks"].append(
        {"check": "annotation", "kind": "flag", "text_has": "today",
         "near": {"where": {"period": "M24"}}})

    # 176 — survey master figure
    T.append(bar(
        "The definitive survey figure: stack all of 'survey_results' per "
        "'topic' by 'response' under the 'dusk' palette with key, rims, "
        "weft; kindle the Strongly agree segment of Four-day week and flag "
        "it 'strongest signal'; entitle 'What the team wants'.",
        "survey_results", "topic", "share", stacked=True,
        stack_tint="response", legend=True, weft_rise=True, palette="dusk",
        kindle_where={"topic": "Four-day week",
                      "response": "Strongly agree"},
        annotate=("strongest signal",
                  {"topic": "Four-day week", "response": "Strongly agree"},
                  "flag"),
        title="What the team wants"))

    # 177 — city atlas: scatter + top-bars + shared story
    p = P()
    panels = p.split("p0", "span", 2)
    b1 = p.sow(panels[0], "city_stats", "disc")
    p.meter(b1, "stance", "growth")
    p.meter(b1, "perch", "transit_share")
    p.meter(b1, "bulk", "population")
    p.meter(b1, "tint", "continent")
    p.settle(panels[0], "strew")
    p.key(panels[0], b1, "tint")
    p.rim(panels[0], "south")
    p.rim(panels[0], "west")
    p.entitle(panels[0], "Growth vs transit")
    L = p.marshal("city_stats", "growth", "waning")
    L2 = p.crop(L, 5)
    from .builders import levels_from_rows as _lvl
    from glyphbench.verify import apply_transform as _apt
    rows5 = _apt("city_stats", [["marshal", "growth", "waning"],
                                ["crop", 5]])
    cells = p.carve(panels[1], "rise", L2, "city", _lvl(rows5, "city"))
    b2 = p.sow(panels[1], L2, "slab", key="city")
    p.meter(b2, "girth", "growth")
    p.badge(b2, vein="growth", aim="east")
    p.rim(panels[1], "west")
    p.entitle(panels[1], "Fastest growing")
    T.append(task(
        "A city atlas from 'city_stats': left panel scatters 'growth' vs "
        "'transit_share' (bulk by 'population', tint by 'continent', key, "
        "rims); right panel ranks the five fastest-growing cities as "
        "horizontal badged bars of 'growth' with a west rim. Titles on "
        "both.",
        p, [{"check": "parcel", "where": {"split_count": 2},
             "label": "two panels"},
            {"check": "brood", "weight": 5, "where": {
                "form": "disc",
                "meter": {"stance": "growth", "perch": "transit_share",
                          "bulk": "population", "tint": "continent"},
                "in": {"law": "strew"}}},
            {"check": "brood", "weight": 5, "where": {
                "form": "slab",
                "data": {"from": "city_stats",
                         "transform": [["marshal", "growth", "waning"],
                                       ["crop", 5]]},
                "meter": {"girth": "growth"}, "badge_vein": "growth",
                "in": {"carved_by": "city", "carve_along": "rise"}}},
            {"check": "guide", "kind": "key", "trait": "tint"}],
        ["city_stats"]))

    # 178 — architecture with pipes for volume (mixing cords and pipes)
    p = P()
    p.settle("p0", "current", heading="east")
    for form, name in [("capsule", "Clients"), ("capsule", "LB"),
                       ("capsule", "API-1"), ("capsule", "API-2"),
                       ("drum", "Postgres")]:
        p.place("p0", form, name)
    p.pipe("Clients", "LB", 980)
    p.pipe("LB", "API-1", 540)
    p.pipe("LB", "API-2", 440)
    c = p.tether("API-1", "Postgres")
    c2 = p.tether("API-2", "Postgres")
    p.corral(["API-1", "API-2"], label="Stateless tier")
    T.append(task(
        "Traffic through a load balancer, east: pipe 'Clients' → 'LB' "
        "(980), then 'LB' → 'API-1' (540) and 'LB' → 'API-2' (440); both "
        "APIs tether ordinary cords to drum 'Postgres'. Corral the two "
        "APIs as 'Stateless tier'.",
        p, [{"check": "pipe_proportional", "weight": 4, "pairs": [
            ["Clients", "LB", 980], ["LB", "API-1", 540],
            ["LB", "API-2", 440]]},
            {"check": "cord", "from": "API-1", "to": "Postgres"},
            {"check": "cord", "from": "API-2", "to": "Postgres"},
            {"check": "corral", "contains_named": ["API-1", "API-2"],
             "label_has": "Stateless"}],
        []))

    # 179 — dual axis + inset + note (finance master)
    T.append(dual_axis(
        "Rebuild the two-year finance view from 'monthly_finance' "
        "('revenue' slabs, loosened ember 'margin' strand, rims on all "
        "three sides, weft), kindle the after-launch era, flag M24 "
        "'highest margin', entitle 'Growth after launch' and note 'margin "
        "on the east gauge'.",
        "monthly_finance", "period", "revenue", "margin",
        kindle_bar_where={"era": "after launch"},
        flag_line=("highest margin", {"period": "M24"}),
        title="Growth after launch", note="margin on the east gauge"))

    # 180 — energy transition story
    p = P()
    panels = p.split("p0", "span", 2)
    L = p.sift("energy_mix", "source", "among",
               ["Hydro", "Wind", "Solar"])
    p.hoop(panels[0], inner=0.5)
    b = p.sow(panels[0], L, "slab")
    p.meter(b, "girth", "share")
    p.meter(b, "tint", "source")
    p.badge(b, vein="share", aim="center")
    p.entitle(panels[0], "Renewables")
    L2 = p.sift("energy_mix", "source", "among",
                ["Nuclear", "Gas", "Coal"])
    p.hoop(panels[1], inner=0.5)
    b2 = p.sow(panels[1], L2, "slab")
    p.meter(b2, "girth", "share")
    p.meter(b2, "tint", "source")
    p.badge(b2, vein="share", aim="center")
    p.entitle(panels[1], "Non-renewables")
    p.entitle("p0", "Generation mix, split")
    T.append(task(
        "Split 'energy_mix' into two open rings: renewables (Hydro, Wind, "
        "Solar) left and the rest (Nuclear, Gas, Coal) right, each wedge "
        "badged with its 'share' value in the middle, tinted by 'source', "
        "panel titles plus a ground title.",
        p, [{"check": "parcel", "where": {"split_count": 2},
             "label": "two panels"},
            {"check": "brood", "weight": 5, "where": {
                "form": "slab",
                "data": {"from": "energy_mix",
                         "transform": [["sift", "source", "among",
                                        ["Hydro", "Wind", "Solar"]]]},
                "meter": {"girth": "share", "tint": "source"},
                "badge_vein": "share", "in": {"hooped": True}}},
            {"check": "brood", "weight": 5, "where": {
                "form": "slab",
                "data": {"from": "energy_mix",
                         "transform": [["sift", "source", "among",
                                        ["Nuclear", "Gas", "Coal"]]]},
                "meter": {"girth": "share", "tint": "source"},
                "badge_vein": "share", "in": {"hooped": True}}},
            {"check": "guide", "kind": "entitle"}],
        ["energy_mix"]))

    # 181 — full checkout flow, mastery diagram
    T.append(diagram(
        "The full checkout, east: 'Browse' → 'Cart' → 'Checkout' → rhomb "
        "'Paid?' → 'Fulfil' (badge 'yes') and 'Retry' (badge 'no'); "
        "'Retry' tethers back to 'Checkout'; 'Fulfil' → 'Ship' → 'Done'. "
        "Corral Fulfil/Ship/Done as 'Warehouse', kindle the happy-path "
        "cords Checkout→Paid? and Paid?→Fulfil, hush 'Retry', entitle "
        "'Order lifecycle'.",
        [("capsule", "Browse"), ("capsule", "Cart"), ("capsule", "Checkout"),
         ("rhomb", "Paid?"), ("capsule", "Fulfil"), ("capsule", "Retry"),
         ("capsule", "Ship"), ("capsule", "Done")],
        [("Browse", "Cart"), ("Cart", "Checkout"), ("Checkout", "Paid?"),
         ("Paid?", "Fulfil", "yes"), ("Paid?", "Retry", "no"),
         ("Retry", "Checkout"), ("Fulfil", "Ship"), ("Ship", "Done")],
        corrals=[(["Fulfil", "Ship", "Done"], "Warehouse")],
        kindle_cords=[("Checkout", "Paid?"), ("Paid?", "Fulfil")],
        hush_nodes=["Retry"], title="Order lifecycle"))

    # 182 — histogram + strew overlay (distribution + points)
    p = P()
    B = p.bin("ticket_resolution", "hours", 10)
    from glyphbench.verify import apply_transform as _apt2
    rows10 = _apt2("ticket_resolution", [["bin", "hours", 10]])
    cells = p.carve("p0", "span", B, "bin", _lvl(rows10, "bin"), gap=0.06)
    b = p.sow("p0", B, "slab", key="bin")
    p.meter(b, "stature", "tally")
    top = max(rows10, key=lambda r: r["tally"])["bin"]
    f = p.pick(b, "bin", "is", top)
    p.kindle(f)
    p.flag(f, "the common case")
    p.rim("p0", "south")
    p.rim("p0", "west")
    p.weft("p0", "rise")
    p.entitle("p0", "Resolution time")
    p.note("p0", "long tail beyond 8 hours")
    T.append(task(
        "The mastery histogram: bin 'ticket_resolution' 'hours' into about "
        "10 bins, kindle and flag the tallest bin 'the common case', rims, "
        "weft, entitled 'Resolution time', noted 'long tail beyond 8 "
        "hours'.",
        p, [{"check": "brood", "weight": 5, "where": {
            "form": "slab",
            "data": {"from": "ticket_resolution",
                     "transform": [["bin", "hours", 10]]},
            "meter": {"stature": "tally"}, "in": {"carved_by": "bin"}}},
            {"check": "emphasis", "mode": "kindle", "exclusive": True,
             "target": {"where": {"bin": top}}},
            {"check": "annotation", "kind": "flag", "text_has": "common",
             "near": {"where": {"bin": top}}},
            {"check": "guide", "kind": "entitle"},
            {"check": "guide", "kind": "note"}],
        ["ticket_resolution"]))

    # 183 — model matrix: two grouped views abutted
    p = P()
    panels = p.split("p0", "rise", 2)
    cells1 = p.carve(panels[0], "span", "model_evals", "benchmark",
                     ["Reasoning", "Coding", "Math", "Recall"])
    b1 = p.sow(panels[0], "model_evals", "slab", key="benchmark")
    p.meter(b1, "stature", "score")
    p.meter(b1, "tint", "model")
    p.key(panels[0], b1, "tint")
    p.rim(panels[0], "west")
    p.entitle(panels[0], "By benchmark")
    cells2 = p.carve(panels[1], "span", "model_evals", "model",
                     ["Kestrel", "Petrel", "Osprey", "Harrier", "Merlin"])
    b2 = p.sow(panels[1], "model_evals", "slab", key="model")
    p.meter(b2, "stature", "score")
    p.meter(b2, "tint", "benchmark")
    p.key(panels[1], b2, "tint")
    p.rim(panels[1], "west")
    p.rim(panels[1], "south")
    p.entitle(panels[1], "By model")
    p.share(panels[0], panels[1], "stature")
    T.append(task(
        "Both cuts of 'model_evals' stacked vertically: top groups 'score' "
        "by 'benchmark' (tint per model), bottom groups by 'model' (tint "
        "per benchmark), each with its own key and west rim, stature "
        "shared between panels, titles on both.",
        p, [{"check": "parcel", "where": {"split_count": 2,
                                          "split_along": "rise"},
             "label": "two stacked panels"},
            {"check": "brood", "weight": 4, "where": {
                "form": "slab", "meter": {"stature": "score",
                                          "tint": "model"},
                "in": {"carved_by": "benchmark"}}},
            {"check": "brood", "weight": 4, "where": {
                "form": "slab", "meter": {"stature": "score",
                                          "tint": "benchmark"},
                "in": {"carved_by": "model"}}},
            {"check": "share_or_abut"}],
        ["model_evals"]))

    # 184 — pipes with heft badges and hushed side-branch
    p = P()
    p.settle("p0", "current", heading="south")
    for name in ("Raised", "Screened", "Interviewed", "Hired"):
        p.place("p0", "capsule", name)
    p.place("p0", "capsule", "Referrals")
    p.pipe("Raised", "Screened", 420)
    p.pipe("Screened", "Interviewed", 160)
    p.pipe("Interviewed", "Hired", 32)
    c = p.tether("Referrals", "Interviewed")
    p.hush("Referrals")
    p.entitle("p0", "Southward funnel")
    T.append(task(
        "A funnel flowing SOUTH this time: pipes 'Raised' → 'Screened' "
        "(420) → 'Interviewed' (160) → 'Hired' (32), plus a hushed side "
        "capsule 'Referrals' tethered into 'Interviewed'. Entitle "
        "'Southward funnel'.",
        p, [{"check": "parcel", "where": {"law": "current",
                                          "heading": "south"},
             "label": "southward current"},
            {"check": "pipe_proportional", "weight": 4, "pairs": [
                ["Raised", "Screened", 420],
                ["Screened", "Interviewed", 160],
                ["Interviewed", "Hired", 32]]},
            {"check": "cord", "from": "Referrals", "to": "Interviewed"},
            {"check": "emphasis", "mode": "hush",
             "target": {"named": "Referrals"}}],
        []))

    # 185 — retention: donut + key + kindle (gap from 157)
    T.append(pie(
        "One more ring: 'feature_usage' hooped with inner 0.55, angular "
        "share from 'users', tint per 'feature' with key, kindle "
        "Dashboards, entitle 'Usage share'.",
        "feature_usage", "feature", "users", inner=0.55, badge_cat=False,
        legend=True, kindle_where={"feature": "Dashboards"},
        title="Usage share"))

    # 186 — the everything-line: multi series + flags + weft + note
    T.append(multi_line(
        "The experiment finale: all three variants of 'experiment_results' "
        "threaded over 'day' (Control slate, Variant B ember, Variant C "
        "moss), labels at D14, Variant B kindled, rims, weft, entitled "
        "'Fourteen days of testing'.",
        "experiment_results", "day", "conversion", "variant",
        [("Control", "slate"), ("Variant B", "ember"),
         ("Variant C", "moss")],
        label_at="D14", kindle_series="Variant B",
        title="Fourteen days of testing"))
    T[-1]["reference_program"].append(["note", {
        "parcel": "p0", "text": "B shipped to 100% on day 15"}])
    T[-1]["hidden_goal"]["checks"].append({"check": "guide", "kind": "note"})

    # 187 — warehouse map with pipes + corral + drum
    p = P()
    p.settle("p0", "current", heading="east")
    for form, name in [("capsule", "Stores"), ("capsule", "Returns"),
                       ("capsule", "Sorting"), ("capsule", "Restock"),
                       ("drum", "Inventory")]:
        p.place("p0", form, name)
    p.pipe("Stores", "Sorting", 310)
    p.pipe("Returns", "Sorting", 120)
    p.pipe("Sorting", "Restock", 290)
    p.tether("Restock", "Inventory")
    p.corral(["Sorting", "Restock"], label="Warehouse")
    p.flag("Sorting", "bottleneck shift")
    T.append(task(
        "Goods flow east: 'Stores' (310) and 'Returns' (120) pipe into "
        "'Sorting', which pipes 290 to 'Restock'; Restock tethers to drum "
        "'Inventory'. Corral Sorting and Restock as 'Warehouse' and flag "
        "Sorting 'bottleneck shift'.",
        p, [{"check": "pipe_proportional", "weight": 4, "pairs": [
            ["Stores", "Sorting", 310], ["Returns", "Sorting", 120],
            ["Sorting", "Restock", 290]]},
            {"check": "cord", "from": "Restock", "to": "Inventory"},
            {"check": "corral", "contains_named": ["Sorting", "Restock"],
             "label_has": "Warehouse"},
            {"check": "annotation", "kind": "flag", "text_has": "bottleneck",
             "near": {"named": "Sorting"}}],
        []))

    # 188 — quarterly report card (grouped + share note + hush)
    p = P()
    L = p.sift("quarterly_revenue", "region", "is", "Americas")
    cells = p.carve("p0", "span", L, "quarter", ["Q1", "Q2", "Q3", "Q4"])
    b = p.sow("p0", L, "slab", key="quarter")
    p.meter(b, "stature", "revenue")
    p.meter(b, "tint", "product")
    p.key("p0", b, "tint")
    f = p.pick(b, "product", "is", "Cove")
    p.hush(f)
    p.rim("p0", "south")
    p.rim("p0", "west")
    p.weft("p0", "rise")
    p.entitle("p0", "Americas, Cove de-emphasized")
    T.append(task(
        "Americas quarters from 'quarterly_revenue', grouped by product "
        "with key, rims and weft — but hush every Cove slab so the two "
        "lead products carry the story. Entitle accordingly.",
        p, [{"check": "brood", "weight": 5, "where": {
            "form": "slab",
            "data": {"from": "quarterly_revenue",
                     "transform": [["sift", "region", "is", "Americas"]]},
            "meter": {"stature": "revenue", "tint": "product"},
            "in": {"carved_by": "quarter", "law": "abreast"}}},
            {"check": "emphasis", "mode": "hush",
             "target": {"where": {"product": "Cove"}}},
            {"check": "guide", "kind": "key", "trait": "tint"},
            {"check": "guide", "kind": "entitle"}],
        ["quarterly_revenue"]))

    # 189 — timeline meets flow: milestones + tethered chain
    p = P()
    b = p.sow("p0", "milestones", "disc")
    p.meter(b, "stance", "week")
    p.meter(b, "bulk", "impact")
    p.settle("p0", "strew")
    p.thread(b, by="week")
    p.badge(b, vein="milestone", aim="north")
    f1 = p.pick(b, "milestone", "is", "Beta")
    p.kindle(f1)
    f2 = p.pick(b, "milestone", "is", "Launch")
    p.kindle(f2)
    p.flag(f2, "shipped")
    p.rim("p0", "south")
    p.entitle("p0", "Road to launch")
    p.note("p0", "disc size = impact")
    T.append(task(
        "The definitive 'milestones' timeline: discs by 'week', bulk from "
        "'impact', badges, threaded; kindle Beta and Launch, flag Launch "
        "'shipped', south rim, title 'Road to launch', note 'disc size = "
        "impact'.",
        p, [{"check": "brood", "weight": 6, "where": {
            "form": "disc", "meter": {"stance": "week", "bulk": "impact"},
            "threaded_by": "week", "badge_vein": "milestone",
            "in": {"law": "strew"}}},
            {"check": "emphasis", "mode": "kindle",
             "target": {"where": {"milestone": "Launch"}}},
            {"check": "annotation", "kind": "flag", "text_has": "shipped",
             "near": {"where": {"milestone": "Launch"}}},
            {"check": "guide", "kind": "note"}],
        ["milestones"]))

    # 190 — pipes as sankey-lite across three tiers
    p = P()
    p.settle("p0", "current", heading="east")
    for name in ("Organic", "Paid", "Site", "Trial", "Paid plan"):
        p.place("p0", "capsule", name)
    p.pipe("Organic", "Site", 700)
    p.pipe("Paid", "Site", 330)
    p.pipe("Site", "Trial", 210)
    p.pipe("Trial", "Paid plan", 60)
    p.kindle("Trial")
    p.entitle("p0", "Acquisition flow")
    T.append(task(
        "A three-tier acquisition flow east with pipes: 'Organic' (700) "
        "and 'Paid' (330) into 'Site'; 'Site' → 'Trial' (210); 'Trial' → "
        "'Paid plan' (60). Kindle Trial. Entitle 'Acquisition flow'.",
        p, [{"check": "pipe_proportional", "weight": 4, "pairs": [
            ["Organic", "Site", 700], ["Paid", "Site", 330],
            ["Site", "Trial", 210], ["Trial", "Paid plan", 60]]},
            {"check": "emphasis", "mode": "kindle",
             "target": {"named": "Trial"}},
            {"check": "guide", "kind": "entitle"}],
        []))

    # 191 — two-level carve masterwork
    p = P()
    L = p.sift("quarterly_revenue", "product", "is", "Aria")
    outer = p.carve("p0", "span", L, "region",
                    ["Europe", "Americas", "Asia"])
    for region, cell in outer.items():
        Lr = p.sift(L, "region", "is", region)
        inner = p.carve(cell, "span", Lr, "quarter",
                        ["Q1", "Q2", "Q3", "Q4"], gap=0.08)
        br = p.sow(cell, Lr, "slab", key="quarter")
        p.meter(br, "stature", "revenue")
    p.rim("p0", "west")
    p.weft("p0", "rise")
    p.entitle("p0", "Aria by region and quarter")
    T.append(task(
        "Aria's world from 'quarterly_revenue': outer regions per 'region', "
        "inner cells per 'quarter', a revenue slab in each, west rim, "
        "weft, entitled 'Aria by region and quarter'.",
        p, [{"check": "parcel", "where": {"carved_by": "region"},
             "label": "outer carve by region"},
            {"check": "brood", "weight": 5, "where": {
                "form": "slab", "meter": {"stature": "revenue"},
                "in": {"carved_by": "quarter",
                       "outer_carved_by": "region"}}},
            {"check": "guide", "kind": "rim", "side": "west"},
            {"check": "guide", "kind": "entitle"}],
        ["quarterly_revenue"]))

    # 192 — dual-axis + pipes hybrid dashboard
    p = P()
    panels = p.split("p0", "rise", 2)
    p.settle(panels[0], "current", heading="east")
    for name in ("Visitors", "Signups", "Customers"):
        p.place(panels[0], "capsule", name)
    p.pipe("Visitors", "Signups", 330)
    p.pipe("Signups", "Customers", 95)
    p.entitle(panels[0], "Conversion")
    L = p.sift("site_traffic", "channel", "is", "Search")
    b = p.sow(panels[1], L, "wisp")
    p.meter(b, "stance", "week")
    p.meter(b, "perch", "visits")
    p.settle(panels[1], "strew")
    p.thread(b, by="week")
    p.rim(panels[1], "south")
    p.rim(panels[1], "west")
    p.entitle(panels[1], "Search visits")
    T.append(task(
        "A hybrid dashboard: top panel pipes 'Visitors' → 'Signups' (330) "
        "→ 'Customers' (95) eastward; bottom panel threads Search "
        "'visits' from 'site_traffic' over 'week' with rims. Entitle both "
        "panels.",
        p, [{"check": "parcel", "where": {"split_count": 2},
             "label": "two panels"},
            {"check": "pipe_proportional", "weight": 3, "pairs": [
                ["Visitors", "Signups", 330], ["Signups", "Customers", 95]]},
            {"check": "brood", "weight": 4, "where": {
                "form": "wisp",
                "data": {"from": "site_traffic",
                         "transform": [["sift", "channel", "is",
                                        "Search"]]},
                "threaded_by": "week",
                "in": {"in_split_panel": True}}}],
        ["site_traffic"]))

    # 193 — grand traffic report
    p = P()
    panels = p.split("p0", "rise", 2)
    checksT = [{"check": "parcel", "where": {"split_count": 2},
                "label": "two panels"}]
    for value, hue in [("Search", "tide"), ("Social", "ember"),
                       ("Direct", "moss"), ("Email", "plum")]:
        L = p.sift("site_traffic", "channel", "is", value)
        b = p.sow(panels[0], L, "wisp")
        p.meter(b, "stance", "week")
        p.meter(b, "perch", "visits")
        s = p.thread(b, by="week")
        p.tint(b, hue)
        p.tint(s, hue)
    p.settle(panels[0], "strew")
    p.rim(panels[0], "west")
    p.entitle(panels[0], "All channels")
    checksT.append({"check": "strand_count", "n": 4})
    L2 = p.distill("site_traffic", "channel", "sum", "visits")
    p.hoop(panels[1], inner=0.5)
    b2 = p.sow(panels[1], L2, "slab")
    p.meter(b2, "girth", "visits")
    p.meter(b2, "tint", "channel")
    p.badge(b2, vein="channel", aim="rim")
    p.entitle(panels[1], "Total share")
    checksT.append({"check": "brood", "weight": 5, "where": {
        "form": "slab",
        "data": {"from": "site_traffic",
                 "transform": [["distill", "channel", "visits", "sum"]]},
        "meter": {"girth": "visits", "tint": "channel"},
        "badge_vein": "channel", "in": {"hooped": True}}})
    p.entitle("p0", "Twelve weeks of traffic")
    checksT.append({"check": "guide", "kind": "entitle",
                    "text_has": "Twelve"})
    T.append(task(
        "The quarter's traffic report from 'site_traffic': top panel "
        "threads all four channels over 'week' in distinct hues with a "
        "west rim; bottom panel is an open ring of total visits per "
        "channel, badged at the rim. Entitle panels and ground ('Twelve "
        "weeks of traffic').",
        p, checksT, ["site_traffic"]))

    # 194 — deep org chart with kindled chain
    T.append(diagram(
        "A deep chain of command, south: 'Board' → 'CEO' → 'CTO' → "
        "'VP Platform' → 'Team Lead' → 'Engineer'; kindle every cord along "
        "the chain from CEO down to Engineer; entitle 'Reporting line'.",
        [("capsule", "Board"), ("capsule", "CEO"), ("capsule", "CTO"),
         ("capsule", "VP Platform"), ("capsule", "Team Lead"),
         ("capsule", "Engineer")],
        [("Board", "CEO"), ("CEO", "CTO"), ("CTO", "VP Platform"),
         ("VP Platform", "Team Lead"), ("Team Lead", "Engineer")],
        heading="south",
        kindle_cords=[("CEO", "CTO"), ("CTO", "VP Platform"),
                      ("VP Platform", "Team Lead"),
                      ("Team Lead", "Engineer")],
        title="Reporting line"))

    # 195 — everything bar: two-level + badges + kindle + inset
    p = P()
    L = p.sift("site_traffic", "week", "among", ["W11", "W12"])
    outer = p.carve("p0", "span", L, "week", ["W11", "W12"])
    for wk, cell in outer.items():
        Lw = p.sift(L, "week", "is", wk)
        inner = p.carve(cell, "span", Lw, "channel",
                        ["Search", "Social", "Direct", "Email"], gap=0.08)
        bw = p.sow(cell, Lw, "slab", key="channel")
        p.meter(bw, "stature", "visits")
        p.badge(bw, vein="visits", aim="north")
    p.rim("p0", "west")
    p.entitle("p0", "Final fortnight, by channel")
    T.append(task(
        "The final fortnight of 'site_traffic' (weeks W11 and W12): outer "
        "cells per 'week', inner cells per 'channel', a badged visits slab "
        "in each, west rim, entitled 'Final fortnight, by channel'.",
        p, [{"check": "parcel", "where": {"carved_by": "week"},
             "label": "outer carve by week"},
            {"check": "brood", "weight": 5, "where": {
                "form": "slab", "meter": {"stature": "visits"},
                "badge_vein": "visits",
                "in": {"carved_by": "channel",
                       "outer_carved_by": "week"}}},
            {"check": "guide", "kind": "rim", "side": "west"},
            {"check": "guide", "kind": "entitle"}],
        ["site_traffic"]))

    # 196 — pyramid: age bands horizontal + inverted + annotations
    p = P()
    cells = p.carve("p0", "rise", "age_distribution", "age_band",
                    ["0-9", "10-19", "20-29", "30-39", "40-49", "50-59",
                     "60-69", "70+"])
    b = p.sow("p0", "age_distribution", "slab", key="age_band")
    p.meter(b, "girth", "population")
    p.invert("p0", "rise")
    p.badge(b, vein="population", aim="east")
    f = p.pick(b, "age_band", "is", "30-39")
    p.kindle(f)
    p.flag(f, "peak cohort")
    p.rim("p0", "west")
    p.entitle("p0", "Population pyramid")
    T.append(task(
        "A half-pyramid from 'age_distribution': horizontal 'population' "
        "bars per 'age_band', youngest at the bottom (rise inverted), "
        "values badged east, the 30-39 bar kindled and flagged 'peak "
        "cohort', west rim, entitled 'Population pyramid'.",
        p, [{"check": "brood", "weight": 5, "where": {
            "form": "slab", "meter": {"girth": "population"},
            "badge_vein": "population",
            "in": {"carved_by": "age_band", "carve_along": "rise"}}},
            {"check": "parcel", "where": {"inverted": "rise"},
             "label": "rise inverted"},
            {"check": "emphasis", "mode": "kindle", "exclusive": True,
             "target": {"where": {"age_band": "30-39"}}},
            {"check": "annotation", "kind": "flag", "text_has": "cohort",
             "near": {"where": {"age_band": "30-39"}}}],
        ["age_distribution"]))

    # 197 — pipes + nested minis (the two late grammars together)
    p = P()
    p.settle("p0", "current", heading="east")
    for name in ("Intake", "Processing", "Delivery"):
        p.place("p0", "capsule", name)
    p.pipe("Intake", "Processing", 420)
    p.pipe("Processing", "Delivery", 310)
    n = p.nest(host="Processing", aim="south")
    L = p.sift("latency_profile", "service", "is", "Orders")
    b = p.sow(n, L, "slab")
    p.meter(b, "stature", "ms")
    p.flag("Processing", "watch the tail")
    T.append(task(
        "Pipes east: 'Intake' → 'Processing' (420) → 'Delivery' (310). "
        "Nest the Orders rows of 'latency_profile' beneath 'Processing' as "
        "mini 'ms' columns, and flag Processing 'watch the tail'.",
        p, [{"check": "pipe_proportional", "weight": 3, "pairs": [
            ["Intake", "Processing", 420], ["Processing", "Delivery", 310]]},
            {"check": "brood", "weight": 5, "where": {
                "form": "slab", "meter": {"stature": "ms"},
                "in": {"nested_under": "Processing"}}},
            {"check": "annotation", "kind": "flag", "text_has": "tail",
             "near": {"named": "Processing"}}],
        ["latency_profile"]))

    # 198 — closing scatter masterpiece
    T.append(scatter(
        "The closing scatter from 'city_stats': 'growth' across, "
        "'transit_share' up, bulk by 'population', tint by 'continent' "
        "with key, rims and title 'Cities compared'; kindle the Asian "
        "cities and flag Busan 'transit champion'.",
        "city_stats", "growth", "transit_share", bulk="population",
        tint_cat="continent", legend=True, title="Cities compared",
        kindle_where={"continent": "Asia"},
        annotate=("transit champion", {"city": "Busan"}, "flag")))

    # 199 — closing finance figure (Example B reprise, no scaffolding)
    T.append(dual_axis(
        "Once more, from memory: 'monthly_finance' revenue slabs by "
        "'period', margin threaded on a loosened ember gauge, all rims, "
        "weft, kindle after-launch, flag M24 'highest margin', entitled "
        "'The growth story', noted 'prepared with VELD'.",
        "monthly_finance", "period", "revenue", "margin",
        kindle_bar_where={"era": "after launch"},
        flag_line=("highest margin", {"period": "M24"}),
        title="The growth story", note="prepared with VELD"))

    # 200 — the grand finale: architecture + funnel + chart in panels
    p = P()
    panels = p.split("p0", "rise", 2, gap=0.1)
    p.settle(panels[0], "current", heading="east")
    p.place(panels[0], "capsule", "Users")
    p.place(panels[0], "capsule", "Gateway")
    p.place(panels[0], "capsule", "Payments")
    p.place(panels[0], "capsule", "Search")
    p.place(panels[0], "drum", "Ledger DB")
    p.tether("Users", "Gateway")
    c = p.tether("Gateway", "Payments")
    p.tether("Gateway", "Search")
    p.tether("Payments", "Ledger DB")
    p.corral(["Payments", "Search"], label="Core")
    p.kindle(c)
    p.kindle("Payments")
    p.entitle(panels[0], "The platform")
    L = p.sift("latency_profile", "metric", "is", "p99")
    cells = p.carve(panels[1], "span", L, "service",
                    ["Gateway", "Payments", "Orders", "Search", "Profiles"])
    b = p.sow(panels[1], L, "slab", key="service")
    p.meter(b, "stature", "ms")
    p.badge(b, vein="ms", aim="north")
    f = p.pick(b, "service", "is", "Search")
    p.kindle(f)
    p.rim(panels[1], "south")
    p.rim(panels[1], "west")
    p.entitle(panels[1], "p99 latency")
    p.entitle("p0", "State of the system")
    T.append(task(
        "The finale, two panels: above, an eastward architecture — 'Users' "
        "→ 'Gateway' → 'Payments' and 'Search' (corralled 'Core'), "
        "Payments → drum 'Ledger DB', the Gateway→Payments cord and "
        "Payments kindled; below, p99 'ms' per 'service' from "
        "'latency_profile' (sift metric p99) as badged columns with rims, "
        "Search kindled. Entitle the panels and the ground 'State of the "
        "system'.",
        p, [{"check": "parcel", "where": {"split_count": 2},
             "label": "two panels"},
            {"check": "cord", "from": "Users", "to": "Gateway"},
            {"check": "cord", "from": "Gateway", "to": "Payments"},
            {"check": "cord", "from": "Payments", "to": "Ledger DB"},
            {"check": "corral", "contains_named": ["Payments", "Search"],
             "label_has": "Core"},
            {"check": "emphasis", "mode": "kindle",
             "target": {"cord_from": "Gateway", "cord_to": "Payments"}},
            {"check": "brood", "weight": 5, "where": {
                "form": "slab",
                "data": {"from": "latency_profile",
                         "transform": [["sift", "metric", "is", "p99"]]},
                "meter": {"stature": "ms"}, "badge_vein": "ms",
                "in": {"carved_by": "service", "in_split_panel": True}}},
            {"check": "emphasis", "mode": "kindle",
             "target": {"where": {"service": "Search", "metric": "p99"}}},
            {"check": "guide", "kind": "entitle", "text_has": "State"}],
        ["latency_profile"]))

    assert len(T) == 40, len(T)
    return T
