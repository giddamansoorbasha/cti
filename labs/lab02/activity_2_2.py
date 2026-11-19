from pymongo import MongoClient
from dotenv import load_dotenv
import os
import json

load_dotenv()

client = MongoClient(os.getenv("DOCKER_URI"))
db = client["bookstore"]
books = db["books"]

# Seed sample data only if collection is empty
if books.count_documents({}) == 0:
    books.insert_many([
        {"title": "Book A", "year": 2005, "price": 200},
        {"title": "Book B", "year": 2012, "price": 300},
        {"title": "Book C", "year": 2008, "price": 150},
        {"title": "Book D", "year": 2018, "price": 450},
        {"title": "Book E", "year": 2009, "price": 220},
    ])
    print("Sample books inserted.")

print("\nBooks BEFORE update:")
for b in books.find():
    print(b)

# Update: increase price by 10% for books published before 2010
result = books.update_many(
    {"year": {"$lt": 2010}},
    [{"$set": {"price": {"$multiply": ["$price", 1.10]}}}]
)

print(f"\nMatched: {result.matched_count}, Modified: {result.modified_count}")

print("\nBooks AFTER update:")
all_books = list(books.find({}, {"_id": 0}))
for b in all_books:
    print(b)

with open(r"lab02/books2.json", "w") as f:
    json.dump(all_books, f, indent=2)

print("\nSaved to books.json")