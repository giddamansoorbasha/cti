import csv
import random
import time
from pathlib import Path
from helpers import db, READ, REQ, INUSE, MAX, cache

N = db.reports_test.estimated_document_count()
assert N == 100_000, f"reports_test has {N} docs; run 02_lab72_generate.py first"
random.seed(1)

OUT = Path(__file__).resolve().parent / "data" / "lab72_random_reads.csv"
OUT.parent.mkdir(parents=True, exist_ok=True)


def key(c, *needles):
    return next((k for k in c if all(n in k.lower() for n in needles)), None)


c = cache()
st = db.command("collStats", "reports_test")
data = st["size"] + st["totalIndexSize"]
mx = c[MAX]
ev_key, dirty_key = key(c, "evicted", "application"), key(c, "dirty", "bytes")

print("[1] WiredTiger Cache")
print(f"  max={mx:,}B | in_use={c[INUSE]:,}B ({c[INUSE] / mx * 100:.1f}%) | data+idx={data:,}B ({data / mx * 100:.1f}%)")
print(f"  dirty={c[dirty_key] if dirty_key else 'n/a'} | evicted={c[ev_key] if ev_key else 'n/a'} | pages_read={c[READ]:,}")

print("\n[2] Range Reads (1,000 docs each)")
print(f"  {'part':<8} {'1st_ms':>8} {'2nd_ms':>8}")
for name, a, b in [("start", 0, 1000), ("middle", 49000, 50000), ("end", 99000, 100000)]:
    times = []
    for _ in range(2):
        t = time.perf_counter()
        list(db.reports_test.find({"seq": {"$gte": a, "$lt": b}}))
        times.append((time.perf_counter() - t) * 1000)
    print(f"  {name:<8} {times[0]:>8.1f} {times[1]:>8.1f}")

ROUNDS, READS = 10, 15_000
print(f"\n[3] Random Reads ({ROUNDS} x {READS:,})")
print(f"  {'rnd':>3} {'reads':>8} {'dist%':>6} {'req':>8} {'miss':>7} {'hit%':>7} {'cacheMB':>8} {'%max':>6} {'ms/rd':>7}")
seen, rows = set(), []
for rnd in range(1, ROUNDS + 1):
    before = cache()
    t = time.perf_counter()
    for _ in range(READS):
        s = random.randrange(N)
        seen.add(s)
        assert db.reports_test.find_one({"seq": s}) is not None
    secs = time.perf_counter() - t
    after = cache()
    req, miss = after[REQ] - before[REQ], after[READ] - before[READ]
    row = {
        "round": rnd, "total_reads": rnd * READS, "distinct_pct": len(seen) / N * 100,
        "requests": req, "misses": miss, "hit_ratio_pct": (1 - miss / req) * 100 if req else 0.0,
        "cache_mb": after[INUSE] / 1048576, "cache_pct_of_max": after[INUSE] / mx * 100,
        "ms_per_read": secs / READS * 1000,
    }
    rows.append(row)
    print(f"  {rnd:>3} {row['total_reads']:>8,} {row['distinct_pct']:>5.1f}% {req:>8,} {miss:>7,} "
          f"{row['hit_ratio_pct']:>6.2f}% {row['cache_mb']:>8.1f} {row['cache_pct_of_max']:>5.1f}% {row['ms_per_read']:>7.3f}")

with open(OUT, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)
print(f"  saved={OUT.name}")