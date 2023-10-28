*Instructions: Click on the raw button in the upper right hand corner of this box.  Copy and paste the template into the README.md document on your github.  Fill in the titles, information and links where prompted! Feel free to stray a bit to suit your project but try to stick to the format as closely as possible for consistency across DSWG projects.*

# Project Name
This project is a part of the [Data Science Working Group](http://datascience.codeforsanfrancisco.org) at [Code for San Francisco](http://www.codeforsanfrancisco.org).  Other DSWG projects can be found at the [main GitHub repo](https://github.com/sfbrigade/data-science-wg).

#### -- Project Status: [Active, On-Hold, Completed]

## Project Intro/Objective
The purpose of this project is ________. (Describe the main goals of the project and potential civic impact. Limit to a short paragraph, 3-6 Sentences)

### Partner
* [Name of Partner organization/Government department etc..]
* Website for partner
* Partner contact: [Name of Contact], [slack handle of contact if any]
* If you do not have a partner leave this section out

### Methods Used
* Inferential Statistics
* Machine Learning
* Data Visualization
* Predictive Modeling
* etc.

### Technologies
* R 
* Python
* D3
* PostGres, MySql
* Pandas, jupyter
* HTML
* JavaScript
* etc. 

## Project Description
(Provide more detailed overview of the project.  Talk a bit about your data sources and what questions and hypothesis you are exploring. What specific data analysis/visualization and modelling work are you using to solve the problem? What blockers and challenges are you facing?  Feel free to number or bullet point things here)

## Needs of this project

- frontend developers
- data exploration/descriptive statistics
- data processing/cleaning
- statistical modeling
- writeup/reporting
- etc. (be as specific as possible)

## Getting Started

1. Clone this repo (for help see this [tutorial](https://help.github.com/articles/cloning-a-repository/)).
2. Raw Data is being kept [here](Repo folder containing raw data) within this repo.

    *If using offline data mention that and how they may obtain the data from the froup)*
    
3. Data processing/transformation scripts are being kept [here](Repo folder containing data processing scripts/notebooks)
4. etc...

*If your project is well underway and setup is fairly complicated (ie. requires installation of many packages) create another "setup.md" file and link to it here*  

5. Follow setup [instructions](Link to file)

## Featured Notebooks/Analysis/Deliverables
* [Notebook/Markdown/Slide Deck Title](link)
* [Notebook/Markdown/Slide DeckTitle](link)
* [Blog Post](link)


## Contributing DSWG Members

**Team Leads (Contacts) : [Full Name](https://github.com/[github handle])(@slackHandle)**

#### Other Members:

|Name     |  Slack Handle   | 
|---------|-----------------|
|[Full Name](https://github.com/[github handle])| @johnDoe        |
|[Full Name](https://github.com/[github handle]) |     @janeDoe    |

## Contact
* If you haven't joined the SF Brigade Slack, [you can do that here](http://c4sf.me/slack).  
* Our slack channel is `#datasci-projectname`
* Feel free to contact team leads with any questions or if you are interested in contributing!



# Introduction
At Code for San Francisco we host a PostgreSQL server on Microsoft Azure. We host this under the Resource Group "sba" which is only because the first project to use a PostgreSQL server was the [Small Business Administration Project](https://github.com/sfbrigade/datasci-sba).

This doc will document some commands to make setting up new roles and databases easier.

## Creating a new Database
We recommend to spin up a new database for each project.

To create a new database, you will need to login to the server with administrator credentials. If you do not have administrator credentials please contact the current DSWG Team Leads.

After logging into the PostgreSQL server, use `\l` to view a list of all existing databases within the server

```
\l
```

Then, to create the database:

```
create database YOURDATABASENAME;
```

I would suggest not using any special characters or spaces as it will be very annoying to have to escape those in the future.

## Creating a new Role
With each new project, we recommend to create a different postgres role. Each project should login to the server using their own role.

To create a new role:

```
CREATE ROLE rolename WITH LOGIN PASSWORD 'password';
```

We recommend to not use additional options (e.g. `CREATEDB`, `CREATEUSER`). Administrative access should be controlled only by the administrator account. Please talk to the Data Science Working Group team leads if you need additional priveleges.

See the (official docs)[https://www.postgresql.org/docs/9.6/static/sql-createrole.html] for more information.

## Granting Priveleges
We should have one database and one main role. Once you have set up the database and the role for the project, you will need to `GRANT ALL PRIVELEGES` for the role to the database. This will ensure that the role can do everything it needs to (e.g. write tables, read, etc.) in that specific database. To do this:

```
GRANT ALL PRIVILEGES ON DATABASE datasbasename to username;
```

## Setting up a Read Only User
Setting up a Read Only User is a great/low effort way to share data with others while maintaining security of the database (more often than not we're just trying to protect ourselves from accidental writes to the DB!). Note that as of October 2017, it is not possible to automatically grant read access to all schemas and **all future schemas**, you will need to do this manually for each schema. In the example below, I am granting read only access to two schemas: `public` and `data_ingest`. If you were to add new schemas in the future you would need to `GRANT USAGE` and `GRANT SELECT ON ALL TABLES IN SCHEMA` for that particular schema.

First, follow the steps above to create a new user. In the example below, I am using `readonly` as the user.

```
-- Grant connect on database
GRANT CONNECT ON DATABASE databasename to readonly;

-- Connect to [databasename] on local database cluster
\c databasename 

-- Grant Usage to schemas
GRANT USAGE ON SCHEMA public TO readonly;
GRANT USAGE ON SCHEMA data_ingest TO readonly;

-- Grant access to future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA data_ingest GRANT SELECT ON TABLES to readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA data_ingest GRANT ALL ON TABLES TO readonly;

GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA data_ingest TO readonly;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA data_ingest TO readonly;
```

After creating a role, you can (optionally) create different users with the same `readonly` role. For example

```
-- Create a final user with password
CREATE USER otherreadonlyuser WITH PASSWORD 'secret';
GRANT readonly TO otherreadonlyuser;
```

Note that if you are running into issues even after running the above commands, make sure you are logged in as the user who is the owner of the particular schema. This will likely be the main user given to the project that was done by using:

```
GRANT ALL PRIVILEGES ON DATABASE datasbasename to username;
```

To list all schemas and the owners you can type `\dn` into the psql console. For example:

```
datascicongressionaldata=> \dn
             List of schemas
     Name      |          Owner
---------------+--------------------------
 data_ingest   | datascicongressionaldata
 public        | azure_superuser
 stg_analytics | datascicongressionaldata
 trg_analytics | datascicongressionaldata
(4 rows)
```

## Creating a Staging Database
There will be times where you will want to create a copy of a production database to create a staging database. This will allow members to push changes to a live database but not affect your "production" database. To do this start by copying the staging database:

```
CREATE DATABASE newdb WITH TEMPLATE originaldb;
```

You will want to create a new user/role first as described above in this doc. Preferably the name will indicate a `stg` name.

When you do this, you will next have to change the owner:

```
alter database stgdatascicongressionaldata owner to stgdatascicongressionaldata;
```

```
ALTER SCHEMA data_ingest OWNER TO stgdatascicongressionaldata;
```

```
reassign owned by datascicongressionaldata to stgdatascicongressionaldata;
```

In order to do the above you may have to assign the stg role to the original role

```
grant stgdatascicongressionaldata to datascicongressionaldata
```

### Projects On Hold

The following are in need of new project leads and contributing members.  Please check them out and reach out to DSWG team leads if you are interested in reviving one of these projects!

+ [Campaign Finance Project](https://github.com/sfbrigade/datasci-congressional-data)
+ [SF OpenData Search Analytics for Improving UX](https://github.com/sfbrigade/datasci-open-data-search)
+ [CTA-NorCal Homeless Program Outcomes Analysis](https://github.com/sfbrigade/datasci-sf-homeless-project)
+ [Interactive visualization of SF's building emissions and energy use](https://github.com/sfbrigade/datasci-SF-Environment-Benchmark)

### Past Projects
+ [Predicting Relative Risk of Fire in SF's Buildings](https://github.com/sfbrigade/datasci-firerisk/)
+ [Small Business Association](https://github.com/sfbrigade/datasci-sba) 
+ [Friends of the Urban Forest: Analyses and Visualizations](https://github.com/sfbrigade/datasci-urban-forest)
+ [CA Dept. of Justice OpenJustice Hypothesis Testing and Predictive Modeling](https://github.com/sfbrigade/CA_DOJ_OpenJustice)
+ [U.S. Dept. of Transportation Hazmat Incident Prediction and Anomaly Detection](https://github.com/bayeshack2016/cfsf-datasci_dot-hazmat)
+ [City of SF 311 Case Data Analysis](https://github.com/sfbrigade/data-science-wg/tree/master/projects-in-this-repo/SF_311_Data-Analysis)
+ [City of SF Budget Visualization](https://github.com/sameerank/sf-budget-visualization)
+ [U.S. Dept. of Transportation Traffic Fatality Analyses](https://github.com/sfbrigade/datasci-dot-fars)
