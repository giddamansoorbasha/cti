from pymongo import MongoClient
from pymongo import UpdateOne
import json

client = MongoClient("mongodb://localhost:27015/")
db = client["inventory"]
products = db["products"]

# Step 1: Upsert function - update price if SKU exists, insert with defaults if not
def upsert_price(sku, price):
    result = products.update_one(
        {"sku": sku},
        {
            "$set": {"price": price},
            "$setOnInsert": {"name": f"Product {sku}", "stock": 0, "tags": [], "is_active": True}
        },
        upsert=True
    )
    return result

print("Upsert existing SKU 'A' with new price:")
r1 = upsert_price("A", 27)
print(f"matched={r1.matched_count}, modified={r1.modified_count}, upserted_id={r1.upserted_id}")

print("\nUpsert new SKU 'Z' (doesn't exist yet):")
r2 = upsert_price("Z", 99)
print(f"matched={r2.matched_count}, modified={r2.modified_count}, upserted_id={r2.upserted_id}")

# Step 2: Bulk write - 5 simultaneous updates
bulk_ops = [
    UpdateOne({"sku": "A"}, {"$inc": {"stock": 10}}),
    UpdateOne({"sku": "B"}, {"$inc": {"stock": 10}}),
    UpdateOne({"sku": "C"}, {"$inc": {"stock": 10}}),
    UpdateOne({"sku": "D"}, {"$set": {"is_active": False}}),
    UpdateOne({"sku": "E"}, {"$set": {"is_active": False}}),
]
bulk_result = products.bulk_write(bulk_ops)

print("\nBulk write result:")
print(f"matched_count={bulk_result.matched_count}")
print(f"modified_count={bulk_result.modified_count}")
print(f"upserted_count={bulk_result.upserted_count}")

print("\nUpdated products A-E:")
final_state = list(products.find({"sku": {"$in": ["A", "B", "C", "D", "E"]}}, {"_id": 0}))
for p in final_state:
    print(p)

with open(r"lab04/output4.json", "a") as f:
    json.dump({
        "bulk_summary": {
            "matched": bulk_result.matched_count,
            "modified": bulk_result.modified_count,
            "upserted": bulk_result.upserted_count
        },
        "final_state": final_state
    }, f, indent=2)

print("\nSaved to output.json")