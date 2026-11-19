
import random
import time
from pymongo import MongoClient, ASCENDING, DESCENDING

client = MongoClient("mongodb://127.0.0.1:27015")
db = client["index_lab"]
products = db["products_benchmark"]

categories = ["Electronics", "Clothing", "Books", "Furniture", "Sports"]
tags = ["new", "popular", "sale", "premium", "budget", "trending"]


def generate_products(start, count):
    data = []

    for i in range(start, start + count):
        data.append({
            "name": f"Product {i}",
            "category": random.choice(categories),
            "price": round(random.uniform(10, 5000), 2),
            "rating": round(random.uniform(1, 5), 1),
            "stock": random.randint(0, 1000),
            "tags": random.sample(tags, 3)
        })

    return data


# Start with only the default _id index
products.drop()

# First insertion: No secondary indexes
data1 = generate_products(0, 10000)

start = time.perf_counter()
products.insert_many(data1)
time_without_indexes = time.perf_counter() - start

print("Insertion without indexes:", round(time_without_indexes, 4), "seconds")


# Create five indexes
products.create_index(
    [("category", ASCENDING), ("price", ASCENDING)],
    name="category_price_idx"
)
products.create_index([("price", ASCENDING)], name="price_idx")
products.create_index([("tags", ASCENDING)], name="tags_idx")
products.create_index([("name", ASCENDING)], name="name_idx")
products.create_index([("rating", DESCENDING)], name="rating_idx")

# Second insertion: With five secondary indexes
data2 = generate_products(10000, 10000)

start = time.perf_counter()
products.insert_many(data2)
time_with_indexes = time.perf_counter() - start

print("Insertion with indexes:", round(time_with_indexes, 4), "seconds")


# Calculate insertion slowdown
if time_without_indexes > 0:
    slowdown = (
        (time_with_indexes - time_without_indexes)
        / time_without_indexes
    ) * 100
else:
    slowdown = 0

print("Insertion slowdown:", round(slowdown, 2), "%")


# Drop all but the most critical index
for index in products.list_indexes():
    if index["name"] not in ["_id_", "category_price_idx"]:
        products.drop_index(index["name"])

print("\nRemaining indexes:")

for index in products.list_indexes():
    print(index["name"])


# Run five representative queries
queries = [
    ("Category and Price Sort",
     lambda: products.find({"category": "Electronics"}).sort("price", ASCENDING)),

    ("Price Range",
     lambda: products.find({"price": {"$gte": 500, "$lte": 2000}})),

    ("Find by Tag",
     lambda: products.find({"tags": "popular"})),

    ("Name Search",
     lambda: products.find({"name": {"$regex": "^Product 1"}})),

    ("Rating Search and Sort",
     lambda: products.find({"rating": {"$gte": 4}}).sort("rating", DESCENDING))
]

print("\n--- Query Performance With One Index ---")

for name, query_function in queries:
    result = query_function().explain()

    print("\nQuery:", name)
    print("Winning Plan:", result["queryPlanner"]["winningPlan"])
    print("Documents Examined:", result["executionStats"]["totalDocsExamined"])
    print("Keys Examined:", result["executionStats"]["totalKeysExamined"])

client.close()