from pymongo import MongoClient
from config.config import MONGO_URI,DATABASE_NAME

def get_db_connection():
    """Establish connection and then return the databse object"""
    client = MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]
    return db