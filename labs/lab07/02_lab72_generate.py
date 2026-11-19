import random
import time
import bson
from bson import ObjectId
from pymongo import ASCENDING
from helpers import db, INUSE, MAX, cache, fetch_readme, parse_reports

N = 100_000
TARGET = 2048
BATCH = 1000
random.seed(7)

CATEGORIES = ["Threat Landscape", "Incident Response", "Vulnerability", "Cloud Security", "Ransomware", "Identity"]
WORDS = ("attack threat actor malware phishing exploit patch breach credential endpoint network cloud "
         "ransomware vulnerability campaign indicator defense detection response intrusion payload "
         "lateral movement supply chain identity access report trend analysis").split()


def filler(n):
    out, length = [], 0
    while length < n:
        w = random.choice(WORDS)
        out.append(w)
        length += len(w) + 1
    return " ".join(out)[:n].ljust(n, "x")


def load_reports():
    try:
        text, _ = fetch_readme()
        items = list(parse_reports(text).items())
        if items:
            return [(v[:60], u[:300]) for u, v in items]
    except Exception:
        pass
    return [(f"Vendor-{i:02d}", f"https://example.com/report-{i}") for i in range(50)]


REPORTS = load_reports()


def make_doc(i):
    vendor, url = REPORTS[i % len(REPORTS)]
    doc = {
        "_id": ObjectId(), "seq": i, "vendor": vendor, "report_url": url,
        "title": f"{vendor} annual security report #{i}",
        "year": random.randint(2018, 2026), "category": random.choice(CATEGORIES),
        "padding": "",
    }
    doc["padding"] = filler(TARGET - len(bson.encode(doc)))
    return doc


if __name__ == "__main__":
    db.reports_test.drop()
    assert len(bson.encode(make_doc(0))) == TARGET

    t0 = time.perf_counter()
    batch = []
    for i in range(N):
        batch.append(make_doc(i))
        if len(batch) == BATCH:
            db.reports_test.insert_many(batch, ordered=False)
            batch = []
    if batch:
        db.reports_test.insert_many(batch, ordered=False)
    db.reports_test.create_index([("seq", ASCENDING)], unique=True)

    s = list(db.reports_test.aggregate([
        {"$project": {"s": {"$bsonSize": "$$ROOT"}}},
        {"$group": {"_id": None, "count": {"$sum": 1}, "total": {"$sum": "$s"},
                    "avg": {"$avg": "$s"}, "min": {"$min": "$s"}, "max": {"$max": "$s"}}}
    ]))[0]
    st = db.command("collStats", "reports_test")
    c = cache()

    print(f"inserted={s['count']:,} | time={time.perf_counter() - t0:.1f}s | avg={s['avg']:.0f}B | total={s['total']:,}B")
    print(f"dataSize={st['size']:,}B | storageSize={st['storageSize']:,}B | indexSize={st['totalIndexSize']:,}B")
    print(f"cache={c[INUSE]:,}/{c[MAX]:,}B ({c[INUSE] / c[MAX] * 100:.1f}%) | working_set={(st['size'] + st['totalIndexSize']) / c[MAX] * 100:.1f}% of cache")