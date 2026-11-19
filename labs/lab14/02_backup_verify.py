import argparse
import shutil
import subprocess
import time
from datetime import datetime, timedelta
from pathlib import Path
from common import db

BACKUPS = Path(__file__).parent / "backups"
BACKUPS.mkdir(exist_ok=True)
HOST = "rs0/mongo1:27117,mongo2:27118,mongo3:27119"
COLL = "backup_test"


def run(*cmd):
    subprocess.run(cmd, check=True, capture_output=True)


def backup():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    t0 = time.perf_counter()
    run("docker", "exec", "cti-mongo1", "mongodump", "--host", HOST, "--db", "cti", "--collection", COLL, "--out", f"/tmp/{ts}")
    run("docker", "cp", f"cti-mongo1:/tmp/{ts}", str(BACKUPS / ts))
    return ts, time.perf_counter() - t0


def restore(ts):
    t0 = time.perf_counter()
    run("docker", "cp", str(BACKUPS / ts), f"cti-mongo1:/tmp/restore_{ts}")
    run("docker", "exec", "cti-mongo1", "mongorestore", "--host", HOST, "--drop", "--nsInclude", f"cti.{COLL}", f"/tmp/restore_{ts}")
    return time.perf_counter() - t0


def retention(days=7):
    cutoff = datetime.now() - timedelta(days=days)
    removed = []
    for d in BACKUPS.iterdir():
        if d.is_dir() and datetime.fromtimestamp(d.stat().st_mtime) < cutoff:
            shutil.rmtree(d)
            removed.append(d.name)
    return removed


def verify(n=1000):
    col = db[COLL]
    col.drop()
    col.insert_many([{"i": i, "verified": False} for i in range(n)])
    before = list(col.find().sort("i"))
    ts, _ = backup()
    col.update_many({}, {"$set": {"verified": True}})  # damage the data
    restore(ts)
    after = list(db[COLL].find().sort("i"))
    print("restore verified:", len(after), "docs identical to the backup" if after == before else "MISMATCH!")


def benchmark():
    print(f"{'docs':>8}{'backup s':>10}{'restore s':>11}")
    rows = []
    for n in (1000, 10000, 100000):
        col = db[COLL]
        col.drop()
        for k in range(0, n, 10000):
            col.insert_many([{"i": i, "payload": "x" * 100} for i in range(k, min(k + 10000, n))])
        ts, b = backup()
        r = restore(ts)
        rows.append((n, b, r))
        print(f"{n:>8}{b:>10.1f}{r:>11.1f}")
    db[COLL].drop()
    print("RPO = backup interval (1 hour). RTO = restore time + app restart time.")
    lines = [
        "# Lab 14.2: Backup and Restore Benchmark",
        "",
        "| Documents | Backup (s) | Restore (s) |",
        "|---:|---:|---:|",
        *[f"| {n:,} | {b:.1f} | {r:.1f} |" for n, b, r in rows],
        "",
        "- RPO = backup interval (1 hour): up to 1 hour of recent data can be lost.",
        "- RTO = restore time + app restart time. Restore times above are measured; app restart time was not measured.",
        "- Test data: small documents with a 100-character payload, on one local machine using Docker.",
    ]
    (Path(__file__).parent / "benchmark_results.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


ap = argparse.ArgumentParser()
ap.add_argument("mode", choices=["verify", "benchmark", "hourly", "retention"])
mode = ap.parse_args().mode
if mode == "verify":
    verify()
elif mode == "benchmark":
    benchmark()
elif mode == "retention":
    print("old backups removed:", retention() or "none (nothing older than 7 days)")
else:
    while True:
        print("backup", backup()[0], "| old backups removed:", retention())
        time.sleep(3600)