"""
local_pipeline_dag.py

Orchestrates the local development pipeline loop.

What this DAG does:
    1. Verifies the Pub/Sub emulator is reachable and the topic exists
    2. Runs the producer for a fixed duration (60s by default) to generate
       a batch of transactions
    3. Runs the Beam pipeline with DirectRunner to consume those messages,
       score them, and write results to BigQuery

This runs on a schedule during active development so you always have fresh
data in BigQuery without having to manually start/stop the producer and
pipeline in separate terminals.

This DAG is intentionally simple — no sensors, no complex branching. It's a
local dev tool, not a production pipeline. The Beam pipeline in step 3 runs
as a subprocess that exits once the emulator subscription is drained (using
a max_messages approach rather than running indefinitely).

Schedule: every 30 minutes during business hours (so BigQuery data stays
fresh while you're working without burning CPU overnight).
"""

import subprocess
import os
import sys
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator

# ---------------------------------------------------------------------------
# Paths — resolve relative to the repo root mounted into the Airflow container
# ---------------------------------------------------------------------------
REPO_ROOT = os.environ.get("REPO_ROOT", "/opt/airflow/repo")
PRODUCER_DIR = os.path.join(REPO_ROOT, "producer")
PIPELINE_DIR = os.path.join(REPO_ROOT, "pipeline")
VENV_PYTHON = os.environ.get("VENV_PYTHON", sys.executable)

# How many seconds to run the producer before stopping it.
# 60s at 0.5s/message = ~120 transactions per run, enough for meaningful
# windowed aggregates without flooding the emulator.
PRODUCER_RUN_SECONDS = 60

# ---------------------------------------------------------------------------
# Default args
# ---------------------------------------------------------------------------
default_args = {
    "owner": "spencer",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
    "email_on_failure": False,
}

# ---------------------------------------------------------------------------
# Task functions
# ---------------------------------------------------------------------------

def check_emulator(**context):
    """
    Verify the Pub/Sub emulator is up and the b2b-transactions topic exists.
    Fails fast so the rest of the DAG doesn't run against a missing emulator.
    """
    import urllib.request
    import json

    emulator_host = os.environ.get("PUBSUB_EMULATOR_HOST", "pubsub-emulator:8085")
    url = f"http://{emulator_host}/v1/projects/local-dev-project/topics"

    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            data = json.loads(response.read())
            topics = [t["name"] for t in data.get("topics", [])]
            target = "projects/local-dev-project/topics/b2b-transactions"
            if target not in topics:
                raise RuntimeError(
                    f"Topic '{target}' not found on emulator. "
                    f"Run init_emulator.py first. Found: {topics}"
                )
            print(f"✅ Emulator healthy. Found topic: {target}")
    except Exception as e:
        raise RuntimeError(f"Pub/Sub emulator check failed: {e}")


def run_producer(**context):
    """
    Run the producer as a subprocess for PRODUCER_RUN_SECONDS, then kill it.
    We use --delay 0.2 for faster throughput during scheduled runs.
    """
    import signal
    import time

    cmd = [
        VENV_PYTHON,
        os.path.join(PRODUCER_DIR, "producer.py"),
        "--inject-anomalies",
        "--delay", "0.2",
    ]

    env = {**os.environ, "PUBSUB_EMULATOR_HOST": "pubsub-emulator:8085"}
    print(f"Starting producer for {PRODUCER_RUN_SECONDS}s: {' '.join(cmd)}")

    proc = subprocess.Popen(cmd, cwd=PRODUCER_DIR, env=env)

    time.sleep(PRODUCER_RUN_SECONDS)
    proc.send_signal(signal.SIGINT)
    proc.wait(timeout=10)

    print(f"✅ Producer finished. Return code: {proc.returncode}")


def run_beam_pipeline(**context):
    """
    Run the Beam DirectRunner pipeline. The pipeline runs in streaming mode
    and would normally run forever — we let it run for long enough to drain
    the messages the producer just generated, then stop it.

    In practice, 90 seconds is enough for DirectRunner to consume ~120 messages
    through the full scoring + windowing + BigQuery write path.
    """
    import signal
    import time

    cmd = [
        VENV_PYTHON,
        os.path.join(PIPELINE_DIR, "beam_pipeline.py"),
    ]

    env = {
        **os.environ,
        "PUBSUB_EMULATOR_HOST": "localhost:8085",
        "GOOGLE_CLOUD_PROJECT": os.environ.get(
            "GOOGLE_CLOUD_PROJECT", "portfolio-analytics-499108"
        ),
    }

    print(f"Starting Beam pipeline (DirectRunner): {' '.join(cmd)}")
    proc = subprocess.Popen(cmd, cwd=PIPELINE_DIR, env=env)

    # Give it 90s to process the batch from the producer
    time.sleep(90)
    proc.send_signal(signal.SIGINT)
    proc.wait(timeout=30)

    print(f"✅ Beam pipeline finished. Return code: {proc.returncode}")


# ---------------------------------------------------------------------------
# DAG definition
# ---------------------------------------------------------------------------
with DAG(
    dag_id="local_pipeline_dev",
    description="Local dev loop: producer → Beam DirectRunner → BigQuery",
    default_args=default_args,
    start_date=datetime(2026, 1, 1),
    schedule_interval="*/30 8-18 * * 1-5",  # every 30 min, business hours, weekdays
    catchup=False,
    tags=["local", "dev", "pipeline"],
) as dag:

    check_emulator_task = PythonOperator(
        task_id="check_pubsub_emulator",
        python_callable=check_emulator,
        doc_md="""
        Verifies the Pub/Sub emulator is running and the b2b-transactions topic exists.
        Fails immediately if the emulator is down so we don't waste time running
        the producer against nothing.
        """,
    )

    run_producer_task = PythonOperator(
        task_id="run_producer",
        python_callable=run_producer,
        doc_md="""
        Runs the transaction producer for 60 seconds with anomaly injection.
        Publishes ~120 transactions to the local Pub/Sub emulator.
        """,
    )

    run_pipeline_task = PythonOperator(
        task_id="run_beam_pipeline",
        python_callable=run_beam_pipeline,
        doc_md="""
        Runs the Beam DirectRunner pipeline for 90 seconds to consume and
        score the messages generated by the producer, then writes results
        to BigQuery (real GCP, always).
        """,
    )

    # Dependencies: check emulator → produce messages → process messages
    check_emulator_task >> run_producer_task >> run_pipeline_task