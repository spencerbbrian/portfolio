from src.db_connection import get_db_connection
import random, sys
from random import choice
from faker import Faker
from data_config import COUNTRIES, MERCHANT_TYPES, ACCOUNT_TYPES, CURRENCIES
import uuid

fake = Faker()

def generate_banks(num_banks):
    banks = []  # List to store bank dictionaries
    bank_ids = set()  # Set to track unique bank IDs
    while len(banks) < num_banks:
        bank_id = fake.unique.random_int(min=1, max=999999)  # Increase the range for unique bank ID
        if bank_id not in bank_ids:
            bank = {
                "bank_id": bank_id,
                "bank_name": fake.unique.company(),
                "country": random.choice(COUNTRIES),
                "transfer_fee": round(random.uniform(5.0, 15.0), 2),
                "minimum_balance": round(random.uniform(50.0, 150.0), 2)
            }
            banks.append(bank)
            bank_ids.add(bank_id)
    return banks 

def generate_merchants(num_merchants):
    merchants = []
    merchants_accounts = []
    db = get_db_connection()
    
    for _ in range(num_merchants):
        # Modified merchant_id generation
        merchant_id = int(f"{fake.unique.random_int(min=1, max=9999999)}")  # Increase range for uniqueness
        country = random.choice(COUNTRIES)
        currency = CURRENCIES[0]["code"] if country == "USA" else CURRENCIES[1]["code"]
        country_banks = list(db.banks.find({"country": country}))
        
        if country_banks:
            company_bankid = choice(country_banks)["bank_id"]
        else:
            print("No registered banks in this country!")
            continue

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
            "account_type": "regular",
            "current_balance": 0.0,
            "minimum_balance": 0.0,
            "bank_id": company_bankid,
            "currency": currency,
            "account_category": "Merchant"
        }
        merchants_accounts.append(merchant_account)
        merchants.append(merchant)
    return merchants, merchants_accounts

def generate_accounts(num_accounts):
    accounts = []
    db = get_db_connection()
    
    while len(accounts) < num_accounts:
        country = random.choice(COUNTRIES)
        country_banks = list(db.banks.find({"country": country}))
        
        if not country_banks:
            print(f"No banks available in {country}. Skipping account generation for this iteration.")
            continue
        
        currency = CURRENCIES[0]["code"] if country == "USA" else CURRENCIES[1]["code"]
        customer_bankid = choice(country_banks)["bank_id"]
        account_type = random.choice(ACCOUNT_TYPES)
        
        # Setting credit-specific fields based on account type
        credit_limit = 0.0
        credit_balance = 0.0
        if account_type == "credit":
            credit_limit = round(random.uniform(1000.0, 5000.0), 2)
            credit_balance = round(random.uniform(0.0, credit_limit), 2)
        
        account_holder_name = fake.name()
        current_balance = round(random.uniform(100.0, 150000.0), 2)
        minimum_balance = db.banks.find_one({"bank_id": customer_bankid, "country": country})["minimum_balance"]
        
        # Modified account_id generation for uniqueness
        account_id = f"{country[:2].upper()}{str(customer_bankid)[:3]}{account_type[:3].upper()}{uuid.uuid4().hex[:8]}"
        
        customer_account = {
            "account_id": account_id,
            "account_holder_name": account_holder_name,
            "account_type": account_type,
            "current_balance": current_balance,
            "minimum_balance": minimum_balance,
            "credit_limit": credit_limit,
            "credit_balance": credit_balance,
            "bank_id": customer_bankid,
            "currency": currency,
            "account_category": "Customer"
        }
        
        accounts.append(customer_account)
        
    return accounts

def load_data(db, banks, merchants, merchants_accounts, accounts):
    if banks:
        db.banks.insert_many(banks)
        print(f"Inserted {len(banks)} banks in the banks collection.")
    if merchants:
        db.merchants.insert_many(merchants)
        print(f"Inserted {len(merchants)} merchants in the merchants collection.")
    if merchants_accounts:
        db.accounts.insert_many(merchants_accounts)
        print(f"Inserted {len(merchants_accounts)} merchant accounts in the accounts collection.")
    if accounts:
        db.accounts.insert_many(accounts)
        print(f"Inserted {len(accounts)} accounts in the accounts collection.")

def main():
    if len(sys.argv) != 4:
        print("Usage: python data_loader.py <num_banks> <num_accounts> <num_merchants>")
        sys.exit(1)

    num_banks = int(sys.argv[1])
    num_merchants = int(sys.argv[2])
    num_accounts = int(sys.argv[3])

    db = get_db_connection()

    banks = generate_banks(num_banks)
    merchants, merchants_accounts = generate_merchants(num_merchants)
    accounts = generate_accounts(num_accounts)

    load_data(db, banks, merchants, merchants_accounts, accounts)

if __name__ == "__main__":
    main()
