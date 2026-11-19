from pymongo import MongoClient
from dotenv import load_dotenv
import os
import json

load_dotenv()

client = MongoClient(os.getenv("DOCKER_URI"))
db = client["bookstore"]
books = db["books"]

print("Books BEFORE update:")
for b in books.find():
    print(b)

# Try it yourself: decrease price by 5% for books published in 2015 or later
result = books.update_many(
    {"year": {"$gte": 2015}},
    [{"$set": {"price": {"$multiply": ["$price", 0.95]}}}]
)

print(f"\nMatched: {result.matched_count}, Modified: {result.modified_count}")

print("\nBooks AFTER update:")
all_books = list(books.find({}, {"_id": 0}))
for b in all_books:
    print(b)

with open(r"lab02/output2.json", "w") as f:
    json.dump(all_books, f, indent=2)

print("\nSaved to output.json")