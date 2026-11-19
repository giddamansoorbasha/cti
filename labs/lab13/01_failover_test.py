import argparse
import os
import time
from pymongo import MongoClient

URI = os.getenv(
    "KEYFILE_MONGO_URI",
    "mongodb://admin:admin123@prod1:27317,prod2:27318,prod3:27319/?replicaSet=rs1&authSource=admin",
)
c = MongoClient(URI, serverSelectionTimeoutMS=8000)

ap = argparse.ArgumentParser()
ap.add_argument("--ticks", type=int, default=5, help="writes to run (0 = infinite)")
args = ap.parse_args()

tick = 0
try:
    while args.ticks == 0 or tick < args.ticks:
        now = time.strftime("%H:%M:%S")
        try:
            c.cti.failover_test.insert_one({"t": time.time()})
            print(f"{now} | OK   | write=1 | primary={c.primary}")
        except Exception as e:
            print(f"{now} | FAIL | {type(e).__name__}")
        tick += 1
        if args.ticks == 0 or tick < args.ticks:
            time.sleep(1)
except KeyboardInterrupt:
    pass