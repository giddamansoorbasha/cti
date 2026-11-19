import time
from helpers import db, LIMIT


def stats(name):
    r = list(db[name].aggregate([
        {"$project": {"s": {"$bsonSize": "$$ROOT"}}},
        {"$group": {"_id": None, "count": {"$sum": 1}, "total": {"$sum": "$s"},
                    "avg": {"$avg": "$s"}, "min": {"$min": "$s"}, "max": {"$max": "$s"}}},
    ]))
    if not r:
        raise RuntimeError(f"Collection '{name}' is empty.")
    return r[0]


def over(name, threshold):
    r = list(db[name].aggregate([
        {"$project": {"s": {"$bsonSize": "$$ROOT"}}},
        {"$match": {"s": {"$gt": threshold}}},
        {"$count": "n"},
    ]))
    return r[0]["n"] if r else 0


def avg_ms(fn, n=200):
    fn()
    t = time.perf_counter()
    for _ in range(n):
        fn()
    return (time.perf_counter() - t) / n * 1000


LOOKUP = [
    {"$lookup": {"from": "sources", "localField": "source_id", "foreignField": "_id", "as": "source"}},
    {"$unwind": "$source"},
]

print("[1] Document Sizes (16 MB limit)")
for name in ["threats", "sources"]:
    s = stats(name)
    pct = s["max"] / LIMIT * 100
    status = "PASS" if s["max"] < LIMIT * 0.5 else "FAIL"
    print(f"  {name:<8} | count={s['count']} | avg={s['avg']:.1f}B | min={s['min']}B | max={s['max']}B ({pct:.4f}%) | >16MB={over(name, LIMIT)} | {status}")

print("\n[2] Referenced vs Embedded (threat -> source)")
db.threats_embedded.drop()
db.threats.aggregate(LOOKUP + [
    {"$project": {"source_id": 0, "source._id": 0, "source.feed_url": 0}},
    {"$out": "threats_embedded"},
])
ref, emb = stats("threats"), stats("threats_embedded")
t_ref = avg_ms(lambda: list(db.threats.aggregate(LOOKUP + [{"$project": {"title": 1, "source.name": 1}}])))
t_emb = avg_ms(lambda: list(db.threats_embedded.find({}, {"title": 1, "source.name": 1})))

top = next(db.threats.aggregate([{"$group": {"_id": "$source_id", "n": {"$sum": 1}}}, {"$sort": {"n": -1}}, {"$limit": 1}]))
src = db.sources.find_one({"_id": top["_id"]})
old = src["name"]
r1 = db.sources.update_one({"_id": src["_id"]}, {"$set": {"name": old + " (renamed)"}})
db.sources.update_one({"_id": src["_id"]}, {"$set": {"name": old}})
r2 = db.threats_embedded.update_many({"source.name": old}, {"$set": {"source.name": old + " (renamed)"}})
db.threats_embedded.update_many({"source.name": old + " (renamed)"}, {"$set": {"source.name": old}})

print(f"  size   : ref={ref['avg']:.1f}B | emb={emb['avg']:.1f}B | diff={emb['avg'] - ref['avg']:+.1f}B")
print(f"  read   : ref={t_ref:.2f}ms | emb={t_emb:.2f}ms | speedup={t_ref / t_emb:.1f}x")
print(f"  update : rename '{old}' -> ref={r1.modified_count} doc | emb={r2.modified_count} docs")

print("\n[3] Unbounded IOC Array Growth Test")
base = db.threats.find_one({}, {"_id": 0})


def size_with(n):
    d = dict(base)
    d["iocs"] = [{"type": "ip", "value": f"10.{(i >> 16) & 255}.{(i >> 8) & 255}.{i & 255}", "first_seen": "2026-10-06"} for i in range(n)]
    db.tmp_growth.drop()
    try:
        db.tmp_growth.insert_one(d)
        return list(db.tmp_growth.aggregate([{"$project": {"s": {"$bsonSize": "$$ROOT"}}}]))[0]["s"]
    except Exception as e:
        return type(e).__name__
    finally:
        db.tmp_growth.drop()


sizes = {}
print(f"  {'IOCs':>10} {'Bytes':>12} {'% of 16MB':>10}")
for n in [0, 10, 100, 1_000, 10_000, 100_000, 300_000]:
    s = sizes[n] = size_with(n)
    if isinstance(s, int):
        print(f"  {n:>10,} {s:>12,} {s / LIMIT * 100:>9.2f}%")
    else:
        print(f"  {n:>10,} {'REJECTED':>12}  ({s})")

per = (sizes[10_000] - sizes[1_000]) / 9_000
mx = next(db.threats.aggregate([{"$project": {"n": {"$size": "$iocs"}}}, {"$sort": {"n": -1}}, {"$limit": 1}]))["n"]
print(f"  bytes/IOC={per:.1f} | max_iocs_before_16MB={(LIMIT - sizes[0]) / per:,.0f} | max_real_iocs={mx}")