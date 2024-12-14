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
        print(f"Selected transaction type: {transaction_type}")
        deposit_withdrawal_amount = round(random.uniform(100.0, 1000.0), 2)
        if deposit_withdrawal_amount <= 0:
            print("Invalid transaction amount.")
            return
        primary_account = random.choice(list(db.accounts.find({"account_category": "Customer"})))
        secondary_account = random.choice(list(db.accounts.find({
        "account_category": "Customer", 
        "_id": {"$ne": primary_account["_id"]}
        })))
    

        bank_charge = round(random.uniform(0.5, 1.0), 2)

        minimum_balance = primary_account["minimum_balance"]
        primary_account_balance = primary_account["current_balance"]
        secondary_account_balance = secondary_account["current_balance"]

        primary_account_currency = primary_account["currency"]
        secondary_account_currency = secondary_account["currency"]
    
        if transaction_type == "deposit":
            new_balance = primary_account["current_balance"] + deposit_withdrawal_amount
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
                if temp_balance > minimum_balance:
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
            initial_amount = amount

            if merchant['currency'] != primary_account['currency']:
                amount = convert_currency(db,f"{primary_account_currency}/{merchant['currency']}",amount)

            temp_balance = primary_account["current_balance"] - amount - bank_charge
            if temp_balance > primary_account["minimum_balance"]:
                print(f"Making a purchase of {amount} for {random_pos_item} at a(n) {category} merchant.")
                db.accounts.update_one({"_id": primary_account['_id']},{"$set": {"current_balance": temp_balance}})
                db.accounts.update_one({"_id": merchant['_id']},{"$inc": {"current_balance": amount}})
                transaction = {
                    "transaction_id": get_next_transaction_id(db),
                    "transaction_type": transaction_type,
                    "intitial_amount": initial_amount,
                    "amount": amount,
                    "charge": bank_charge,
                    "currency": primary_account["currency"],
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
            cheque_amount = round(random.uniform(1001.0, 10000.0), 2)
            initial_amount = cheque_amount
            if secondary_account_balance > cheque_amount:

                if primary_account['currency'] != secondary_account['currency']:
                    cheque_amount = convert_currency(db,f"{secondary_account_currency}/{primary_account_currency}",amount)

                print(f"Depositing a cheque of {cheque_amount} into account {primary_account['account_id']} from account {secondary_account['account_id']} .")
                new_balance = primary_account["current_balance"] + cheque_amount
                secondary_account_balance -= (cheque_amount + bank_charge)
                db.accounts.update_one({"_id": primary_account['_id']},{"$set": {"current_balance": new_balance}})
                db.accounts.update_one({"_id": secondary_account['_id']},{"$set": {"current_balance": secondary_account_balance}})
                transaction = {
                    "transaction_id": get_next_transaction_id(db),
                    "transaction_type": transaction_type,
                    "intitial_amount": initial_amount,
                    "amount": cheque_amount,
                    "charge": bank_charge,
                    "currency": primary_account["currency"],
                    "sender_account_id": secondary_account['account_id'],
                    "receiver_account_id": primary_account["account_id"],
                    "timestamp": datetime.combine(fake.date_this_month(), datetime.min.time()),
                    "status": "success"
                    }
                db.transactions.insert_one(transaction)
                return
            else:
                print(f"Insufficient funds in account {secondary_account['account_id']} to deposit a cheque of {cheque_amount}.")
                return
            
        elif transaction_type == "cheque withdrawal":
            cheque_amount = round(random.uniform(1001.0, 10000.0), 2)
            if secondary_account_balance > cheque_amount:
                print(f"Withdrawing a cheque of {cheque_amount} from account {secondary_account['account_id']}.")
                secondary_account_balance -= (cheque_amount + bank_charge)
                db.accounts.update_one({"_id": secondary_account['_id']},{"$set": {"current_balance": secondary_account_balance}})
                transaction = {
                    "transaction_id": get_next_transaction_id(db),
                    "transaction_type": transaction_type,
                    "amount": cheque_amount,
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
            charge_amount = round(random.uniform(1.5, 2.0), 2)
            new_balance = primary_account["current_balance"] - charge_amount
            print(f"Charging {charge_amount} to account {primary_account['account_id']}.")
            db.accounts.update_one({"_id": primary_account['_id']},{"$set": {"current_balance": new_balance}})
            transaction = {
                    "transaction_id": get_next_transaction_id(db),
                    "transaction_type": transaction_type,
                    "amount": charge_amount,
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
            transfer_amount = round(random.uniform(1.0, 1250.0), 2)
            initial_amount = transfer_amount
            temp_balance = primary_account_balance - transfer_amount - bank_charge
            if temp_balance > primary_account["minimum_balance"]:

                if primary_account['currency'] != secondary_account['currency']:
                    transfer_amount = convert_currency(db,f"{primary_account_currency}/{secondary_account_currency}",amount)

                print(f"Transferring {transfer_amount} from account {primary_account['account_id']} to account {secondary_account['account_id']}.")
                db.accounts.update_one({"_id": primary_account['_id']},{"$set": {"current_balance": temp_balance}})
                secondary_account_balance += transfer_amount
                db.accounts.update_one({"_id": secondary_account['_id']},{"$set": {"current_balance": secondary_account_balance}})
                transaction = {
                    "transaction_id": get_next_transaction_id(db),
                    "transaction_type": transaction_type,
                    "intitial_amount": initial_amount,
                    "amount": transfer_amount,
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
                print(f"Insufficient funds in account {primary_account['account_id']} to transfer {transfer_amount}.")
                return               
    except Exception as e:
        print(f"An error occurred: Transaction could not be completed. {e}")
        return
    
def main():
    db = get_db_connection()
    if db is not None:
        for i in range(1):
            generate_transactions(db)
    else:
        print("Could not connect to the database.")
        

if __name__ == "__main__":
    main()