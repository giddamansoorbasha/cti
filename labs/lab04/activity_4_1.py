from pymongo import MongoClient
import json

client = MongoClient("mongodb://localhost:27015/")
db = client["inventory"]
db.drop_collection("products")

# Step 1: Schema validation
db.create_collection("products", validator={
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["name", "price", "stock", "tags"],
        "properties": {
            "name": {"bsonType": "string"},
            "price": {"bsonType": ["int", "double"], "minimum": 0, "exclusiveMinimum": True},
            "stock": {"bsonType": "int", "minimum": 0},
            "tags": {"bsonType": "array", "items": {"bsonType": "string"}}
        }
    }
})

products = db["products"]

# Step 1: Insert 10 products with varying attributes
products.insert_many([
    {"sku": "A", "name": "Wireless Mouse", "price": 25, "stock": 15, "tags": ["electronics", "wireless"]},
    {"sku": "B", "name": "USB Keyboard", "price": 30, "stock": 0, "tags": ["electronics"]},
    {"sku": "C", "name": "Bluetooth Speaker", "price": 45, "stock": 8, "tags": ["electronics", "wireless", "premium"]},
    {"sku": "D", "name": "Cotton T-Shirt", "price": 15, "stock": 40, "tags": ["clothing"]},
    {"sku": "E", "name": "Leather Wallet", "price": 60, "stock": 12, "tags": ["accessories", "premium"]},
    {"sku": "F", "name": "Gaming Chair", "price": 150, "stock": 0, "tags": ["furniture", "premium"]},
    {"sku": "G", "name": "Water Bottle", "price": 10, "stock": 100, "tags": ["accessories"]},
    {"sku": "H", "name": "Wireless Earbuds", "price": 55, "stock": 20, "tags": ["electronics", "wireless"]},
    {"sku": "I", "name": "Office Desk", "price": 200, "stock": 5, "tags": ["furniture"]},
    {"sku": "J", "name": "Notebook Set", "price": 8, "stock": 0, "tags": ["stationery"]},
])
print("10 products inserted.\n")

# Step 2: Comparison operators
print("Products priced between 20 and 50:")
for p in products.find({"price": {"$gte": 20, "$lte": 50}}, {"_id": 0}):
    print(p)

print("\nOut-of-stock products (stock == 0):")
for p in products.find({"stock": 0}, {"_id": 0}):
    print(p)

# Step 3: Logical operators
print("\nOut of stock OR priced above 100:")
for p in products.find({"$or": [{"stock": 0}, {"price": {"$gt": 100}}]}, {"_id": 0}):
    print(p)

print("\nIn stock AND tagged 'premium':")
for p in products.find({"$and": [{"stock": {"$gt": 0}}, {"tags": "premium"}]}, {"_id": 0}):
    print(p)

# Step 4: Array operators
print("\nProducts with BOTH 'electronics' AND 'wireless' tags:")
for p in products.find({"tags": {"$all": ["electronics", "wireless"]}}, {"_id": 0}):
    print(p)

print("\nProducts with exactly 2 tags:")
for p in products.find({"tags": {"$size": 2}}, {"_id": 0}):
    print(p)

# Step 5: Pagination function
def get_page(page_number, items_per_page):
    skip_count = (page_number - 1) * items_per_page
    return list(
        products.find({}, {"_id": 0})
        .sort("name", 1)
        .skip(skip_count)
        .limit(items_per_page)
    )

print("\nPagination - Page 1 (3 per page):")
page1 = get_page(1, 3)
for p in page1:
    print(p)

print("\nPagination - Page 2 (3 per page):")
page2 = get_page(2, 3)
for p in page2:
    print(p)

with open(r"lab04/output2.json", "a") as f:
    json.dump({"page1": page1, "page2": page2}, f, indent=2)

print("\nSaved to output.json")