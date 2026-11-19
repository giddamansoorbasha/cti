from datetime import datetime, timedelta
from bson import ObjectId
from pymongo import MongoClient

c = MongoClient("mongodb://localhost:27217", serverSelectionTimeoutMS=5000)
db = c["lab11"]
N = 10_000

c.drop_database("lab11")
c.admin.command("enableSharding", "lab11")
c.admin.command("shardCollection", "lab11.hotspot_data", key={"ts": 1})
c.admin.command("shardCollection", "lab11.even_data", key={"user_id": "hashed"})

start = datetime(2025, 1, 1)
db.hotspot_data.insert_many([{"ts": start + timedelta(seconds=30 * i), "v": i} for i in range(N)])
db.even_data.insert_many([{"user_id": ObjectId(), "v": i} for i in range(N)])


def spread(name):
    return {
        s["shard"]: s["storageStats"]["count"]
        for s in db[name].aggregate([{"$collStats": {"storageStats": {}}}])
    }


def plan(name, flt):
    wp = db[name].find(flt).explain()["queryPlanner"]["winningPlan"]
    return wp["stage"], [x["shardName"] for x in wp.get("shards", [])]


print("[1] Chunk Distribution (10,000 docs each)")
print(f"  hotspot_data (ts: 1)          | {spread('hotspot_data')}")
print(f"  even_data (user_id: hashed)   | {spread('even_data')}")

print("\n[2] Query Targeting")
stage1, shards1 = plan("hotspot_data", {"ts": {"$gte": datetime(2025, 1, 1), "$lt": datetime(2025, 12, 31)}})
stage2, shards2 = plan("even_data", {"user_id": {"$gte": ObjectId("000000000000000000000000")}})
print(f"  range on ts                   | stage={stage1} | shards={shards1}")
print(f"  range on hashed user_id       | stage={stage2} | shards={shards2}")