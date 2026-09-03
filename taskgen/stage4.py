"""Stage 4 (tasks 111-160): advanced composition, 8-15 concepts.
New here: loosen (dual gauges), nest under glyphs, inset parcels, abut,
two-level carving, ramp tints, cord routing (crook/heft)."""

from diagrambench.verify import apply_transform

from .builders import (P, task, bar, pie, line, scatter, histogram, diagram,
                       levels_from_rows)
from .stage3 import multi_line


def dual_axis(instruction, ds, x, bar_y, line_y, transform=None, title=None,
              kindle_bar_where=None, flag_line=None, note=None,
              line_hue="ember"):
    from .builders import transformed
    p = P()
    rows, build_ref = transformed(ds, transform)
    ref = build_ref(p)
    b1 = p.sow("p0", ref, "slab")
    p.meter(b1, "stance", x)
    p.meter(b1, "stature", bar_y)
    b2 = p.sow("p0", ref, "wisp")
    p.meter(b2, "stance", x)
    p.meter(b2, "perch", line_y)
    p.loosen(b2, "perch")
    p.settle("p0", "strew")
    s = p.thread(b2, by=x)
    p.tint(b2, line_hue)
    p.tint(s, line_hue)
    if kindle_bar_where:
        f = None
        for vein, value in kindle_bar_where.items():
            f = p.pick(f or b1, vein, "is", value)
        p.kindle(f)
    if flag_line:
        text, where = flag_line
        f = None
        for vein, value in where.items():
            f = p.pick(f or b2, vein, "is", value)
        p.flag(f, text)
    p.weft("p0", "rise")
    p.rim("p0", "south")
    p.rim("p0", "west")
    p.rim("p0", "east")
    if title:
        p.entitle("p0", title)
    if note:
        p.note("p0", note)
    tf = transform or []
    checks = [
        {"check": "brood", "weight": 5, "where": {
            "form": "slab", "data": {"from": ds, "transform": tf},
            "meter": {"stance": x, "stature": bar_y},
            "in": {"law": "strew"}}},
        {"check": "brood", "weight": 5, "where": {
            "form": "wisp", "data": {"from": ds, "transform": tf},
            "meter": {"stance": x, "perch": line_y},
            "loose": ["perch"], "threaded_by": x}},
        {"check": "guide", "kind": "rim", "side": "south"},
        {"check": "guide", "kind": "rim", "side": "west"},
        {"check": "guide", "kind": "rim", "side": "east"},
    ]
    if kindle_bar_where:
        checks.append({"check": "emphasis", "mode": "kindle",
                       "target": {"where": kindle_bar_where}})
    if flag_line:
        text, where = flag_line
        checks.append({"check": "annotation", "kind": "flag",
                       "text_has": max(text.split(), key=len),
                       "near": {"where": where}})
    if title:
        checks.append({"check": "guide", "kind": "entitle"})
    if note:
        checks.append({"check": "guide", "kind": "note"})
    return task(instruction, p, checks, [ds])


def build():
    T = []

    # 111 — first dual axis
    T.append(dual_axis(
        "From 'monthly_finance', station monthly 'revenue' as slabs by "
        "'period' and lay 'margin' over them as an ember strand on its own "
        "loosened gauge (east rim for margin, west for revenue, south for "
        "periods; weft).",
        "monthly_finance", "period", "revenue", "margin"))

    # 112 — first nested mini-chart under a node
    p = P()
    p.settle("p0", "current", heading="east")
    p.place("p0", "capsule", "Gateway")
    p.place("p0", "capsule", "Payments")
    p.tether("Gateway", "Payments")
    n = p.nest(host="Payments", aim="south")
    L = p.sift("latency_profile", "service", "is", "Payments")
    b = p.sow(n, L, "slab")
    p.meter(b, "stature", "ms")
    p.badge(b, vein="metric", aim="center")
    T.append(task(
        "Sketch 'Gateway' → 'Payments' flowing east; beneath the Payments "
        "capsule, nest a fresh parcel and sow that service's rows of "
        "'latency_profile' as mini columns metered by 'ms', badged with "
        "their 'metric'.",
        p, [{"check": "glyph", "named": "Gateway", "form": "capsule"},
            {"check": "glyph", "named": "Payments", "form": "capsule"},
            {"check": "cord", "from": "Gateway", "to": "Payments"},
            {"check": "brood", "weight": 6, "where": {
                "form": "slab",
                "data": {"from": "latency_profile",
                         "transform": [["sift", "service", "is",
                                        "Payments"]]},
                "meter": {"stature": "ms"},
                "in": {"nested_under": "Payments"}}}],
        ["latency_profile"]))

    # 113 — inset pie over a bar chart
    p = P()
    L = p.distill("quarterly_revenue", "quarter", "sum", "revenue")
    cells = p.carve("p0", "span", L, "quarter", ["Q1", "Q2", "Q3", "Q4"])
    b = p.sow("p0", L, "slab", key="quarter")
    p.meter(b, "stature", "revenue")
    p.rim("p0", "south")
    p.rim("p0", "west")
    n = p.nest(parcel="p0", aim="east", breadth=0.3, depth=0.42)
    L2 = p.distill("quarterly_revenue", "region", "sum", "revenue")
    p.hoop(n)
    b2 = p.sow(n, L2, "slab")
    p.meter(b2, "girth", "revenue")
    p.meter(b2, "tint", "region")
    p.badge(b2, vein="region", aim="center")
    p.entitle("p0", "Revenue by quarter, mix by region")
    T.append(task(
        "Quarterly total 'revenue' columns from 'quarterly_revenue' with "
        "rims; then nest an inset parcel toward the east, hoop it, and show "
        "total revenue share per 'region' as tinted wedges badged with the "
        "region name. Entitle the whole ground.",
        p, [{"check": "brood", "weight": 4, "where": {
            "form": "slab",
            "data": {"from": "quarterly_revenue",
                     "transform": [["distill", "quarter", "revenue", "sum"]]},
            "meter": {"stature": "revenue"}, "in": {"carved_by": "quarter"}}},
            {"check": "brood", "weight": 5, "where": {
                "form": "slab",
                "data": {"from": "quarterly_revenue",
                         "transform": [["distill", "region", "revenue",
                                        "sum"]]},
                "meter": {"girth": "revenue", "tint": "region"},
                "in": {"hooped": True, "in_nest": True}}},
            {"check": "guide", "kind": "entitle"}],
        ["quarterly_revenue"]))

    # 114 — abutted panels
    p = P()
    panels = p.split("p0", "rise", 2)
    b1 = p.sow(panels[0], "monthly_finance", "wisp")
    p.meter(b1, "stance", "period")
    p.meter(b1, "perch", "revenue")
    p.settle(panels[0], "strew")
    p.thread(b1, by="period")
    p.rim(panels[0], "west")
    p.entitle(panels[0], "Revenue")
    b2 = p.sow(panels[1], "monthly_finance", "wisp")
    p.meter(b2, "stance", "period")
    p.meter(b2, "perch", "margin")
    p.settle(panels[1], "strew")
    s2 = p.thread(b2, by="period")
    p.tint(b2, "ember")
    p.tint(s2, "ember")
    p.rim(panels[1], "west")
    p.rim(panels[1], "south")
    p.entitle(panels[1], "Margin")
    p.abut(panels[0], panels[1], "west")
    T.append(task(
        "Two stacked panels over the same months of 'monthly_finance': "
        "'revenue' threaded above, ember 'margin' threaded below, west rims "
        "on both, south rim below, panels abutting along their west edges "
        "so the strands align.",
        p, [{"check": "parcel", "where": {"split_count": 2,
                                          "split_along": "rise"},
             "label": "stacked panels"},
            {"check": "brood", "weight": 4, "where": {
                "form": "wisp", "meter": {"stance": "period",
                                          "perch": "revenue"},
                "threaded_by": "period",
                "in": {"in_split_panel": True}}},
            {"check": "brood", "weight": 4, "where": {
                "form": "wisp", "meter": {"stance": "period",
                                          "perch": "margin"},
                "threaded_by": "period"}},
            {"check": "share_or_abut"}],
        ["monthly_finance"]))

    # 115 — two-level carve (nested grouping)
    p = P()
    L = p.sift("quarterly_revenue", "region", "is", "Europe")
    outer = p.carve("p0", "span", L, "quarter", ["Q1", "Q2", "Q3", "Q4"])
    for q, cell in outer.items():
        Lq = p.sift(L, "quarter", "is", q)
        inner = p.carve(cell, "span", Lq, "product",
                        ["Aria", "Breeze", "Cove"], gap=0.08)
        b = p.sow(cell, Lq, "slab", key="product")
        p.meter(b, "stature", "revenue")
    p.rim("p0", "south")
    p.rim("p0", "west")
    T.append(task(
        "Carve twice: European rows of 'quarterly_revenue' arranged with an "
        "outer region per 'quarter' and, inside each, an inner cell per "
        "'product' holding that product's revenue slab. Rims south and "
        "west.",
        p, [{"check": "parcel", "label": "outer carve by quarter",
             "where": {"carved_by": "quarter"}},
            {"check": "parcel", "label": "inner carve by product",
             "where": {"carved_by": "product"}},
            {"check": "brood", "weight": 5, "where": {
                "form": "slab", "meter": {"stature": "revenue"},
                "in": {"carved_by": "product",
                       "outer_carved_by": "quarter"}}},
            {"check": "guide", "kind": "rim", "side": "south"},
            {"check": "guide", "kind": "rim", "side": "west"}],
        ["quarterly_revenue"]))

    # 116 — ramp tint scatter
    T.append(scatter(
        "Scatter 'city_stats' by 'growth' and 'transit_share', tinting each "
        "disc by its counted 'population' so bigger cities read darker "
        "(a ramp, not bands), with a key showing the ramp and both rims.",
        "city_stats", "growth", "transit_share", tint_cat="population",
        legend=True))

    # 117 — dual axis traffic
    T.append(dual_axis(
        "Station Search 'visits' from 'site_traffic' as weekly slabs, with "
        "Email visits threaded over them on a loosened gauge (ember), full "
        "rims and weft.",
        "site_traffic", "week", "visits", "visits",
        transform=[["sift", "channel", "is", "Search"]]))
    # replace the line brood's data with the Email sift
    t = T[-1]
    prog = t["reference_program"]
    prog.insert(2, ["sift", {"ledger": "site_traffic", "vein": "channel",
                             "relation": "is", "value": "Email"}])
    for op, args in prog:
        if op == "sow" and args.get("form") == "wisp":
            args["ledger"] = "L2"
    for c in t["hidden_goal"]["checks"]:
        w = c.get("where", {})
        if w.get("form") == "wisp":
            w["data"]["transform"] = [["sift", "channel", "is", "Email"]]

    # 118 — org chart + hush + corral + flag
    T.append(diagram(
        "A southward org tree: 'VP Eng' → 'Platform', 'Product', 'Data'; "
        "'Platform' → 'SRE' and 'Dev Exp'. Corral SRE and Dev Exp as "
        "'Platform org', hush the Data capsule (open headcount), and flag "
        "'VP Eng' with 'interim'.",
        [("capsule", "VP Eng"), ("capsule", "Platform"),
         ("capsule", "Product"), ("capsule", "Data"), ("capsule", "SRE"),
         ("capsule", "Dev Exp")],
        [("VP Eng", "Platform"), ("VP Eng", "Product"), ("VP Eng", "Data"),
         ("Platform", "SRE"), ("Platform", "Dev Exp")],
        heading="south",
        corrals=[(["SRE", "Dev Exp"], "Platform org")],
        hush_nodes=["Data"],
        flags=[("VP Eng", "interim")]))

    # 119 — funnel bars + derived conversion + flags
    p = P()
    L = p.derive("hiring_funnel", "kept", "total_share", "candidates")
    cells = p.carve("p0", "rise", L, "stage",
                    ["Applicants", "Screen", "Interview", "Offer", "Hired"])
    b = p.sow("p0", L, "slab", key="stage")
    p.meter(b, "girth", "candidates")
    p.badge(b, vein="candidates", aim="east")
    f = p.pick(b, "stage", "is", "Screen")
    p.flag(f, "steepest drop after this stage")
    p.rim("p0", "west")
    p.entitle("p0", "Hiring funnel")
    T.append(task(
        "The hiring funnel sideways ('hiring_funnel', bar length from "
        "'candidates', one row per 'stage', candidate badges east, west "
        "rim, title), with a flag 'steepest drop after this stage' on the "
        "Screen bar.",
        p, [{"check": "brood", "weight": 6, "where": {
            "form": "slab", "meter": {"girth": "candidates"},
            "badge_vein": "candidates",
            "in": {"carved_by": "stage", "carve_along": "rise"}}},
            {"check": "annotation", "kind": "flag", "text_has": "drop",
             "near": {"where": {"stage": "Screen"}}},
            {"check": "guide", "kind": "rim", "side": "west"},
            {"check": "guide", "kind": "entitle"}],
        ["hiring_funnel"]))

    # 120 — two eras, two strands, kindle after
    p = P()
    checks = []
    for era, hue in [("before launch", "slate"), ("after launch", "ember")]:
        L = p.sift("monthly_finance", "era", "is", era)
        b = p.sow("p0", L, "wisp")
        p.meter(b, "stance", "period")
        p.meter(b, "perch", "revenue")
        s = p.thread(b, by="period")
        p.tint(b, hue)
        p.tint(s, hue)
        if era == "after launch":
            p.kindle(s)
        checks.append({"check": "brood", "weight": 4, "where": {
            "form": "wisp",
            "data": {"from": "monthly_finance",
                     "transform": [["sift", "era", "is", era]]},
            "meter": {"stance": "period", "perch": "revenue"},
            "threaded_by": "period"}})
    p.settle("p0", "strew")
    p.rim("p0", "south")
    p.rim("p0", "west")
    p.inscribe("launch", near=None)
    checks += [{"check": "guide", "kind": "rim", "side": "south"},
               {"check": "guide", "kind": "rim", "side": "west"},
               {"check": "annotation", "text_has": "launch"}]
    T.append(task(
        "Split 'monthly_finance' by 'era' into two strands on one ground — "
        "slate before launch, kindled ember after — over shared rims, with "
        "an inscription 'launch' marking the divide.",
        p, checks, ["monthly_finance"]))

    # 121 — architecture with bend routing
    p = P()
    p.settle("p0", "current", heading="east")
    for form, name in [("capsule", "Ingress"), ("capsule", "Auth"),
                       ("capsule", "App"), ("drum", "Sessions"),
                       ("drum", "Users DB")]:
        p.place("p0", form, name)
    c1 = p.tether("Ingress", "Auth")
    c2 = p.tether("Auth", "App")
    c3 = p.tether("Auth", "Sessions")
    p.crook(c3, "bend")
    c4 = p.tether("App", "Users DB")
    p.crook(c4, "bend")
    p.corral(["Sessions", "Users DB"], label="State")
    T.append(task(
        "An eastward auth flow: 'Ingress' → 'Auth' → 'App'; 'Auth' also "
        "bends a cord to drum 'Sessions' and 'App' bends one to drum "
        "'Users DB'. Corral the two drums as 'State'.",
        p, [{"check": "glyph", "named": "Auth", "form": "capsule"},
            {"check": "glyph", "named": "Sessions", "form": "drum"},
            {"check": "cord", "from": "Ingress", "to": "Auth"},
            {"check": "cord", "from": "Auth", "to": "App"},
            {"check": "cord", "from": "Auth", "to": "Sessions"},
            {"check": "cord", "from": "App", "to": "Users DB"},
            {"check": "corral", "contains_named": ["Sessions", "Users DB"],
             "label_has": "State"}],
        []))

    # 122 — polished report bar
    T.append(bar(
        "A report-ready chart from 'feature_usage': columns of 'users' per "
        "'feature' ranked waning, tinted by counted 'satisfaction' (ramp), "
        "value badges, key for the ramp, rims, weft, entitled 'Feature "
        "adoption vs satisfaction', noted 'Q3 product analytics'.",
        "feature_usage", "feature", "users", sort=("users", "waning"),
        tint_cat="satisfaction", legend=True, badge_vein="users",
        weft_rise=True, title="Feature adoption vs satisfaction",
        note="Q3 product analytics", law_check=False))

    # 123 — nested minis under two nodes
    p = P()
    p.settle("p0", "current", heading="east")
    p.place("p0", "capsule", "Gateway")
    p.place("p0", "capsule", "Orders")
    p.place("p0", "capsule", "Search")
    p.tether("Gateway", "Orders")
    p.tether("Gateway", "Search")
    for svc in ("Orders", "Search"):
        n = p.nest(host=svc, aim="south")
        L = p.sift("latency_profile", "service", "is", svc)
        b = p.sow(n, L, "slab")
        p.meter(b, "stature", "ms")
    T.append(task(
        "Gateway fans out to 'Orders' and 'Search' (eastward). Under each "
        "service, nest a parcel showing that service's 'latency_profile' "
        "rows as mini columns metered by 'ms'.",
        p, [{"check": "cord", "from": "Gateway", "to": "Orders"},
            {"check": "cord", "from": "Gateway", "to": "Search"},
            {"check": "brood", "weight": 5, "where": {
                "form": "slab",
                "data": {"from": "latency_profile",
                         "transform": [["sift", "service", "is", "Orders"]]},
                "meter": {"stature": "ms"},
                "in": {"nested_under": "Orders"}}},
            {"check": "brood", "weight": 5, "where": {
                "form": "slab",
                "data": {"from": "latency_profile",
                         "transform": [["sift", "service", "is", "Search"]]},
                "meter": {"stature": "ms"},
                "in": {"nested_under": "Search"}}}],
        ["latency_profile"]))

    # 124 — survey with dusk palette + inverted stack order note
    T.append(bar(
        "Stack 'survey_results' per 'topic' (tint by 'response') under the "
        "'dusk' palette with key, rims, weft and the title 'Sentiment by "
        "topic'.",
        "survey_results", "topic", "share", stacked=True,
        stack_tint="response", legend=True, weft_rise=True,
        palette="dusk", title="Sentiment by topic"))

    # 125 — dual axis pipeline (deals bars, value line)
    T.append(dual_axis(
        "From 'sales_pipeline', station 'deals' as slabs per 'phase' and "
        "thread 'value' over them on its own loosened gauge, full rims, "
        "weft, entitled 'Pipeline health'.",
        "sales_pipeline", "phase", "deals", "value",
        title="Pipeline health"))

    # 126 — comparative histograms, shared rise
    p = P()
    panels = p.split("p0", "span", 2)
    L1 = p.sift("experiment_results", "variant", "is", "Control")
    B1 = p.bin(L1, "conversion", 6)
    rows1 = apply_transform("experiment_results",
                            [["sift", "variant", "is", "Control"],
                             ["bin", "conversion", 6]])
    c1 = p.carve(panels[0], "span", B1, "bin",
                 levels_from_rows(rows1, "bin"), gap=0.06)
    b1 = p.sow(panels[0], B1, "slab", key="bin")
    p.meter(b1, "stature", "tally")
    p.rim(panels[0], "west")
    p.entitle(panels[0], "Control")
    L2 = p.sift("experiment_results", "variant", "is", "Variant B")
    B2 = p.bin(L2, "conversion", 6)
    rows2 = apply_transform("experiment_results",
                            [["sift", "variant", "is", "Variant B"],
                             ["bin", "conversion", 6]])
    c2 = p.carve(panels[1], "span", B2, "bin",
                 levels_from_rows(rows2, "bin"), gap=0.06)
    b2 = p.sow(panels[1], B2, "slab", key="bin")
    p.meter(b2, "stature", "tally")
    p.rim(panels[1], "west")
    p.entitle(panels[1], "Variant B")
    p.share(panels[0], panels[1], "stature")
    T.append(task(
        "Compare conversion distributions: two panels, each binning "
        "'conversion' (about 6 bins) for one variant of "
        "'experiment_results' — Control left, Variant B right — with the "
        "stature gauge shared, west rims, and per-panel titles.",
        p, [{"check": "parcel", "where": {"split_count": 2},
             "label": "two panels"},
            {"check": "brood", "weight": 4, "where": {
                "form": "slab",
                "data": {"from": "experiment_results",
                         "transform": [["sift", "variant", "is", "Control"],
                                       ["bin", "conversion", 6]]},
                "meter": {"stature": "tally"}, "in": {"carved_by": "bin"}}},
            {"check": "brood", "weight": 4, "where": {
                "form": "slab",
                "data": {"from": "experiment_results",
                         "transform": [["sift", "variant", "is",
                                        "Variant B"],
                                       ["bin", "conversion", 6]]},
                "meter": {"stature": "tally"}, "in": {"carved_by": "bin"}}},
            {"check": "share_or_abut"}],
        ["experiment_results"]))

    # 127 — donut + kindled wedge + center total + key
    p = P()
    L = p.distill("site_traffic", "channel", "sum", "visits")
    p.hoop("p0", inner=0.58)
    b = p.sow("p0", L, "slab")
    p.meter(b, "girth", "visits")
    p.meter(b, "tint", "channel")
    p.key("p0", b, "tint")
    f = p.pick(b, "channel", "is", "Search")
    p.kindle(f)
    p.inscribe("12 weeks of traffic")
    p.entitle("p0", "Visits by channel")
    T.append(task(
        "An open ring of total 'visits' per 'channel' from 'site_traffic' "
        "(distill first), tinted with a key, the Search wedge kindled, "
        "'12 weeks of traffic' inscribed, entitled 'Visits by channel'.",
        p, [{"check": "brood", "weight": 6, "where": {
            "form": "slab",
            "data": {"from": "site_traffic",
                     "transform": [["distill", "channel", "visits", "sum"]]},
            "meter": {"girth": "visits", "tint": "channel"},
            "in": {"hooped": True, "inner_min": 0.4}}},
            {"check": "guide", "kind": "key", "trait": "tint"},
            {"check": "emphasis", "mode": "kindle", "exclusive": True,
             "target": {"where": {"channel": "Search"}}},
            {"check": "annotation", "text_has": "traffic"},
            {"check": "guide", "kind": "entitle"}],
        ["site_traffic"]))

    # 128 — grouped, era-aware finance columns
    T.append(bar(
        "Keep the 'after launch' era of 'monthly_finance' and chart "
        "'revenue' per 'period' as columns with rims and weft; kindle M24 "
        "and flag it 'record'.",
        "monthly_finance", "period", "revenue",
        transform=[["sift", "era", "is", "after launch"]],
        weft_rise=True, kindle_where={"period": "M24"},
        annotate=("record", {"period": "M24"}, "flag")))

    # 129 — model leaderboard, ramp tint, sorted
    T.append(bar(
        "A leaderboard from 'model_evals': mean 'score' per 'model', "
        "sorted waning, tinted by the counted score itself (ramp), value "
        "badges, rims, entitled 'Overall standings'.",
        "model_evals", "model", "score",
        transform=[["distill", "model", "score", "mean"]],
        sort=("score", "waning"), tint_cat="score", badge_vein="score",
        title="Overall standings", law_check=False))

    # 130 — retention: plain pie after long gap
    T.append(pie(
        "Hoop 'final_month_mix': each 'product' takes an angular share of "
        "'revenue', tinted, rim-badged, entitled 'Final month mix'.",
        "final_month_mix", "product", "revenue",
        title="Final month mix"))

    # 131 — traffic dashboard: stacked + line panel
    p = P()
    panels = p.split("p0", "rise", 2)
    L = p.sift("site_traffic", "week", "among",
               ["W07", "W08", "W09", "W10", "W11", "W12"])
    cells = p.carve(panels[0], "span", L, "week",
                    ["W07", "W08", "W09", "W10", "W11", "W12"])
    b1 = p.sow(panels[0], L, "slab", key="week")
    p.meter(b1, "stature", "visits")
    p.meter(b1, "tint", "channel")
    p.settle(panels[0], "heap")
    p.key(panels[0], b1, "tint")
    p.rim(panels[0], "west")
    p.entitle(panels[0], "Stacked visits")
    L2 = p.sift("site_traffic", "channel", "is", "Search")
    b2 = p.sow(panels[1], L2, "wisp")
    p.meter(b2, "stance", "week")
    p.meter(b2, "perch", "visits")
    p.settle(panels[1], "strew")
    p.thread(b2, by="week")
    p.rim(panels[1], "south")
    p.rim(panels[1], "west")
    p.entitle(panels[1], "Search trend")
    T.append(task(
        "A small traffic dashboard from 'site_traffic': top panel stacks "
        "weekly 'visits' (weeks W07–W12) by channel with key and west rim; "
        "bottom panel threads the Search channel across all weeks with "
        "rims. Entitle both panels.",
        p, [{"check": "parcel", "where": {"split_count": 2,
                                          "split_along": "rise"},
             "label": "two stacked panels"},
            {"check": "brood", "weight": 5, "where": {
                "form": "slab",
                "data": {"from": "site_traffic",
                         "transform": [["sift", "week", "among",
                                        ["W07", "W08", "W09", "W10", "W11",
                                         "W12"]]]},
                "meter": {"stature": "visits", "tint": "channel"},
                "in": {"carved_by": "week", "law": "heap"}}},
            {"check": "brood", "weight": 5, "where": {
                "form": "wisp",
                "data": {"from": "site_traffic",
                         "transform": [["sift", "channel", "is", "Search"]]},
                "meter": {"stance": "week", "perch": "visits"},
                "threaded_by": "week"}},
            {"check": "guide", "kind": "key", "trait": "tint"}],
        ["site_traffic"]))

    # 132 — architecture, 8 nodes, 2 corrals, kindled path
    T.append(diagram(
        "A fuller platform, eastward: 'Users' → 'CDN' → 'Gateway'; Gateway "
        "→ 'Payments', 'Orders', 'Search'; Payments and Orders each tether "
        "to drum 'Ledger DB'; Search tethers to drum 'Index'. Corral the "
        "three services as 'Core', the two drums as 'Storage'. Kindle the "
        "cords Users→CDN, CDN→Gateway and Gateway→Payments, plus the "
        "Payments capsule.",
        [("capsule", "Users"), ("capsule", "CDN"), ("capsule", "Gateway"),
         ("capsule", "Payments"), ("capsule", "Orders"),
         ("capsule", "Search"), ("drum", "Ledger DB"), ("drum", "Index")],
        [("Users", "CDN"), ("CDN", "Gateway"), ("Gateway", "Payments"),
         ("Gateway", "Orders"), ("Gateway", "Search"),
         ("Payments", "Ledger DB"), ("Orders", "Ledger DB"),
         ("Search", "Index")],
        corrals=[(["Payments", "Orders", "Search"], "Core"),
                 (["Ledger DB", "Index"], "Storage")],
        kindle_cords=[("Users", "CDN"), ("CDN", "Gateway"),
                      ("Gateway", "Payments")],
        kindle_nodes=["Payments"]))

    # 133 — age pyramid-ish inverted horizontal
    p = P()
    cells = p.carve("p0", "rise", "age_distribution", "age_band",
                    ["0-9", "10-19", "20-29", "30-39", "40-49", "50-59",
                     "60-69", "70+"])
    b = p.sow("p0", "age_distribution", "slab", key="age_band")
    p.meter(b, "girth", "population")
    p.invert("p0", "rise")
    p.badge(b, vein="population", aim="east")
    p.rim("p0", "west")
    p.entitle("p0", "Population by age")
    T.append(task(
        "Lay 'age_distribution' as horizontal bars per 'age_band' with the "
        "rise inverted so the youngest band sits at the bottom, values "
        "badged east, west rim, entitled 'Population by age'.",
        p, [{"check": "brood", "weight": 5, "where": {
            "form": "slab", "meter": {"girth": "population"},
            "badge_vein": "population",
            "in": {"carved_by": "age_band", "carve_along": "rise"}}},
            {"check": "parcel", "where": {"inverted": "rise"},
             "label": "rise inverted"},
            {"check": "guide", "kind": "rim", "side": "west"}],
        ["age_distribution"]))

    # 134 — margin line + rebased floor + era flag
    T.append(line(
        "Thread 'margin' over 'period' from 'monthly_finance' with rims and "
        "weft; flag M13 'launch effect'.",
        "monthly_finance", "period", "margin",
        annotate=("launch effect", {"period": "M13"}, "flag")))

    # 135 — dual axis: funnel counts + days
    T.append(dual_axis(
        "Station 'hiring_funnel' 'candidates' as slabs per 'stage' with "
        "'median_days' threaded over them on a loosened ember gauge; full "
        "rims, entitled 'Volume vs dwell time'.",
        "hiring_funnel", "stage", "candidates", "median_days",
        title="Volume vs dwell time"))

    # 136 — scatter + corral-free annotation composite
    T.append(scatter(
        "Scatter 'feature_usage' ('users' across, 'satisfaction' up) with "
        "discs sized by 'users', feature badges, rims; kindle Sharing and "
        "flag it 'small but loved'.",
        "feature_usage", "users", "satisfaction", bulk="users",
        badge_vein="feature", kindle_where={"feature": "Sharing"},
        annotate=("small but loved", {"feature": "Sharing"}, "flag")))

    # 137 — three-panel small multiples
    p = P()
    panels = p.split("p0", "span", 3)
    for i, region in enumerate(["Europe", "Americas", "Asia"]):
        L = p.sift("quarterly_revenue", "region", "is", region)
        L2 = p.distill(L, "quarter", "sum", "revenue")
        cells = p.carve(panels[i], "span", L2, "quarter",
                        ["Q1", "Q2", "Q3", "Q4"])
        b = p.sow(panels[i], L2, "slab", key="quarter")
        p.meter(b, "stature", "revenue")
        p.rim(panels[i], "south")
        p.entitle(panels[i], region)
    p.share(panels[0], panels[1], "stature")
    p.share(panels[1], panels[2], "stature")
    T.append(task(
        "Small multiples of 'quarterly_revenue': three panels (Europe, "
        "Americas, Asia), each with quarterly total revenue columns, south "
        "rims, shared stature gauges across all three, and a region title "
        "per panel.",
        p, [{"check": "parcel", "where": {"split_count": 3},
             "label": "three panels"},
            {"check": "brood", "weight": 3, "where": {
                "form": "slab",
                "data": {"from": "quarterly_revenue",
                         "transform": [["sift", "region", "is", "Europe"],
                                       ["distill", "quarter", "revenue",
                                        "sum"]]},
                "meter": {"stature": "revenue"},
                "in": {"carved_by": "quarter"}}},
            {"check": "brood", "weight": 3, "where": {
                "form": "slab",
                "data": {"from": "quarterly_revenue",
                         "transform": [["sift", "region", "is", "Americas"],
                                       ["distill", "quarter", "revenue",
                                        "sum"]]},
                "meter": {"stature": "revenue"}}},
            {"check": "brood", "weight": 3, "where": {
                "form": "slab",
                "data": {"from": "quarterly_revenue",
                         "transform": [["sift", "region", "is", "Asia"],
                                       ["distill", "quarter", "revenue",
                                        "sum"]]},
                "meter": {"stature": "revenue"}}},
            {"check": "share_or_abut"}],
        ["quarterly_revenue"]))

    # 138 — heavy heft chain
    p = P()
    p.settle("p0", "current", heading="east")
    for name in ("Source", "Filter", "Sink"):
        p.place("p0", "capsule", name)
    c1 = p.tether("Source", "Filter")
    c2 = p.tether("Filter", "Sink")
    p.heft(c1, 0.9)
    p.heft(c2, 0.35)
    p.badge(c1, text="9.2k msg/s")
    p.badge(c2, text="3.1k msg/s")
    T.append(task(
        "A throughput sketch flowing east: 'Source' → 'Filter' → 'Sink', "
        "the first cord notably heavier than the second, badged "
        "'9.2k msg/s' and '3.1k msg/s' respectively.",
        p, [{"check": "glyph", "named": "Filter"},
            {"check": "cord", "from": "Source", "to": "Filter",
             "badge_has": "9.2k"},
            {"check": "cord", "from": "Filter", "to": "Sink",
             "badge_has": "3.1k"}],
        []))

    # 139 — polished multi-line with kindle + labels
    T.append(multi_line(
        "A polished comparison of all three 'experiment_results' variants "
        "over 'day' (Control slate, Variant B ember, Variant C moss), "
        "labels inscribed at D14, Variant B kindled, rims, weft, entitled "
        "'Conversion uplift'.",
        "experiment_results", "day", "conversion", "variant",
        [("Control", "slate"), ("Variant B", "ember"),
         ("Variant C", "moss")],
        label_at="D14", kindle_series="Variant B",
        title="Conversion uplift"))

    # 140 — retention: heap after gap
    T.append(bar(
        "Pile the 'Open offices' responses of 'survey_results' into a "
        "single tinted column (heap by 'response') with a key and west "
        "rim.",
        "survey_results", "response", "share",
        transform=[["sift", "topic", "is", "Open offices"]],
        stacked=True, stack_tint="response", legend=True, rims=("west",)))

    # 141 — city dumbbell-ish: two metrics strewn
    p = P()
    L = p.sift("city_stats", "continent", "is", "Europe")
    b1 = p.sow("p0", L, "disc")
    p.meter(b1, "stance", "city")
    p.meter(b1, "perch", "transit_share")
    L2 = p.sift("city_stats", "continent", "is", "Asia")
    b2 = p.sow("p0", L2, "ring")
    p.meter(b2, "stance", "city")
    p.meter(b2, "perch", "transit_share")
    p.settle("p0", "strew")
    p.tint(b1, "tide")
    p.tint(b2, "ember")
    p.rim("p0", "south")
    p.rim("p0", "west")
    p.entitle("p0", "Transit share, Europe vs Asia")
    T.append(task(
        "Station European cities of 'city_stats' as tide discs and Asian "
        "cities as ember rings, both by 'city' across the span and "
        "'transit_share' up the rise, rims and title.",
        p, [{"check": "brood", "weight": 4, "where": {
            "form": "disc",
            "data": {"from": "city_stats",
                     "transform": [["sift", "continent", "is", "Europe"]]},
            "meter": {"stance": "city", "perch": "transit_share"}}},
            {"check": "brood", "weight": 4, "where": {
                "form": "ring",
                "data": {"from": "city_stats",
                         "transform": [["sift", "continent", "is", "Asia"]]},
                "meter": {"stance": "city", "perch": "transit_share"}}},
            {"check": "guide", "kind": "rim", "side": "south"}],
        ["city_stats"]))

    # 142 — deployment map with plaque + bends
    T.append(diagram(
        "A release train eastward: 'Trunk' → 'Nightly' → 'Beta' → 'Stable', "
        "with a plaque 'weekly cadence' alongside, the Beta→Stable cord "
        "badged 'signed', and the Stable capsule kindled.",
        [("capsule", "Trunk"), ("capsule", "Nightly"), ("capsule", "Beta"),
         ("capsule", "Stable"), ("plaque", "weekly cadence")],
        [("Trunk", "Nightly"), ("Nightly", "Beta"),
         ("Beta", "Stable", "signed")],
        kindle_nodes=["Stable"]))

    # 143 — dual-metric latency chart
    p = P()
    cells = p.carve("p0", "span", "service_latency", "service",
                    ["Gateway", "Payments", "Orders", "Search", "Profiles"])
    b1 = p.sow("p0", "service_latency", "slab", key="service")
    p.meter(b1, "stature", "p50")
    b2 = p.sow("p0", "service_latency", "slab", key="service")
    p.meter(b2, "stature", "p99")
    p.veil(b2, 0.45)
    p.rim("p0", "south")
    p.rim("p0", "west")
    p.weft("p0", "rise")
    p.entitle("p0", "p50 vs p99 by service")
    T.append(task(
        "Per 'service' of 'service_latency', place two slabs side by side: "
        "solid 'p50' and a second 'p99' slab veiled to about half opacity. "
        "Rims, weft, entitled 'p50 vs p99 by service'.",
        p, [{"check": "brood", "weight": 4, "where": {
            "form": "slab", "meter": {"stature": "p50"},
            "in": {"carved_by": "service"}}},
            {"check": "brood", "weight": 4, "where": {
                "form": "slab", "meter": {"stature": "p99"},
                "in": {"carved_by": "service"}}},
            {"check": "guide", "kind": "rim", "side": "south"},
            {"check": "guide", "kind": "rim", "side": "west"},
            {"check": "guide", "kind": "entitle"}],
        ["service_latency"]))

    # 144 — donut pair via split
    p = P()
    panels = p.split("p0", "span", 2)
    for i, (topic, title) in enumerate([("Remote work", "Remote work"),
                                        ("Open offices", "Open offices")]):
        L = p.sift("survey_results", "topic", "is", topic)
        p.hoop(panels[i], inner=0.5)
        b = p.sow(panels[i], L, "slab")
        p.meter(b, "girth", "share")
        p.meter(b, "tint", "response")
        p.entitle(panels[i], title)
    p.key("p0", "b2", "tint")
    T.append(task(
        "Two open rings side by side from 'survey_results': response shares "
        "for 'Remote work' (left) and 'Open offices' (right), tinted by "
        "'response' with one key for both, panel titles.",
        p, [{"check": "parcel", "where": {"split_count": 2},
             "label": "two panels"},
            {"check": "brood", "weight": 4, "where": {
                "form": "slab",
                "data": {"from": "survey_results",
                         "transform": [["sift", "topic", "is",
                                        "Remote work"]]},
                "meter": {"girth": "share", "tint": "response"},
                "in": {"hooped": True}}},
            {"check": "brood", "weight": 4, "where": {
                "form": "slab",
                "data": {"from": "survey_results",
                         "transform": [["sift", "topic", "is",
                                        "Open offices"]]},
                "meter": {"girth": "share", "tint": "response"},
                "in": {"hooped": True}}},
            {"check": "guide", "kind": "key", "trait": "tint"}],
        ["survey_results"]))

    # 145 — annotated growth line with derived diff
    T.append(line(
        "Derive monthly profit proxy in 'monthly_finance' — 'revenue' minus "
        "'margin', name it 'net' — and thread it over 'period' with rims "
        "and weft, flagging M24 'best month'.",
        "monthly_finance", "period", "net",
        transform=[["derive", "net", "diff", "revenue", "margin"]],
        annotate=("best month", {"period": "M24"}, "flag")))

    # 146 — corral + nested mini + kindle (composition first)
    p = P()
    p.settle("p0", "current", heading="east")
    p.place("p0", "capsule", "Edge")
    p.place("p0", "capsule", "Payments")
    p.place("p0", "capsule", "Profiles")
    p.tether("Edge", "Payments")
    p.tether("Edge", "Profiles")
    p.corral(["Payments", "Profiles"], label="Services")
    n = p.nest(host="Payments", aim="south")
    L = p.sift("latency_profile", "service", "is", "Payments")
    b = p.sow(n, L, "slab")
    p.meter(b, "stature", "ms")
    p.kindle("Payments")
    T.append(task(
        "Eastward: 'Edge' fans to 'Payments' and 'Profiles'; corral the two "
        "services as 'Services'; kindle Payments and nest its "
        "'latency_profile' rows beneath it as mini 'ms' columns.",
        p, [{"check": "cord", "from": "Edge", "to": "Payments"},
            {"check": "corral", "contains_named": ["Payments", "Profiles"],
             "label_has": "Services"},
            {"check": "emphasis", "mode": "kindle",
             "target": {"named": "Payments"}},
            {"check": "brood", "weight": 5, "where": {
                "form": "slab", "meter": {"stature": "ms"},
                "in": {"nested_under": "Payments"}}}],
        ["latency_profile"]))

    # 147 — wide dual-axis, kindled era
    T.append(dual_axis(
        "The full 24 months of 'monthly_finance': 'revenue' slabs by "
        "'period', 'margin' threaded on a loosened ember gauge, rims on "
        "all three sides, weft, kindle the after-launch slabs (era), and "
        "entitle it 'Two years of growth'.",
        "monthly_finance", "period", "revenue", "margin",
        kindle_bar_where={"era": "after launch"},
        title="Two years of growth"))

    # 148 — sorted stacked (marshal + heap)
    T.append(bar(
        "Stack weekly 'visits' by channel from 'site_traffic' for weeks "
        "W01–W04 ('among'), tint by 'channel', key, rims; pile order "
        "follows the ledger, so first marshal rows by 'visits' waning so "
        "big channels sit at the bottom of each pile.",
        "site_traffic", "week", "visits",
        transform=[["sift", "week", "among", ["W01", "W02", "W03", "W04"]],
                   ["marshal", "visits", "waning"]],
        stacked=True, stack_tint="channel", legend=True))

    # 149 — bulk + ramp + annotations (dense scatter)
    T.append(scatter(
        "A dense reading of 'city_stats': stance 'population', perch "
        "'growth', bulk 'population', ramp tint by 'transit_share', rims, "
        "entitled 'Growth vs size'; flag Austin 'fastest growth'.",
        "city_stats", "population", "growth", bulk="population",
        tint_cat="transit_share", title="Growth vs size",
        annotate=("fastest growth", {"city": "Austin"}, "flag")))

    # 150 — retention: flowchart after gap, with all trimmings
    T.append(diagram(
        "A payment flow east: 'Cart' → 'Checkout' → rhomb '3DS?' → 'Bank "
        "page' (badge 'yes') and 'Capture' (badge 'no'); 'Bank page' → "
        "'Capture' → 'Receipt'. Kindle the no-3DS path cords ('3DS?' → "
        "Capture and Capture → Receipt) and entitle it 'Checkout paths'.",
        [("capsule", "Cart"), ("capsule", "Checkout"), ("rhomb", "3DS?"),
         ("capsule", "Bank page"), ("capsule", "Capture"),
         ("capsule", "Receipt")],
        [("Cart", "Checkout"), ("Checkout", "3DS?"),
         ("3DS?", "Bank page", "yes"), ("3DS?", "Capture", "no"),
         ("Bank page", "Capture"), ("Capture", "Receipt")],
        kindle_cords=[("3DS?", "Capture"), ("Capture", "Receipt")],
        title="Checkout paths"))

    # 151-160: consolidation composites reusing stage-4 machinery
    T.append(dual_axis(
        "Model quality vs coverage from 'model_evals': mean 'score' slabs "
        "per 'model' with the Recall benchmark's scores threaded over on a "
        "loosened gauge; rims all around.",
        "model_evals", "model", "score", "score",
        transform=[["distill", "model", "score", "mean"]]))
    t = T[-1]
    prog = t["reference_program"]
    prog.insert(1, ["sift", {"ledger": "model_evals", "vein": "benchmark",
                             "relation": "is", "value": "Recall"}])
    for op, args in prog:
        if op == "sow" and args.get("form") == "wisp":
            args["ledger"] = "L2"
    for c in t["hidden_goal"]["checks"]:
        w = c.get("where", {})
        if w.get("form") == "wisp":
            w["data"]["transform"] = [["sift", "benchmark", "is", "Recall"]]

    T.append(bar(
        "Group 'engineers' per 'team' by project from 'team_allocation' "
        "(tint per 'project', key, rims, weft) and kindle Product-Beacon; "
        "flag it 'biggest bet'.",
        "team_allocation", "team", "engineers", tint_cat="project",
        legend=True, weft_rise=True,
        kindle_where={"team": "Product", "project": "Beacon"},
        annotate=("biggest bet", {"team": "Product", "project": "Beacon"},
                  "flag")))

    p = P()
    panels = p.split("p0", "span", 2)
    p.settle(panels[0], "current", heading="south")
    for form, name in [("capsule", "Order"), ("capsule", "Pack"),
                       ("capsule", "Ship")]:
        p.place(panels[0], form, name)
    p.tether("Order", "Pack")
    p.tether("Pack", "Ship")
    p.entitle(panels[0], "Fulfilment")
    L = p.distill("sales_pipeline", "phase", "sum", "value")
    cells = p.carve(panels[1], "span", L, "phase",
                    ["Lead", "Qualified", "Proposal", "Negotiation", "Won"])
    b = p.sow(panels[1], L, "slab", key="phase")
    p.meter(b, "stature", "value")
    p.rim(panels[1], "west")
    p.entitle(panels[1], "Pipeline value")
    T.append(task(
        "Mix grammars in two panels: left, a southward three-step flow "
        "'Order' → 'Pack' → 'Ship'; right, columns of 'value' per 'phase' "
        "from 'sales_pipeline' with a west rim. Entitle both panels.",
        p, [{"check": "parcel", "where": {"split_count": 2},
             "label": "two panels"},
            {"check": "cord", "from": "Order", "to": "Pack"},
            {"check": "cord", "from": "Pack", "to": "Ship"},
            {"check": "brood", "weight": 4, "where": {
                "form": "slab", "meter": {"stature": "value"},
                "in": {"carved_by": "phase", "in_split_panel": True}}}],
        ["sales_pipeline"]))

    T.append(multi_line(
        "Thread Direct and Email 'visits' from 'site_traffic' over 'week' "
        "(Direct moss, Email plum), labels at W12, weft and rims, entitled "
        "'The quiet channels'.",
        "site_traffic", "week", "visits", "channel",
        [("Direct", "moss"), ("Email", "plum")],
        label_at="W12", title="The quiet channels"))

    T.append(bar(
        "Total 'revenue' per 'region' from 'quarterly_revenue' as columns "
        "sorted waning with value badges, ramp tint by revenue, rims, "
        "entitled 'Regional totals'.",
        "quarterly_revenue", "region", "revenue",
        transform=[["distill", "region", "revenue", "sum"]],
        sort=("revenue", "waning"), tint_cat="revenue",
        badge_vein="revenue", title="Regional totals", law_check=False))

    # 156 — nested minis under all three services
    p = P()
    p.settle("p0", "current", heading="east")
    p.place("p0", "capsule", "Gateway")
    for svc in ("Payments", "Orders", "Profiles"):
        p.place("p0", "capsule", svc)
        p.tether("Gateway", svc)
    for svc in ("Payments", "Orders", "Profiles"):
        n = p.nest(host=svc, aim="south")
        L = p.sift("latency_profile", "service", "is", svc)
        b = p.sow(n, L, "slab")
        p.meter(b, "stature", "ms")
    checks = [{"check": "cord", "from": "Gateway", "to": s}
              for s in ("Payments", "Orders", "Profiles")]
    for svc in ("Payments", "Orders", "Profiles"):
        checks.append({"check": "brood", "weight": 4, "where": {
            "form": "slab",
            "data": {"from": "latency_profile",
                     "transform": [["sift", "service", "is", svc]]},
            "meter": {"stature": "ms"}, "in": {"nested_under": svc}}})
    T.append(task(
        "Gateway fans east to 'Payments', 'Orders' and 'Profiles'; under "
        "each, nest that service's 'latency_profile' rows as mini 'ms' "
        "columns.",
        p, checks, ["latency_profile"]))

    T.append(pie(
        "Hoop the Won-phase share of pipeline: derive each phase's "
        "percentage of total 'value' in 'sales_pipeline' as 'pct', ring it "
        "(inner about 0.5) tinted by 'phase' with a key, and kindle the "
        "Won wedge.",
        "sales_pipeline", "phase", "pct",
        transform=[["derive", "pct", "total_share", "value"]],
        inner=0.5, badge_cat=False, legend=True,
        kindle_where={"phase": "Won"}))

    T.append(histogram(
        "Bin the 24 monthly 'revenue' values of 'monthly_finance' into "
        "about 6 bins with rims and weft, entitled 'Revenue distribution'.",
        "monthly_finance", "revenue", bins=6,
        title="Revenue distribution"))

    T.append(diagram(
        "An ETL map east: drums 'App events' and 'Billing' both tether to "
        "capsule 'Collector'; 'Collector' → 'Cleaner' → drum 'Lake'; corral "
        "Collector and Cleaner as 'Pipeline'; flag 'Lake' with 'S3-backed'.",
        [("drum", "App events"), ("drum", "Billing"),
         ("capsule", "Collector"), ("capsule", "Cleaner"), ("drum", "Lake")],
        [("App events", "Collector"), ("Billing", "Collector"),
         ("Collector", "Cleaner"), ("Cleaner", "Lake")],
        corrals=[(["Collector", "Cleaner"], "Pipeline")],
        flags=[("Lake", "S3-backed")]))

    T.append(dual_axis(
        "From 'experiment_results' sifted to Variant B: 'conversion' slabs "
        "per 'day' with Control conversion threaded over on a loosened "
        "slate gauge; rims all around, entitled 'B vs control'.",
        "experiment_results", "day", "conversion", "conversion",
        transform=[["sift", "variant", "is", "Variant B"]],
        line_hue="slate", title="B vs control"))
    t = T[-1]
    prog = t["reference_program"]
    prog.insert(2, ["sift", {"ledger": "experiment_results",
                             "vein": "variant", "relation": "is",
                             "value": "Control"}])
    for op, args in prog:
        if op == "sow" and args.get("form") == "wisp":
            args["ledger"] = "L2"
    for c in t["hidden_goal"]["checks"]:
        w = c.get("where", {})
        if w.get("form") == "wisp":
            w["data"]["transform"] = [["sift", "variant", "is", "Control"]]

    assert len(T) == 50, len(T)
    return T
