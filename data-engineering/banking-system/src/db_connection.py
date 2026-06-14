import sys
import os

# Append the config folder to the system path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../config')))

from config import MONGO_URI, DATABASE_NAME
from pymongo import MongoClient

def get_db_connection():
    """Establish connection and then return the databse object"""
    client = MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]
    return db