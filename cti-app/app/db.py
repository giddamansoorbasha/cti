import os
from urllib.parse import quote_plus
from pymongo import MongoClient

user = quote_plus(os.getenv("MONGO_ROOT_USER", "root"))
pwd = quote_plus(os.getenv("MONGO_ROOT_PASSWORD", ""))
uri = os.getenv("MONGO_URI") or f"mongodb://{user}:{pwd}@127.0.0.1:27017/?authSource=admin"

client = MongoClient(uri, serverSelectionTimeoutMS=5000)
db = client[os.getenv("MONGO_DB", "chatbot")]