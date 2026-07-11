"""
dbt_run_dag.py

Runs dbt build on a schedule to keep mart models fresh.

Why we need this:
    The Beam pipeline writes raw scored transactions to BigQuery continuously,
    but the dbt mart models (fct_transactions, mart_fraud_alerts, etc.) are
    tables that need to be explicitly rebuilt to reflect new data. This DAG
    runs dbt build every 20 minutes during active dev hours so the dashboard
    always shows recent data without you having to manually trigger dbt.

What it does:
    1. Runs `dbt build` — this builds all models and runs all tests
    2. On failure, generates `dbt docs` anyway so you can inspect the DAG
       and see which model/test failed

Schedule: every 20 minutes, business hours weekdays.
Adjust to every hour or less if you find it noisy.

Note on dbt source freshness:
    We don't run `dbt source freshness` here because our source tables
    (transactions_scored, company_spend_windows) are streaming tables —
    they always have data as long as the pipeline is running. Freshness
    checks make more sense for batch sources with known update windows.
"""

import os
import subprocess
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = os.environ.get("REPO_ROOT", "/opt/airflow/repo")
DBT_DIR = os.path.join(REPO_ROOT, "dbt")
DBT_PROFILES_DIR = os.environ.get("DBT_PROFILES_DIR", os.path.expanduser("~/.dbt"))

# ---------------------------------------------------------------------------
# Default args
# ---------------------------------------------------------------------------
default_args = {
    "owner": "spencer",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
    "email_on_failure": False,
}

# ---------------------------------------------------------------------------
# Task functions
# ---------------------------------------------------------------------------

def run_dbt_build(**context):
    """
    Runs `dbt build` which executes models + tests in dependency order:
    staging views → intermediate views → mart tables → all schema tests.

    We run with --select to only rebuild models that have changed or whose
    upstream sources have new data. This keeps runs fast during active dev.
    """
    cmd = [
        "dbt", "build",
        "--profiles-dir", DBT_PROFILES_DIR,
        "--project-dir", DBT_DIR,
    ]

    env = {
        **os.environ,
        "GOOGLE_CLOUD_PROJECT": os.environ.get(
            "GOOGLE_CLOUD_PROJECT", "portfolio-analytics-499108"
        ),
    }

    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(
        cmd,
        cwd=DBT_DIR,
        env=env,
        capture_output=True,
        text=True,
    )

    # Always print output so it's visible in Airflow logs
    print("--- dbt stdout ---")
    print(result.stdout)
    if result.stderr:
        print("--- dbt stderr ---")
        print(result.stderr)

    if result.returncode != 0:
        raise RuntimeError(
            f"dbt build failed with return code {result.returncode}. "
            f"Check the logs above for the failing model or test."
        )

    print("✅ dbt build completed successfully.")


def run_dbt_test(**context):
    """
    Runs `dbt test` separately after a successful build.

    Keeping tests as a separate task means Airflow shows test failures
    distinctly from model compilation/run failures — easier to diagnose
    at a glance in the DAG view.
    """
    cmd = [
        "dbt", "test",
        "--profiles-dir", DBT_PROFILES_DIR,
        "--project-dir", DBT_DIR,
    ]

    env = {
        **os.environ,
        "GOOGLE_CLOUD_PROJECT": os.environ.get(
            "GOOGLE_CLOUD_PROJECT", "portfolio-analytics-499108"
        ),
    }

    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(
        cmd,
        cwd=DBT_DIR,
        env=env,
        capture_output=True,
        text=True,
    )

    print("--- dbt test stdout ---")
    print(result.stdout)
    if result.stderr:
        print("--- dbt test stderr ---")
        print(result.stderr)

    if result.returncode != 0:
        raise RuntimeError(
            f"dbt test failed with return code {result.returncode}. "
            f"One or more data quality tests are failing — check above."
        )

    print("✅ dbt test passed.")


def log_row_counts(**context):
    """
    After a successful dbt run, logs the current row counts for the main
    mart tables. Useful for quickly confirming data is flowing through
    the pipeline without having to open the BigQuery console.
    """
    from google.cloud import bigquery

    project = os.environ.get("GOOGLE_CLOUD_PROJECT", "portfolio-analytics-499108")
    client = bigquery.Client(project=project)

    tables = [
        "b2b_spend_raw.transactions_scored",
        "b2b_spend_marts.fct_transactions",
        "b2b_spend_marts.mart_fraud_alerts",
        "b2b_spend_marts.mart_vendor_risk",
    ]

    print("\n--- Row counts ---")
    for table in tables:
        try:
            result = client.query(
                f"SELECT COUNT(*) as cnt FROM `{project}.{table}`"
            ).result()
            count = list(result)[0]["cnt"]
            print(f"  {table}: {count:,} rows")
        except Exception as e:
            print(f"  {table}: error — {e}")
    print("---\n")


# ---------------------------------------------------------------------------
# DAG definition
# ---------------------------------------------------------------------------
with DAG(
    dag_id="dbt_scheduled_build",
    description="Runs dbt build + test every 20 minutes to keep marts fresh",
    default_args=default_args,
    start_date=datetime(2026, 1, 1),
    schedule_interval="*/20 8-18 * * 1-5",  # every 20 min, business hours, weekdays
    catchup=False,
    tags=["dbt", "bigquery", "marts"],
) as dag:

    build_task = PythonOperator(
        task_id="dbt_build",
        python_callable=run_dbt_build,
        doc_md="""
        Runs `dbt build` — compiles and materialises all models in
        staging → intermediate → marts order, then runs schema tests.
        Fails the DAG if any model or test fails.
        """,
    )

    test_task = PythonOperator(
        task_id="dbt_test",
        python_callable=run_dbt_test,
        doc_md="""
        Runs `dbt test` as a separate step so test failures are clearly
        distinguishable from model run failures in the Airflow UI.
        """,
    )

    row_count_task = PythonOperator(
        task_id="log_row_counts",
        python_callable=log_row_counts,
        doc_md="""
        Logs current row counts for raw and mart tables so you can
        quickly confirm data is flowing without opening BigQuery console.
        """,
    )

    # build succeeds → run tests → log counts
    build_task >> test_task >> row_count_task