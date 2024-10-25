from src.db_connection import get_db_connection
import json, random, os, sys
from faker import Faker
from config.data_config import COUNTRIES, MERCHANT_TYPES, ACCOUNT_TYPES, TRANSACTION_TYPES

fake = Faker()

def generate_banks(num_banks):
    banks = []  # List to store bank dictionaries
    bank_ids = set()  # Set to track unique bank IDs
    while len(banks) < num_banks:
        # Create a bank dictionary
        bank_id = fake.unique.random_int(min=1, max=99999)  # Unique bank ID
        if bank_id not in bank_ids:  # Ensure bank ID is unique
            bank = {
                "bank_id": bank_id,
                "bank_name": fake.unique.company(),  # Unique bank name
                "country": random.choice(COUNTRIES),  # Choose a single country
                "transfer_fee": round(random.uniform(5.0, 15.0),2),  # Fixed transfer fee
                "minimum_balance": round(random.uniform(50.0, 150.0),2) # Fixed minimum balance
            }
            banks.append(bank)  # Add the bank to the list
            bank_ids.add(bank_id)  # Track the used bank ID
    return banks 

def load_data(db,banks):
    if banks:
        db.banks.insert_many(banks)
        print(f"Inserted {len(banks)} banks into the banks collection.")

def main():
    if len(sys.argv) != 2:
        print("Usage: python data_loader.py <num_banks>")
        sys.exit(1)

    num_banks = int(sys.argv[1])

    db = get_db_connection()

    banks = generate_banks(num_banks)

    load_data(db, banks)

if __name__ == "__main__":
    main()