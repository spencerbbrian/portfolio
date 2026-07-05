"""
Builds a Great Expectations Data Context wired to the same Snowflake
database that dbt writes to (OLIST_DB). Connection details are read from
the same environment variables already used by the dbt CI/CD Snowflake
profile (see .github/workflows/dbt_cd.yml), so this reuses the existing
GitHub Actions secrets instead of needing a second set of credentials.
"""
import os

import great_expectations as gx
from great_expectations.data_context import AbstractDataContext

DATASOURCE_NAME = "olist_snowflake"
DATABASE = "OLIST_DB"


def build_context() -> AbstractDataContext:
    """Return an ephemeral GX context with the olist Snowflake datasource registered."""
    context = gx.get_context(mode="ephemeral")

    context.sources.add_or_update_snowflake(
        name=DATASOURCE_NAME,
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USER"],
        password=os.environ["SNOWFLAKE_PASSWORD"],
        role=os.environ["SNOWFLAKE_ROLE"],
        warehouse=os.environ["SNOWFLAKE_WAREHOUSE"],
        database=DATABASE,
        schema=os.environ.get("SNOWFLAKE_SCHEMA", "PROD"),
    )
    return context


def build_validator(context: AbstractDataContext, table_name: str, suite_name: str):
    """Return a Validator bound to `table_name`, backed by a (re)created expectation suite.

    Safe to call repeatedly across suites/runs — both the table asset and the
    expectation suite are created idempotently.
    """
    datasource = context.get_datasource(DATASOURCE_NAME)

    existing_assets = {asset.name for asset in datasource.assets}
    asset = (
        datasource.get_asset(table_name)
        if table_name in existing_assets
        else datasource.add_table_asset(name=table_name, table_name=table_name)
    )

    batch_request = asset.build_batch_request()
    context.add_or_update_expectation_suite(suite_name)

    return context.get_validator(
        batch_request=batch_request,
        expectation_suite_name=suite_name,
    )
