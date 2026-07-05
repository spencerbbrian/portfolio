"""
Checks for dim_sellers that complement the not_null / unique tests already
enforced natively in models/mart/dim_sellers.yml.
"""

TABLE_NAME = "dim_sellers"
SUITE_NAME = "dim_sellers_suite"

KNOWN_MARKETING_CHANNELS = [
    "organic_platform",
    "paid_ads",
    "search",
    "social",
    "referral",
    "email",
    "other",
]

EXPECTATIONS = [
    ("expect_table_row_count_to_be_between", {"min_value": 100, "max_value": 20_000}),

    # Belt-and-suspenders: seller_id is already tested `unique` in dbt, but
    # this is a second, independent system asserting the same grain.
    ("expect_column_proportion_of_unique_values_to_be_between", {
        "column": "seller_id", "min_value": 1.0, "max_value": 1.0,
    }),

    ("expect_column_values_to_be_in_set", {
        "column": "is_funnel_acquired",
        "value_set": [True, False],
    }),

    # `mostly` allows a small percentage of unrecognized channels through
    # without hard-failing the whole batch -- a soft tolerance dbt's
    # pass/fail accepted_values test doesn't support.
    ("expect_column_values_to_be_in_set", {
        "column": "marketing_channel",
        "value_set": KNOWN_MARKETING_CHANNELS,
        "mostly": 0.95,
    }),
]
