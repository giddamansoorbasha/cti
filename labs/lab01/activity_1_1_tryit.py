from pymongo import MongoClient
import json

client = MongoClient("mongodb://localhost:27015")
db = client["nosql_exercise"]
collection = db["db_classification_tryit"]

products_tryit = [
    {"product": "ScyllaDB", "family": "Column-Family Store (Wide-Column)",
     "spans_multiple_families": False,
     "reasoning": "Drop-in replacement for Cassandra; same wide-column data model (partition key + clustering columns) and CQL."},

    {"product": "InfluxDB", "family": "Time-Series (closest to Column-Family / Key-Value)",
     "spans_multiple_families": True,
     "reasoning": "Keyed by timestamp + tags, optimized for append-only writes — behaves like both column-family and key-value."},

    {"product": "ArangoDB", "family": "Multi-Model (Document + Graph + Key-Value)",
     "spans_multiple_families": True,
     "reasoning": "Natively supports documents, graphs, and key-value pairs in one engine queryable via AQL — spans multiple families by design."},
]

collection.delete_many({})
collection.insert_many(products_tryit)

for doc in collection.find({}, {"_id": 0}):
    print(doc)

with open(r"lab01/db_classification_tryit.json", "w") as f:
    json.dump(list(collection.find({}, {"_id": 0})), f, indent=2)

print("\nExported to db_classification_tryit.json")