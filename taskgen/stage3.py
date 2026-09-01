"""Stage 3 (tasks 61-110): medium compositions, 4-8 concepts.
New here: corral, split panels, share, derive, veil, plaque, palette,
invert, rebase, multi-series strands, strewn bars."""

from glyphbench.datasets import DATASETS

from .builders import P, task, bar, pie, line, scatter, histogram, diagram


def multi_line(instruction, ds, x, y, series_vein, series, ds_list=None,
               rims=("south", "west"), weft_rise=True, title=None,
               kindle_series=None, hush_others=False, label_at=None):
    """One brood + strand per series, fixed hue each, inscribed labels."""
    p = P()
    checks = []
    for value, hue in series:
        L = p.sift(ds, series_vein, "is", value)
        b = p.sow("p0", L, "wisp")
        p.meter(b, "stance", x)
        p.meter(b, "perch", y)
        s = p.thread(b, by=x)
        p.tint(b, hue)
        p.tint(s, hue)
        if label_at:
            f = p.pick(b, x, "is", label_at)
            p.inscribe(value, near=f, aim="east")
        if kindle_series == value:
            p.kindle(s)
            p.kindle(b)
        elif hush_others and kindle_series:
            p.hush(b)
            p.hush(s)
        where = {"form": "wisp",
                 "data": {"from": ds,
                          "transform": [["sift", series_vein, "is", value]]},
                 "meter": {"stance": x, "perch": y}, "threaded_by": x,
                 "in": {"law": "strew"}}
        checks.append({"check": "brood", "where": where, "weight": 4})
        if label_at:
            checks.append({"check": "annotation", "text_has": value,
                           "near": {"where": {series_vein: value}}})
        if kindle_series == value:
            checks.append({"check": "emphasis", "mode": "kindle",
                           "target": {"where": {series_vein: value}}})
    p.settle("p0", "strew")
    if weft_rise:
        p.weft("p0", "rise")
    for side in rims or []:
        p.rim("p0", side)
        checks.append({"check": "guide", "kind": "rim", "side": side})
    if title:
        p.entitle("p0", title)
        checks.append({"check": "guide", "kind": "entitle"})
    return task(instruction, p, checks, [ds])


def build():
    T = []

    # 61 — first architecture with corral
    T.append(diagram(
        "Architecture, flowing east: capsule 'Users' → capsule 'Gateway' → "
        "three service capsules 'Payments', 'Orders', 'Search'. Corral the "
        "three services under the label 'Core'. Entitle it 'Platform'.",
        [("capsule", "Users"), ("capsule", "Gateway"), ("capsule", "Payments"),
         ("capsule", "Orders"), ("capsule", "Search")],
        [("Users", "Gateway"), ("Gateway", "Payments"), ("Gateway", "Orders"),
         ("Gateway", "Search")],
        corrals=[(["Payments", "Orders", "Search"], "Core")],
        title="Platform"))

    # 62 — multi-series line
    T.append(multi_line(
        "Thread all three variants of 'experiment_results' ('conversion' "
        "over 'day') as separate strands: Control in slate, Variant B in "
        "ember, Variant C in tide. Inscribe each variant's name at its final "
        "point (D14). Rims and weft.",
        "experiment_results", "day", "conversion", "variant",
        [("Control", "slate"), ("Variant B", "ember"), ("Variant C", "tide")],
        label_at="D14"))

    # 63 — stacked with sift + title
    T.append(bar(
        "For product 'Aria' only, stack 'revenue' per 'quarter' by region "
        "(tint per 'region') from 'quarterly_revenue', with key, rims, and "
        "the title 'Aria revenue by region'.",
        "quarterly_revenue", "quarter", "revenue",
        transform=[["sift", "product", "is", "Aria"]],
        stacked=True, stack_tint="region", legend=True,
        title="Aria revenue by region"))

    # 64 — annotated timeline with hush
    p = P()
    b = p.sow("p0", "milestones", "disc")
    p.meter(b, "stance", "week")
    p.meter(b, "bulk", "impact")
    p.settle("p0", "strew")
    p.thread(b, by="week")
    p.badge(b, vein="milestone", aim="north")
    f1 = p.pick(b, "milestone", "is", "Launch")
    p.flag(f1, "go-live")
    f2 = p.pick(b, "milestone", "is", "Retrospective")
    p.hush(f2)
    p.rim("p0", "south")
    p.entitle("p0", "Project timeline")
    T.append(task(
        "An annotated timeline of 'milestones': discs stationed by 'week', "
        "sized by 'impact', badged with milestone names, threaded in order. "
        "Flag Launch as 'go-live', hush the Retrospective point, south rim, "
        "title 'Project timeline'.",
        p, [{"check": "brood", "weight": 6, "where": {
            "form": "disc", "data": {"from": "milestones", "transform": []},
            "meter": {"stance": "week", "bulk": "impact"},
            "threaded_by": "week", "badge_vein": "milestone",
            "in": {"law": "strew"}}},
            {"check": "annotation", "kind": "flag", "text_has": "go-live",
             "near": {"where": {"milestone": "Launch"}}},
            {"check": "emphasis", "mode": "hush",
             "target": {"where": {"milestone": "Retrospective"}}},
            {"check": "guide", "kind": "rim", "side": "south"},
            {"check": "guide", "kind": "entitle"}],
        ["milestones"]))

    # 65 — split panels: bar | line
    p = P()
    panels = p.split("p0", "span", 2)
    L = p.distill("quarterly_revenue", "quarter", "sum", "revenue")
    cells = p.carve(panels[0], "span", L, "quarter", ["Q1", "Q2", "Q3", "Q4"])
    b1 = p.sow(panels[0], L, "slab", key="quarter")
    p.meter(b1, "stature", "revenue")
    p.rim(panels[0], "south")
    p.rim(panels[0], "west")
    p.entitle(panels[0], "Quarterly total")
    b2 = p.sow(panels[1], "monthly_finance", "wisp")
    p.meter(b2, "stance", "period")
    p.meter(b2, "perch", "revenue")
    p.settle(panels[1], "strew")
    p.thread(b2, by="period")
    p.rim(panels[1], "south")
    p.rim(panels[1], "west")
    p.entitle(panels[1], "Monthly trend")
    T.append(task(
        "Split the ground into two side-by-side panels. Left: quarterly "
        "total 'revenue' columns from 'quarterly_revenue', entitled "
        "'Quarterly total'. Right: 'revenue' threaded over 'period' from "
        "'monthly_finance', entitled 'Monthly trend'. Rims on both.",
        p, [{"check": "parcel", "label": "two panels",
             "where": {"split_count": 2, "split_along": "span"}},
            {"check": "brood", "weight": 5, "where": {
                "form": "slab",
                "data": {"from": "quarterly_revenue",
                         "transform": [["distill", "quarter", "revenue",
                                        "sum"]]},
                "meter": {"stature": "revenue"},
                "in": {"carved_by": "quarter", "in_split_panel": True}}},
            {"check": "brood", "weight": 5, "where": {
                "form": "wisp",
                "data": {"from": "monthly_finance", "transform": []},
                "meter": {"stance": "period", "perch": "revenue"},
                "threaded_by": "period",
                "in": {"law": "strew", "in_split_panel": True}}}],
        ["quarterly_revenue", "monthly_finance"]))

    # 66 — strewn bars + companion line (same scale)
    p = P()
    L1 = p.sift("site_traffic", "channel", "is", "Search")
    b1 = p.sow("p0", L1, "slab")
    p.meter(b1, "stance", "week")
    p.meter(b1, "stature", "visits")
    L2 = p.sift("site_traffic", "channel", "is", "Social")
    b2 = p.sow("p0", L2, "wisp")
    p.meter(b2, "stance", "week")
    p.meter(b2, "perch", "visits")
    p.settle("p0", "strew")
    s = p.thread(b2, by="week")
    p.tint(b2, "ember")
    p.tint(s, "ember")
    p.rim("p0", "south")
    p.rim("p0", "west")
    p.weft("p0", "rise")
    p.entitle("p0", "Search vs Social")
    T.append(task(
        "On one ground, station Search-channel 'visits' from 'site_traffic' "
        "as slabs by 'week' (heights from visits), and lay Social visits "
        "over them as an ember strand threaded through wisps at the same "
        "stations. Shared rise. Rims, weft, title 'Search vs Social'.",
        p, [{"check": "brood", "weight": 5, "where": {
            "form": "slab",
            "data": {"from": "site_traffic",
                     "transform": [["sift", "channel", "is", "Search"]]},
            "meter": {"stance": "week", "stature": "visits"},
            "in": {"law": "strew"}}},
            {"check": "brood", "weight": 5, "where": {
                "form": "wisp",
                "data": {"from": "site_traffic",
                         "transform": [["sift", "channel", "is", "Social"]]},
                "meter": {"stance": "week", "perch": "visits"},
                "threaded_by": "week"}},
            {"check": "guide", "kind": "rim", "side": "south"},
            {"check": "guide", "kind": "rim", "side": "west"}],
        ["site_traffic"]))

    # 67 — derive total_share → percent pie
    T.append(pie(
        "Derive each browser's percentage of total 'share' in "
        "'browser_share' (call the new vein 'pct'), hoop the result with "
        "angular share from 'pct', tints per browser, and badge each wedge "
        "with its 'pct' value in the middle of the wedge.",
        "browser_share", "browser", "pct",
        transform=[["derive", "pct", "total_share", "share"]],
        badge_cat=False, badge_val=True, legend=True))

    # 68 — top-5 bar via marshal + crop
    T.append(bar(
        "Keep only the five most-visited cities of 'city_stats' (rank by "
        "'population', keep the top 5) and chart their populations as "
        "columns, badged with 'city' beneath, rims on both sides.",
        "city_stats", "city", "population",
        transform=[["marshal", "population", "waning"], ["crop", 5]],
        badge_vein="population"))

    # 69 — branching process + kindled path
    T.append(diagram(
        "A support process flowing east: 'Ticket' → 'Classify' → rhomb "
        "'Urgent?' branching to 'Page on-call' (badge 'yes') and 'Queue' "
        "(badge 'no'); both continue to 'Resolve'. Kindle the urgent path "
        "cords ('Urgent?' → 'Page on-call' and 'Page on-call' → 'Resolve').",
        [("capsule", "Ticket"), ("capsule", "Classify"), ("rhomb", "Urgent?"),
         ("capsule", "Page on-call"), ("capsule", "Queue"),
         ("capsule", "Resolve")],
        [("Ticket", "Classify"), ("Classify", "Urgent?"),
         ("Urgent?", "Page on-call", "yes"), ("Urgent?", "Queue", "no"),
         ("Page on-call", "Resolve"), ("Queue", "Resolve")],
        kindle_cords=[("Urgent?", "Page on-call"), ("Page on-call", "Resolve")]))

    # 70 — scatter + bulk + key + flag
    T.append(scatter(
        "Scatter 'city_stats' ('growth' across, 'transit_share' up), discs "
        "sized by 'population' and tinted by 'continent', with key and rims. "
        "Flag Busan 'largest city'.",
        "city_stats", "growth", "transit_share",
        tint_cat="continent", bulk="population", legend=True,
        annotate=("largest city", {"city": "Busan"}, "flag")))

    # 71 — inverted rise
    p = P()
    L = p.marshal("hiring_funnel", "stage", "waxing")
    cells = p.carve("p0", "span", L, "stage",
                    ["Applicants", "Screen", "Interview", "Offer", "Hired"])
    b = p.sow("p0", L, "slab", key="stage")
    p.meter(b, "stature", "median_days")
    p.invert("p0", "rise")
    p.badge(b, vein="median_days", aim="south")
    p.rim("p0", "north")
    T.append(task(
        "Chart 'median_days' per 'stage' from 'hiring_funnel' as columns "
        "hanging from the roof (invert the rise), badges below each bar, and "
        "a north rim.",
        p, [{"check": "brood", "weight": 5, "where": {
            "form": "slab",
            "data": {"from": "hiring_funnel", "transform": []},
            "meter": {"stature": "median_days"}, "badge_vein": "median_days",
            "in": {"carved_by": "stage"}}},
            {"check": "parcel", "label": "rise inverted",
             "where": {"inverted": "rise"}},
            {"check": "guide", "kind": "rim", "side": "north"}],
        ["hiring_funnel"]))

    # 72 — fine histogram + note
    T.append(histogram(
        "A finer distribution: bin 'ticket_resolution' 'hours' into about 12 "
        "bins, columns with rims and weft, and note 'n = 40 tickets'.",
        "ticket_resolution", "hours", bins=12))
    T[-1]["reference_program"].append(["note", {"parcel": "p0",
                                                "text": "n = 40 tickets"}])
    T[-1]["hidden_goal"]["checks"].append({"check": "guide", "kind": "note"})

    # 73 — split + two pies
    p = P()
    panels = p.split("p0", "span", 2)
    for i, region in enumerate(["Europe", "Asia"]):
        L = p.sift("quarterly_revenue", "region", "is", region)
        L2 = p.distill(L, "product", "sum", "revenue")
        p.hoop(panels[i])
        b = p.sow(panels[i], L2, "slab")
        p.meter(b, "girth", "revenue")
        p.meter(b, "tint", "product")
        p.badge(b, vein="product", aim="rim")
        p.entitle(panels[i], region)
    T.append(task(
        "Two hooped charts side by side from 'quarterly_revenue': total "
        "'revenue' share per 'product' for Europe (left) and Asia (right), "
        "wedges tinted and badged by product, each panel entitled with its "
        "region.",
        p, [{"check": "parcel", "label": "two panels",
             "where": {"split_count": 2}},
            {"check": "brood", "weight": 5, "where": {
                "form": "slab",
                "data": {"from": "quarterly_revenue",
                         "transform": [["sift", "region", "is", "Europe"],
                                       ["distill", "product", "revenue",
                                        "sum"]]},
                "meter": {"girth": "revenue", "tint": "product"},
                "in": {"hooped": True, "in_split_panel": True}}},
            {"check": "brood", "weight": 5, "where": {
                "form": "slab",
                "data": {"from": "quarterly_revenue",
                         "transform": [["sift", "region", "is", "Asia"],
                                       ["distill", "product", "revenue",
                                        "sum"]]},
                "meter": {"girth": "revenue", "tint": "product"},
                "in": {"hooped": True, "in_split_panel": True}}}],
        ["quarterly_revenue"]))

    # 74 — four-channel multi-line
    T.append(multi_line(
        "Thread all four channels of 'site_traffic' ('visits' over 'week') "
        "as separate strands — Search tide, Social ember, Direct moss, Email "
        "plum — inscribing each channel's name at W12. Rims and weft, "
        "entitled 'Traffic by channel'.",
        "site_traffic", "week", "visits", "channel",
        [("Search", "tide"), ("Social", "ember"), ("Direct", "moss"),
         ("Email", "plum")],
        label_at="W12", title="Traffic by channel"))

    # 75 — architecture, two corrals, shared drum
    T.append(diagram(
        "An eastward architecture: 'Web' and 'Mobile' capsules both tether "
        "to 'API'; 'API' tethers to 'Billing' and 'Catalog'; both services "
        "tether to drum 'Main DB'. Corral Web+Mobile as 'Clients' and "
        "Billing+Catalog as 'Services'.",
        [("capsule", "Web"), ("capsule", "Mobile"), ("capsule", "API"),
         ("capsule", "Billing"), ("capsule", "Catalog"), ("drum", "Main DB")],
        [("Web", "API"), ("Mobile", "API"), ("API", "Billing"),
         ("API", "Catalog"), ("Billing", "Main DB"), ("Catalog", "Main DB")],
        corrals=[(["Web", "Mobile"], "Clients"),
                 (["Billing", "Catalog"], "Services")]))

    # 76 — two veiled areas
    p = P()
    checks = []
    for value, hue in [("Control", "slate"), ("Variant B", "ember")]:
        L = p.sift("experiment_results", "variant", "is", value)
        b = p.sow("p0", L, "wisp")
        p.meter(b, "stance", "day")
        p.meter(b, "perch", "conversion")
        s = p.thread(b, by="day")
        p.flood(s)
        p.tint(b, hue)
        p.tint(s, hue)
        checks.append({"check": "brood", "weight": 4, "where": {
            "form": "wisp",
            "data": {"from": "experiment_results",
                     "transform": [["sift", "variant", "is", value]]},
            "meter": {"stance": "day", "perch": "conversion"},
            "threaded_by": "day", "flooded": True}})
    p.settle("p0", "strew")
    p.rim("p0", "south")
    p.rim("p0", "west")
    checks += [{"check": "guide", "kind": "rim", "side": "south"},
               {"check": "guide", "kind": "rim", "side": "west"}]
    T.append(task(
        "Overlay two flooded strands from 'experiment_results': Control "
        "(slate) and Variant B (ember), 'conversion' over 'day', on shared "
        "rims.",
        p, checks, ["experiment_results"]))

    # 77 — horizontal bars + span weft
    T.append(bar(
        "Horizontal bars of 'p99' per 'service' from 'service_latency', "
        "running east, with rims south and west and weft lines along the "
        "span.",
        "service_latency", "service", "p99", orient="bars"))
    T[-1]["reference_program"].append(["weft", {"parcel": "p0",
                                                "along": "span"}])
    T[-1]["hidden_goal"]["checks"].append(
        {"check": "guide", "kind": "weft", "along": "span"})

    # 78 — pie + kindle largest
    T.append(pie(
        "Hoop 'energy_mix' (share from 'share', tint and rim-badges per "
        "'source'), kindle the Hydro wedge, and entitle the ground "
        "'Generation mix'.",
        "energy_mix", "source", "share",
        kindle_where={"source": "Hydro"}, title="Generation mix"))

    # 79 — era-sifted area + note
    T.append(line(
        "Keep only the 'after launch' era of 'monthly_finance' and show "
        "'revenue' over 'period' as a flooded strand with rims, noting "
        "'post-launch only'.",
        "monthly_finance", "period", "revenue",
        transform=[["sift", "era", "is", "after launch"]],
        area=True, note="post-launch only", weft_rise=False))

    # 80 — full stacked survey + title
    T.append(bar(
        "The full 'survey_results' picture: one column per 'topic', "
        "responses piled in rank order and tinted by 'response', key, rims, "
        "weft, entitled 'Workplace survey'.",
        "survey_results", "topic", "share",
        stacked=True, stack_tint="response", legend=True, weft_rise=True,
        title="Workplace survey"))

    # 81 — grouped by model (generalization pair of #37)
    T.append(bar(
        "Regroup 'model_evals': one region per 'model' with benchmark scores "
        "side by side, tinted by 'benchmark', key and rims.",
        "model_evals", "model", "score",
        tint_cat="benchmark", legend=True))

    # 82 — deployment flow, 2 branches + badges
    T.append(diagram(
        "A deployment flow east: 'Commit' → 'CI' → rhomb 'Pass?' → 'Canary' "
        "(badge 'yes') and 'Fix' (badge 'no'); 'Fix' loops onward to "
        "'Commit' is not needed — instead 'Canary' → 'Fleet'. Include a "
        "plaque 'v2.4 rollout' placed in the flow, untethered.",
        [("capsule", "Commit"), ("capsule", "CI"), ("rhomb", "Pass?"),
         ("capsule", "Canary"), ("capsule", "Fix"), ("capsule", "Fleet"),
         ("plaque", "v2.4 rollout")],
        [("Commit", "CI"), ("CI", "Pass?"), ("Pass?", "Canary", "yes"),
         ("Pass?", "Fix", "no"), ("Canary", "Fleet")]))

    # 83 — scatter with 'among' pick kindled
    T.append(scatter(
        "Scatter 'city_stats' by 'growth' and 'transit_share' with rims; "
        "kindle exactly the European cities (their 'continent' is Europe).",
        "city_stats", "growth", "transit_share",
        kindle_where={"continent": "Europe"}))

    # 84 — pipeline bars + flag Won
    T.append(bar(
        "Columns of 'value' per 'phase' from 'sales_pipeline', badged with "
        "'deals' counts, rims, and a flag 'closed revenue' on the Won "
        "column.",
        "sales_pipeline", "phase", "value", badge_vein="deals",
        annotate=("closed revenue", {"phase": "Won"}, "flag")))

    # 85 — split panels + shared stature gauge
    p = P()
    panels = p.split("p0", "span", 2)
    for i, region in enumerate(["Europe", "Asia"]):
        L = p.sift("quarterly_revenue", "region", "is", region)
        L2 = p.distill(L, "quarter", "sum", "revenue")
        cells = p.carve(panels[i], "span", L2, "quarter",
                        ["Q1", "Q2", "Q3", "Q4"])
        b = p.sow(panels[i], L2, "slab", key="quarter")
        p.meter(b, "stature", "revenue")
        p.rim(panels[i], "south")
        p.rim(panels[i], "west")
        p.entitle(panels[i], region)
    p.share(panels[0], panels[1], "stature")
    T.append(task(
        "Compare regions fairly: two panels of quarterly total 'revenue' "
        "columns from 'quarterly_revenue' — Europe left, Asia right — with "
        "the stature gauge shared so heights are comparable. Rims and a "
        "title per panel.",
        p, [{"check": "parcel", "where": {"split_count": 2},
             "label": "two panels"},
            {"check": "brood", "weight": 4, "where": {
                "form": "slab",
                "data": {"from": "quarterly_revenue",
                         "transform": [["sift", "region", "is", "Europe"],
                                       ["distill", "quarter", "revenue",
                                        "sum"]]},
                "meter": {"stature": "revenue"},
                "in": {"carved_by": "quarter"}}},
            {"check": "brood", "weight": 4, "where": {
                "form": "slab",
                "data": {"from": "quarterly_revenue",
                         "transform": [["sift", "region", "is", "Asia"],
                                       ["distill", "quarter", "revenue",
                                        "sum"]]},
                "meter": {"stature": "revenue"},
                "in": {"carved_by": "quarter"}}},
            {"check": "share_or_abut"}],
        ["quarterly_revenue"]))

    # 86 — timeline with bulk
    p = P()
    b = p.sow("p0", "milestones", "disc")
    p.meter(b, "stance", "week")
    p.meter(b, "bulk", "impact")
    p.settle("p0", "strew")
    p.thread(b, by="week")
    p.badge(b, vein="milestone", aim="north")
    p.rim("p0", "south")
    T.append(task(
        "A weighted timeline: 'milestones' discs stationed by 'week' and "
        "sized by 'impact', badged with names, threaded in week order, "
        "south rim.",
        p, [{"check": "brood", "weight": 6, "where": {
            "form": "disc", "data": {"from": "milestones", "transform": []},
            "meter": {"stance": "week", "bulk": "impact"},
            "threaded_by": "week", "badge_vein": "milestone",
            "in": {"law": "strew"}}},
            {"check": "guide", "kind": "rim", "side": "south"}],
        ["milestones"]))

    # 87 — three-level tree
    T.append(diagram(
        "A three-level org tree flowing south: 'CTO' → 'Platform' and "
        "'Product'; 'Platform' → 'Infra' and 'Tooling'; 'Product' → 'Growth' "
        "and 'Core UX'. Capsules all.",
        [("capsule", "CTO"), ("capsule", "Platform"), ("capsule", "Product"),
         ("capsule", "Infra"), ("capsule", "Tooling"), ("capsule", "Growth"),
         ("capsule", "Core UX")],
        [("CTO", "Platform"), ("CTO", "Product"), ("Platform", "Infra"),
         ("Platform", "Tooling"), ("Product", "Growth"),
         ("Product", "Core UX")],
        heading="south"))

    # 88 — donut via distill + key
    T.append(pie(
        "An open ring of total 'engineers' per 'team' from "
        "'team_allocation', tint per team, key instead of badges, entitled "
        "'Engineering allocation'.",
        "team_allocation", "team", "engineers",
        transform=[["distill", "team", "engineers", "sum"]],
        inner=0.55, badge_cat=False, legend=True,
        title="Engineering allocation"))

    # 89 — rebase floor
    p = P()
    b = p.sow("p0", "monthly_finance", "wisp")
    p.meter(b, "stance", "period")
    p.meter(b, "perch", "margin")
    p.settle("p0", "strew")
    p.thread(b, by="period")
    p.rebase("p0", "perch", floor=0)
    p.weft("p0", "rise")
    p.rim("p0", "south")
    p.rim("p0", "west")
    T.append(task(
        "Thread 'margin' over 'period' from 'monthly_finance', but rebase "
        "the perch gauge so it starts at 0 rather than hugging the data. "
        "Rims and weft.",
        p, [{"check": "brood", "weight": 5, "where": {
            "form": "wisp",
            "data": {"from": "monthly_finance", "transform": []},
            "meter": {"stance": "period", "perch": "margin"},
            "threaded_by": "period", "in": {"law": "strew"}}},
            {"check": "guide", "kind": "rim", "side": "south"},
            {"check": "guide", "kind": "rim", "side": "west"}],
        ["monthly_finance"]))

    # 90 — northward architecture
    T.append(diagram(
        "A dependency stack flowing north (foundations at the bottom): drum "
        "'Postgres' → capsule 'ORM' → capsule 'API' → capsule 'Frontend', "
        "each tethered upward to the next.",
        [("drum", "Postgres"), ("capsule", "ORM"), ("capsule", "API"),
         ("capsule", "Frontend")],
        [("Postgres", "ORM"), ("ORM", "API"), ("API", "Frontend")],
        heading="north"))

    # 91 — the canonical grouped+kindle+flag task
    T.append(bar(
        "Grouped columns of European 'revenue' per 'quarter' from "
        "'quarterly_revenue' (products side by side, tinted by 'product', "
        "key, rims). Kindle Breeze's Q3 slab and flag it 'Peak quarter'.",
        "quarterly_revenue", "quarter", "revenue",
        transform=[["sift", "region", "is", "Europe"]],
        tint_cat="product", legend=True,
        kindle_where={"quarter": "Q3", "product": "Breeze"},
        annotate=("Peak quarter", {"quarter": "Q3", "product": "Breeze"},
                  "flag")))

    # 92 — histogram + flag the modal bin
    p = P()
    L = p.bin("ticket_resolution", "hours", 8)
    from .builders import levels_from_rows
    from glyphbench.verify import apply_transform
    rows = apply_transform("ticket_resolution", [["bin", "hours", 8]])
    cells = p.carve("p0", "span", L, "bin", levels_from_rows(rows, "bin"),
                    gap=0.06)
    b = p.sow("p0", L, "slab", key="bin")
    p.meter(b, "stature", "tally")
    top_bin = max(rows, key=lambda r: r["tally"])["bin"]
    f = p.pick(b, "bin", "is", top_bin)
    p.flag(f, "most tickets")
    p.rim("p0", "south")
    p.rim("p0", "west")
    T.append(task(
        "Bin 'ticket_resolution' 'hours' into about 8 bins as columns with "
        "rims, and flag the tallest bin 'most tickets'.",
        p, [{"check": "brood", "weight": 5, "where": {
            "form": "slab",
            "data": {"from": "ticket_resolution",
                     "transform": [["bin", "hours", 8]]},
            "meter": {"stature": "tally"}, "in": {"carved_by": "bin"}}},
            {"check": "annotation", "kind": "flag", "text_has": "tickets",
             "near": {"where": {"bin": top_bin}}},
            {"check": "guide", "kind": "rim", "side": "south"},
            {"check": "guide", "kind": "rim", "side": "west"}],
        ["ticket_resolution"]))

    # 93 — multi-line, kindle winner, hush rest
    T.append(multi_line(
        "Thread all three variants of 'experiment_results' over 'day'; "
        "kindle the Variant B strand and hush the other two so the winner "
        "carries the eye. Rims south and west.",
        "experiment_results", "day", "conversion", "variant",
        [("Control", "slate"), ("Variant C", "moss"), ("Variant B", "ember")],
        kindle_series="Variant B", hush_others=True, weft_rise=False))

    # 94 — palette + badges
    T.append(bar(
        "Chart 'visits' per 'channel' for week W12 of 'site_traffic' "
        "(sift first) as columns tinted by 'channel' under the 'dusk' "
        "palette, badges above, key and rims.",
        "site_traffic", "channel", "visits",
        transform=[["sift", "week", "is", "W12"]],
        tint_cat="channel", legend=True, badge_vein="visits",
        palette="dusk"))

    # 95 — funnel as horizontal bars + east badges
    p = P()
    cells = p.carve("p0", "rise", "hiring_funnel", "stage",
                    ["Applicants", "Screen", "Interview", "Offer", "Hired"])
    b = p.sow("p0", "hiring_funnel", "slab", key="stage")
    p.meter(b, "girth", "candidates")
    p.badge(b, vein="median_days", aim="east")
    p.rim("p0", "west")
    p.entitle("p0", "Hiring funnel")
    T.append(task(
        "The hiring funnel sideways: one row per 'stage' from "
        "'hiring_funnel', bar length from 'candidates', each badged east "
        "with its 'median_days'. West rim, entitled 'Hiring funnel'.",
        p, [{"check": "brood", "weight": 6, "where": {
            "form": "slab",
            "data": {"from": "hiring_funnel", "transform": []},
            "meter": {"girth": "candidates"}, "badge_vein": "median_days",
            "in": {"carved_by": "stage", "carve_along": "rise"}}},
            {"check": "guide", "kind": "rim", "side": "west"},
            {"check": "guide", "kind": "entitle"}],
        ["hiring_funnel"]))

    # 96 — split: scatter | bars
    p = P()
    panels = p.split("p0", "span", 2)
    b1 = p.sow(panels[0], "city_stats", "disc")
    p.meter(b1, "stance", "growth")
    p.meter(b1, "perch", "transit_share")
    p.settle(panels[0], "strew")
    p.rim(panels[0], "south")
    p.rim(panels[0], "west")
    p.entitle(panels[0], "Growth vs transit")
    L = p.marshal("city_stats", "population", "waning")
    L2 = p.crop(L, 6)
    from .builders import levels_from_rows as _lvl
    rows6 = apply_transform("city_stats",
                            [["marshal", "population", "waning"], ["crop", 6]])
    cells = p.carve(panels[1], "span", L2, "city", _lvl(rows6, "city"))
    b2 = p.sow(panels[1], L2, "slab", key="city")
    p.meter(b2, "stature", "population")
    p.rim(panels[1], "west")
    p.entitle(panels[1], "Population (top 6)")
    T.append(task(
        "Two views of 'city_stats' side by side: left, a strewn scatter of "
        "'growth' vs 'transit_share' with rims; right, columns of "
        "'population' for the six largest cities (rank then keep 6), west "
        "rim. Entitle each panel.",
        p, [{"check": "parcel", "where": {"split_count": 2},
             "label": "two panels"},
            {"check": "brood", "weight": 4, "where": {
                "form": "disc", "meter": {"stance": "growth",
                                          "perch": "transit_share"},
                "in": {"law": "strew", "in_split_panel": True}}},
            {"check": "brood", "weight": 4, "where": {
                "form": "slab",
                "data": {"from": "city_stats",
                         "transform": [["marshal", "population", "waning"],
                                       ["crop", 6]]},
                "meter": {"stature": "population"},
                "in": {"carved_by": "city", "in_split_panel": True}}}],
        ["city_stats"]))

    # 97 — process with hush
    T.append(diagram(
        "An escalation flow east: 'Report' → 'Review' → rhomb 'Severe?' → "
        "'Escalate' (badge 'yes') and 'Archive' (badge 'no'). Hush the "
        "Archive capsule to de-emphasize the cold path.",
        [("capsule", "Report"), ("capsule", "Review"), ("rhomb", "Severe?"),
         ("capsule", "Escalate"), ("capsule", "Archive")],
        [("Report", "Review"), ("Review", "Severe?"),
         ("Severe?", "Escalate", "yes"), ("Severe?", "Archive", "no")],
        hush_nodes=["Archive"]))

    # 98 — area + flag peak + weft + note
    T.append(line(
        "Flood Social-channel 'visits' from 'site_traffic' over 'week' with "
        "weft and rims; flag W12 'holiday spike' and note 'tracking since "
        "January'.",
        "site_traffic", "week", "visits",
        transform=[["sift", "channel", "is", "Social"]],
        area=True, annotate=("holiday spike", {"week": "W12"}, "flag"),
        note="tracking since January"))

    # 99 — pie with is_not sift
    T.append(pie(
        "Hoop 'energy_mix' without coal: sift out rows where 'source' is "
        "Coal ('is_not'), angular share from 'share', tints and rim badges "
        "per source.",
        "energy_mix", "source", "share",
        transform=[["sift", "source", "is_not", "Coal"]]))

    # 100 — grouped bars over an 'among' subset
    T.append(bar(
        "From 'model_evals', keep only the Reasoning and Coding benchmarks "
        "('among'), then chart 'score' per 'model' with the two benchmarks "
        "side by side, tinted by 'benchmark', key and rims.",
        "model_evals", "model", "score",
        transform=[["sift", "benchmark", "among", ["Reasoning", "Coding"]]],
        tint_cat="benchmark", legend=True))

    # 101 — derived ratio bar
    T.append(bar(
        "Derive each service's tail ratio in 'service_latency' — 'p99' "
        "divided by 'p50', name it 'tail_ratio' — and chart it as columns "
        "with value badges and rims, entitled 'Tail amplification'.",
        "service_latency", "service", "tail_ratio",
        transform=[["derive", "tail_ratio", "ratio", "p99", "p50"]],
        badge_vein="tail_ratio", title="Tail amplification"))

    # 102 — architecture with latency badges on cords
    T.append(diagram(
        "An eastward call graph: 'Client' → 'Edge' (cord badged '12ms') → "
        "'App' (cord badged '27ms') → drum 'Store' (cord badged '38ms'). "
        "Kindle the App capsule.",
        [("capsule", "Client"), ("capsule", "Edge"), ("capsule", "App"),
         ("drum", "Store")],
        [("Client", "Edge", "12ms"), ("Edge", "App", "27ms"),
         ("App", "Store", "38ms")],
        kindle_nodes=["App"]))

    # 103 — two scatters sharing the rise
    p = P()
    panels = p.split("p0", "span", 2)
    for i, cont in enumerate(["Europe", "Asia"]):
        L = p.sift("city_stats", "continent", "is", cont)
        b = p.sow(panels[i], L, "disc")
        p.meter(b, "stance", "growth")
        p.meter(b, "perch", "transit_share")
        p.settle(panels[i], "strew")
        p.rim(panels[i], "south")
        p.rim(panels[i], "west")
        p.entitle(panels[i], cont)
    p.share(panels[0], panels[1], "perch")
    T.append(task(
        "Side-by-side scatters of 'city_stats' for Europe and Asia ('growth' "
        "vs 'transit_share'), with the perch gauge shared so the panels are "
        "comparable. Rims and per-panel titles.",
        p, [{"check": "parcel", "where": {"split_count": 2},
             "label": "two panels"},
            {"check": "brood", "weight": 4, "where": {
                "form": "disc",
                "data": {"from": "city_stats",
                         "transform": [["sift", "continent", "is",
                                        "Europe"]]},
                "meter": {"stance": "growth", "perch": "transit_share"}}},
            {"check": "brood", "weight": 4, "where": {
                "form": "disc",
                "data": {"from": "city_stats",
                         "transform": [["sift", "continent", "is", "Asia"]]},
                "meter": {"stance": "growth", "perch": "transit_share"}}},
            {"check": "share_or_abut"}],
        ["city_stats"]))

    # 104 — sorted horizontal bars + badges + title
    T.append(bar(
        "Horizontal bars of all twelve cities' 'population' from "
        "'city_stats', longest first (rank by population), city badges "
        "inside the rise carve, values badged east, west rim, entitled "
        "'City populations'.",
        "city_stats", "city", "population", orient="bars",
        sort=("population", "waning"), badge_vein="population",
        rims=("west",), title="City populations"))

    # 105 — line with start/end inscriptions
    p = P()
    b = p.sow("p0", "monthly_finance", "wisp")
    p.meter(b, "stance", "period")
    p.meter(b, "perch", "revenue")
    p.settle("p0", "strew")
    p.thread(b, by="period")
    f1 = p.pick(b, "period", "is", "M01")
    p.inscribe("120 at start", near=f1, aim="north")
    f2 = p.pick(b, "period", "is", "M24")
    p.inscribe("295 at close", near=f2, aim="west")
    p.rim("p0", "south")
    p.rim("p0", "west")
    T.append(task(
        "Thread 'revenue' over 'period' from 'monthly_finance' with rims; "
        "inscribe '120 at start' by the first point and '295 at close' by "
        "the last.",
        p, [{"check": "brood", "weight": 5, "where": {
            "form": "wisp",
            "data": {"from": "monthly_finance", "transform": []},
            "meter": {"stance": "period", "perch": "revenue"},
            "threaded_by": "period", "in": {"law": "strew"}}},
            {"check": "annotation", "text_has": "start",
             "near": {"where": {"period": "M01"}}},
            {"check": "annotation", "text_has": "close",
             "near": {"where": {"period": "M24"}}}],
        ["monthly_finance"]))

    # 106 — polished stacked traffic
    T.append(bar(
        "Stacked weekly traffic, polished: from 'site_traffic' keep weeks "
        "W07–W12 ('among'), one column per 'week', channels piled and "
        "tinted, key, rims, weft, entitled 'Traffic, second half'.",
        "site_traffic", "week", "visits",
        transform=[["sift", "week", "among",
                    ["W07", "W08", "W09", "W10", "W11", "W12"]]],
        stacked=True, stack_tint="channel", legend=True, weft_rise=True,
        title="Traffic, second half"))

    # 107 — data pipeline with plaque note
    T.append(diagram(
        "A data pipeline east: drum 'Events' → capsule 'Ingest' → capsule "
        "'Transform' → drum 'Warehouse'; plus a plaque 'hourly batches' "
        "placed alongside and a flag 'PII scrubbed here' tied to Transform.",
        [("drum", "Events"), ("capsule", "Ingest"), ("capsule", "Transform"),
         ("drum", "Warehouse"), ("plaque", "hourly batches")],
        [("Events", "Ingest"), ("Ingest", "Transform"),
         ("Transform", "Warehouse")],
        flags=[("Transform", "PII scrubbed here")]))

    # 108 — donut with center inscription
    p = P()
    p.hoop("p0", inner=0.6)
    b = p.sow("p0", "energy_mix", "slab")
    p.meter(b, "girth", "share")
    p.meter(b, "tint", "source")
    p.badge(b, vein="source", aim="rim")
    p.inscribe("100 GW total")
    T.append(task(
        "An open ring of 'energy_mix' (share by 'source', tinted, rim "
        "badges) with the words '100 GW total' inscribed on the ground.",
        p, [{"check": "brood", "weight": 5, "where": {
            "form": "slab", "data": {"from": "energy_mix", "transform": []},
            "meter": {"girth": "share", "tint": "source"},
            "badge_vein": "source",
            "in": {"hooped": True, "inner_min": 0.4}}},
            {"check": "annotation", "text_has": "total"}],
        ["energy_mix"]))

    # 109 — mean by benchmark + flag weakest
    T.append(bar(
        "Average 'score' per 'benchmark' across models in 'model_evals' and "
        "chart the means as columns with rims; flag the Math column 'weakest "
        "area'.",
        "model_evals", "benchmark", "score",
        transform=[["distill", "benchmark", "score", "mean"]],
        annotate=("weakest area", {"benchmark": "Math"}, "flag")))

    # 110 — grouped + kindled + key + note composite
    T.append(bar(
        "For the Americas, group 'revenue' per 'quarter' by product from "
        "'quarterly_revenue' (tint per 'product', key, rims, weft). Kindle "
        "Aria's Q4 slab and note 'Aria drove the Q4 record'.",
        "quarterly_revenue", "quarter", "revenue",
        transform=[["sift", "region", "is", "Americas"]],
        tint_cat="product", legend=True, weft_rise=True,
        kindle_where={"quarter": "Q4", "product": "Aria"},
        note="Aria drove the Q4 record"))

    assert len(T) == 50, len(T)
    return T
