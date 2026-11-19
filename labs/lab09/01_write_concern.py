import csv
import time
from pathlib import Path
from pymongo.write_concern import WriteConcern
from helpers import db

N = 1000
rows = []

for w in (1, "majority", 3):
    for j in (False, True):
        col = db.get_collection("lab9_wc", write_concern=WriteConcern(w=w, j=j))
        col.drop()
        t0 = time.perf_counter()
        for i in range(N):
            col.insert_one({"i": i, "payload": "x" * 100})
        total = time.perf_counter() - t0
        rows.append((str(w), j, round(total, 2), round(total / N * 1000, 2)))

print(f"{'w':<10} {'j':<7} {'total_s':>8} {'avg_ms':>8}")
for w, j, total, avg in rows:
    print(f"{w:<10} {str(j):<7} {total:>8.2f} {avg:>8.2f}")

out = Path(__file__).parent / "results.csv"
with open(out, "w", newline="") as f:
    csv.writer(f).writerows([("w", "j", "total_s", "avg_ms")] + rows)
print(f"saved={out.name}")