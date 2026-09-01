"""Bundled deterministic datasets ("base ledgers").

Small, hand-authored, never randomized. Vein kinds:
  told    — nominal category (str, no inherent order)
  ranked  — ordered category (str listed in RANKED_ORDERS)
  counted — quantity (int/float)
"""

# Explicit orderings for ranked veins (vein name -> ordered values).
RANKED_ORDERS = {
    "quarter": ["Q1", "Q2", "Q3", "Q4"],
    "month": [
        "Jan", "Feb", "Mar", "Apr", "May", "Jun",
        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
    ],
    "week": [f"W{i:02d}" for i in range(1, 13)],
    "stage": ["Applicants", "Screen", "Interview", "Offer", "Hired"],
    "phase": ["Lead", "Qualified", "Proposal", "Negotiation", "Won"],
    "age_band": ["0-9", "10-19", "20-29", "30-39", "40-49", "50-59", "60-69", "70+"],
    "response": ["Strongly disagree", "Disagree", "Neutral", "Agree", "Strongly agree"],
    "day": [f"D{i:02d}" for i in range(1, 15)],
    "period": [f"M{i:02d}" for i in range(1, 25)],
    "metric": ["p50", "p95", "p99"],
}


def _rows(cols, data):
    return [dict(zip(cols, r)) for r in data]


DATASETS = {
    # ------------------------------------------------------------------
    "quarterly_revenue": _rows(
        ("quarter", "product", "region", "revenue"),
        [
            ("Q1", "Aria", "Europe", 42), ("Q1", "Aria", "Americas", 55), ("Q1", "Aria", "Asia", 31),
            ("Q1", "Breeze", "Europe", 30), ("Q1", "Breeze", "Americas", 44), ("Q1", "Breeze", "Asia", 26),
            ("Q1", "Cove", "Europe", 21), ("Q1", "Cove", "Americas", 28), ("Q1", "Cove", "Asia", 19),
            ("Q2", "Aria", "Europe", 48), ("Q2", "Aria", "Americas", 58), ("Q2", "Aria", "Asia", 36),
            ("Q2", "Breeze", "Europe", 38), ("Q2", "Breeze", "Americas", 47), ("Q2", "Breeze", "Asia", 30),
            ("Q2", "Cove", "Europe", 25), ("Q2", "Cove", "Americas", 31), ("Q2", "Cove", "Asia", 22),
            ("Q3", "Aria", "Europe", 51), ("Q3", "Aria", "Americas", 61), ("Q3", "Aria", "Asia", 41),
            ("Q3", "Breeze", "Europe", 64), ("Q3", "Breeze", "Americas", 52), ("Q3", "Breeze", "Asia", 35),
            ("Q3", "Cove", "Europe", 28), ("Q3", "Cove", "Americas", 33), ("Q3", "Cove", "Asia", 24),
            ("Q4", "Aria", "Europe", 55), ("Q4", "Aria", "Americas", 66), ("Q4", "Aria", "Asia", 45),
            ("Q4", "Breeze", "Europe", 49), ("Q4", "Breeze", "Americas", 57), ("Q4", "Breeze", "Asia", 39),
            ("Q4", "Cove", "Europe", 33), ("Q4", "Cove", "Americas", 37), ("Q4", "Cove", "Asia", 27),
        ],
    ),
    # ------------------------------------------------------------------
    "monthly_finance": _rows(
        ("period", "revenue", "margin", "era"),
        [
            ("M01", 120, 8.1, "before launch"), ("M02", 124, 8.4, "before launch"),
            ("M03", 131, 9.0, "before launch"), ("M04", 128, 8.7, "before launch"),
            ("M05", 137, 9.6, "before launch"), ("M06", 142, 10.2, "before launch"),
            ("M07", 149, 10.8, "before launch"), ("M08", 146, 10.4, "before launch"),
            ("M09", 158, 11.5, "before launch"), ("M10", 164, 12.1, "before launch"),
            ("M11", 171, 12.6, "before launch"), ("M12", 169, 12.3, "before launch"),
            ("M13", 196, 14.9, "after launch"), ("M14", 210, 16.2, "after launch"),
            ("M15", 224, 17.8, "after launch"), ("M16", 219, 17.1, "after launch"),
            ("M17", 236, 18.9, "after launch"), ("M18", 248, 20.4, "after launch"),
            ("M19", 262, 21.8, "after launch"), ("M20", 255, 20.9, "after launch"),
            ("M21", 271, 22.7, "after launch"), ("M22", 284, 24.1, "after launch"),
            ("M23", 279, 23.4, "after launch"), ("M24", 295, 25.2, "after launch"),
        ],
    ),
    # ------------------------------------------------------------------
    "site_traffic": _rows(
        ("week", "channel", "visits"),
        [(w, c, v) for (w, quad) in [
            ("W01", (820, 410, 530, 190)), ("W02", (860, 445, 515, 205)),
            ("W03", (905, 480, 540, 220)), ("W04", (890, 520, 560, 215)),
            ("W05", (940, 575, 585, 235)), ("W06", (985, 640, 570, 250)),
            ("W07", (1010, 700, 595, 265)), ("W08", (990, 745, 620, 260)),
            ("W09", (1050, 815, 640, 280)), ("W10", (1085, 880, 625, 295)),
            ("W11", (1120, 950, 655, 310)), ("W12", (1160, 1030, 680, 330)),
        ] for c, v in zip(("Search", "Social", "Direct", "Email"), quad)],
    ),
    # ------------------------------------------------------------------
    "model_evals": _rows(
        ("model", "benchmark", "score"),
        [
            ("Kestrel", "Reasoning", 71.2), ("Kestrel", "Coding", 66.5),
            ("Kestrel", "Math", 58.9), ("Kestrel", "Recall", 80.4),
            ("Petrel", "Reasoning", 76.8), ("Petrel", "Coding", 72.1),
            ("Petrel", "Math", 64.3), ("Petrel", "Recall", 83.0),
            ("Osprey", "Reasoning", 82.5), ("Osprey", "Coding", 79.4),
            ("Osprey", "Math", 73.6), ("Osprey", "Recall", 86.2),
            ("Harrier", "Reasoning", 79.1), ("Harrier", "Coding", 83.8),
            ("Harrier", "Math", 69.0), ("Harrier", "Recall", 81.7),
            ("Merlin", "Reasoning", 88.3), ("Merlin", "Coding", 85.2),
            ("Merlin", "Math", 81.9), ("Merlin", "Recall", 90.1),
        ],
    ),
    # ------------------------------------------------------------------
    "survey_results": _rows(
        ("topic", "response", "share"),
        [
            ("Remote work", "Strongly disagree", 6), ("Remote work", "Disagree", 11),
            ("Remote work", "Neutral", 18), ("Remote work", "Agree", 37),
            ("Remote work", "Strongly agree", 28),
            ("Four-day week", "Strongly disagree", 4), ("Four-day week", "Disagree", 9),
            ("Four-day week", "Neutral", 15), ("Four-day week", "Agree", 33),
            ("Four-day week", "Strongly agree", 39),
            ("Open offices", "Strongly disagree", 24), ("Open offices", "Disagree", 31),
            ("Open offices", "Neutral", 22), ("Open offices", "Agree", 15),
            ("Open offices", "Strongly agree", 8),
        ],
    ),
    # ------------------------------------------------------------------
    "city_stats": _rows(
        ("city", "population", "growth", "transit_share", "continent"),
        [
            ("Lisbon", 0.55, 1.1, 22, "Europe"), ("Oslo", 0.71, 1.7, 34, "Europe"),
            ("Zurich", 0.43, 1.3, 41, "Europe"), ("Porto", 0.24, 0.8, 18, "Europe"),
            ("Austin", 0.98, 2.9, 6, "Americas"), ("Denver", 0.72, 2.1, 9, "Americas"),
            ("Montreal", 1.78, 1.4, 26, "Americas"), ("Medellin", 2.53, 1.9, 20, "Americas"),
            ("Fukuoka", 1.61, 0.9, 30, "Asia"), ("Da Nang", 1.19, 2.6, 8, "Asia"),
            ("Busan", 3.36, 0.3, 38, "Asia"), ("Chiang Mai", 0.43, 1.6, 5, "Asia"),
        ],
    ),
    # ------------------------------------------------------------------
    "age_distribution": _rows(
        ("age_band", "population"),
        [
            ("0-9", 11.8), ("10-19", 12.4), ("20-29", 13.9), ("30-39", 14.6),
            ("40-49", 13.2), ("50-59", 12.1), ("60-69", 10.4), ("70+", 11.6),
        ],
    ),
    # ------------------------------------------------------------------
    "hiring_funnel": _rows(
        ("stage", "candidates", "median_days"),
        [
            ("Applicants", 1240, 2), ("Screen", 420, 5), ("Interview", 160, 12),
            ("Offer", 45, 4), ("Hired", 32, 3),
        ],
    ),
    # ------------------------------------------------------------------
    "service_latency": _rows(
        ("service", "p50", "p99", "requests"),
        [
            ("Gateway", 12, 84, 980), ("Payments", 38, 210, 310),
            ("Orders", 27, 145, 425), ("Search", 44, 260, 615),
            ("Profiles", 19, 96, 245),
        ],
    ),
    # ------------------------------------------------------------------
    "sales_pipeline": _rows(
        ("phase", "deals", "value"),
        [
            ("Lead", 310, 4.9), ("Qualified", 186, 3.8), ("Proposal", 94, 2.9),
            ("Negotiation", 41, 1.8), ("Won", 27, 1.2),
        ],
    ),
    # ------------------------------------------------------------------
    "experiment_results": _rows(
        ("day", "variant", "conversion"),
        [(d, v, c) for (d, trio) in [
            ("D01", (3.1, 3.0, 3.2)), ("D02", (3.2, 3.4, 3.1)), ("D03", (3.0, 3.6, 3.3)),
            ("D04", (3.3, 3.8, 3.2)), ("D05", (3.1, 4.1, 3.4)), ("D06", (3.4, 4.0, 3.3)),
            ("D07", (3.2, 4.4, 3.5)), ("D08", (3.3, 4.6, 3.4)), ("D09", (3.1, 4.5, 3.6)),
            ("D10", (3.4, 4.9, 3.5)), ("D11", (3.3, 5.1, 3.7)), ("D12", (3.5, 5.0, 3.6)),
            ("D13", (3.4, 5.3, 3.8)), ("D14", (3.6, 5.6, 3.7)),
        ] for v, c in zip(("Control", "Variant B", "Variant C"), trio)],
    ),
    # ------------------------------------------------------------------
    "energy_mix": _rows(
        ("source", "share"),
        [
            ("Hydro", 28), ("Wind", 22), ("Solar", 14), ("Nuclear", 17),
            ("Gas", 13), ("Coal", 6),
        ],
    ),
    # ------------------------------------------------------------------
    "browser_share": _rows(
        ("browser", "share"),
        [("Chrome", 58), ("Safari", 21), ("Edge", 9), ("Firefox", 7), ("Other", 5)],
    ),
    # ------------------------------------------------------------------
    "feature_usage": _rows(
        ("feature", "users", "satisfaction"),
        [
            ("Dashboards", 4820, 4.1), ("Alerts", 3210, 3.6), ("Reports", 2940, 3.9),
            ("Exports", 1875, 3.2), ("Sharing", 1540, 4.4), ("API", 960, 3.8),
        ],
    ),
    # ------------------------------------------------------------------
    "ticket_resolution": _rows(
        ("ticket", "hours"),
        [
            ("T01", 1.2), ("T02", 2.8), ("T03", 0.6), ("T04", 4.1), ("T05", 3.3),
            ("T06", 1.9), ("T07", 7.4), ("T08", 2.2), ("T09", 0.9), ("T10", 5.6),
            ("T11", 3.8), ("T12", 2.4), ("T13", 1.5), ("T14", 9.2), ("T15", 4.7),
            ("T16", 2.9), ("T17", 1.1), ("T18", 6.3), ("T19", 3.1), ("T20", 2.0),
            ("T21", 12.5), ("T22", 4.4), ("T23", 1.7), ("T24", 3.6), ("T25", 2.6),
            ("T26", 8.1), ("T27", 1.4), ("T28", 5.2), ("T29", 2.3), ("T30", 3.9),
            ("T31", 0.8), ("T32", 6.8), ("T33", 2.7), ("T34", 1.6), ("T35", 4.9),
            ("T36", 10.3), ("T37", 3.4), ("T38", 2.1), ("T39", 1.8), ("T40", 5.9),
        ],
    ),
    # ------------------------------------------------------------------
    "latency_profile": _rows(
        ("service", "metric", "ms"),
        [
            ("Gateway", "p50", 12), ("Gateway", "p95", 41), ("Gateway", "p99", 84),
            ("Payments", "p50", 38), ("Payments", "p95", 122), ("Payments", "p99", 210),
            ("Orders", "p50", 27), ("Orders", "p95", 88), ("Orders", "p99", 145),
            ("Search", "p50", 44), ("Search", "p95", 150), ("Search", "p99", 260),
            ("Profiles", "p50", 19), ("Profiles", "p95", 60), ("Profiles", "p99", 96),
        ],
    ),
    # ------------------------------------------------------------------
    "milestones": _rows(
        ("milestone", "week", "impact"),
        [
            ("Kickoff", "W01", 2), ("Design freeze", "W03", 4),
            ("Alpha", "W05", 6), ("Beta", "W08", 8),
            ("Launch", "W10", 10), ("Retrospective", "W12", 3),
        ],
    ),
    # ------------------------------------------------------------------
    "final_month_mix": _rows(
        ("product", "revenue"),
        [("Aria", 128), ("Breeze", 102), ("Cove", 65)],
    ),
    # ------------------------------------------------------------------
    "team_allocation": _rows(
        ("team", "project", "engineers"),
        [
            ("Platform", "Atlas", 6), ("Platform", "Beacon", 4), ("Platform", "Cinder", 2),
            ("Product", "Atlas", 3), ("Product", "Beacon", 7), ("Product", "Cinder", 5),
            ("Infra", "Atlas", 5), ("Infra", "Beacon", 2), ("Infra", "Cinder", 3),
        ],
    ),
}


def vein_kind(name, values):
    """Infer a vein's kind from its name and values."""
    if all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in values):
        return "counted"
    if name in RANKED_ORDERS:
        return "ranked"
    return "told"


def ranked_sort_key(vein, value):
    order = RANKED_ORDERS.get(vein)
    if order and value in order:
        return order.index(value)
    return value
