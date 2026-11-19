
from datetime import datetime

from pymongo import MongoClient

MONGO_URI = "mongodb://127.0.0.1:27015"

client = MongoClient(MONGO_URI)
db = client["sales_analytics"]
orders = db["sales_orders"]

sample_orders = [
    {"customer": "Mansoor", "product": "Laptop", "quantity": 1, "unit_price": 65000, "order_date": "2026-01-05", "status": "Delivered"},
    {"customer": "Rahul", "product": "Mouse", "quantity": 2, "unit_price": 500, "order_date": "2026-01-10", "status": "Delivered"},
    {"customer": "Priya", "product": "Keyboard", "quantity": 1, "unit_price": 1500, "order_date": "2026-01-15", "status": "Pending"},
    {"customer": "Arjun", "product": "Monitor", "quantity": 2, "unit_price": 12000, "order_date": "2026-01-20", "status": "Delivered"},
    {"customer": "Mansoor", "product": "Mouse", "quantity": 3, "unit_price": 500, "order_date": "2026-02-02", "status": "Delivered"},
    {"customer": "Rahul", "product": "Laptop", "quantity": 1, "unit_price": 65000, "order_date": "2026-02-08", "status": "Pending"},
    {"customer": "Priya", "product": "Monitor", "quantity": 1, "unit_price": 12000, "order_date": "2026-02-12", "status": "Delivered"},
    {"customer": "Arjun", "product": "Keyboard", "quantity": 2, "unit_price": 1500, "order_date": "2026-02-18", "status": "Cancelled"},
    {"customer": "Mansoor", "product": "Laptop", "quantity": 1, "unit_price": 65000, "order_date": "2026-03-03", "status": "Delivered"},
    {"customer": "Rahul", "product": "Mouse", "quantity": 4, "unit_price": 500, "order_date": "2026-03-09", "status": "Delivered"},
    {"customer": "Priya", "product": "Keyboard", "quantity": 1, "unit_price": 1500, "order_date": "2026-03-14", "status": "Pending"},
    {"customer": "Arjun", "product": "Monitor", "quantity": 1, "unit_price": 12000, "order_date": "2026-03-21", "status": "Delivered"},
]

# Prepare sample data
for order in sample_orders:
    order["order_date"] = datetime.strptime(
        order["order_date"], "%Y-%m-%d"
    )

# Reset and insert data
orders.delete_many({})
orders.insert_many(sample_orders)

print("\nTotal orders:", orders.count_documents({}))

# 1. Monthly revenue
print("\n--- MONTHLY REVENUE ---")

monthly_pipeline = [
    {
        "$group": {
            "_id": {
                "$dateToString": {
                    "format": "%Y-%m",
                    "date": "$order_date"
                }
            },
            "total_revenue": {
                "$sum": {
                    "$multiply": ["$quantity", "$unit_price"]
                }
            }
        }
    },
    {"$sort": {"_id": 1}}
]

for result in orders.aggregate(monthly_pipeline):
    print(result)

# 2. Top 3 customers by spending
print("\n--- TOP 3 CUSTOMERS ---")

customer_pipeline = [
    {
        "$group": {
            "_id": "$customer",
            "total_spending": {
                "$sum": {
                    "$multiply": ["$quantity", "$unit_price"]
                }
            },
            "products": {"$push": "$product"}
        }
    },
    {"$sort": {"total_spending": -1}},
    {"$limit": 3}
]

for result in orders.aggregate(customer_pipeline):
    print(result)

# 3. Average order value by status
print("\n--- AVERAGE ORDER VALUE BY STATUS ---")

status_pipeline = [
    {
        "$addFields": {
            "order_value": {
                "$multiply": ["$quantity", "$unit_price"]
            }
        }
    },
    {
        "$group": {
            "_id": "$status",
            "average_order_value": {"$avg": "$order_value"},
            "total_orders": {"$sum": 1}
        }
    },
    {"$sort": {"_id": 1}}
]

for result in orders.aggregate(status_pipeline):
    print(result)

client.close()