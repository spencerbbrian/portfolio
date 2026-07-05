# Spencer Baiden — Data & Analytics Engineering Portfolio

Projects spanning analytics engineering (dbt, warehouse modeling, orchestration) and data engineering (streaming, cloud-native pipelines, IaC). Actively job-hunting for a September start — the **Featured Projects** below are the ones I lead with in interviews; everything else is earlier/learning work kept for range.

Static site: https://sites.google.com/view/spencerbbrian/about
Tableau: https://public.tableau.com/app/profile/spencer.baiden/vizzes

---

## Featured Projects

### 1. [Real-Time B2B Spend & Anomaly Analytics on GCP](data-engineering/b2b-realtime-spend-GCP/)
**Stack:** Pub/Sub, Apache Beam/Dataflow, BigQuery, dbt, Terraform, Python (Isolation Forest), Docker
End-to-end streaming pipeline simulating B2B company-to-vendor transactions: ingests via Pub/Sub, scores each transaction with a hybrid rules + ML anomaly detector in Beam, lands raw/scored/aggregated data in BigQuery through dbt marts, all infrastructure defined in Terraform. Built with a zero-cost local dev mode (OrbStack) and a real-GCP deploy path.
**Status:** core pipeline built. *Next: adding a Looker Studio/Streamlit dashboard on top of the BigQuery marts to close the loop from raw event to visualized insight.*

### 2. [Olist E-Commerce Analytics](analytics-engineering/dbt/olist/)
**Stack:** dbt, Snowflake, GitHub Actions
Batch ELT + warehouse modeling project: staging → intermediate → mart layers (11 staging models, fact/dimension marts for orders, sellers, and B2B2C marketing attribution). CI/CD via GitHub Actions runs `dbt test`/`dbt build` on PR and merge.
**Demonstrates:** production dbt project structure, testing, and CI/CD — not just a local build.

### 3. [Hotel Booking Management Analytics](analytics-engineering/dbt/hotel_mgt/)
**Stack:** dbt, seeds
Cancellation analysis, customer segmentation, and daily revenue-per-hotel marts built on staging/intermediate/mart layers.

### 4. [Customer Spend Analysis](analytics-engineering/dbt/customer_analysis/)
**Stack:** dbt, Python (synthetic data generation), custom macros
Custom SQL macro library, a Python data generator for seed data, and dbt test assertions (e.g. every customer has at least one order).

### 5. [Analytics Orchestration (Airflow)](analytics-engineering/Airflow/)
**Stack:** Docker Compose, Apache Airflow 2.9.3
Local Airflow deployment orchestrating a daily dbt run (05:00 UTC) — shows the scheduling/orchestration layer sitting on top of the dbt projects above.

### 6. [Banking Transaction System](data-engineering/banking-system/)
**Stack:** Python, MongoDB
Backend for bank/fund transactions — account and transaction services, schema validation, a fraud-detection script, and a test suite (`tests/`).

---

## In Progress

### [Golden Heights University Database System](projects-in-progress/golden-heights/)
**Stack:** Flask, MongoDB/SQLite, Python
University data system (students, housing, courses, advisors, grading, scholarships). Currently being rebuilt from the legacy notebook version (`legacy/`) into a proper Flask app (`gh_app/`).

---

## Archive (earlier / learning projects)

Kept for breadth — mostly single-notebook or single-script exercises, superseded by the featured projects above.

**BI / Dashboarding**
- `POWERBi/climate change` — Power BI dashboard on global/city/country climate data
- `POWERBi/employee attrition` — Power BI dashboard on HR attrition drivers (`.pbix` file)
- `pizza` — Tableau + SQL sales dashboard (best/worst sellers, busiest hours, category mix)

**SQL Analytics**
- `SQL/movie-insights` — 6-file SQL query set on movie budget/rating/genre/director analysis
- `SQL/pos-log-transactions` — point-of-sale transaction log analysis
- `SQL/supply_chain` — customer, department, product, and shipment analysis queries
- `SQL/airbnb-listings` — Airbnb listings exploration notebook

**Streaming**
- `Kafka` — basic Kafka producer example
- `real-time-temperature-sensing` — Kafka producer/consumer pattern for sensor data
- `real-time-stock-price-analysis` — Kafka-style streaming stock price script

**Batch / Cloud Pipelines**
- `batch_sales_analytics_pipeline` — Kafka → S3 → Snowflake/BigQuery via AWS Lambda, dbt on top
- `databricks/earthquake_pipeline` — medallion (bronze/silver/gold) architecture on Databricks

**ML / AI**
- `Machine Learning & AI` — CNN, deep learning, and neural network fundamentals notebooks

**Other**
- `flask_market` — Flask marketplace web app
- `data_extraction` — company revenue data extraction notebook
- `hotel-management` — early/raw version of the hotel booking dataset (superseded by `analytics-engineering/dbt/hotel_mgt`)
- `dbt/agora` — starter dbt template project (superseded by the three featured dbt projects)

---

## Technologies

Python · SQL · dbt · Snowflake · BigQuery · Apache Beam/Dataflow · Pub/Sub · Kafka · Airflow · Terraform · Docker · MongoDB · Postgres · Power BI · Tableau · Flask

## Contact

Reach me via my socials linked on my profile — especially if you want to build something together.
