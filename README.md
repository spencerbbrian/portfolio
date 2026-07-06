# Data Analytics & Engineering Portfolio

Hi, I'm Spencer, an Analytics Engineer / Data Engineer wrapping up a Master's degree via an alternance contract at Decathlon Digital. This repo collects the data engineering, analytics engineering, and dashboarding projects I've built to practice production-grade patterns: layered dbt modeling, cloud-native pipelines, orchestration, and CI/CD.

For visual walkthroughs of select projects, see my static [portfolio site](https://sites.google.com/view/spencerbbrian/about).

## Featured Projects

### Olist E-Commerce Analytics — dbt + Snowflake + Airflow + GCP
`dbt/olist/`
End-to-end analytics engineering pipeline: raw e-commerce data ingested into Snowflake via GCP, orchestrated with Apache Airflow, and transformed through a layered dbt architecture (staging → intermediate → marts), including multi-channel marketing attribution models. CI/CD is handled with GitHub Actions (`dbt_ci.yml` / `dbt_cd.yml`).

### Banking System — Transaction Processing with MongoDB
`data-engineering/banking-system/`
Backend system modeling core banking transaction flows, using MongoDB for flexible, document-oriented storage of accounts and transfers.

### Golden Heights University Database System — Flask *(in progress)*
`projects-in-progress/golden-heights/`
A university database system built with Flask, covering core CRUD operations and relational data modeling for academic records.

### Analytics Engineering Projects
`analytics-engineering/`
Additional dashboarding, SQL, and analytics engineering work, including executive dashboard design (e.g., a multi-dashboard Tableau build covering global performance, profitability/risk, and customer growth using LOD expressions and YoY BAN card patterns).

## Project Types

- Analytics Engineering (dbt, layered data modeling)
- Data Engineering & Orchestration (Airflow, cloud pipelines)
- Dashboarding & Executive Reporting
- SQL-focused projects
- Flask/Django apps supporting DE projects
- Miniature Python projects

## Technologies Used

- **Languages:** Python, SQL
- **Data Warehousing:** Snowflake
- **Transformation:** dbt (dbt Core)
- **Orchestration:** Apache Airflow
- **Cloud:** GCP
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
