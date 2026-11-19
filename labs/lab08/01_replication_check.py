import time
from pymongo import MongoClient
from helpers import db

NODES = [("mongo1", 27117), ("mongo2", 27118), ("mongo3", 27119)]

r = db.lab8test.insert_one({"msg": "hello from python", "t": time.time()})
print(f"inserted={r.inserted_id}")
time.sleep(1)

for host, port in NODES:
    c = MongoClient(host, port, directConnection=True, serverSelectionTimeoutMS=3000)
    role = "PRIMARY" if c.admin.command("hello")["isWritablePrimary"] else "SECONDARY"
    found = c.cti.lab8test.count_documents({"_id": r.inserted_id}) == 1
    print(f"  {host}:{port} | {role:<9} | replicated={found}")