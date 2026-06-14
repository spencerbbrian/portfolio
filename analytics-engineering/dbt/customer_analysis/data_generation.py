import csv
import random
from datetime import datetime, timedelta
import os
import json
import argparse # New import for command-line arguments

# --- Configuration ---
NUM_USERS = 100 
CUSTOMER_FILE = 'data/customers.csv'
ORDERS_FILE = 'data/orders.csv'
STATE_FILE = 'data/data_generation_state.json' # To store last generated IDs/dates

# Ensure the data directory exists
os.makedirs('data', exist_ok=True)

# Simple lists for customer data
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

# --- State Management Functions ---
def load_state():
    """Loads max_order_id and latest_order_date from state file."""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            state = json.load(f)
            return state.get('max_order_id', 100), datetime.strptime(state.get('latest_order_date', '2025-01-01'), '%Y-%m-%d')
    return 100, datetime(2025, 1, 1) # Default initial state

def save_state(max_id, latest_date):
    """Saves current max_order_id and latest_order_date to state file."""
    state = {
        'max_order_id': max_id,
        'latest_order_date': latest_date.strftime('%Y-%m-%d')
    }
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=4)

# --- Helper for random dates ---
def random_date(start, end):
    """Generates a random date between start and end (inclusive)."""
    delta = end - start
    random_days = random.randint(0, delta.days)
    return start + timedelta(days=random_days)

# --- Data Generation Functions ---
def generate_customers():
    """Generates (or overwrites) the customers.csv file."""
    print(f"Generating {NUM_USERS} customer records to {CUSTOMER_FILE}...")
    with open(CUSTOMER_FILE, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['customer_id', 'first_name', 'last_name', 'email'])
        for customer_id in range(1, NUM_USERS + 1):
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)
            email = f"{first_name.lower()}.{last_name.lower()}@example.com"
            writer.writerow([customer_id, first_name, last_name, email])
    print("Customer data generated.")

def generate_orders(num_orders_to_add, initial_run=False):
    """
    Generates new order data, either starting fresh or appending incrementally.
    """
    current_max_order_id, current_latest_order_date = load_state()

    if initial_run:
        print(f"\n--- Performing INITIAL order generation ({num_orders_to_add} records) ---")
        # For an initial run, we start fresh and clear existing files
        if os.path.exists(ORDERS_FILE):
            os.remove(ORDERS_FILE)
            print(f"Removed existing {ORDERS_FILE} for a fresh initial load.")
        
        # Reset state for truly fresh start
        new_order_id_start = 101
        new_order_date_start = datetime(2025, 1, 1)
        # Generate initial data for a longer period
        new_order_date_end = new_order_date_start + timedelta(days=180) # Initial 6 months
        
        mode = 'w' # Write mode to create/overwrite file
        write_header = True
    else:
        print(f"\n--- Performing INCREMENTAL order generation ({num_orders_to_add} records) ---")
        # For incremental run, use the last saved state
        new_order_id_start = current_max_order_id + 1
        new_order_date_start = current_latest_order_date + timedelta(days=1)
        # Generate incremental data for a shorter period
        new_order_date_end = new_order_date_start + timedelta(days=30) # New data for next month

        mode = 'a' # Append mode
        write_header = not os.path.exists(ORDERS_FILE) or os.path.getsize(ORDERS_FILE) == 0

    print(f"Generating orders from ID: {new_order_id_start}")
    print(f"Generating order dates between: {new_order_date_start.strftime('%Y-%m-%d')} and {new_order_date_end.strftime('%Y-%m-%d')}")

    with open(ORDERS_FILE, mode=mode, newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        if write_header:
            writer.writerow(['order_id', 'customer_id', 'order_date', 'amount', 'order_status'])

        latest_generated_date = new_order_date_start # Track max date generated in this run
        for i in range(num_orders_to_add):
            order_id = new_order_id_start + i
            customer_id = random.randint(1, NUM_USERS)
            order_date_dt = random_date(new_order_date_start, new_order_date_end)
            order_date_str = order_date_dt.strftime('%Y-%m-%d')
            
            if order_date_dt > latest_generated_date: # Keep track of the latest date *in this batch*
                latest_generated_date = order_date_dt

            amount = round(random.uniform(10.0, 200.0), 2)
            order_status = random.choice(['completed', 'pending', 'cancelled', 'returned', 'shipped']) # More statuses for realism
            writer.writerow([order_id, customer_id, order_date_str, f"{amount:.2f}", order_status])

    final_max_order_id = new_order_id_start + num_orders_to_add - 1
    save_state(final_max_order_id, latest_generated_date) # Save the state based on what was actually generated
    print(f"Finished generating {num_orders_to_add} records.")
    print(f"Current state saved: Max order_id={final_max_order_id}, Latest order_date={latest_generated_date.strftime('%Y-%m-%d')}")


# --- Main Execution Logic with Argparse ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate customer and order data for dbt seed files, supporting initial and incremental loads."
    )
    parser.add_argument(
        '--mode',
        choices=['initial', 'incremental'],
        default='incremental',
        help="Specify 'initial' for a full data generation (overwrites existing files) or 'incremental' to append new data."
    )
    parser.add_argument(
        '--num-orders',
        type=int,
        default=50, # Default for incremental batches
        help="Number of order records to generate. Default is 50 for incremental, 2000 for initial if not specified."
    )

    args = parser.parse_args()

    print("Starting data generation process...")
    generate_customers() # Customers are always regenerated as a full file (small enough)

    if args.mode == 'initial':
        initial_order_count = args.num_orders if args.num_orders != 50 else 2000 # Use 2000 as default for initial if user didn't specify
        generate_orders(initial_order_count, initial_run=True)
    elif args.mode == 'incremental':
        generate_orders(args.num_orders, initial_run=False)

    print("\nData generation complete.")
    print(f"Check your 'data/' directory for updated CSVs and '{STATE_FILE}' for state persistence.")