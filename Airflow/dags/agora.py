from __future__ import annotations
import pendulum
from airflow.models.dag import DAG
from airflow.operators.bash import BashOperator # Import the BashOperator
import sys
import os

# --- CRITICAL: Set the internal path to the dbt project directory ---
DBT_PROJECT_DIR = '/opt/airflow/dbt'  # Assuming you mounted the dbt project here

# --- Dbt Profile Configuration (used by dbt CLI) ---
# NOTE: This target name must match the 'target' defined in your profiles.yml
DBT_TARGET = 'dev' 

with DAG(
    dag_id="agora_dbt_transform_load",
    schedule="0 5 * * *", # Runs daily 1 hour *after* the Python data load (04:00 AM)
    start_date=pendulum.datetime(2025, 11, 24, tz="UTC"),
    catchup=False,
    tags=["supply_chain", "dbt", "snowflake"],
) as dag:
    
    # Task 1: Execute the entire transactional generation and raw data load (This is the Python part, kept separate)
    # NOTE: You would typically run your Python script first to load the raw data. 
    # For this example, we assume that task is Task 1 and dbt is Task 2.
    
    # Task 2: Run the dbt transformation models
    run_dbt_models = BashOperator(
        task_id="run_dbt_transformations",
        # The command executes dbt run from the project directory, targeting the dev profile.
        bash_command=f"""
        cd {DBT_PROJECT_DIR} && \
        dbt run --project-dir . --target {DBT_TARGET} --profiles-dir /usr/local/airflow/.dbt
        """,
        # NOTE: The profiles-dir path must point to where your dbt profiles.yml is located.
        # If running inside a container without a custom profile volume, adjust this path.
        env={
            # You can inject environment variables required by your dbt profiles.yml here
            'DBT_USER': 'teamuser',
            'DBT_WAREHOUSE': 'COMPUTE_WH',
        }
    )
    
    # (If you had a preceding Python task named 'load_raw_data', the dependency would be: 
    # load_raw_data >> run_dbt_models)