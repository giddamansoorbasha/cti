
from pymongo import MongoClient

MONGO_URI = "mongodb://127.0.0.1:27015"

client = MongoClient(MONGO_URI)
db = client["sales_analytics"]

products = db["lookup_products"]
orders = db["lookup_orders"]

# Product sample data
product_data = [
    {"_id": "P101", "name": "Laptop", "base_price": 65000},
    {"_id": "P102", "name": "Mouse", "base_price": 500},
    {"_id": "P103", "name": "Keyboard", "base_price": 1500},
    {"_id": "P104", "name": "Monitor", "base_price": 12000},
    {"_id": "P105", "name": "Headphones", "base_price": 2500},
    {"_id": "P106", "name": "Webcam", "base_price": 3500},
]

# Order sample data
order_data = [
    {"order_id": 1, "product_id": "P101", "quantity": 1},
    {"order_id": 2, "product_id": "P102", "quantity": 2},
    {"order_id": 3, "product_id": "P103", "quantity": 1},
    {"order_id": 4, "product_id": "P104", "quantity": 1},
    {"order_id": 5, "product_id": "P101", "quantity": 2},
    {"order_id": 6, "product_id": "P102", "quantity": 3},
    {"order_id": 7, "product_id": "P103", "quantity": 2},
    {"order_id": 8, "product_id": "P104", "quantity": 1},
    {"order_id": 9, "product_id": "P101", "quantity": 1},
    {"order_id": 10, "product_id": "P102", "quantity": 1},
    {"order_id": 11, "product_id": "P103", "quantity": 3},
    {"order_id": 12, "product_id": "P104", "quantity": 2},
]

# Reset and insert data
products.delete_many({})
orders.delete_many({})

products.insert_many(product_data)
orders.insert_many(order_data)

print("Products:", products.count_documents({}))
print("Orders:", orders.count_documents({}))

# 1. Join orders with products
print("\n--- ORDERS WITH PRODUCT DETAILS ---")

lookup_pipeline = [
    {
        "$lookup": {
            "from": "lookup_products",
            "localField": "product_id",
            "foreignField": "_id",
            "as": "product_details"
        }
    },
    {"$unwind": "$product_details"},
    {
        "$project": {
            "_id": 0,
            "order_id": 1,
            "product_name": "$product_details.name",
            "quantity": 1,
            "unit_price": "$product_details.base_price",
            "total_price": {
                "$multiply": [
                    "$quantity",
                    "$product_details.base_price"
                ]
            }
        }
    }
]

for result in orders.aggregate(lookup_pipeline):
    print(result)

# 2. Find products that were never ordered
print("\n--- PRODUCTS NEVER ORDERED ---")

unused_pipeline = [
    {
        "$lookup": {
            "from": "lookup_orders",
            "localField": "_id",
            "foreignField": "product_id",
            "as": "order_details"
        }
    },
    {
        "$match": {
            "order_details": {"$eq": []}
        }
    },
    {
        "$project": {
            "_id": 1,
            "name": 1,
            "base_price": 1
        }
    }
]

for result in products.aggregate(unused_pipeline):
    print(result)

client.close()