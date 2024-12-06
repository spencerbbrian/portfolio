from src.db_connection import get_db_connection
from config.data_config import TRANSACTION_TYPES, POS_PAYMENTS
import random

def generate_transactions():
    transaction_type = random.choice(TRANSACTION_TYPES)
    deposit_withdrawal_amount = round(random.uniform(100.0, 1000.0), 2)
    primary_account = db.accounts.find_one({"account_category": "Customer"})
    bank_charge = round(random.uniform(0.5, 1.0), 2)
    if transaction_type == "deposit":
        new_balance = primary_account["current_balance"] + deposit_withdrawal_amount - bank_charge
        db.accounts.update_one({"_id": primary_account['_id']},{"$set": {"current_balance": new_balance}})
    elif transaction_type == "withdrawal":
        primary_account_balance = primary_account["current_balance"]
        minimum_balance = primary_account["minimum_balance"]
        total_withdrawal_amount = deposit_withdrawal_amount + bank_charge
        temp_balance = primary_account_balance - total_withdrawal_amount
        if total_withdrawal_amount > primary_account_balance:
            if temp_balance > minimum_balance:
                db.accounts.update_one({"_id": primary_account['_id']},{"$set": {"current_balance": temp_balance}})
            else:
                print(f"Insufficient funds in account {primary_account['account_id']} to withdraw {deposit_withdrawal_amount}. Skipping transaction.")
                return
    elif transaction_type == "purchase" or transaction_type == "POS" or transaction_type == "payment":
        pos = random.choice(list(POS_PAYMENTS))
        amount = round(random.uniform(10.0, 1000.0), 2)
    elif transaction_type == "cheque":
        cheque_amount = round(random.uniform(1001.0, 10000.0), 2)
    elif transaction_type == "charge":
        charge_amount = round(random.uniform(1.5, 2.0), 2)
    elif transaction_type == "transfer":
        transfer_amount = round(random.uniform(1.0, 1250.0), 2)
        


if __name__ == "__main__":
    db = get_db_connection()