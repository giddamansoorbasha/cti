from pymongo import MongoClient
import json

client = MongoClient("mongodb://localhost:27015")
db = client["nosql_exercise"]
collection = db["db_classification"]

products = [
    {"product": "Amazon S3", "family": "Key-Value Store (Object Store)",
     "reasoning": "Data is stored and retrieved by a unique object key with no internal querying capability.",
     "best_for": "Storing large unstructured objects (images, backups, logs) accessed by key at massive scale.",
     "limitation": "No secondary indexing or complex querying on object content."},

    {"product": "Couchbase", "family": "Document Database",
     "reasoning": "Stores JSON documents and supports secondary indexes and querying on document fields.",
     "best_for": "Content management / catalog systems needing flexible schema and fast reads/writes.",
     "limitation": "Multi-document ACID transactions across shards are more complex than in RDBMS."},

    {"product": "Apache HBase", "family": "Column-Family Store",
     "reasoning": "Organizes data into column families and is optimized for wide rows with millions of columns.",
     "best_for": "Large-scale time-series / sensor data with very high write throughput (e.g., IoT telemetry).",
     "limitation": "No native secondary indexes; ad-hoc queries not part of a fixed row key are inefficient."},

    {"product": "Amazon Neptune", "family": "Graph Database",
     "reasoning": "Designed specifically for storing and querying property graph data using SPARQL and Gremlin.",
     "best_for": "Social networks / recommendation engines needing fast multi-hop relationship traversal.",
     "limitation": "Not efficient for simple key lookups or bulk analytical scans of flat data."},

    {"product": "Memcached", "family": "Key-Value Store",
     "reasoning": "Stores arbitrary byte arrays indexed by string keys with no query capability.",
     "best_for": "Caching frequently accessed data (session data, query results) to reduce DB load.",
     "limitation": "Data is volatile (in-memory only, no persistence) and has no querying beyond exact key lookup."},
]

collection.delete_many({})
collection.insert_many(products)

for doc in collection.find({}, {"_id": 0}):
    print(doc)

with open(r"lab01/db_classification.json", "w") as f:
    json.dump(list(collection.find({}, {"_id": 0})), f, indent=2)

print("\nExported to db_classification.json")