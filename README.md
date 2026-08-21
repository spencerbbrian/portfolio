# Data Analytics & Engineering Portfolio

Hi, I'm Spencer, an Analytics Engineer / Data Engineer wrapping up a Master's degree via an alternance contract at Decathlon Digital. This repo collects the data engineering, analytics engineering, and dashboarding projects I've built to practice production-grade patterns: layered dbt modeling, cloud-native pipelines, orchestration, data quality, and CI/CD.

For visual walkthroughs of select projects, see my static [portfolio site](https://sites.google.com/view/spencerbbrian/about).

## Featured Projects

### Real-Time B2B Spend & Anomaly Analytics — GCP + Beam + BigQuery + dbt + Terraform
[`data-engineering/b2b-realtime-spend-GCP/`](data-engineering/b2b-realtime-spend-GCP/)
Real-time streaming pipeline simulating B2B company-to-vendor transactions: ingests via Pub/Sub, scores each transaction with a hybrid rules + ML (Isolation Forest) anomaly detector in Apache Beam/Dataflow, lands raw/scored/aggregated data in BigQuery through dbt marts, with all infrastructure defined in Terraform. Built with a zero-cost local dev mode (OrbStack) and a real-GCP deploy path. *Next up: a Looker Studio/Streamlit dashboard on top of the BigQuery marts.*

### Olist E-Commerce Analytics — dbt + Snowflake + GitHub Actions + Great Expectations
[`analytics-engineering/dbt/olist/`](analytics-engineering/dbt/olist/)
End-to-end analytics engineering pipeline: raw e-commerce data modeled through a layered dbt architecture (staging → intermediate → marts) in Snowflake, including multi-channel B2B2C marketing attribution models. CI runs `dbt test` on every PR; CD runs `dbt run --target prod` on merge followed by a **Great Expectations** suite (`quality/`) catching row-count anomalies, cross-column temporal integrity issues, and distribution drift that dbt's native tests don't cover — a data-quality layer independent of dbt's own testing framework.

### Hotel Booking Management Analytics — dbt
[`analytics-engineering/dbt/hotel_mgt/`](analytics-engineering/dbt/hotel_mgt/)
Cancellation analysis, customer segmentation, and daily revenue-per-hotel marts built on a staging/intermediate/mart dbt architecture.

### Customer Spend Analysis — dbt
[`analytics-engineering/dbt/customer_analysis/`](analytics-engineering/dbt/customer_analysis/)
Custom SQL macro library, a Python synthetic data generator for seed data, and dbt test assertions (e.g. every customer has at least one order).

### Analytics Orchestration — Airflow
[`analytics-engineering/Airflow/`](analytics-engineering/Airflow/)
Local Airflow deployment (Docker Compose) orchestrating a daily dbt run — the scheduling layer sitting on top of the dbt projects above.

### Banking System — Transaction Processing with MongoDB
[`data-engineering/banking-system/`](data-engineering/banking-system/)
Backend system modeling core banking transaction flows: account/transaction services, schema validation, a fraud-detection script, and a test suite, using MongoDB for document-oriented storage of accounts and transfers.

## In Progress

### Golden Heights University Database System — Flask
[`projects-in-progress/golden-heights/`](projects-in-progress/golden-heights/)
A university database system covering students, housing, courses, advisors, grading, and scholarships. Currently being rebuilt from a legacy notebook version (`legacy/`) into a proper Flask app (`gh_app/`).

## Archive (earlier / learning projects)

Kept for breadth — mostly single-notebook or single-script exercises, superseded by the featured projects above.

**BI / Dashboarding**
- [`.archive/POWERBi/climate change/`](.archive/POWERBi/climate%20change/) — Power BI dashboard on global/city/country climate data
- [`.archive/POWERBi/employee attrition/`](.archive/POWERBi/employee%20attrition/) — Power BI dashboard on HR attrition drivers
- [`.archive/pizza/`](.archive/pizza/) — Tableau + SQL sales dashboard (best/worst sellers, busiest hours, category mix)

**SQL Analytics**
- [`.archive/SQL/movie-insights/`](.archive/SQL/movie-insights/) — 6-file SQL query set on movie budget/rating/genre/director analysis
- [`.archive/SQL/pos-log-transactions/`](.archive/SQL/pos-log-transactions/) — point-of-sale transaction log analysis
- [`.archive/SQL/supply_chain/`](.archive/SQL/supply_chain/) — customer, department, product, and shipment analysis queries
- [`.archive/SQL/airbnb-listings.ipynb`](.archive/SQL/airbnb-listings.ipynb) — Airbnb listings exploration notebook

**Streaming**
- [`.archive/Kafka/`](.archive/Kafka/) — basic Kafka producer example
- [`.archive/real-time-temperature-sensing/`](.archive/real-time-temperature-sensing/) — Kafka producer/consumer pattern for sensor data
- [`.archive/real-time-stock-price-analysis/`](.archive/real-time-stock-price-analysis/) — Kafka-style streaming stock price script

**Batch / Cloud Pipelines**
- [`.archive/batch_sales_analytics_pipeline/`](.archive/batch_sales_analytics_pipeline/) — Kafka → S3 → Snowflake/BigQuery via AWS Lambda, dbt on top
- [`.archive/databricks/earthquake_pipeline/`](.archive/databricks/earthquake_pipeline/) — medallion (bronze/silver/gold) architecture on Databricks

**ML / AI**
- [`.archive/Machine Learning & AI/`](.archive/Machine%20Learning%20&%20AI/) — CNN, deep learning, and neural network fundamentals notebooks

**Other**
- [`.archive/flask_market/`](.archive/flask_market/) — Flask marketplace web app
- [`.archive/data_extraction/`](.archive/data_extraction/) — company revenue data extraction notebook
- [`.archive/hotel-management/`](.archive/hotel-management/) — early/raw version of the hotel booking dataset (superseded by `analytics-engineering/dbt/hotel_mgt`)
- [`.archive/agora/`](.archive/agora/) — starter dbt template project (superseded by the featured dbt projects above)

## Project Types

- Analytics Engineering (dbt, layered data modeling, data quality/observability)
- Data Engineering & Orchestration (Airflow, cloud-native streaming pipelines, IaC)
- Dashboarding & Executive Reporting
- SQL-focused projects
- Flask/Django apps supporting DE projects
- Miniature Python projects

## Technologies Used

- **Languages:** Python, SQL
- **Data Warehousing:** Snowflake, BigQuery
- **Transformation:** dbt (dbt Core)
- **Data Quality:** Great Expectations
- **Orchestration:** Apache Airflow
- **Streaming:** Apache Beam/Dataflow, Pub/Sub, Kafka
- **Cloud & IaC:** GCP, Terraform, Docker
- **Databases:** PostgreSQL, MongoDB
- **BI/Visualization:** Tableau, Power BI
- **Other:** Jupyter, GitHub Actions (CI/CD)

Tech stack varies by project — see each project's own README for specifics.

### Tableau

Find my Tableau profile [here](https://public.tableau.com/app/profile/spencer.baiden/vizzes).

### Contributors

Just me for now — always open to collaborating.

## Contact

Feel free to reach out through any of the socials on my GitHub profile, especially if you'd like to collaborate on a project.
