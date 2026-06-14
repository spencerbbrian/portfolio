from src.db_connection import get_db_connection
import json

def create_collections(db):
    schemas = {
        'banks': 'schemas/banks_schema.json',
        'accounts': 'schemas/accounts_schema.json',
        'exchange': 'schemas/exchange_schema.json',
        'merchants': 'schemas/merchants_schema.json',
        'transactions': 'schemas/transactions_schema.json'
    }

    for collection, schema_file in schemas.items():
        if collection not in db.list_collection_names():
            db.create_collection(collection)
            print(f"Collection '{collection}' created.")

            with open(schema_file) as f:
                schema = json.load(f)
                db.command("collMod", collection, validator=schema)
                print(f"Schema applied to collection '{collection}'.")
        else:
            print(f"Collection '{collection}' already exists.")

if __name__ == '__main__':
    db = get_db_connection()
    create_collections(db)
    print("All collections created.")