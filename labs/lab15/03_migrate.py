import statistics, sys, time
from datetime import datetime, timezone
from pathlib import Path
from common import db

TENANTS = ["windows", "linux", "macos", "android", "ios"]

for t in TENANTS:
    db[f"tasks_tenant_{t}"].drop()
    list(db.tasks.aggregate([{"$match": {"tenant_id": t}}, {"$out": f"tasks_tenant_{t}"}]))

print("validation:")
for t in TENANTS:
    a = db.tasks.count_documents({"tenant_id": t})
    c = db[f"tasks_tenant_{t}"]
    leak = c.count_documents({"tenant_id": {"$ne": t}})
    print(f"  {t:8} source={a} copy={c.count_documents({})} leak={leak}", "OK" if a == c.count_documents({}) and leak == 0 else "MISMATCH")


def ms(fn, runs=20):
    times = []
    for _ in range(runs):
        t0 = time.perf_counter(); fn(); times.append((time.perf_counter() - t0) * 1000)
    return statistics.median(times)


def new_doc():
    return {"tenant_id": "windows", "owner": "bench", "title": "bench", "status": "open",
            "created_at": datetime.now(timezone.utc)}


def cross_docs():
    return list(db.tasks.aggregate([{"$group": {"_id": {"t": "$tenant_id", "s": "$status"}, "n": {"$sum": 1}}}]))


def cross_cols():
    return [list(db[f"tasks_tenant_{t}"].aggregate([{"$group": {"_id": "$status", "n": {"$sum": 1}}}])) for t in TENANTS]


print(f"\n{'median ms (20 runs)':28}{'one collection':>16}{'per tenant':>14}")
print(f"{'list one tenant':28}{ms(lambda: list(db.tasks.find({'tenant_id': 'windows'}).sort('created_at', -1))):>16.2f}"
      f"{ms(lambda: list(db.tasks_tenant_windows.find().sort('created_at', -1))):>14.2f}")
print(f"{'create one task':28}{ms(lambda: db.tasks.insert_one(new_doc())):>16.2f}"
      f"{ms(lambda: db.tasks_tenant_windows.insert_one(new_doc())):>14.2f}")
print(f"{'cross-tenant analytics':28}{ms(cross_docs):>16.2f}{ms(cross_cols):>14.2f}")
db.tasks.delete_many({"title": "bench"}); db.tasks_tenant_windows.delete_many({"title": "bench"})