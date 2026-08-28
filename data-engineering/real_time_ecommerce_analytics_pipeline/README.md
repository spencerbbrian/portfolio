# 🛒 Real-Time E-Commerce Analytics Pipeline

A production-style data engineering pipeline that simulates an online store, streams events through Kafka, stores and models data in MongoDB Atlas, orchestrates transformations with Airflow, and serves live KPIs on a Streamlit dashboard.

> Built as a portfolio project to demonstrate end-to-end data engineering skills across ingestion, storage, transformation, quality, and serving layers.

---

## Architecture

```
Event Simulator (Python + Faker)
        │
        ▼
Kafka (Confluent Cloud)          ← streaming layer
        │
        ▼
Python Consumer                  ← validates + enriches events (geo, device)
        │
        ▼
MongoDB Atlas                    ← raw store (events, orders, products, users)
        │
   ┌────┴────────────┐
   ▼                 ▼
Airflow DAGs     Great Expectations   ← orchestration + data quality
   │
   ▼
MongoDB Atlas (aggregated)       ← products.stats, users.rfm updated nightly
   │
   ▼
Streamlit Dashboard + FastAPI    ← live KPIs + REST API
```

---

## Features

- **Event streaming** — simulates realistic e-commerce events (page views, add-to-cart, purchases, returns) at configurable throughput via Kafka
- **Enrichment** — Kafka consumer geo-enriches events (country, city) and parses device type from User-Agent
- **MongoDB modelling** — document schema designed around read patterns with embedded snapshots, pre-aggregated stats, and TTL-indexed raw events
- **Airflow orchestration** — nightly DAGs compute RFM scores, update product stats, run quality checks, and archive stale data
- **Data quality** — Great Expectations suite validates nulls, value ranges, referential integrity, and flags anomalies
- **Live dashboard** — Streamlit app shows revenue by hour, conversion funnel, top products, cart abandonment rate, and user segments
- **REST API** — FastAPI exposes aggregated insights as JSON endpoints

---

## Tech Stack

| Layer | Tool | Notes |
|---|---|---|
| Simulation | Python + Faker | Configurable event rate |
| Streaming | Kafka (Confluent Cloud) | Free tier |
| Storage | MongoDB Atlas | Free tier (M0) |
| Orchestration | Apache Airflow | Astronomer free tier |
| Data quality | Great Expectations | Runs inside Airflow DAG |
| Serving | Streamlit + FastAPI | Community Cloud (free) |

---

## Project Structure

```
real_time_ecommerce_analytics_pipeline/
├── simulator/
│   ├── event_generator.py       # Faker-based event producer
│   └── kafka_producer.py        # Publishes to Kafka topics
├── consumer/
│   ├── kafka_consumer.py        # Reads from Kafka, enriches, writes to Mongo
│   └── enrichers/
│       ├── geo_enricher.py      # IP → country/city
│       └── device_enricher.py   # UA string → device type
├── mongo/
│   ├── schemas.py               # Collection schemas + index definitions
│   └── setup.py                 # Creates collections and indexes on Atlas
├── dags/
│   ├── nightly_aggregations.py  # Updates products.stats and users.rfm
│   ├── data_quality.py          # Runs Great Expectations suite
│   └── archive_events.py        # Moves old events to cold storage
├── quality/
│   └── expectations/            # Great Expectations checkpoint configs
├── api/
│   └── main.py                  # FastAPI app with aggregation endpoints
├── dashboard/
│   └── app.py                   # Streamlit dashboard
├── docs/
│   └── DECISIONS.md             # Architecture and tradeoff log
├── docker-compose.yml           # Local Kafka + Airflow setup
├── requirements.txt
└── README.md
```

---

## MongoDB Collections

| Collection | Key design decision |
|---|---|
| `events` | Flat schema, TTL index (90 days), enriched by consumer |
| `orders` | Line items and address embedded as snapshots (prices can change) |
| `products` | Category name embedded to avoid joins; `stats` updated by DAG |
| `users` | Last 10 orders embedded; RFM scores updated nightly by DAG |

See [`docs/DECISIONS.md`](docs/DECISIONS.md) for detailed schema rationale.

---

## Getting Started

### Prerequisites

- Python 3.11+
- Docker + Docker Compose (for local Kafka + Airflow)
- MongoDB Atlas account (free tier)
- Confluent Cloud account (free tier)

### 1. Clone and install

```bash
git clone https://github.com/your-username/ecommerce-pipeline.git
cd ecommerce-pipeline
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Fill in: MONGO_URI, KAFKA_BOOTSTRAP_SERVERS, KAFKA_API_KEY, KAFKA_API_SECRET
```

### 3. Set up MongoDB Atlas

```bash
python mongo/setup.py
# Creates collections and all indexes
```

### 4. Start local services

```bash
docker-compose up -d
# Starts Airflow webserver + scheduler
```

### 5. Run the pipeline

```bash
# Terminal 1 — start the consumer
python consumer/kafka_consumer.py

# Terminal 2 — start the event simulator
python simulator/event_generator.py --rate 10  # events per second
```

### 6. Launch the dashboard

```bash
streamlit run dashboard/app.py
```

---

## Key Metrics Tracked

- Revenue by hour / day / week
- Conversion funnel (view → cart → purchase)
- Cart abandonment rate
- Top 10 products by revenue and by views
- Revenue by user segment (RFM-based)
- Geographic breakdown of orders
- Mobile vs desktop conversion comparison

---

## Data Quality Checks

Run via Airflow DAG or manually:

```bash
great_expectations checkpoint run ecommerce_checkpoint
```

Checks include:
- No null `user_id`, `type`, or `timestamp` in events
- Order totals match sum of line items (within rounding tolerance)
- Product inventory quantities are non-negative
- All order `status` values are within the allowed enum

---

## Design Decisions

Key tradeoffs documented in [`docs/DECISIONS.md`](docs/DECISIONS.md), including:

- Why line items are embedded in orders rather than referenced
- Why raw events use a TTL index instead of manual archiving
- Why RFM scores are pre-computed by a DAG rather than calculated at query time
- Kafka vs direct MongoDB write for the simulator

---

## What I Learned / Talking Points

- Designing MongoDB schemas around read patterns rather than normalisation
- Using aggregation pipelines as the MongoDB equivalent of dbt models
- TTL indexes for automatic data lifecycle management
- Building idempotent Airflow DAGs with proper sensors and retries
- Data quality as a first-class concern integrated into orchestration

---

## Roadmap (nice to have)

- [ ] Add MongoDB Atlas Search for full-text product search endpoint
- [ ] Swap Streamlit for a React frontend consuming the FastAPI
- [ ] Add a dead-letter queue in Kafka for malformed events
- [ ] Deploy on GCP (Cloud Run + Atlas) for a fully cloud-hosted demo

---

## License

MIT