# Real-Time B2B Spend & Anomaly Analytics on GCP

A real-time data engineering pipeline that ingests simulated **company-to-vendor transactions** (B2B card/ACH spend), processes them through a GCP-native streaming stack, scores each transaction with a hybrid rules + ML anomaly detection system, and serves both real-time alerts and aggregated spend analytics through dbt-modeled BigQuery marts and a dashboard.

This project simulates the kind of platform a B2B fintech (e.g. a corporate card / expense management company) would build internally: one team needs near-real-time anomaly alerts on company spending, another team needs reliable aggregated analytics for reporting.

---

## 1. Why This Project Exists

This is the third project in a three-project data engineering portfolio, each deliberately built on a different part of the modern data stack:

| Project | Focus | Stack |
|---|---|---|
| OLIST E-Commerce Analytics | Batch ELT + warehouse modeling | dbt + Snowflake + Looker, GitHub Actions CI/CD |
| Real-Time E-Commerce Pipeline | Self-managed streaming | Kafka (Confluent Cloud) + MongoDB Atlas + Airflow + FastAPI + Streamlit |
| **This project** | **Cloud-native streaming + IaC** | **Pub/Sub + Dataflow (Beam) + BigQuery + dbt + Terraform + GCP** |

The goal of this project specifically is to demonstrate comfort with **managed cloud streaming services** and **infrastructure as code** — skills that batch/warehouse projects and self-hosted Kafka projects don't cover on their own.

---

## 2. Domain: B2B Company Spend Monitoring

Instead of modeling individual consumers, this pipeline tracks **companies** as the core entity. Each simulated transaction represents a company spending money with a vendor/merchant — similar to corporate card platforms (Ramp, Brex, Airbase) or expense management systems.

**Why companies instead of individual users:**
- A small number of companies can generate a large, continuous volume of realistic transactions (multiple departments, vendors, recurring subscriptions, one-off purchases) without needing millions of synthetic "people."
- Spend monitoring at the company level naturally supports multiple analytical angles: department-level budgets, vendor concentration, month-over-month spend trends, and anomaly detection on irregular company behavior — all without touching individual PII.
- It mirrors a real, common fintech product surface: **"is this company's spending behaving normally, and is any single transaction suspicious?"**

### Simulated entities
- **Companies** — id, name, industry, size tier (SMB/mid-market/enterprise), home country, "normal" monthly spend baseline
- **Vendors/Merchants** — id, name, category (SaaS, travel, office supplies, payroll services, advertising, etc.), risk tier
- **Transactions** — company_id, vendor_id, amount, currency, timestamp, payment method, department, transaction_id

### What "anomaly" means in this context
- A company suddenly transacting **far above its historical baseline** spend
- **Velocity spikes** — an unusual number of transactions in a short window for that company
- **New/rare vendor categories** for that company (e.g. a company that never spends on "travel" suddenly has five travel transactions)
- **Round-trip/duplicate-like transactions** — same amount, same vendor, in rapid succession
- **Off-hours or off-pattern timing** relative to that company's typical transaction times

---

## 3. Architecture

This project is deliberately split into a **local-first development environment** (runs entirely on your MacBook via OrbStack, zero cloud cost) and a **cloud deployment target** (real GCP, used for short demo bursts). The pipeline code itself doesn't change between the two — only where it points.

```
┌─────────────────────────── LOCAL (OrbStack containers + your Mac) ───────────────────────────┐
│                                                                                                │
│   Python Producer (Faker) ──publish──▶ Pub/Sub Emulator (container)                          │
│                                              │ subscribe                                       │
│                                              ▼                                                │
│                              Apache Beam — DirectRunner (same code as Dataflow)                │
│                              parse → features → rules → Isolation Forest → windowing           │
│                                       │                          │                              │
│                            raw + scored txns           windowed aggregates                     │
│                                       │                          │                              │
│                              fake-gcs-server (model artifact storage during dev)                │
│                                                                                                │
│   Local Airflow (Docker via OrbStack) ──orchestrates──▶ dbt (local CLI)                        │
│                                                                                                │
└──────────────────────────────────────────┬───────────────────────────────────────────────────┘
                                            │ writes to / reads from
                                            ▼
                                ┌─────────────────────────┐
                                │   BigQuery (real GCP)     │   ← always real, never local
                                │  raw, scored, aggregated   │
                                └─────────────┬───────────────┘
                                              │
                                              ▼
                                  ┌───────────────────────┐
                                  │  Looker Studio /        │
                                  │  Streamlit on Cloud Run  │
                                  └───────────────────────┘

┌──────────────────── REAL GCP (deploy/demo bursts only) ────────────────────┐
│  Real Pub/Sub → Dataflow (same Beam code, Dataflow Runner) → BigQuery       │
│  Cloud Functions + Cloud Scheduler — lightweight triggers, always real GCP  │
│  Real GCS — model artifact storage for the deployed version                 │
└──────────────────────────────────────────────────────────────────────────────┘

Terraform: provisions real Pub/Sub, BigQuery, GCS, Dataflow, Cloud Functions, Cloud Scheduler, IAM
GitHub Actions: CI/CD for dbt runs, Terraform plan/apply, Dataflow job deploys
```

**What's local vs. cloud, end to end:**

| Component | Local (default, dev) | Cloud (deploy/demo) |
|---|---|---|
| Pub/Sub | Emulator (container) | Real Pub/Sub |
| Beam pipeline | `DirectRunner` (your Mac) | Dataflow Runner |
| Model artifact storage | `fake-gcs-server` (container) | Real GCS |
| Airflow | Local (Docker, via OrbStack) — **stays local permanently**, never deployed to Composer | n/a |
| dbt | Local CLI — **stays local permanently**, just points at BigQuery either way | Same |
| BigQuery | **Always real GCP** — no local stand-in used | Same |
| Cloud Functions / Scheduler | n/a | **Always real GCP** — lightweight triggers for retraining/dbt hooks |
| Dashboard | Streamlit local, or Looker Studio against real BQ | Same |

The only things that ever cost real money are **BigQuery** (free tier covers this project easily), **Cloud Functions/Scheduler** (essentially free at this volume), and the **brief Dataflow bursts** you run when you want a real-cloud demo. Pub/Sub, Beam processing, Airflow, and dbt cost you nothing because they never need to leave your laptop.

---

## 4. Tech Stack

| Layer | Tool | Local or Cloud |
|---|---|---|
| Event generation | Python + Faker | Local |
| Message broker | Google Pub/Sub | **Local (emulator)** for dev; real Pub/Sub only for deploy/demo bursts |
| Stream processing | Apache Beam (Python SDK) | **Local (`DirectRunner`)** for dev; Dataflow Runner only for deploy/demo bursts |
| Anomaly detection | Isolation Forest (scikit-learn) + rule-based checks | Local — trained and tested entirely on your Mac |
| Raw/model artifact storage | Google Cloud Storage | **Local (`fake-gcs-server`)** for dev; real GCS for deploy |
| Warehouse | BigQuery | **Always real GCP** — no local stand-in, free tier covers this project's volume |
| Transformation | dbt (BigQuery adapter) | **Local CLI, permanently** — dbt always runs from your machine (or CI), targeting real BigQuery |
| Data quality | dbt tests / Great Expectations | Local |
| Orchestration | Airflow | **Local (Docker via OrbStack), permanently** — no Cloud Composer at all |
| Lightweight cloud triggers | Cloud Functions + Cloud Scheduler | **Always real GCP** — used for periodic retrain hooks / dbt-run triggers when the pipeline is deployed |
| Dashboard | Looker Studio (or Streamlit on Cloud Run) | Local for Streamlit dev; Looker Studio reads real BigQuery either way |
| IaC | Terraform | Targets real GCP resources only (Pub/Sub, BigQuery, GCS, Dataflow, Cloud Functions, Scheduler, IAM) |
| CI/CD | GitHub Actions | dbt CI, Terraform plan/apply, Dataflow deploy |
| Local dev environment | **OrbStack** (Docker on macOS) | Runs Pub/Sub emulator, `fake-gcs-server`, local Airflow — see Phase 0.5 |

---

## 5. The ML Model: Hybrid Rules + Isolation Forest

The anomaly scoring is intentionally simple and explainable — this mirrors how real fraud/anomaly systems are described in practice: **deterministic rules catch known patterns, an unsupervised model catches the unknown ones.**

### Rule-based checks (fast, deterministic)
- Transaction amount > N standard deviations above company's rolling average
- More than X transactions for a company within Y minutes
- Vendor category never seen before for this company
- Duplicate-like transaction (same vendor + amount within a short window)

### Isolation Forest (unsupervised ML)
- **Features per transaction:** amount relative to company baseline, time since company's last transaction, vendor category frequency for that company, hour-of-day, day-of-week, department spend ratio
- **Training:** offline, on a batch of simulated "normal" historical transactions (a script generates this separately from the live stream)
- **Output:** an anomaly score per transaction; combined with rule flags into a final `risk_score` and `risk_flag` (boolean)
- **Where it runs:** model artifact (`joblib`) stored in GCS; loaded once per Dataflow worker in `DoFn.setup()`; applied per-record in `process()`

### Final score
```
final_risk_score = weighted_combination(rule_flags, isolation_forest_score)
risk_flag = final_risk_score > threshold
```
Both feed into BigQuery so dbt marts and the dashboard can separate "rule-triggered" alerts from "model-flagged" alerts — a useful distinction to discuss in interviews.

---

## 6. Data Model (BigQuery / dbt layers)

**Staging**
- `stg_transactions` — cleaned raw transactions
- `stg_companies`, `stg_vendors` — dimension cleanup

**Intermediate**
- `int_transactions_scored` — transactions joined with risk scores
- `int_company_spend_windows` — windowed aggregates (5-min, hourly, daily)

**Marts**
- `fct_transactions` — transaction-grain fact table with risk scores
- `dim_companies`, `dim_vendors`
- `mart_fraud_alerts` — flagged transactions, ready for dashboard
- `mart_company_spend_summary` — daily/weekly/monthly spend by company, department, vendor category
- `mart_vendor_risk` — vendor-level aggregation (which vendors show up disproportionately in flagged transactions)

---

## 7. Step-by-Step Build Checklist

### Phase 0 — Setup
- [ ] Create GCP project, enable billing alerts/budget (important — Dataflow can get expensive if left running)
- [ ] Enable APIs: Pub/Sub, Dataflow, BigQuery, Cloud Storage, Cloud Build, Artifact Registry
- [ ] Install `gcloud` CLI on macOS, authenticate (`gcloud auth login`, `gcloud auth application-default login`)
- [ ] Set up Python virtual environment (3.10+), install `apache-beam[gcp]`, `google-cloud-pubsub`, `google-cloud-bigquery`, `scikit-learn`, `faker`, `dbt-bigquery`
- [ ] Initialize GitHub repo, set up `.gitignore` for `.env`, credentials, `__pycache__`

### Phase 0.5 — Local Development Environment (OrbStack)

This is the foundation that makes the rest of the project free to develop. Set this up before writing any pipeline code.

- [ ] Confirm OrbStack is running and `docker`/`docker compose` commands work through it
- [ ] Create a `docker-compose.yml` at the repo root with three services: Pub/Sub emulator, `fake-gcs-server`, and local Airflow

```yaml
# docker-compose.yml
services:
  pubsub-emulator:
    image: gcr.io/google.com/cloudsdktool/google-cloud-cli:emulators
    command: gcloud beta emulators pubsub start --host-port=0.0.0.0:8085 --project=local-dev-project
    ports:
      - "8085:8085"

  fake-gcs-server:
    image: fsouza/fake-gcs-server
    command: -scheme http -port 4443
    ports:
      - "4443:4443"
    volumes:
      - ./local-gcs-data:/data

  airflow:
    image: apache/airflow:2.9.3
    environment:
      - AIRFLOW__CORE__EXECUTOR=LocalExecutor
      - AIRFLOW__CORE__LOAD_EXAMPLES=false
    ports:
      - "8080:8080"
    volumes:
      - ./airflow/dags:/opt/airflow/dags
      - ./airflow/logs:/opt/airflow/logs
    command: standalone
```

- [ ] Start everything: `docker compose up -d`
- [ ] Verify Pub/Sub emulator: set `PUBSUB_EMULATOR_HOST=localhost:8085` and create a test topic/subscription with `gcloud` (works the same as real Pub/Sub once that env var is set)
- [ ] Verify `fake-gcs-server`: hits `http://localhost:4443`, confirm a test bucket/object can be created (point `STORAGE_EMULATOR_HOST` at it)
- [ ] Verify local Airflow: open `http://localhost:8080`, confirm webserver + scheduler are healthy
- [ ] Add a `.env.local` with emulator host variables so producer/pipeline code can switch between local and cloud with one env file swap
- [ ] Note in README which pieces stay local permanently (Airflow, dbt CLI) vs. which are swapped to real GCP only for deploy/demo (Pub/Sub, Beam runner)

This means **Pub/Sub, Beam, model-artifact storage, and Airflow never need to touch real GCP during development.** Only BigQuery (always real) and Cloud Functions/Scheduler (always real, but essentially free) cost anything ongoing — plus short Dataflow bursts whenever you want a live cloud demo.

### Phase 1 — Infrastructure as Code (real GCP resources only)
- [ ] Write Terraform for: BigQuery datasets (raw, staging, marts), GCS bucket for the *deployed* model artifact, real Pub/Sub topic + subscription (used only for deploy/demo bursts), Cloud Functions + Cloud Scheduler (for retrain/dbt-run triggers), service accounts + IAM roles
- [ ] Terraform remote state (GCS backend)
- [ ] `terraform plan` / `terraform apply` locally, confirm resources created
- [ ] Document Terraform variables in a `terraform.tfvars.example`
- [ ] Note: Airflow and the Pub/Sub emulator are **not** provisioned by Terraform — they're pure local Docker via OrbStack and never touch GCP

### Phase 2 — Data Simulation
- [ ] Define company and vendor reference data (CSV or generated via Faker) — e.g. 30–50 companies, 100+ vendors across categories
- [ ] Build Python producer that:
  - [ ] Generates realistic transactions per company based on a baseline spend profile
  - [ ] Publishes JSON-encoded transactions to Pub/Sub — **defaults to the local emulator** (`PUBSUB_EMULATOR_HOST`), with a config flag to point at real Pub/Sub for deploy/demo
  - [ ] Has a `--inject-anomalies` flag/mode to deliberately generate spend spikes, velocity bursts, and new-vendor-category events
- [ ] Run producer locally against the emulator, confirm messages arrive (pull from the emulator subscription via `gcloud` with `PUBSUB_EMULATOR_HOST` set)

### Phase 3 — Offline Model Training
- [ ] Generate a separate batch dataset of "normal" historical transactions for training
- [ ] Feature engineering script (mirrors what will run in the streaming job)
- [ ] Train Isolation Forest, evaluate against your own injected anomalies (sanity check, not a formal benchmark — be upfront about this in the README/interview)
- [ ] Save model with `joblib`, upload artifact to **`fake-gcs-server`** for local dev; same upload code points at real GCS when you deploy
- [ ] Document model features, training data assumptions, and limitations

### Phase 4 — Stream Processing (Beam — local `DirectRunner` first, Dataflow only for demo bursts)
- [ ] Build Beam pipeline targeting the **local Pub/Sub emulator**, run with `DirectRunner`:
  - [ ] Read from Pub/Sub (emulator)
  - [ ] Parse + validate JSON, handle malformed records (dead-letter pattern)
  - [ ] Feature engineering `DoFn`
  - [ ] Rule-based check `DoFn`
  - [ ] ML scoring `DoFn` (loads model from `fake-gcs-server` in `setup()`)
  - [ ] Combine into final risk score
  - [ ] Windowed aggregation branch (fixed/sliding windows per company)
  - [ ] Write scored transactions to BigQuery (real — point credentials at your real BQ project even while everything else is local)
  - [ ] Write windowed aggregates to BigQuery
- [ ] Run the full pipeline end-to-end with `DirectRunner` against the emulator + local producer — this is your main development loop, costs nothing, iterates fast
- [ ] Set up dead-letter handling for malformed/failing records (local file/`fake-gcs-server` during dev, real GCS/BQ table when deployed)
- [ ] **Only when you want a real-cloud demo:** swap config to point at real Pub/Sub + real GCS, deploy the *same* pipeline code to Dataflow Runner, let it run briefly, capture your demo, then cancel/drain the job (`gcloud dataflow jobs cancel`)

### Phase 5 — Transformation Layer (dbt)
- [ ] Initialize dbt project with BigQuery adapter, configure `profiles.yml`
- [ ] Build staging models (`stg_transactions`, `stg_companies`, `stg_vendors`)
- [ ] Build intermediate models (scored transactions, windowed spend)
- [ ] Build mart models (`fct_transactions`, `mart_fraud_alerts`, `mart_company_spend_summary`, `mart_vendor_risk`)
- [ ] Add dbt tests (not null, accepted values, relationships, freshness)
- [ ] Document models (`schema.yml` descriptions) for `dbt docs generate`

### Phase 6 — Orchestration
- [ ] Build Airflow DAGs in **local Airflow (Docker via OrbStack)** — this is permanent, not just for dev; no Cloud Composer anywhere in this project
- [ ] DAG: triggers local producer runs / Beam DirectRunner pipeline runs for scheduled local testing
- [ ] DAG: triggers dbt runs against real BigQuery on a schedule (e.g. every 15–30 minutes)
- [ ] Separately, set up **Cloud Functions + Cloud Scheduler (real GCP)** for the deployed-pipeline path — e.g. a scheduled function that triggers model retraining or kicks off a dbt Cloud/CI job when the pipeline is running against real Dataflow. These are intentionally lightweight (pay-per-invocation, effectively free at this volume) and don't require Airflow at all on the cloud side
- [ ] Document clearly which orchestration path is active when: local Airflow orchestrates your local dev loop; Cloud Functions/Scheduler orchestrate the deployed/demo path

### Phase 7 — Dashboard
- [ ] Decide: Looker Studio (faster, GCP-native, good for portfolio screenshots) vs. Streamlit on Cloud Run (more custom, more "built it myself" credit)
- [ ] Build views: real-time fraud alert feed, company spend over time, vendor category breakdown, top flagged vendors
- [ ] Connect directly to BigQuery marts

### Phase 8 — CI/CD
- [ ] GitHub Actions workflow: `terraform plan` on PR, `terraform apply` on merge to main (with manual approval gate)
- [ ] GitHub Actions workflow: dbt build + test on PR against a dev BigQuery dataset
- [ ] GitHub Actions workflow: lint/test Beam pipeline code, deploy to Dataflow on merge (or document as a manual step if you want to control cost)

### Phase 9 — Documentation & Polish
- [ ] Architecture diagram (image, not just ASCII) for the README
- [ ] Cost notes — what you ran, what it cost, how you controlled Dataflow/BigQuery spend (this is a genuinely good interview talking point)
- [ ] Clear "limitations" section: simulated data, simple model, not a production fraud system
- [ ] Demo video or GIF of the dashboard + a flagged transaction appearing in near real time
- [ ] Clean up / tear down instructions (`terraform destroy`) so you're not paying for idle infra

---

## 8. Cost Profile (with local-first dev)

| Service | Cost |
|---|---|
| Pub/Sub emulator, Beam DirectRunner, fake-gcs-server, local Airflow, dbt CLI | **$0** — all run on your MacBook via OrbStack, indefinitely |
| BigQuery | **$0–5/month** — free tier (1TB queries, 10GB storage) comfortably covers this project's volume |
| Cloud Functions + Cloud Scheduler | **~$0** — pay-per-invocation, negligible at this scale |
| Real Pub/Sub + Dataflow (only during deploy/demo bursts) | **$2–10 total**, if you only run it for short demo sessions and cancel/drain the job afterward rather than leaving it streaming |
| GCS (real, for deployed model artifact) | **$0–1/month** |

**Bottom line:** with this setup, the entire project should cost you single-digit dollars total, even across weeks of development — as long as you remember to cancel/drain any real Dataflow job after a demo rather than leaving it running. Set a GCP budget alert anyway (e.g. $10, $25) as a safety net.

## 9. Repo Structure (suggested)

```
gcp-realtime-spend-analytics/
├── docker-compose.yml          # Pub/Sub emulator, fake-gcs-server, local Airflow
├── .env.local                  # emulator host vars (gitignored if it has secrets)
├── local-gcs-data/             # fake-gcs-server volume (gitignored)
├── airflow/
│   ├── dags/
│   │   ├── local_dev_pipeline_dag.py
│   │   └── dbt_run_dag.py
│   └── logs/                   # gitignored
├── terraform/
│   ├── main.tf                 # real GCP only: BigQuery, GCS, Pub/Sub (deploy), Cloud Functions, Scheduler
│   ├── variables.tf
│   ├── outputs.tf
│   └── terraform.tfvars.example
├── producer/
│   ├── generate_reference_data.py
│   ├── producer.py              # defaults to PUBSUB_EMULATOR_HOST, flag to switch to real Pub/Sub
│   └── requirements.txt
├── ml/
│   ├── train_isolation_forest.py
│   ├── feature_engineering.py
│   └── model_artifacts/         # gitignored, lives in fake-gcs-server locally / real GCS when deployed
├── pipeline/
│   ├── beam_pipeline.py         # same code for DirectRunner and DataflowRunner
│   ├── transforms/
│   │   ├── parsing.py
│   │   ├── rules.py
│   │   ├── scoring.py
│   │   └── windowing.py
│   └── requirements.txt
├── cloud_functions/
│   └── retrain_trigger/         # real GCP — triggered by Cloud Scheduler
├── dbt/
│   ├── models/
│   │   ├── staging/
│   │   ├── intermediate/
│   │   └── marts/
│   ├── dbt_project.yml
│   └── packages.yml
├── dashboard/
│   └── (Looker Studio link doc OR Streamlit app code)
├── .github/workflows/
│   ├── terraform.yml
│   ├── dbt.yml
│   └── pipeline-deploy.yml      # deploys Beam pipeline to Dataflow (manual trigger recommended, for cost control)
├── docs/
│   └── architecture-diagram.png
└── README.md
```

---

## 10. Talking Points for Interviews

- Why Pub/Sub + Dataflow over a self-managed Kafka setup (managed scaling, GCP-native IAM, tighter BigQuery integration) — and you can contrast this directly with your Kafka project.
- Why a hybrid rules + Isolation Forest approach instead of jumping straight to a complex model — explainability and maintainability matter in fraud/anomaly systems.
- How windowing works in Beam and why you chose fixed/sliding windows for the aggregation branch.
- How you controlled GCP cost on a personal project — running Pub/Sub, Beam, Airflow, and dbt entirely locally via OrbStack/Docker, and only spinning up real Pub/Sub + Dataflow for short, deliberate demo bursts. This is a strong, concrete answer to "how do you think about cost in cloud data engineering."
- The deliberate choice to model **companies** rather than individual users — multi-entity spend modeling, department/vendor dimensions, and why that's a more business-relevant framing for B2B fintech than consumer-level fraud.

## 11. Syntaxes to Document
- curl http://localhost:4443/storage/v1/b/b2b-spend-models (check on created bucket with name b2b-spend-models)
- python init_gcs.py (run the initiating file for the cloud container and bucket)
- curl -X GET http://localhost:8085/
v1/projects/local-dev-project/topics (check the topics created)
- python init_emulator.py (create local topic and subscription)
- mkdir -p airflow/dags airflow/logs (create the directories and do nothing if the folders already exist -p parent)
- chmod -R 777 airflow   (grants read write and execute privileges) not recommended
- docker compose exec airflow cat /opt/airflow/standalone_admin_password.txt (get airflow password)
- docker compose exec airflow airflow users reset-password \
  --username admin \
  --password admin   (update password and username if option above doesn't work)
- brew install terraform
- terraform -version
- gcloud storage buckets create gs://[preffered bucket name] --project=[project id] --location=europe-west1     --uniform-bucket-level-access
- gcloud auth application-default login
- gcloud config set project YOUR_REAL_PROJECT_ID
- terraform init
- terraform plan
- terraform apply
- export PUBSUB_EMULATOR_HOST=localhost:8085 (safety check for pubsub_emulator)
- python producer.py (run to local pubsub for testing function)
- gcloud pubsub subscriptions pull b2b-transactions-sub \
  --project=local-dev-project \
  --limit=5 \
  --auto-ack    (pull the last 5 messages to verify)
- python producer.py --use-real-pubsub (publish to pubsub gcloud)
- gcloud pubsub subscriptions pull b2b-transactions-sub \
  --project=portfolio-analytics-499108 \
  --limit=5 \
  --auto-ack (check for messages sent)