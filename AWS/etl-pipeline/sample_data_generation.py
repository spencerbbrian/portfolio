import csv
import random
from datetime import datetime, timedelta

# Function to generate random date
def random_date(start, end):
    return start + timedelta(
        seconds=random.randint(0, int((end - start).total_seconds())),
    )

# Sample data
order_ids = range(1, 101)
customer_names = ['Alice', 'Bob', 'Charlie', 'David', 'Eva']
start_date = datetime(2021, 1, 1)
end_date = datetime(2021, 12, 31)

# Generate sample data
rows = []
for order_id in order_ids:
    order_date = random_date(start_date, end_date).strftime('%Y-%m-%d')
    customer_name = random.choice(customer_names)
    price = round(random.uniform(10.0, 100.0), 2)
    rows.append([order_id, order_date, customer_name, price])

# Write to CSV file
with open('sales_data.csv', 'w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['order_id', 'order_date', 'customer_name', 'price'])
    writer.writerows(rows)

print("Sample CSV file 'sales_data.csv' created successfully.")