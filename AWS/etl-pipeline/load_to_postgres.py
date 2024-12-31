import pandas as pd
import psycopg2

# Database credentials
db_config = {
    'dbname': 'etldb123',  # Default database to connect to
    'user': 'postgres',
    'password': 'password123',
    'host': 'etldb123.czsw0a0qua2l.us-west-2.rds.amazonaws.com',
    'port': '5432'
}

# Load the transformed data
transformed_file = 'transformed_sales_data.csv'
df = pd.read_csv(transformed_file)

# Connect to the PostgreSQL database
conn = psycopg2.connect(**db_config)
cursor = conn.cursor()

# Load the data into the 'sales_data' table
for index, row in df.iterrows():
    insert_query = """
    INSERT INTO sales_data (order_date, customer_name, price)
    VALUES (%s, %s, %s);
    """
    cursor.execute(insert_query, (row['order_date'], row['customer_name'], row['price']))

conn.commit()
print('Data loaded to PostgreSQL')
cursor.close()
conn.close()