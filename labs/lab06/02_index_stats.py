
from pymongo import MongoClient, ASCENDING, DESCENDING

client = MongoClient("mongodb://127.0.0.1:27015")
db = client["index_lab"]
products = db["products"]

# Ensure Activity 6.1 has been executed
if products.count_documents({}) == 0:
    print("Run index_design.py first to generate products.")
    client.close()
    raise SystemExit(1)

# Ensure indexes exist
products.create_index(
    [("category", ASCENDING), ("price", ASCENDING)],
    name="category_price_idx"
)
products.create_index([("price", ASCENDING)], name="price_idx")
products.create_index([("tags", ASCENDING)], name="tags_idx")
products.create_index([("name", ASCENDING)], name="name_idx")
products.create_index([("rating", DESCENDING)], name="rating_idx")

# Execute queries multiple times
print("Executing queries...")

for i in range(10):
    list(products.find({"category": "Electronics"}).sort("price", ASCENDING).limit(100))
    list(products.find({"price": {"$gte": 500, "$lte": 2000}}).limit(100))
    list(products.find({"tags": "popular"}).limit(100))
    list(products.find({"name": {"$regex": "^Product Alpha 1"}}).limit(100))
    list(products.find({"rating": {"$gte": 4}}).sort("rating", DESCENDING).limit(100))

print("Queries executed successfully.")

# Display index usage statistics
print("\n--- Index Usage Statistics ---")

stats = list(products.aggregate([
    {"$indexStats": {}}
]))

for index in stats:
    print("\nIndex Name:", index["name"])
    print("Access Count:", index["accesses"]["ops"])
    print("Since:", index["accesses"]["since"])

client.close()
