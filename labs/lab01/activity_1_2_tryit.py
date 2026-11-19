from pymongo import MongoClient
import json

client = MongoClient("mongodb://localhost:27015")
db = client["nosql_exercise"]
collection = db["healthcare_family_mapping"]

healthcare_mapping = [
    {"app": "Hospital Patient Management", "data_domain": "Live patient vitals",
     "family": "Key-Value / Time-Series (e.g., Redis, InfluxDB)",
     "reasoning": "Written every few seconds per patient, read by ID for real-time alerts."},

    {"app": "Hospital Patient Management", "data_domain": "Patient medical records",
     "family": "Document Database (e.g., MongoDB)",
     "reasoning": "Nested, semi-structured (visits, allergies, prescriptions) — flexible schema needed."},

    {"app": "Hospital Patient Management", "data_domain": "Lab test result history",
     "family": "Column-Family Store (e.g., Cassandra)",
     "reasoning": "Append-only, high volume, queried by patient ID + date range."},

    {"app": "Hospital Patient Management", "data_domain": "Doctor-patient referral network",
     "family": "Graph Database (e.g., Neo4j)",
     "reasoning": "Multi-hop traversal for referral paths, specialist networks, fraud detection."},
]

collection.delete_many({})
collection.insert_many(healthcare_mapping)

for doc in collection.find({}, {"_id": 0}):
    print(doc)

with open(r"lab01/healthcare_family_mapping.json", "w") as f:
    json.dump(list(collection.find({}, {"_id": 0})), f, indent=2)

print("\nExported to healthcare_family_mapping.json")