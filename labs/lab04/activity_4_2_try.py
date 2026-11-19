from pymongo import MongoClient
from pymongo import UpdateOne
import json

client = MongoClient("mongodb://localhost:27015/")
db = client["inventory"]
products = db["products"]

def bulk_import(import_data):
    ops = [
        UpdateOne(
            {"sku": item["sku"]},
            {"$set": item},
            upsert=True
        )
        for item in import_data
    ]
    return products.bulk_write(ops)

import_batch = [
    {"sku": "K", "name": "Desk Lamp", "price": 20, "stock": 30, "tags": ["furniture"]},
    {"sku": "L", "name": "Phone Stand", "price": 12, "stock": 50, "tags": ["accessories"]},
]

print("First import run:")
r1 = bulk_import(import_batch)
print(f"matched={r1.matched_count}, modified={r1.modified_count}, upserted={r1.upserted_count}")

print("\nSecond import run (same data - should NOT duplicate or modify):")
r2 = bulk_import(import_batch)
print(f"matched={r2.matched_count}, modified={r2.modified_count}, upserted={r2.upserted_count}")

count_k = products.count_documents({"sku": "K"})
count_l = products.count_documents({"sku": "L"})
print(f"\nDocument count for SKU K: {count_k} (should be 1, not 2)")
print(f"Document count for SKU L: {count_l} (should be 1, not 2)")

with open(r"lab04/output3.json", "a") as f:
    json.dump({
        "first_run": {"matched": r1.matched_count, "modified": r1.modified_count, "upserted": r1.upserted_count},
        "second_run": {"matched": r2.matched_count, "modified": r2.modified_count, "upserted": r2.upserted_count},
        "sku_K_count": count_k,
        "sku_L_count": count_l
    }, f, indent=2)

print("\nSaved to output.json")