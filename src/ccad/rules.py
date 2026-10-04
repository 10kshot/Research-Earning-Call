"""Rule book v1: fixed constants every later step depends on.

Changes here after return data has been examined must be logged in
docs/rulebook_changelog.md with the date and reason.
"""

RULEBOOK_VERSION = "v1"

# Fixed claim dimensions. `margin` is used for AD only, never for CC matching.
DIMENSIONS = (
    "end_demand",
    "orders_backlog",
    "inventory_own",
    "inventory_downstream",
    "selling_price",
    "input_cost",
    "capacity_supply",
    "capex_procurement",
    "margin",
)
AD_ONLY_DIMENSIONS = {"margin"}

SUBJECT_SCOPES = ("own", "named_counterparty", "anonymous_counterparty", "end_market", "industry")
HORIZON_REFS = ("fiscal_quarter", "calendar", "relative", "unspecified")
COMPARISON_BASES = ("sequential", "year_over_year", "unspecified")
SEGMENTS = ("prepared", "qa")

DIRECTION_RANGE = (-2, 2)  # 5-point ordinal for the *change* over the target period
HEDGE_LEVELS = (0, 1, 2)  # 0 plain, 1 qualified, 2 heavily hedged
MAX_HEDGE_FOR_CC = 1  # hedge == 2 is excluded from level-contradiction scoring

REJECTION_REASONS = ("no_direction", "no_horizon", "reported_fact", "boilerplate")

# Mapping table: (supplier dimension, customer dimension, expected sign, allowed lag in quarters).
# Lag = customer target quarter minus supplier target quarter.
MAPPING_TABLE = (
    ("inventory_downstream", "inventory_own", +1, (0, 0)),
    ("selling_price", "input_cost", +1, (0, 0)),
    ("orders_backlog", "capex_procurement", +1, (0, 0)),
    ("orders_backlog", "end_demand", +1, (0, 1)),
    ("capacity_supply", "capacity_supply", +1, (0, 0)),
)

# Resolution labels and evidence tiers.
LABELS = ("right", "wrong", "flat", "early", "late", "conflicted", "unresolved")
TIERS = ("A", "B", "C")  # C = later manager statements; robustness only, never clears a claim
NO_CALL_ZONE_SD = 1.0  # |seasonal-adjusted change| <= 1 SD counts as flat
SEASONAL_BASELINE_YEARS = (3, 5)
CHECK_DATE_EXTRA_QUARTERS = 1  # first-reported numbers for target_end, plus one quarter

# Extraction validation bar on the held-out gold set.
VALIDATION_BAR = {
    "dimension_accuracy": 0.85,
    "direction_accuracy": 0.80,
    "opposite_sign_error_max": 0.05,
}

# Credibility score shrinkage (pseudo-count toward the sample mean).
CREDIBILITY_PRIOR_WEIGHT = 10
