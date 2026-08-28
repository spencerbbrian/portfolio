"""
Entry point Dagster looks for when you run `dagster dev`. This turns the
existing churn_radar dbt project (staging -> intermediate -> marts) into
real Dagster assets -- one asset per dbt model, wired together in the same
dependency graph dbt already knows about.
"""
import os
import time
from pathlib import Path

import dagster as dg
import requests
from dagster_dbt import DbtCliResource, DbtProject, dbt_assets
from dotenv import load_dotenv
from google.cloud import bigquery

# Loads AIRBYTE_CLIENT_ID / AIRBYTE_CLIENT_SECRET from a local .env file
# (gitignored -- see .env.example for the template) instead of hardcoding
# secrets in this file, which is committed to a public repo.
load_dotenv(Path(__file__).parent / ".env")

# Same service account key used for dbt's BigQuery profile.
GCP_PROJECT = "portfolio-analytics-499108"
GCP_KEYFILE = "/Users/spencer/Desktop/Important Keys etc/portfolio-analytics-499108-9435a03839e5.json"

AIRBYTE_CONNECTION_ID = "029c1db7-1133-4471-8fa5-171b0d270057"

# Path to the dbt project, relative to this file.
DBT_PROJECT_DIR = Path(__file__).joinpath("..", "..", "dbt", "churn_radar").resolve()

dbt_project = DbtProject(
    project_dir=DBT_PROJECT_DIR,
    profiles_dir=str(Path.home() / ".dbt"),
)

# In dev, this makes sure dbt's manifest.json (the file describing every
# model and how they depend on each other) is freshly generated before
# Dagster tries to read it.
dbt_project.prepare_if_dev()


@dbt_assets(manifest=dbt_project.manifest_path)
def churn_radar_dbt_assets(context: dg.AssetExecutionContext, dbt: DbtCliResource):
    """One Dagster asset per dbt model. Running this asset runs `dbt build`."""
    yield from dbt.cli(["build"], context=context).stream()


def _get_airbyte_token() -> str:
    """Exchanges the client_id/secret for a short-lived (15 min) bearer token."""
    response = requests.post(
        "https://api.airbyte.com/v1/applications/token",
        json={
            "client_id": os.environ["AIRBYTE_CLIENT_ID"],
            "client_secret": os.environ["AIRBYTE_CLIENT_SECRET"],
        },
        timeout=30,
    )
    response.raise_for_status()
    return response.json()["access_token"]


@dg.asset
def airbyte_sync(context: dg.AssetExecutionContext) -> dg.MaterializeResult:
    """Triggers the Airbyte Cloud sync for Churn Radar and waits for it to finish."""
    token = _get_airbyte_token()
    headers = {"Authorization": f"Bearer {token}"}

    trigger = requests.post(
        "https://api.airbyte.com/v1/jobs",
        headers=headers,
        json={"connectionId": AIRBYTE_CONNECTION_ID, "jobType": "sync"},
        timeout=30,
    )
    trigger.raise_for_status()
    job = trigger.json()
    job_id = job["jobId"]
    context.log.info(f"Triggered Airbyte sync -- job_id={job_id}")

    status = job["status"]
    while status in ("pending", "running", "incomplete"):
        time.sleep(15)
        poll = requests.get(
            f"https://api.airbyte.com/v1/jobs/{job_id}", headers=headers, timeout=30
        )
        poll.raise_for_status()
        status = poll.json()["status"]
        context.log.info(f"Airbyte sync status: {status}")

    if status != "succeeded":
        raise Exception(f"Airbyte sync did not succeed -- final status: {status}")

    return dg.MaterializeResult(metadata={"job_id": job_id, "status": status})


@dg.asset_check(asset=dg.AssetKey(["fct_churn_risk"]), blocking=True)
def health_score_in_range(context: dg.AssetCheckExecutionContext) -> dg.AssetCheckResult:
    """Fails if any customer's health_score falls outside the valid 0-100 range."""
    client = bigquery.Client.from_service_account_json(GCP_KEYFILE, project=GCP_PROJECT)
    query = f"""
        SELECT COUNT(*) AS bad_rows
        FROM `{GCP_PROJECT}.churn_radar_dev.fct_churn_risk`
        WHERE health_score IS NOT NULL
          AND (health_score < 0 OR health_score > 100)
    """
    bad_rows = list(client.query(query).result())[0]["bad_rows"]
    return dg.AssetCheckResult(
        passed=bad_rows == 0,
        metadata={"bad_rows": bad_rows},
    )


def _chunks(items, size):
    for i in range(0, len(items), size):
        yield items[i : i + size]


@dg.asset(deps=[dg.AssetKey(["fct_churn_risk"])])
def hubspot_sync(context: dg.AssetExecutionContext) -> dg.MaterializeResult:
    """Pushes health_score and churn_risk_tier from fct_churn_risk into HubSpot
    Company records, upserted by customer_id. Only runs if the upstream
    health_score_in_range check passed (it's a blocking check)."""
    bq = bigquery.Client.from_service_account_json(GCP_KEYFILE, project=GCP_PROJECT)
    rows = list(
        bq.query(
            f"""
            SELECT customer_id, company_name, health_score, churn_risk_tier
            FROM `{GCP_PROJECT}.churn_radar_dev.fct_churn_risk`
            """
        ).result()
    )

    headers = {
        "Authorization": f"Bearer {os.environ['HUBSPOT_ACCESS_TOKEN']}",
        "Content-Type": "application/json",
    }

    synced = 0
    for batch in _chunks(rows, 100):
        inputs = [
            {
                "idProperty": "customer_id",
                "id": row["customer_id"],
                "properties": {
                    "customer_id": row["customer_id"],
                    "name": row["company_name"],
                    "churn_risk_tier": row["churn_risk_tier"],
                    "health_score": row["health_score"],
                },
            }
            for row in batch
        ]
        resp = requests.post(
            "https://api.hubapi.com/crm/v3/objects/companies/batch/upsert",
            headers=headers,
            json={"inputs": inputs},
            timeout=60,
        )
        if not resp.ok:
            context.log.error(f"HubSpot error response: {resp.text}")
        resp.raise_for_status()
        synced += len(batch)
        context.log.info(f"Synced {synced}/{len(rows)} companies to HubSpot")

    return dg.MaterializeResult(metadata={"companies_synced": synced})


@dg.asset(deps=[dg.AssetKey(["fct_churn_risk"])])
def slack_alert(context: dg.AssetExecutionContext) -> dg.MaterializeResult:
    """Posts a Slack alert listing customers currently in the Critical risk
    tier. Only runs if the upstream health_score_in_range check passed."""
    bq = bigquery.Client.from_service_account_json(GCP_KEYFILE, project=GCP_PROJECT)
    rows = list(
        bq.query(
            f"""
            SELECT company_name, health_score
            FROM `{GCP_PROJECT}.churn_radar_dev.fct_churn_risk`
            WHERE churn_risk_tier = 'Critical'
            ORDER BY health_score ASC
            """
        ).result()
    )

    if not rows:
        text = "Churn Radar: no customers in the Critical risk tier right now."
    else:
        lines = [f"*Churn Radar: {len(rows)} customer(s) at Critical risk*"]
        for row in rows[:10]:
            lines.append(f"- {row['company_name']} (health score: {row['health_score']})")
        if len(rows) > 10:
            lines.append(f"...and {len(rows) - 10} more.")
        text = "\n".join(lines)

    resp = requests.post(
        os.environ["SLACK_WEBHOOK_URL"],
        json={"text": text},
        timeout=30,
    )
    if not resp.ok:
        context.log.error(f"Slack error response: {resp.text}")
    resp.raise_for_status()

    return dg.MaterializeResult(metadata={"critical_customers": len(rows)})


churn_radar_job = dg.define_asset_job(
    name="churn_radar_dbt_job",
    selection=[churn_radar_dbt_assets, hubspot_sync, slack_alert],
)

airbyte_sync_job = dg.define_asset_job(
    name="airbyte_sync_job",
    selection=[airbyte_sync],
)

# Schedule now triggers the Airbyte sync, not dbt directly.
airbyte_sync_schedule = dg.ScheduleDefinition(
    job=airbyte_sync_job,
    cron_schedule="0 6 * * *",  # every day at 6am
)


# Fires automatically whenever airbyte_sync finishes materializing --
# whether that happened via the schedule above or a manual trigger --
# and kicks off the dbt job right after. This is the piece that makes
# "new raw data landed" automatically cause "rebuild the models."
@dg.asset_sensor(asset_key=dg.AssetKey("airbyte_sync"), job=churn_radar_job)
def run_dbt_after_sync_sensor(context: dg.SensorEvaluationContext, asset_event):
    yield dg.RunRequest(run_key=context.cursor)


defs = dg.Definitions(
    assets=[churn_radar_dbt_assets, airbyte_sync, hubspot_sync, slack_alert],
    asset_checks=[health_score_in_range],
    jobs=[churn_radar_job, airbyte_sync_job],
    schedules=[airbyte_sync_schedule],
    sensors=[run_dbt_after_sync_sensor],
    resources={
        "dbt": DbtCliResource(
            project_dir=dbt_project,
            profiles_dir=str(Path.home() / ".dbt"),
        ),
    },
)
