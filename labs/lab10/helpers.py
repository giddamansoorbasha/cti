import os
from pymongo import MongoClient

MONGO_URI = os.getenv(
    "MONGO_URI",
    "mongodb://mongo1:27117,mongo2:27118,mongo3:27119/?replicaSet=rs0",
)
client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
db = client["cti"]