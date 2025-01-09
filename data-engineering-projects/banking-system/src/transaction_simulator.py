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


def check_funds_available(db, account_id, amount, charge):
    account = db.accounts.find_one({"account_id": account_id})
    if not account:
        raise ValueError("Account not found")
    current_balance = account["current_balance"]
    minimum_balance = account["minimum_balance"]

    if current_balance - amount - charge < minimum_balance:
        return False
    return True


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
            if not check_funds_available(db, primary_account["account_id"], deposit_withdrawal_amount, bank_charge):
                print(f"Insufficient funds in account {primary_account['account_id']}.")
                transaction = {
                    "transaction_id": get_next_transaction_id(db),
                    "transaction_type": transaction_type,
                    "amount": deposit_withdrawal_amount,
                    "charge": bank_charge,
                    "currency": primary_account_currency,
                    "sender_account_id": primary_account["account_id"],
                    "receiver_account_id": "NA",
                    "timestamp": datetime.now(),
                    "status": "failed",
                    "reason": "Insufficient funds"
                }
                db.transactions.insert_one(transaction)
            else:
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
                    "sender_account_id": primary_account["account_id"],
                    "receiver_account_id": "NA",
                    "timestamp": datetime.now(),
                    "status": "success"
                }
                db.transactions.insert_one(transaction)
            return  
        
        elif transaction_type == "purchase" or transaction_type == "POS" or transaction_type == "payment":

            merchant_account = random.choice(list(db.accounts.find({"account_category": "Merchant"})))

            if transaction_type == "purchase":
                amount = round(random.uniform(10.0, 1000.0), 2)
                print(amount)
            else:
                amount = round(random.uniform(1.0, 250.0), 2)
                print(amount)

            print(f"{primary_account_balance}")
            if primary_account_currency != merchant_account["currency"]:
                merchant_amount = amount
                amount = convert_currency(db, f"{merchant_account['currency']}/{primary_account_currency}", amount)
            else:
                amount = amount
                merchant_amount = amount

            if not check_funds_available(db, primary_account["account_id"], amount, bank_charge):
                print(f"Insufficient funds in account {primary_account['account_id']}.")
                transaction = {
                    "transaction_id": get_next_transaction_id(db),
                    "transaction_type": transaction_type,
                    "amount": amount,
                    "charge": bank_charge,
                    "currency": primary_account_currency,
                    "sender_account_id": primary_account["account_id"],
                    "receiver_account_id": merchant_account["account_id"],
                    "timestamp": datetime.now(),
                    "status": "failed",
                    "reason": "Insufficient funds"
                }
                db.transactions.insert_one(transaction)
            else:
                primary_account_balance -= (amount + bank_charge)
                print(f"Making a payment of {merchant_amount} to merchant account {merchant_account['account_id']}.")
                print(f"New balance: {primary_account_balance}")

                merchant_account_balance = merchant_account["current_balance"]
                merchant_account_balance += merchant_amount

                db.accounts.update_one(
                    {"_id": primary_account['_id']},
                    {"$set": {"current_balance": primary_account_balance}}
                )

                db.accounts.update_one(
                    {"_id": merchant_account['_id']},
                    {"$set": {"current_balance": merchant_account_balance}}
                )

                
                transaction = {
                    "transaction_id": get_next_transaction_id(db),
                    "transaction_type": transaction_type,
                    "amount": amount,
                    "charge": bank_charge,
                    "currency": primary_account_currency,
                    "sender_account_id": primary_account["account_id"],
                    "receiver_account_id": merchant_account["account_id"],
                    "timestamp": datetime.now(),
                    "status": "success"
                }
                db.transactions.insert_one(transaction)
            return
            
        elif transaction_type == "cheque deposit":
            print(f"{primary_account_balance}")
            cheque_amount = round(random.uniform(2500.0, 100000.0), 2)

            if not check_funds_available(db, secondary_account["account_id"], cheque_amount, bank_charge):
                print(f"Insufficient funds in account {secondary_account['account_id']}.")
                transaction = {
                    "transaction_id": get_next_transaction_id(db),
                    "transaction_type": transaction_type,
                    "amount": cheque_amount,
                    "charge": bank_charge,
                    "currency": secondary_account_currency,
                    "sender_account_id": secondary_account["account_id"],
                    "receiver_account_id": primary_account["account_id"],
                    "timestamp": datetime.now(),
                    "status": "failed",
                    "reason": "Insufficient funds"
                }
                db.transactions.insert_one(transaction)
            else:
                if primary_account_currency != secondary_account_currency:
                    cheque_amount_converted = convert_currency(db, f"{secondary_account_currency}/{primary_account_currency}", cheque_amount)
                else:
                    cheque_amount_converted = cheque_amount

                primary_account_balance += cheque_amount_converted
                secondary_account_balance -= (cheque_amount + bank_charge)
                print(f"Depositing {cheque_amount_converted} into account {primary_account['account_id']} from account {secondary_account['account_id']}.")
                print(f"New balance: {primary_account_balance}")

                db.accounts.update_one(
                    {"_id": primary_account['_id']},
                    {"$set": {"current_balance": primary_account_balance}}
                )
                db.accounts.update_one(
                    {"_id": secondary_account['_id']},
                    {"$set": {"current_balance": secondary_account_balance}}
                )

                transaction = {
                    "transaction_id": get_next_transaction_id(db),
                    "transaction_type": transaction_type,
                    "amount": cheque_amount,
                    "charge": bank_charge,
                    "currency": secondary_account_currency,
                    "sender_account_id": secondary_account["account_id"],
                    "receiver_account_id": primary_account["account_id"],
                    "timestamp": datetime.now(),
                    "status": "success"
                }
                db.transactions.insert_one(transaction)
            return
        
        elif transaction_type == "cheque withdrawal":
            print(f"{secondary_account_balance}")
            cheque_amount = round(random.uniform(2500.0, 100000.0), 2)

            if not check_funds_available(db, secondary_account["account_id"], cheque_amount, bank_charge):
                print(f"Insufficient funds in account {secondary_account['account_id']}.")
                transaction = {
                    "transaction_id": get_next_transaction_id(db),
                    "transaction_type": transaction_type,
                    "amount": cheque_amount,
                    "charge": bank_charge,
                    "currency": secondary_account_currency,
                    "sender_account_id": secondary_account["account_id"],
                    "receiver_account_id": "external",
                    "timestamp": datetime.now(),
                    "status": "failed",
                    "reason": "Insufficient funds"
                }
                db.transactions.insert_one(transaction)
            else:
                secondary_account_balance -= (cheque_amount + bank_charge)
                print(f"Withdrawing {cheque_amount} from account {secondary_account['account_id']} via cheque.")
                print(f"New balance: {secondary_account_balance}")

                db.accounts.update_one(
                    {"_id": secondary_account['_id']},
                    {"$set": {"current_balance": secondary_account_balance}}
                )

                transaction = {
                    "transaction_id": get_next_transaction_id(db),
                    "transaction_type": transaction_type,
                    "amount": cheque_amount,
                    "charge": bank_charge,
                    "currency": secondary_account_currency,
                    "sender_account_id": secondary_account["account_id"],
                    "receiver_account_id": "external",
                    "timestamp": datetime.now(),
                    "status": "success"
                }
                db.transactions.insert_one(transaction)
            return

        elif transaction_type == "transfer":
            print(f"{primary_account_balance}")
            transfer_amount = round(random.uniform(10.0, 10000.0), 2)
            transfer_amount_init = transfer_amount

            if not check_funds_available(db, primary_account["account_id"], transfer_amount, bank_charge):
                print(f"Insufficient funds in account {primary_account['account_id']}.")
                transaction = {
                    "transaction_id": get_next_transaction_id(db),
                    "transaction_type": transaction_type,
                    "amount": transfer_amount,
                    "charge": bank_charge,
                    "currency": primary_account_currency,
                    "sender_account_id": primary_account["account_id"],
                    "receiver_account_id": secondary_account["account_id"],
                    "timestamp": datetime.now(),
                    "status": "failed",
                    "reason": "Insufficient funds"
                }
                db.transactions.insert_one(transaction)
            else:
                if primary_account_currency != secondary_account_currency:
                    transfer_amount = convert_currency(db, f"{primary_account_currency}/{secondary_account_currency}", transfer_amount)
                    primary_account_balance -= (transfer_amount_init + bank_charge)
                    print(f"Transferring {transfer_amount_init}{primary_account_currency} from account {primary_account['account_id']} to account {secondary_account['account_id']}.")
                else:
                    transfer_amount = transfer_amount
                    primary_account_balance -= (transfer_amount + bank_charge)
                    print(f"Transferring {transfer_amount}{primary_account_currency} from account {primary_account['account_id']} to account {secondary_account['account_id']}.")

                secondary_account_balance += transfer_amount
                print(f"New balance: {primary_account_balance}")

                db.accounts.update_one(
                    {"_id": primary_account['_id']},
                    {"$set": {"current_balance": primary_account_balance}}
                )
                db.accounts.update_one(
                    {"_id": secondary_account['_id']},
                    {"$set": {"current_balance": secondary_account_balance}}
                )

                transaction = {
                    "transaction_id": get_next_transaction_id(db),
                    "transaction_type": transaction_type,
                    "amount": transfer_amount,
                    "charge": bank_charge,
                    "currency": secondary_account_currency,
                    "sender_account_id": primary_account["account_id"],
                    "receiver_account_id": secondary_account["account_id"],
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