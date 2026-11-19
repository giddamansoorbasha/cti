import argparse
import csv
import time
from datetime import datetime, timezone
from pathlib import Path
from helpers import db, READ, REQ, INUSE, MAX, cache, fetch_readme, parse_reports

INTERVAL = 10
GITHUB_EVERY = 6
CSV_PATH = Path(__file__).resolve().parent / "data" / "lab72_monitor.csv"
etag = None


def github_check():
    global etag
    try:
        text, etag = fetch_readme(etag)
        if text is None:
            print("[GitHub] unchanged (HTTP 304)")
            return
        reports = parse_reports(text)
        known = {d["_id"] for d in db.annual_reports.find({}, {"_id": 1})}
        new = {u: v for u, v in reports.items() if u not in known}
        print(f"[GitHub] total={len(reports)} | db={len(known)} | new={len(new)}")
        if new:
            db.annual_reports.insert_many(
                [{"_id": u, "vendor": v, "found_at": datetime.now(timezone.utc)} for u, v in new.items()],
                ordered=False,
            )
    except Exception as e:
        print(f"[GitHub] error: {type(e).__name__}: {e}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--ticks", type=int, default=2, help="ticks to run (0 = infinite)")
    ap.add_argument("--forget", type=int, default=0, help="remove N reports to test NEW detection")
    args = ap.parse_args()

    if args.forget:
        ids = [d["_id"] for d in db.annual_reports.aggregate([{"$sample": {"size": args.forget}}])]
        db.annual_reports.delete_many({"_id": {"$in": ids}})
        print(f"removed={len(ids)}")

    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    first = prev = cache()
    mx = first[MAX]
    print(f"interval={INTERVAL}s | cache_max={mx:,}B")
    github_check()

    new_file = not CSV_PATH.exists()
    with open(CSV_PATH, "a", newline="") as f:
        w = csv.writer(f)
        if new_file:
            w.writerow(["time", "requests", "misses", "interval_hit_pct", "total_hit_pct", "cache_bytes", "cache_pct_of_max"])

        print(f"{'time':>8} {'req':>8} {'miss':>7} {'10s_hit%':>9} {'tot_hit%':>9} {'cacheMB':>8} {'%max':>6}")
        tick = 0
        try:
            while args.ticks == 0 or tick < args.ticks:
                time.sleep(INTERVAL)
                tick += 1
                cur = cache()
                req, miss = cur[REQ] - prev[REQ], cur[READ] - prev[READ]
                treq, tmiss = cur[REQ] - first[REQ], cur[READ] - first[READ]
                hit = (1 - miss / req) * 100 if req > 0 else None
                thit = (1 - tmiss / treq) * 100 if treq > 0 else None
                now = datetime.now().strftime("%H:%M:%S")

                h_str = f"{hit:.2f}%" if hit is not None else "n/a"
                t_str = f"{thit:.2f}%" if thit is not None else "n/a"
                print(f"{now:>8} {req:>8,} {miss:>7,} {h_str:>9} {t_str:>9} {cur[INUSE] / 1048576:>8.1f} {cur[INUSE] / mx * 100:>5.1f}%")
                w.writerow([now, req, miss, f"{hit:.2f}" if hit is not None else "",
                            f"{thit:.2f}" if thit is not None else "", cur[INUSE], f"{cur[INUSE] / mx * 100:.1f}"])
                f.flush()
                prev = cur
                if tick % GITHUB_EVERY == 0:
                    github_check()
        except KeyboardInterrupt:
            pass