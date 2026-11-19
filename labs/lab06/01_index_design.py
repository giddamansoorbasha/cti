
import random
from pymongo import MongoClient, ASCENDING, DESCENDING

client = MongoClient("mongodb://127.0.0.1:27015")
db = client["index_lab"]
products = db["products"]

categories = ["Electronics", "Clothing", "Books", "Furniture", "Sports"]
tag_options = ["new", "popular", "sale", "premium", "budget", "trending"]

# Generate 50,000 products
products.drop()

data = []

for i in range(50000):
    data.append({
        "name": f"Product Alpha {i}",
        "category": random.choice(categories),
        "price": round(random.uniform(10, 5000), 2),
        "rating": round(random.uniform(1, 5), 1),
        "stock": random.randint(0, 1000),
        "tags": random.sample(tag_options, 3)
    })

for i in range(0, len(data), 5000):
    products.insert_many(data[i:i + 5000])

print("Inserted:", products.count_documents({}))


# Five representative queries
queries = [
    ("Category and Price Sort",
     lambda: products.find({"category": "Electronics"}).sort("price", ASCENDING)),

    ("Price Range",
     lambda: products.find({"price": {"$gte": 500, "$lte": 2000}})),

    ("Find by Tag",
     lambda: products.find({"tags": "popular"})),

    ("Name Search",
     lambda: products.find({"name": {"$regex": "^Product Alpha 1"}})),

    ("Rating Search and Sort",
     lambda: products.find({"rating": {"$gte": 4}}).sort("rating", DESCENDING))
]


def explain_queries(title):
    print("\n", "=" * 60)
    print(title)
    print("=" * 60)

    for name, query_function in queries:
        result = query_function().explain()
        stats = result["executionStats"]

        print("\nQuery:", name)
        print("Winning Plan:", result["queryPlanner"]["winningPlan"])
        print("Documents Examined:", stats["totalDocsExamined"])
        print("Keys Examined:", stats["totalKeysExamined"])


# Before indexes
explain_queries("BEFORE INDEXING")


# Create five indexes
products.create_index([
    ("category", ASCENDING),
    ("price", ASCENDING)
], name="category_price_idx")

products.create_index([("price", ASCENDING)], name="price_idx")
products.create_index([("tags", ASCENDING)], name="tags_idx")
products.create_index([("name", ASCENDING)], name="name_idx")
products.create_index([("rating", DESCENDING)], name="rating_idx")

print("\nFive indexes created successfully.")


# After indexes
explain_queries("AFTER INDEXING")

print("\n--- Index List ---")

for index in products.list_indexes():
    print(index)

client.close()