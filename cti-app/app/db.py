import os
from pymongo import MongoClient

MONGO_URI = os.getenv("MONGO_URI", "mongodb://admin:admin123@127.0.0.1:27017/?authSource=admin")
DB_NAME = os.getenv("MONGO_DB", "cti")

client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
db = client[DB_NAME]