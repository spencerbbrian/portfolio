import sys
import os
import json

# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from db_connection import get_db_connection
db = get_db_connection()

file_path = '..\schemas\exchange_rates.json'

with open(file_path, 'r') as file:
    data = json.load(file)

for exchange_rate in data:
    currency_pair = exchange_rate['currency_pair']
    rate = exchange_rate['rate']
    db.exchange.find_one_and_update({"currency_pair": currency_pair}, {"$set": {"exchange_rate": rate}}, upsert=True)
    print(f"Inserted exchange rate for {currency_pair} with rate {rate}")

