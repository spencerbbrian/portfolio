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
        deposit_withdrawal_amount = round(random.uniform(100.0, 1000.0), 2)

        primary_account = random.choice(list(db.accounts.find({"account_category": "Customer"})))
        primary_account_currency = primary_account["currency"]
        primary_minimum_balance = primary_account["minimum_balance"]
        primary_account_balance = primary_account["current_balance"]

        secondary_account = random.choice(list(db.accounts.find({
        "account_category": "Customer", 
        "_id": {"$ne": primary_account["_id"]}
        })))
        secondary_account_currency = secondary_account["currency"]
        secondary_minimum_balance = primary_account["minimum_balance"]
        secondary_account_balance = secondary_account["current_balance"]
    
        bank_charge = round(random.uniform(0.5, 1.0), 2)
    
        if transaction_type == "deposit":
            new_balance = primary_account_balance + deposit_withdrawal_amount
            print(f"Depositing {deposit_withdrawal_amount} into account {primary_account['account_id']}.")
            db.accounts.update_one(
                {"_id": primary_account['_id']},
                {"$set": {"current_balance": new_balance}}
                )
            transaction = {
            "transaction_id": get_next_transaction_id(db),
            "transaction_type": transaction_type,
            "amount": deposit_withdrawal_amount,
            "charge": 0,
            "currency": primary_account["currency"],
            "sender_account_id": "external",
            "receiver_account_id": primary_account["account_id"],
            "timestamp": datetime.combine(fake.date_this_month(), datetime.min.time()),
            "status": "success"
            }
            db.transactions.insert_one(transaction)
            return

        elif transaction_type == "withdrawal":
            total_withdrawal_amount = deposit_withdrawal_amount + bank_charge
            temp_balance = primary_account_balance - total_withdrawal_amount
            if total_withdrawal_amount < primary_account_balance:
                if temp_balance > primary_minimum_balance:
                    print(f"Withdrawing {deposit_withdrawal_amount} from account {primary_account['account_id']}.")
                    db.accounts.update_one({"_id": primary_account['_id']},{"$set": {"current_balance": temp_balance}})

                    transaction = {
                    "transaction_id": get_next_transaction_id(db),
                    "transaction_type": transaction_type,
                    "amount": deposit_withdrawal_amount,
                    "charge": bank_charge,
                    "currency": primary_account["currency"],
                    "sender_account_id": "NA",
                    "receiver_account_id": primary_account["account_id"],
                    "timestamp": datetime.combine(fake.date_this_month(), datetime.min.time()), 
                    "status": "success"
                    }

                    db.transactions.insert_one(transaction)
                    return
                else:
                    print(f"Insufficient funds in account {primary_account['account_id']} to withdraw {deposit_withdrawal_amount}.")
                    return
            else:
                print(f"Insufficient funds in account {primary_account['account_id']} to withdraw {deposit_withdrawal_amount}.")
                return
            
        elif transaction_type == "purchase" or transaction_type == "POS" or transaction_type == "payment":
            category = random.choice(list(POS_PAYMENTS.keys()))
            random_pos_item = random.choice(POS_PAYMENTS[category])

            merchant = random.choice(list(db.merchants.find({"merchant_type": category})))

            amount = round(random.uniform(1.0, 1000.0), 2)
        

            if merchant['currency'] != primary_account_currency:
                final_amount = convert_currency(db,f"{merchant['currency']}/{primary_account_currency}",amount)
            else:
                final_amount = amount

            temp_balance = primary_account["current_balance"] - final_amount - bank_charge

            if temp_balance > primary_minimum_balance:
                print(f"Making a purchase of {amount} {merchant['currency']} for {random_pos_item} at {category} merchant.")
                db.accounts.update_one({"_id": primary_account['_id']},{"$set": {"current_balance": temp_balance}})
                db.accounts.update_one({"_id": merchant['_id']},{"$inc": {"current_balance": amount}})

                transaction = {
                    "transaction_id": get_next_transaction_id(db),
                    "transaction_type": transaction_type,
                    "intitial_amount": amount,
                    "amount": final_amount,
                    "charge": bank_charge,
                    "currency": merchant["currency"],
                    "sender_account_id": primary_account['account_id'],
                    "receiver_account_id": merchant["account_id"],
                    "timestamp": datetime.combine(fake.date_this_month(), datetime.min.time()),
                    "status": "success"
                    }
                db.transactions.insert_one(transaction)
                return
            else:
                print(f"Insufficient funds in account {primary_account['account_id']} to make a purchase of {amount}.")
                return
            
        elif transaction_type == "cheque deposit":
            amount = round(random.uniform(1001.0, 10000.0), 2)
            temp_balance = secondary_account["current_balance"] - amount - bank_charge

            if secondary_account_balance > amount:
                if temp_balance > secondary_minimum_balance:

                    if primary_account['currency'] != secondary_account['currency']:
                        final_amount = convert_currency(db,f"{secondary_account_currency}/{primary_account_currency}",amount)
                    else:
                        final_amount = amount

                    print(f"Depositing a cheque of {amount}{secondary_account_currency} into account {primary_account['account_id']} from account {secondary_account['account_id']}.")
                    primary_account_balance += final_amount
                    secondary_account_balance -= (amount + bank_charge)

                    db.accounts.update_one({"_id": primary_account['_id']},{"$set": {"current_balance": primary_account_balance}})
                    db.accounts.update_one({"_id": secondary_account['_id']},{"$set": {"current_balance": secondary_account_balance}})

                    transaction = {
                        "transaction_id": get_next_transaction_id(db),
                        "transaction_type": transaction_type,
                        "intitial_amount": amount,
                        "amount": final_amount,
                        "charge": bank_charge,
                        "currency": secondary_account_currency,
                        "sender_account_id": secondary_account['account_id'],
                        "receiver_account_id": primary_account["account_id"],
                        "timestamp": datetime.combine(fake.date_this_month(), datetime.min.time()),
                        "status": "success"
                        }
                    db.transactions.insert_one(transaction)
                    return
                else:
                    print(f"Insufficient funds in account {secondary_account['account_id']} to deposit a cheque of {amount}.")
                    return
            
        elif transaction_type == "cheque withdrawal":
            amount = round(random.uniform(1001.0, 10000.0), 2)
            temp_balance = secondary_account_balance - amount - bank_charge

            if secondary_account_balance > amount:
                if temp_balance > secondary_minimum_balance:
                    print(f"Withdrawing a cheque of {amount}{secondary_account_currency} from account {secondary_account['account_id']}.")
                    secondary_account_balance -= (amount + bank_charge)
                    db.accounts.update_one({"_id": secondary_account['_id']},{"$set": {"current_balance": secondary_account_balance}})

                    transaction = {
                        "transaction_id": get_next_transaction_id(db),
                        "transaction_type": transaction_type,
                        "amount": amount,
                        "charge": bank_charge,
                        "currency": secondary_account["currency"],
                        "sender_account_id": secondary_account['account_id'],
                        "receiver_account_id": "external",
                        "timestamp": datetime.combine(fake.date_this_month(), datetime.min.time()),
                        "status": "success"
                        }
                    db.transactions.insert_one(transaction)
                    return

        elif transaction_type == "charge":
            amount = round(random.uniform(1.5, 2.0), 2)
            primary_account_balance -= amount
            print(f"Charging {amount} to account {primary_account['account_id']}.")
            db.accounts.update_one({"_id": primary_account['_id']},{"$set": {"current_balance": primary_account_balance}})

            transaction = {
                    "transaction_id": get_next_transaction_id(db),
                    "transaction_type": transaction_type,
                    "amount": amount,
                    "charge": 0.0,
                    "currency": primary_account["currency"],
                    "sender_account_id": primary_account['account_id'],
                    "receiver_account_id": "NA",
                    "timestamp": datetime.combine(fake.date_this_month(), datetime.min.time()),
                    "status": "success"
                    }
            db.transactions.insert_one(transaction)
            return
        
        elif transaction_type == "transfer":
            amount = round(random.uniform(1.0, 1250.0), 2)

            temp_balance = primary_account_balance - amount - bank_charge
            if temp_balance > primary_minimum_balance:
                if primary_account_currency != secondary_account_currency:
                    final_amount = convert_currency(db,f"{primary_account_currency}/{secondary_account_currency}",amount)
                else:
                    final_amount = amount

                secondary_account_balance += final_amount

                print(f"Transferring {amount}{primary_account_currency} from account {primary_account['account_id']} to account {secondary_account['account_id']}.")
                db.accounts.update_one({"_id": primary_account['_id']},{"$set": {"current_balance": temp_balance}})
                db.accounts.update_one({"_id": secondary_account['_id']},{"$set": {"current_balance": secondary_account_balance}})

                transaction = {
                    "transaction_id": get_next_transaction_id(db),
                    "transaction_type": transaction_type,
                    "intitial_amount": amount,
                    "amount": final_amount,
                    "charge": bank_charge,
                    "currency": primary_account["currency"],
                    "sender_account_id": primary_account['account_id'],
                    "receiver_account_id": secondary_account['account_id'],
                    "timestamp": datetime.combine(fake.date_this_month(), datetime.min.time()),
                    "status": "success"
                    }
                db.transactions.insert_one(transaction)
                return
            else:
                print(f"Insufficient funds in account {primary_account['account_id']} to transfer {amount}.")
                log_failed_transaction(db, transaction_type, amount, bank_charge, primary_account_currency, primary_account['account_id'])
                return               
    except Exception as e:
        print(f"An error occurred: Transaction could not be completed. {e}")
        return
    
def log_failed_transaction(db, transaction_type, amount, charge, currency, account_id):
    transaction = {
        "transaction_id": get_next_transaction_id(db),
        "transaction_type": transaction_type,
        "amount": amount,
        "charge": charge,
        "currency": currency,
        "account_id": account_id,
        "timestamp": datetime.combine(fake.date_this_month(), datetime.min.time()),
        "status": "failed"
    }
    db.transactions.insert_one(transaction)
    
def main():
    db = get_db_connection()
    if db is not None:
        for i in range(1):
            generate_transactions(db)
    else:
        print("Could not connect to the database.")
        

if __name__ == "__main__":
    main()