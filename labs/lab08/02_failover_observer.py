import argparse
import time
from helpers import client, db

ap = argparse.ArgumentParser()
ap.add_argument("--ticks", type=int, default=5, help="checks to run (0 = infinite)")
args = ap.parse_args()

tick = 0
try:
    while args.ticks == 0 or tick < args.ticks:
        now = time.strftime("%H:%M:%S")
        try:
            n = db.threats.count_documents({})
            print(f"{now} | OK   | threats={n} | primary={client.primary}")
        except Exception as e:
            print(f"{now} | FAIL | {type(e).__name__}")
        tick += 1
        if args.ticks == 0 or tick < args.ticks:
            time.sleep(1)
except KeyboardInterrupt:
    pass