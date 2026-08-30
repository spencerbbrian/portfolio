# Data Analytics & Engineering Portfolio

Hi, I'm Spencer, an Analytics Engineer / Data Engineer wrapping up a Master's degree via an alternance contract at Decathlon Digital. This repo collects the data engineering, analytics engineering, and dashboarding projects I've built to practice production-grade patterns: layered dbt modeling, cloud-native pipelines, orchestration, data quality, and CI/CD.

For visual walkthroughs of select projects, see my static [portfolio site](https://sites.google.com/view/spencerbbrian/about) and my [Tableau Public profile](https://public.tableau.com/app/profile/spencer.baiden/vizzes).

---

## Data Engineering

### [Churn Radar](data-engineering/churn-radar/) — Health Scoring & Reverse ETL (Dagster, Airbyte, dbt, BigQuery, HubSpot, Slack)
Customer health-scoring and churn-prevention pipeline for a simulated SaaS product. A custom Airbyte connector lands usage/billing/customer data in BigQuery, dbt models a composite health score and churn-risk tier, and Dagster orchestrates the whole thing end to end — a schedule triggers the Airbyte sync, an asset sensor cascades into the dbt rebuild the moment new data lands, and a blocking data-quality check gates the churn-risk mart before reverse ETL pushes updated risk scores into HubSpot (Company records) and posts Critical-tier alerts to Slack. Fully documented with real screenshots of the pipeline in action.

### [Real-Time B2B Spend & Anomaly Analytics](data-engineering/b2b-realtime-spend-GCP/) — GCP + Beam + BigQuery + dbt + Terraform
Real-time streaming pipeline simulating B2B company-to-vendor transactions: ingests via Pub/Sub, scores each transaction with a hybrid rules + ML (Isolation Forest) anomaly detector in Apache Beam/Dataflow, lands raw/scored/aggregated data in BigQuery through dbt marts, with all infrastructure defined in Terraform and CI/CD via GitHub Actions (dbt + Terraform + Dataflow deploy workflows). Built with a zero-cost local dev mode (OrbStack) and a real-GCP deploy path.

### [Banking System](data-engineering/banking-system/) — Transaction Processing with MongoDB
Backend system modeling core banking transaction flows: account/transaction services, schema validation, a fraud-detection script, and a test suite, using MongoDB for document-oriented storage of accounts and transfers.

---

## Analytics Engineering

### [Olist E-Commerce Analytics](analytics-engineering/dbt/olist/) — dbt + Snowflake + GitHub Actions + Great Expectations
End-to-end analytics engineering pipeline: raw e-commerce data modeled through a layered dbt architecture (staging → intermediate → marts) in Snowflake, including a B2B2C marketing-attribution mart linking end-customer orders back to the channel and rep that acquired the seller who fulfilled them. CI runs `dbt test` on every PR; CD runs `dbt run --target prod` on merge followed by a **Great Expectations** suite (`quality/`) catching row-count anomalies, cross-column temporal integrity issues, and distribution drift that dbt's native tests don't cover.

### [Hotel Booking Management Analytics](analytics-engineering/dbt/hotel_mgt/) — dbt
Staging → intermediate → mart dbt project on hotel booking data: cancellation deep-dive analysis, RFM-style customer segmentation, and a daily booking-revenue-per-hotel mart.

### [Customer Spend Analysis](analytics-engineering/dbt/customer_analysis/) — dbt
Smaller dbt project modeling customer spend: staging models for customers/orders, an intermediate customer-spend model, and a daily sales summary mart, plus a custom SQL macro library and a synthetic seed-data generator.

### [Analytics Orchestration](analytics-engineering/Airflow/) — Airflow
Local Airflow deployment (Docker Compose) scheduling a daily dbt run for the Agora dbt project — the orchestration layer sitting on top of the dbt projects above.

---

## In Progress

### [Real-Time E-Commerce Analytics Pipeline](data-engineering/real_time_ecommerce_analytics_pipeline/) — Kafka + MongoDB Atlas + Airflow
Event simulator publishes realistic e-commerce events (page views, cart adds, purchases) to Kafka; a consumer enriches them (geo, device) and writes to MongoDB Atlas; an Airflow DAG computes nightly product/RFM aggregates. Working so far: simulator, Kafka producer/consumer, Mongo setup + seeding, and one nightly aggregation DAG. The Streamlit dashboard, FastAPI serving layer, and Great Expectations quality suite described in the project's own README are designed but not yet built — noted here as the honest state rather than implied done.

### [Golden Heights University Database System](projects-in-progress/golden-heights/) — Flask
A university database system covering students, housing, courses, advisors, grading, and scholarships. Currently being rebuilt from a legacy notebook version (`legacy/`) into a proper Flask app (`gh_app/`).

---

## Archive (earlier / learning projects)

Kept for breadth — mostly single-notebook or single-script exercises, superseded by the featured projects above. See the [`.archive/`](.archive/) folder for everything.

**BI / Dashboarding**
- [`.archive/POWERBi/climate change/`](.archive/POWERBi/climate%20change/) — Power BI dashboard on global/city/country climate data
- [`.archive/POWERBi/employee attrition/`](.archive/POWERBi/employee%20attrition/) — Power BI dashboard on HR attrition drivers
- [`.archive/pizza/`](.archive/pizza/) — Tableau + SQL sales dashboard (best/worst sellers, busiest hours, category mix)
- [`.archive/pizza_sales/`](.archive/pizza_sales/) — earlier, more detailed pass at the same pizza-sales dataset: normalized schema, EDA, and its own Tableau visuals

**SQL Analytics**
- [`.archive/SQL/movie-insights/`](.archive/SQL/movie-insights/) — 6-file SQL query set on movie budget/rating/genre/director analysis
- [`.archive/SQL/pos-log-transactions/`](.archive/SQL/pos-log-transactions/) — point-of-sale transaction log analysis
- [`.archive/SQL/supply_chain/`](.archive/SQL/supply_chain/) — customer, department, product, and shipment analysis queries
- [`.archive/SQL/airbnb-listings.ipynb`](.archive/SQL/airbnb-listings.ipynb) — Airbnb listings exploration notebook

**Data Cleaning / Prep**
- [`.archive/supply_chain/`](.archive/supply_chain/) — pandas-based cleaning of the raw supply-chain CSVs (customers, orders, departments, shipments) that feed the SQL analysis above

**Streaming**
- [`.archive/Kafka/`](.archive/Kafka/) — basic Kafka producer example
- [`.archive/real-time-temperature-sensing/`](.archive/real-time-temperature-sensing/) — Kafka producer/consumer pattern for sensor data
- [`.archive/real-time-stock-price-analysis/`](.archive/real-time-stock-price-analysis/) — Flask app serving simulated real-time stock price data
- [`.archive/stock-market/`](.archive/stock-market/) — Kafka producer/consumer notebooks for stock market data

**Batch / Cloud Pipelines**
- [`.archive/batch_sales_analytics_pipeline/`](.archive/batch_sales_analytics_pipeline/) — Kafka → S3 → Snowflake/BigQuery via AWS Lambda, dbt on top
- [`.archive/databricks/earthquake_pipeline/`](.archive/databricks/earthquake_pipeline/) — medallion (bronze/silver/gold) architecture on Databricks

**ML / AI**
- [`.archive/Machine Learning & AI/`](.archive/Machine%20Learning%20&%20AI/) — CNN, deep learning, and neural network fundamentals notebooks

**Python Practice**
- [`.archive/python/beginner/`](.archive/python/beginner/) — small standalone scripts (Pig Latin converter, Mad Libs, basic math)
- [`.archive/python/intermediate/Quiz/`](.archive/python/intermediate/Quiz/) — a small quiz app

**Other**
- [`.archive/flask_market/`](.archive/flask_market/) — Flask marketplace web app
- [`.archive/data_extraction/`](.archive/data_extraction/) — company revenue data extraction notebook
- [`.archive/hotel-management/`](.archive/hotel-management/) — early/raw version of the hotel booking dataset (superseded by `analytics-engineering/dbt/hotel_mgt`)
- [`.archive/agora/`](.archive/agora/) — starter dbt template project (superseded by the featured dbt projects above)

---

## Project Types

- Analytics Engineering (dbt, layered data modeling, data quality/observability)
- Data Engineering & Orchestration (Airflow, Dagster, cloud-native streaming pipelines, IaC)
- Reverse ETL (warehouse → CRM/chat tools)
- Dashboarding & Executive Reporting
- SQL-focused projects
- Flask/Django apps supporting DE projects
- Miniature Python projects

## Technologies Used

- **Languages:** Python, SQL
- **Data Warehousing:** Snowflake, BigQuery
- **Transformation:** dbt (dbt Core)
- **Data Quality:** Great Expectations, dbt tests
- **Orchestration:** Apache Airflow, Dagster
- **Ingestion / EL:** Airbyte
- **Streaming:** Apache Beam/Dataflow, Pub/Sub, Kafka
- **Reverse ETL:** HubSpot API, Slack webhooks
- **Cloud & IaC:** GCP, Terraform, Docker
- **Databases:** PostgreSQL, MongoDB
- **BI/Visualization:** Tableau, Power BI
- **Other:** Jupyter, GitHub Actions (CI/CD)

Tech stack varies by project — see each project's own README for specifics.

### Contributors

Just me for now — always open to collaborating.

## Contact

Feel free to reach out through any of the socials on my GitHub profile, especially if you'd like to collaborate on a project.
