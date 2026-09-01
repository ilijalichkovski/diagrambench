"""Stage 2 (tasks 26-60): short compositions of 2-4 familiar primitives,
occasionally introducing one new concept."""

from .builders import P, task, bar, pie, line, scatter, histogram, diagram


def build():
    T = []

    # 26 — grouped bar
    T.append(bar(
        "From 'quarterly_revenue', keep Europe only and show 'revenue' per "
        "'quarter', one slab per product side by side in each quarter, tinted "
        "by 'product', with a key and both rims.",
        "quarterly_revenue", "quarter", "revenue",
        transform=[["sift", "region", "is", "Europe"]],
        tint_cat="product", legend=True))

    # 27 — pie with badges
    T.append(pie(
        "Turn 'browser_share' into a hooped chart: angular share from "
        "'share', tint per 'browser', each wedge badged with its browser at "
        "the rim.",
        "browser_share", "browser", "share"))

    # 28 — flowchart chain with title
    T.append(diagram(
        "Draw a four-step pipeline flowing east: capsules 'Ingest' → 'Clean' "
        "→ 'Train' → 'Serve', each step tethered to the next. Entitle it "
        "'Model pipeline'.",
        [("capsule", "Ingest"), ("capsule", "Clean"), ("capsule", "Train"),
         ("capsule", "Serve")],
        [("Ingest", "Clean"), ("Clean", "Train"), ("Train", "Serve")],
        title="Model pipeline"))

    # 29 — two-level hierarchy
    T.append(diagram(
        "Show a two-level hierarchy flowing south: a capsule 'CEO' on top, "
        "tethered down to capsules 'Product', 'Engineering' and 'Sales'.",
        [("capsule", "CEO"), ("capsule", "Product"),
         ("capsule", "Engineering"), ("capsule", "Sales")],
        [("CEO", "Product"), ("CEO", "Engineering"), ("CEO", "Sales")],
        heading="south"))

    # 30 — line with flag at the peak
    T.append(line(
        "Thread the 'revenue' of 'monthly_finance' across 'period', with rims "
        "and weft. Tie a flag reading 'record month' to the final point "
        "(period M24).",
        "monthly_finance", "period", "revenue",
        annotate=("record month", {"period": "M24"}, "flag")))

    # 31 — scatter with tint + key
    T.append(scatter(
        "Scatter 'city_stats' by 'growth' and 'transit_share', tinted by "
        "'continent', with a key and both rims.",
        "city_stats", "growth", "transit_share", tint_cat="continent",
        legend=True))

    # 32 — stacked bar
    T.append(bar(
        "Stack 'team_allocation': one column per 'project', slabs piled by "
        "team with tint per 'team', a key, and both rims.",
        "team_allocation", "project", "engineers",
        stacked=True, stack_tint="team", legend=True))

    # 33 — donut (hoop inner)
    T.append(pie(
        "Make an open-middled ring of 'energy_mix': angular share from "
        "'share', tint by 'source', badges at the rim, and a clear hole in "
        "the middle.",
        "energy_mix", "source", "share", inner=0.55))

    # 34 — area (flood)
    T.append(line(
        "Chart Search-channel 'visits' from 'site_traffic' across weeks as a "
        "threaded strand, then flood the region beneath it. Rims south and "
        "west.",
        "site_traffic", "week", "visits",
        transform=[["sift", "channel", "is", "Search"]],
        area=True, weft_rise=False))

    # 35 — histogram + title
    T.append(histogram(
        "Bin the 'hours' of 'ticket_resolution' (about 8 bins) into columns "
        "with rims and weft, entitled 'Time to resolution'.",
        "ticket_resolution", "hours", bins=8, title="Time to resolution"))

    # 36 — sorted bar + badges
    T.append(bar(
        "Rank the features of 'feature_usage' from most to least 'users' as "
        "columns, badge each with its value above, and add both rims.",
        "feature_usage", "feature", "users",
        sort=("users", "waning"), badge_vein="users"))

    # 37 — grouped bar, model evals
    T.append(bar(
        "From 'model_evals', chart 'score' with one region per 'benchmark', "
        "models side by side tinted by 'model', a key, and rims.",
        "model_evals", "benchmark", "score",
        tint_cat="model", legend=True))

    # 38 — sifted line + flag
    T.append(line(
        "Keep only the 'Variant B' rows of 'experiment_results' and thread "
        "'conversion' over 'day'. Flag the final day (D14) with "
        "'best conversion'.",
        "experiment_results", "day", "conversion",
        transform=[["sift", "variant", "is", "Variant B"]],
        annotate=("best conversion", {"day": "D14"}, "flag")))

    # 39 — pie from sifted survey
    T.append(pie(
        "Hooped view of opinions: keep the 'Four-day week' rows of "
        "'survey_results' and give each 'response' an angular share of "
        "'share', tinted by response, with a key.",
        "survey_results", "response", "share",
        transform=[["sift", "topic", "is", "Four-day week"]],
        badge_cat=False, legend=True))

    # 40 — decision flowchart (rhomb) with cord badges
    T.append(diagram(
        "Draw an order flow heading east: capsule 'Submit' → capsule "
        "'Validate' → rhomb 'Valid?' branching to capsule 'Fulfil' (cord "
        "badged 'yes') and capsule 'Reject' (cord badged 'no').",
        [("capsule", "Submit"), ("capsule", "Validate"), ("rhomb", "Valid?"),
         ("capsule", "Fulfil"), ("capsule", "Reject")],
        [("Submit", "Validate"), ("Validate", "Valid?"),
         ("Valid?", "Fulfil", "yes"), ("Valid?", "Reject", "no")]))

    # 41 — mini architecture with a drum
    T.append(diagram(
        "Sketch a service and its store, flowing east: capsule 'API' → "
        "capsule 'Worker' → drum 'Queue DB'. Entitle it 'Job system'.",
        [("capsule", "API"), ("capsule", "Worker"), ("drum", "Queue DB")],
        [("API", "Worker"), ("Worker", "Queue DB")],
        title="Job system"))

    # 42 — horizontal bars (girth)
    T.append(bar(
        "Lay 'city_stats' out as horizontal bars: one row per 'city', bar "
        "length from 'population' running east, rims south and west.",
        "city_stats", "city", "population", orient="bars"))

    # 43 — stacked survey, all topics
    T.append(bar(
        "Stack all of 'survey_results': one column per 'topic', responses "
        "piled and tinted by 'response', with a key and rims.",
        "survey_results", "topic", "share",
        stacked=True, stack_tint="response", legend=True))

    # 44 — area + note
    T.append(line(
        "Thread and flood the Control variant of 'experiment_results' "
        "('conversion' over 'day'), rims south/west, and note the ground "
        "'baseline cohort'.",
        "experiment_results", "day", "conversion",
        transform=[["sift", "variant", "is", "Control"]],
        area=True, note="baseline cohort", weft_rise=False))

    # 45 — scatter + badges
    T.append(scatter(
        "Scatter 'feature_usage' with 'users' across the span and "
        "'satisfaction' up the rise, badge each disc with its 'feature', "
        "rims on south and west.",
        "feature_usage", "users", "satisfaction", badge_vein="feature"))

    # 46 — bar + kindle + inscription
    T.append(bar(
        "Chart total 'revenue' per 'quarter' from 'quarterly_revenue' as "
        "columns with rims; kindle the Q4 column and inscribe 'strongest "
        "finish' beside it.",
        "quarterly_revenue", "quarter", "revenue",
        transform=[["distill", "quarter", "revenue", "sum"]],
        kindle_where={"quarter": "Q4"},
        annotate=("strongest finish", {"quarter": "Q4"}, "inscribe")))

    # 47 — timeline
    p = P()
    b = p.sow("p0", "milestones", "disc")
    p.meter(b, "stance", "week")
    p.settle("p0", "strew")
    p.thread(b, by="week")
    p.badge(b, vein="milestone", aim="north")
    f = p.pick(b, "milestone", "is", "Launch")
    p.flag(f, "go-live")
    p.rim("p0", "south")
    T.append(task(
        "Lay the 'milestones' ledger out as a timeline: discs stationed by "
        "'week' on one strand, each badged with its 'milestone', a south rim, "
        "and a flag 'go-live' on the Launch point.",
        p, [{"check": "brood", "weight": 5, "where": {
            "form": "disc",
            "data": {"from": "milestones", "transform": []},
            "meter": {"stance": "week"}, "threaded_by": "week",
            "badge_vein": "milestone", "in": {"law": "strew"}}},
            {"check": "guide", "kind": "rim", "side": "south"},
            {"check": "annotation", "kind": "flag", "text_has": "go-live",
             "near": {"where": {"milestone": "Launch"}}}],
        ["milestones"]))

    # 48 — five-node flow with badges
    T.append(diagram(
        "Chart a release flow heading east: 'Build' → 'Test' (cord badged "
        "'ci') → 'Stage' → 'Approve' → 'Ship' (cord from Approve badged "
        "'manual'), all capsules.",
        [("capsule", "Build"), ("capsule", "Test"), ("capsule", "Stage"),
         ("capsule", "Approve"), ("capsule", "Ship")],
        [("Build", "Test", "ci"), ("Test", "Stage"), ("Stage", "Approve"),
         ("Approve", "Ship", "manual")]))

    # 49 — donut + key
    T.append(pie(
        "An open-middled ring of 'team_allocation' sifted to project 'Atlas': "
        "share from 'engineers', tint per 'team', explained by a key rather "
        "than badges.",
        "team_allocation", "team", "engineers",
        transform=[["sift", "project", "is", "Atlas"]],
        inner=0.5, badge_cat=False, legend=True))

    # 50 — grouped bar over sifted weeks (among)
    T.append(bar(
        "From 'site_traffic', keep weeks W01 through W04 only (they are "
        "'among' a list) and chart 'visits' per 'week' with channels side by "
        "side, tinted by 'channel', key and rims.",
        "site_traffic", "week", "visits",
        transform=[["sift", "week", "among", ["W01", "W02", "W03", "W04"]]],
        tint_cat="channel", legend=True))

    # 51 — distill mean
    T.append(bar(
        "Average each model's 'score' across benchmarks in 'model_evals' "
        "(mean, not sum) and chart the means as columns with badges and "
        "rims.",
        "model_evals", "model", "score",
        transform=[["distill", "model", "score", "mean"]],
        badge_vein="score"))

    # 52 — margin line
    T.append(line(
        "Thread 'margin' over 'period' from 'monthly_finance' with weft and "
        "rims, entitled 'Operating margin'.",
        "monthly_finance", "period", "margin", title="Operating margin"))

    # 53 — pie via distill
    T.append(pie(
        "Total the 'engineers' of 'team_allocation' per 'team' and hoop the "
        "result: angular share per team, tinted, badged at the rim.",
        "team_allocation", "team", "engineers",
        transform=[["distill", "team", "engineers", "sum"]]))

    # 54 — deeper hierarchy
    T.append(diagram(
        "Grow a southward tree: 'Root' to 'Left' and 'Right'; 'Left' to "
        "'L1' and 'L2'; 'Right' to 'R1'. All capsules.",
        [("capsule", "Root"), ("capsule", "Left"), ("capsule", "Right"),
         ("capsule", "L1"), ("capsule", "L2"), ("capsule", "R1")],
        [("Root", "Left"), ("Root", "Right"), ("Left", "L1"),
         ("Left", "L2"), ("Right", "R1")],
        heading="south"))

    # 55 — scatter with tint + bulk + key
    T.append(scatter(
        "Scatter 'city_stats' by 'growth' and 'transit_share'; size discs by "
        "'population', tint by 'continent', add a key and rims.",
        "city_stats", "growth", "transit_share",
        tint_cat="continent", bulk="population", legend=True))

    # 56 — bar + kindle + flag
    T.append(bar(
        "Columns of 'population' per 'age_band' from 'age_distribution' with "
        "rims; kindle the 30-39 column and flag it 'largest cohort'.",
        "age_distribution", "age_band", "population",
        kindle_where={"age_band": "30-39"},
        annotate=("largest cohort", {"age_band": "30-39"}, "flag")))

    # 57 — vertical flow (south)
    T.append(diagram(
        "A southward incident flow: 'Alert' → 'Triage' → 'Mitigate' → "
        "'Postmortem', capsules tethered in order.",
        [("capsule", "Alert"), ("capsule", "Triage"), ("capsule", "Mitigate"),
         ("capsule", "Postmortem")],
        [("Alert", "Triage"), ("Triage", "Mitigate"),
         ("Mitigate", "Postmortem")],
        heading="south"))

    # 58 — area + kindled strand
    T.append(line(
        "Flood the area under threaded 'revenue' over 'period' "
        "('monthly_finance'), kindle the strand itself, rims south and west.",
        "monthly_finance", "period", "revenue",
        area=True, kindle_strand=True, weft_rise=False))

    # 59 — pipeline value bars + note + badges
    T.append(bar(
        "Chart 'value' per 'phase' of 'sales_pipeline' as columns in phase "
        "order, badge values above, rims, and note 'values in $M'.",
        "sales_pipeline", "phase", "value",
        badge_vein="value", note="values in $M"))

    # 60 — hiring funnel as bars
    T.append(bar(
        "Show the hiring funnel: 'candidates' per 'stage' from "
        "'hiring_funnel' as columns in stage order, badged with candidate "
        "counts, rims south and west, entitled 'Hiring funnel'.",
        "hiring_funnel", "stage", "candidates",
        badge_vein="candidates", title="Hiring funnel"))

    assert len(T) == 35, len(T)
    return T
