
from pymongo import MongoClient

MONGO_URI = "mongodb://127.0.0.1:27015"

client = MongoClient(MONGO_URI)
db = client["sales_analytics"]
orders = db["bucket_orders"]

sample_orders = [
    {"customer": "Mansoor", "product": "Pen", "quantity": 2, "unit_price": 10},
    {"customer": "Rahul", "product": "Notebook", "quantity": 3, "unit_price": 15},
    {"customer": "Priya", "product": "Mouse", "quantity": 1, "unit_price": 500},
    {"customer": "Arjun", "product": "Keyboard", "quantity": 1, "unit_price": 1500},
    {"customer": "Mansoor", "product": "USB Cable", "quantity": 2, "unit_price": 25},
    {"customer": "Rahul", "product": "Headphones", "quantity": 1, "unit_price": 2500},
    {"customer": "Priya", "product": "Monitor", "quantity": 1, "unit_price": 12000},
    {"customer": "Arjun", "product": "Laptop", "quantity": 1, "unit_price": 65000},
    {"customer": "Mansoor", "product": "Notebook", "quantity": 2, "unit_price": 20},
    {"customer": "Rahul", "product": "Mouse", "quantity": 1, "unit_price": 500},
]

orders.delete_many({})
orders.insert_many(sample_orders)

print("Total orders:", orders.count_documents({}))

pipeline = [
    {
        "$addFields": {
            "order_value": {
                "$multiply": ["$quantity", "$unit_price"]
            }
        }
    },
    {
        "$bucket": {
            "groupBy": "$order_value",
            "boundaries": [0, 50, 200.01, 1000000],
            "default": "Other",
            "output": {
                "order_count": {"$sum": 1},
                "total_revenue": {"$sum": "$order_value"},
                "orders": {
                    "$push": {
                        "customer": "$customer",
                        "product": "$product",
                        "order_value": "$order_value"
                    }
                }
            }
        }
    },
    {
        "$addFields": {
            "category": {
                "$switch": {
                    "branches": [
                        {
                            "case": {"$eq": ["$_id", 0]},
                            "then": "Small"
                        },
                        {
                            "case": {"$eq": ["$_id", 50]},
                            "then": "Medium"
                        },
                        {
                            "case": {"$eq": ["$_id", 200.01]},
                            "then": "Large"
                        }
                    ],
                    "default": "Other"
                }
            }
        }
    },
    {"$sort": {"_id": 1}}
]

print("\n--- SALES BUCKET ANALYSIS ---")

for result in orders.aggregate(pipeline):
    print(result)

client.close()