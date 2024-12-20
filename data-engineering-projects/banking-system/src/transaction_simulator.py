import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from db_connection import get_db_connection
from data_config import TRANSACTION_TYPES, POS_PAYMENTS
from pymongo import DESCENDING
from datetime import datetime

import faker
import random

fake = faker.Faker()

def convert_currency(db,currency_pair,amount):
    rate = db.exchange.find_one({"currency_pair": currency_pair})['exchange_rate']
    return amount * rate  


def get_next_transaction_id(db):
    latest_transaction = db.transactions.find_one(
        sort=[("transaction_id", DESCENDING)]
    )

    if latest_transaction:
        last_id = latest_transaction["transaction_id"]
        last_number = int(last_id.replace("TX", ""))
        new_id = f"TX{last_number + 1:09d}"
    else:
        new_id = "TX000000001"
        
    return new_id


def generate_transactions(db):
    try:
        transaction_type = random.choice(TRANSACTION_TYPES)
        deposit_withdrawal_amount = round(random.uniform(100.0, 10000.0), 2)

        primary_account = random.choice(list(db.accounts.find({"account_category": "Customer"})))
        primary_account_currency = primary_account["currency"]
        primary_minimum_balance = primary_account["minimum_balance"]
        primary_account_balance = primary_account["current_balance"]

        secondary_account = random.choice(list(db.accounts.find({"account_category": "Customer", "_id": {"$ne": primary_account["_id"]}})))
        secondary_account_currency = secondary_account["currency"]
        secondary_minimum_balance = secondary_account["minimum_balance"]
        secondary_account_balance = secondary_account["current_balance"]
    
        bank_charge = round(random.uniform(0.5, 1.0), 2)
    
        if transaction_type == "deposit":
            print(f"{primary_account_balance}")
            primary_account_balance += deposit_withdrawal_amount
            print(f"Depositing {deposit_withdrawal_amount} into account {primary_account['account_id']}.")
            print(f"New balance: {primary_account_balance}")

            db.accounts.update_one(
                {"_id": primary_account['_id']},
                {"$set": {"current_balance": primary_account_balance}}
                )
            
            transaction = {
            "transaction_id": get_next_transaction_id(db),
            "transaction_type": transaction_type,
            "amount": deposit_withdrawal_amount,
            "charge": 0.0,
            "currency": primary_account_currency,
            "sender_account_id": "external",
            "receiver_account_id": primary_account["account_id"],
            "timestamp": datetime.now(),
            "status": "success"
            }
            db.transactions.insert_one(transaction)
            return  
        
        elif transaction_type == "withdrawal":
            print(f"{primary_account_balance}")
            primary_account_balance -= (deposit_withdrawal_amount + bank_charge)
            print(f"Withdrawing {deposit_withdrawal_amount} from account {primary_account['account_id']}.")
            print(f"New balance: {primary_account_balance}")

            db.accounts.update_one(
                {"_id": primary_account['_id']},
                {"$set": {"current_balance": primary_account_balance}}
                )
            
            transaction = {
            "transaction_id": get_next_transaction_id(db),
            "transaction_type": transaction_type,
            "amount": deposit_withdrawal_amount,
            "charge": bank_charge,
            "currency": primary_account_currency,
            "sender_account_id": "NA",
            "receiver_account_id": primary_account["account_id"],
            "timestamp": datetime.now(),
            "status": "success"
            }
            db.transactions.insert_one(transaction)
            return  

    except Exception as e:
        print(f"An error occurred: Transaction could not be completed. {e}")
        return
    
# def log_failed_transaction(db, transaction_type, amount, charge, currency, account_id):
#     transaction = {
#         "transaction_id": get_next_transaction_id(db),
#         "transaction_type": transaction_type,
#         "amount": amount,
#         "charge": charge,
#         "currency": currency,
#         "account_id": account_id,
#         "timestamp": datetime.combine(fake.date_this_month(), datetime.min.time()),
#         "status": "failed"
#     }
#     db.transactions.insert_one(transaction)
    
def main():
    db = get_db_connection()
    if db is not None:
        for i in range(1):
            generate_transactions(db)
    else:
        print("Could not connect to the database.")
        
if __name__ == "__main__":
    main()