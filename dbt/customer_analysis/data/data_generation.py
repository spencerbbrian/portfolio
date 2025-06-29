import csv
import random
from datetime import datetime, timedelta

num_users = 1000

# Simple lists of first and last names
first_names = [
    "James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda",
    "William", "Elizabeth", "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica",
    "Thomas", "Sarah", "Charles", "Karen"
]
last_names = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
    "Thomas", "Taylor", "Moore", "Jackson", "Martin"
]

with open('customers.csv', mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerow(['customer_id', 'first_name', 'last_name', 'email'])
    for customer_id in range(1, num_users + 1):
        first_name = random.choice(first_names)
        last_name = random.choice(last_names)
        email = f"{first_name.lower()}.{last_name.lower()}@example.com"
        writer.writerow([customer_id, first_name, last_name, email])

num_orders = 2000
order_start_id = 101
order_dates_start = datetime(2025, 1, 1)
order_dates_end = datetime(2025, 6, 30)

def random_date(start, end):
    delta = end - start
    random_days = random.randint(0, delta.days)
    return start + timedelta(days=random_days)

with open('orders.csv', mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerow(['order_id', 'customer_id', 'order_date', 'amount'])
    for order_id in range(order_start_id, order_start_id + num_orders):
        customer_id = random.randint(1, num_users)
        order_date = random_date(order_dates_start, order_dates_end).strftime('%Y-%m-%d')
        amount = round(random.uniform(10.0, 200.0), 2)
        writer.writerow([order_id, customer_id, order_date, f"{amount:.2f}"])