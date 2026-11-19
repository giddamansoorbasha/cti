import random
from pymongo import MongoClient, ASCENDING

client = MongoClient("mongodb://127.0.0.1:27015")
db = client["index_lab"]
products = db["products_covered"]

# Generate sample products
products.drop()

categories = ["Electronics", "Clothing", "Books", "Furniture"]
data = []

for i in range(10000):
    data.append({
        "name": f"Product {i}",
        "category": random.choice(categories),
        "price": round(random.uniform(100, 5000), 2),
        "stock": random.randint(0, 100)
    })

products.insert_many(data)
print("Inserted:", products.count_documents({}))

# Create a compound index covering the query
products.create_index(
    [
        ("category", ASCENDING),
        ("price", ASCENDING),
        ("name", ASCENDING)
    ],
    name="covered_query_idx"
)
print("Covered query index created.")

# Covered query
query = {"category": "Electronics"}
projection = {
    "_id": 0,
    "category": 1,
    "price": 1,
    "name": 1
}

print("\n--- Covered Query Results ---")
cursor = products.find(query, projection).hint("covered_query_idx")

for result in cursor.limit(10):
    print(result)

# Verify using explain()
print("\n--- Explain Execution Statistics ---")
explanation = products.find(query, projection).hint("covered_query_idx").explain()

print("Winning Plan:")
print(explanation["queryPlanner"]["winningPlan"])

stats = explanation["executionStats"]
print("\nTotal Documents Examined:", stats["totalDocsExamined"])
print("Total Keys Examined:", stats["totalKeysExamined"])

plan = str(explanation["queryPlanner"]["winningPlan"])
if "FETCH" not in plan:
    print("\nCovered Query Verified: FETCH stage eliminated.")
else:
    print("\nFETCH stage found. Query is not fully covered.")

client.close()