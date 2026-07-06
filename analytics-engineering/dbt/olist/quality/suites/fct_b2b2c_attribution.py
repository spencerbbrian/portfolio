"""
Checks for fct_b2b2c_attribution that complement the not_null tests already
enforced natively in models/mart/fct_b2b2c_attribution.yml.
"""

TABLE_NAME = "fct_b2b2c_attribution"
SUITE_NAME = "fct_b2b2c_attribution_suite"

EXPECTATIONS = [
    ("expect_table_row_count_to_be_between", {"min_value": 1000, "max_value": 600_000}),

    ("expect_column_values_to_be_between", {
        "column": "attributed_revenue", "min_value": 0, "max_value": 50_000,
    }),
    ("expect_column_values_to_be_between", {
        "column": "attributed_freight", "min_value": 0, "max_value": 5_000,
    }),

    # attributed_total_value = attributed_revenue + attributed_freight, so it
    # should never be smaller than attributed_revenue alone.
    ("expect_column_pair_values_a_to_be_greater_than_b", {
        "column_A": "attributed_total_value",
        "column_B": "attributed_revenue",
        "or_equal": True,
        "ignore_row_if": "either_value_is_missing",
    }),
]
