"""
Entry point for the Olist data-quality layer.

Runs a Great Expectations checkpoint against every mart table listed in
SUITES, after dbt has materialized them in Snowflake. Wired into
.github/workflows/dbt_cd.yml immediately after `dbt run --target prod`, so
these checks run against the tables that were just built, not stale data.

Exits non-zero if any expectation fails, which fails the CI/CD job the same
way a failed `dbt test` would.
"""
import sys

from context import build_context, build_validator
from suites import dim_sellers, fct_b2b2c_attribution, fct_orders

SUITES = [fct_orders, dim_sellers, fct_b2b2c_attribution]


def run_suite(context, suite_module) -> bool:
    validator = build_validator(context, suite_module.TABLE_NAME, suite_module.SUITE_NAME)

    for expectation_type, kwargs in suite_module.EXPECTATIONS:
        getattr(validator, expectation_type)(**kwargs)

    validator.save_expectation_suite(discard_failed_expectations=False)

    checkpoint = context.add_or_update_checkpoint(
        name=f"{suite_module.TABLE_NAME}_checkpoint",
        validator=validator,
    )
    result = checkpoint.run()
    return bool(result.success)


def main() -> int:
    context = build_context()

    all_passed = True
    for suite_module in SUITES:
        print(f"\n=== Running quality checks: {suite_module.TABLE_NAME} ===")
        passed = run_suite(context, suite_module)
        print(f"{'PASSED' if passed else 'FAILED'}: {suite_module.TABLE_NAME}")
        all_passed = all_passed and passed

    context.build_data_docs()  # local HTML report at quality/gx/uncommitted/data_docs/

    if not all_passed:
        print("\nOne or more data quality checks failed.")
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
