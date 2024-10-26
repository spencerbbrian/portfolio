from src.db_connection import get_db_connection
import json, random, os, sys
from random import choice
from faker import Faker
from config.data_config import COUNTRIES, MERCHANT_TYPES, ACCOUNT_TYPES, TRANSACTION_TYPES, CURRENCIES

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

def generate_merchants(num_merchants):
    merchants = []
    merchants_accounts = []
    db = get_db_connection()
    
   
    for merchant in range(num_merchants):
        merchant_id = int(f"{fake.unique.random_int(min=1,max=99999)}{fake.unique.random_int(min=10,max=100)}")
        country = random.choice(COUNTRIES)
        if country == "USA":
            currency = CURRENCIES[0]["code"]
        else:
            currency = CURRENCIES[1]["code"]
        country_banks = list(db.banks.find({"country": country}))
        if country_banks:
            company_bankid = choice(country_banks)["bank_id"]
        else:
            print("No registered banks in this country!")


        merchant = {
            "merchant_id": merchant_id,
            "merchant_name": fake.company(),
            "merchant_type": random.choice(MERCHANT_TYPES),
            "currency": currency,
            "location": {
                    "address": fake.address(),
                    "country": country,
            },
            "contact_details": {
                "phone_number": fake.phone_number(),
                "email": fake.company_email()
            },
            "account_id": merchant_id
        }
        merchant_account = {
            "account_id": merchant_id,
            "account_holder_name": merchant["merchant_name"],
            "account_type": "savings",
            "current_balance": 0.0,
            "minimum_balance": 0.0,
            "bank_id": company_bankid,
            "currency": currency,
            "account_category": "Merchant"
        }
        merchants_accounts.append(merchant_account)
        merchants.append(merchant)
    return merchants, merchants_accounts




def load_data(db,merchants,merchants_accounts):
    if merchants:
        db.merchants.insert_many(merchants)
        print(f"Inserted {len(merchants)} merchants into the banks collection.")
    if merchants_accounts:
        db.accounts.insert_many(merchants_accounts)
        print(f"Inserted {len(merchants_accounts)} merchant accounts in the accounts collection.")

def main():
    if len(sys.argv) != 2:
        print("Usage: python data_loader.py <num_merchants>")
        sys.exit(1)

    num_merchants = int(sys.argv[1])

    db = get_db_connection()

    merchants, merchants_accounts = generate_merchants(num_merchants)

    load_data(db, merchants, merchants_accounts)

if __name__ == "__main__":
    main()