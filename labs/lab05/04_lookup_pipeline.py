
from pymongo import MongoClient

MONGO_URI = "mongodb://127.0.0.1:27015"

client = MongoClient(MONGO_URI)
db = client["sales_analytics"]

products = db["pipeline_products"]
orders = db["pipeline_orders"]

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
    {"order_id": 4, "product_id": "P104", "quantity": 3},
    {"order_id": 5, "product_id": "P101", "quantity": 2},
    {"order_id": 6, "product_id": "P102", "quantity": 4},
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

# Advanced lookup with pipeline
pipeline = [
    {
        "$lookup": {
            "from": "pipeline_orders",
            "let": {
                "product_id": "$_id"
            },
            "pipeline": [
                {
                    "$match": {
                        "$expr": {
                            "$and": [
                                {
                                    "$eq": [
                                        "$product_id",
                                        "$$product_id"
                                    ]
                                },
                                {
                                    "$gte": [
                                        "$quantity",
                                        2
                                    ]
                                }
                            ]
                        }
                    }
                },
                {
                    "$project": {
                        "_id": 0,
                        "order_id": 1,
                        "quantity": 1
                    }
                }
            ],
            "as": "matching_orders"
        }
    },
    {
        "$match": {
            "matching_orders": {"$ne": []}
        }
    },
    {
        "$project": {
            "_id": 1,
            "name": 1,
            "base_price": 1,
            "matching_orders": 1
        }
    }
]

print("\n--- PRODUCTS WITH ORDERS OF QUANTITY 2 OR MORE ---")

for result in products.aggregate(pipeline):
    print(result)

client.close()