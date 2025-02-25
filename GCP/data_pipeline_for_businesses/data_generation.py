import pandas as pd
import numpy as np
from faker import Faker
import random

# Initialize Faker for realistic data
fake = Faker()

# Generate customer data
num_customers = 100000

customer_data = { 
    "customer_id": [f"CUST{10000 + i}" for i in range(num_customers)],
    "name": [fake.name() for _ in range(num_customers)],
    "email": [fake.email() for _ in range(num_customers)],
    "phone": [fake.phone_number() for _ in range(num_customers)],
    "city": [fake.city() for _ in range(num_customers)],
    "state": [fake.state() for _ in range(num_customers)],
    "zipcode": [fake.zipcode() for _ in range(num_customers)],
    "join_date": [fake.date_between(start_date='-3y', end_date='today') for _ in range(num_customers)]
}

# Create a pandas DataFrame
df_customers = pd.DataFrame(customer_data)

df_customers.to_csv("customer_data.csv", index=False)
print("Customer data generated and saved to customer_data.csv")


# Generate sales transaction data
num_sales = 1000000

# Generate unique product IDs for sales data
product_ids_sales = [f"PROD{i + 1}" for i in range(100)]  # 100 unique products

data_sales = {
    "transaction_id": [f"TXN{100000 + i}" for i in range(num_sales)],
    "customer_id": random.choices(df_customers["customer_id"], k=num_sales),
    "product_id": random.choices(product_ids_sales, k=num_sales),  # Use the same product IDs
    "quantity": [random.randint(1, 10) for _ in range(num_sales)],
    "price": [round(random.uniform(10, 500), 2) for _ in range(num_sales)],
    "transaction_date": [fake.date_time_between(start_date='-2y', end_date='now') for _ in range(num_sales)],
    "store_id": [f"STORE{random.randint(1, 50)}" for _ in range(num_sales)],
    "payment_method": [random.choice(["Credit Card", "Debit Card", "Cash", "Online Payment"]) for _ in range(num_sales)]
}

df_sales = pd.DataFrame(data_sales)
df_sales["total_sales"] = df_sales["quantity"] * df_sales["price"]

df_sales.to_csv("sales_data.csv", index=False)
print("Sales data generated and saved to sales_data.csv")


# Generate inventory data
num_rows = 500000  # 500,000 rows

# Use the same product IDs as in sales data
product_ids_inventory = product_ids_sales  # Ensure matching product IDs

# Generate synthetic inventory data
data_inventory = {
    "product_id": random.choices(product_ids_inventory, k=num_rows),  # Match product IDs
    "product_name": [fake.catch_phrase() for _ in range(num_rows)],
    "warehouse_id": [f"WH{random.randint(1, 20)}" for _ in range(num_rows)],
    "stock_level": [random.randint(0, 1000) for _ in range(num_rows)],
    "reorder_level": [random.randint(50, 200) for _ in range(num_rows)],
    "last_restock_date": [fake.date_between(start_date="-2y", end_date="now") for _ in range(num_rows)],
}

# Create a DataFrame
df_inventory = pd.DataFrame(data_inventory)

# Save to CSV
df_inventory.to_csv("inventory_data.csv", index=False)
print("Inventory data generated and saved to inventory_data.csv")