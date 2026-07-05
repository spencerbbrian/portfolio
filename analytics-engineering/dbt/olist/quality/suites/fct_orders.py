"""
Checks for fct_orders that complement (rather than duplicate) the
not_null / unique / accepted_values tests already enforced natively in
models/mart/fct_orders.yml.
"""

TABLE_NAME = "fct_orders"
SUITE_NAME = "fct_orders_suite"

# Olist's known order lifecycle statuses. fct_orders.yml doesn't test
# order_status against a value set today -- filled in here instead.
VALID_ORDER_STATUSES = [
    "created",
    "approved",
    "processing",
    "invoiced",
    "shipped",
    "delivered",
    "canceled",
    "unavailable",
]

EXPECTATIONS = [
    # Volume anomaly: catches a load that silently drops or duplicates rows.
    ("expect_table_row_count_to_be_between", {"min_value": 1000, "max_value": 500_000}),

    ("expect_column_values_to_be_in_set", {
        "column": "order_status",
        "value_set": VALID_ORDER_STATUSES,
    }),

    # Financial sanity: no negative money, no absurd outlier order values.
    ("expect_column_values_to_be_between", {
        "column": "total_items_price", "min_value": 0, "max_value": 50_000,
    }),
    ("expect_column_values_to_be_between", {
        "column": "total_freight_value", "min_value": 0, "max_value": 5_000,
    }),
    ("expect_column_values_to_be_between", {
        "column": "total_order_item_value", "min_value": 0, "max_value": 55_000,
    }),

    # Temporal integrity across two columns on the same row -- dbt's generic
    # tests can't compare two columns without a custom singular test macro;
    # GE expresses this natively.
    ("expect_column_pair_values_a_to_be_greater_than_b", {
        "column_A": "delivered_customer_date",
        "column_B": "purchase_date",
        "or_equal": True,
        "ignore_row_if": "either_value_is_missing",
    }),
    ("expect_column_pair_values_a_to_be_greater_than_b", {
        "column_A": "delivered_carrier_date",
        "column_B": "approved_date",
        "or_equal": True,
        "ignore_row_if": "either_value_is_missing",
    }),

    # Distribution drift: average order value moving far outside its known
    # historical band is exactly what a warehouse-level anomaly check (as
    # opposed to a per-row test) is meant to catch.
    ("expect_column_mean_to_be_between", {
        "column": "total_order_item_value", "min_value": 50, "max_value": 400,
    }),
]
