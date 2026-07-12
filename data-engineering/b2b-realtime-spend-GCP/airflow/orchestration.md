# Orchestration

This project uses two separate orchestration systems for two separate contexts.
They are deliberately kept independent — neither knows about the other.

---

## Local dev orchestration: Airflow (Docker via OrbStack)

**Always local. Never deployed to Cloud Composer.**

Airflow runs in Docker on your Mac and orchestrates your local dev loop.
It is the only thing that starts/stops the producer and Beam pipeline
during development.

### DAGs

#### `local_pipeline_dev`
**Schedule:** every 30 minutes, 08:00–18:00, weekdays

```
check_pubsub_emulator → run_producer (60s) → run_beam_pipeline (90s)
```

Verifies the Pub/Sub emulator is healthy, runs the producer to generate
~120 transactions with anomaly injection, then runs the Beam DirectRunner
pipeline to score and write them to BigQuery. Gives you fresh data every
30 minutes without manual intervention.

#### `dbt_scheduled_build`
**Schedule:** every 20 minutes, 08:00–18:00, weekdays

```
dbt_build → dbt_test → log_row_counts
```

Rebuilds all dbt mart models and runs schema tests so the dashboard
always reflects the latest scored transactions. Logs row counts to
Airflow task logs after each run.

### Airflow UI
Available at http://localhost:8080 while OrbStack is running.
Login: admin / admin (or whatever your docker-compose sets).

### When is Airflow running?
Only when OrbStack is running on your Mac. There is no always-on
orchestration for the local dev path — that's intentional. When you're
not actively developing, nothing runs and nothing costs money.

---

## Cloud orchestration: Cloud Functions + Cloud Scheduler (real GCP)

**Used only when the pipeline is deployed to Dataflow for a demo burst.**

This path is intentionally minimal — it's not a full workflow orchestrator,
just a lightweight daily trigger that checks whether the model needs retraining.

### What's deployed

#### `retrain-trigger` (Cloud Function, `europe-west1`)
An HTTP-triggered Cloud Function that:
1. Queries BigQuery to count new transactions since the last retrain
2. Logs the result to `b2b_spend_raw.retrain_audit_log`
3. Returns a JSON summary of whether a retrain is recommended

It does NOT automatically retrain — it signals that a retrain is needed.
Actually running the training script (`ml/train_isolation_forest.py`) is
a manual or CI-triggered step. This is intentional: auto-retraining a
model that writes to a production pipeline without a human review step
is a bad pattern.

#### `retrain-trigger-schedule` (Cloud Scheduler job)
Calls the Cloud Function once per day at 06:00 UTC via HTTP POST
with OIDC authentication.

### Cost
One Cloud Function invocation per day = fractions of a cent per month.
Cloud Scheduler: free tier covers 3 jobs/month, this uses 1.

### Deployed vs. not deployed
The Cloud Function and Scheduler are always deployed (Terraform manages them)
but the Cloud Function only does meaningful work when there's data flowing
through the real Dataflow pipeline. On idle days it simply logs
"0 new transactions, no retrain needed" to the audit table.

---

## Which path is active when?

| Situation | What's orchestrating | What's running |
|---|---|---|
| Active local dev (OrbStack up) | Local Airflow DAGs | Producer → DirectRunner → BigQuery → dbt |
| OrbStack off / overnight | Nothing | Nothing (no cost) |
| Demo burst (Dataflow deployed) | Manual start + Cloud Scheduler | Real Pub/Sub → Dataflow → BigQuery → dbt (manual or CI) |
| Always (in background) | Cloud Scheduler | Daily retrain check function (negligible cost) |

---

## Starting the local orchestration from scratch

```bash
# 1. Start OrbStack / Docker containers
docker compose up -d

# 2. Initialise the Pub/Sub emulator topic
python init_emulator.py

# 3. Retrain and re-upload model artifact (if fake-gcs was wiped)
cd ml && python train_isolation_forest.py

# 4. Open Airflow UI and enable both DAGs
open http://localhost:8080

# 5. Trigger manually for the first run (or wait for schedule)
# In the UI: toggle DAG on → click "Trigger DAG"
```