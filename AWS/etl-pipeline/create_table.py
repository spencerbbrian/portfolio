import psycopg2
from psycopg2 import sql

# Database credentials for connecting to the default postgres database
db_config = {
    'dbname': 'postgres',  # Default database to connect to
    'user': 'postgres',
    'password': 'password123',
    'host': 'etldb123.czsw0a0qua2l.us-west-2.rds.amazonaws.com',
    'port': '5432'
}

# Connect to the PostgreSQL database
conn = psycopg2.connect(**db_config)
conn.autocommit = True  # Set autocommit to True to allow CREATE DATABASE

cursor = conn.cursor()

# Check if the database exists
cursor.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = 'etldb123';")
exists = cursor.fetchone()

if not exists:
    # If the database doesn't exist, create it
    cursor.execute('CREATE DATABASE "etldb123";')
    print("Database 'etldb123' created successfully!")

# Close the connection to the default database and reconnect to 'etldb123'
conn.close()

# Update the connection settings to point to the new database
db_config['dbname'] = 'etldb123'

# Reconnect to the 'etldb123' database
conn = psycopg2.connect(**db_config)
cursor = conn.cursor()

# Create a table in 'etldb123'
create_table_query = """
CREATE TABLE IF NOT EXISTS sales_data (
    order_id SERIAL PRIMARY KEY,
    order_date DATE,
    customer_name TEXT,
    price numeric
);
"""
cursor.execute(create_table_query)
conn.commit()

print("Table created successfully!")
cursor.close()
conn.close()
