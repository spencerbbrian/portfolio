Welcome to your new dbt project!

### Using the starter project

Try running the following commands:
- dbt run
- dbt test


### Resources:
- Learn more about dbt [in the docs](https://docs.getdbt.com/docs/introduction)
- Check out [Discourse](https://discourse.getdbt.com/) for commonly asked questions and answers


Stage 1:
Prepare and sync data on snowflake through dbt and using a seed for now.
Data Sources: Sample generated data with python for now.
Environment setup: Configured dbt and snowflake with the necessary developer roles as well.
ROLE: DBT_DEVELOPER
DATABASE: DBT_ANALYTICS


Stage 2:
Objective: Enhance the project by implementing incremental models for frequently updated data, using materialized views for key aggregate tables, and adding more robust data quality checks.
- Task 1: Create a new dbt model that processes new order     records.
- Task 2: Use the materialied incremental configuration for the stg_orders.sql.
- Task 3: Test Incremental model
- Task 4: Create a daily sales summary model
- Task 5: Configure as materialized view
- Task 6: Test materialized view
- Task 7: Add a freshness test for sources
- Task 8: Implement a customer singularity test for customers having at least one order.
- Task 9: Create a custome aggregate test to ensure completed orders in in daily summary matches the orders that are marked as completed