import argparse
import os
import time
from datetime import datetime
from pathlib import Path
import requests
from common import client, REQ, READ

LOG = Path(__file__).parent / "metrics.log"
WEBHOOK = os.getenv("WEBHOOK_URL")  # Slack or Discord webhook (optional)

ap = argparse.ArgumentParser()
ap.add_argument("--interval", type=int, default=30)
ap.add_argument("--cache-min", type=float, default=0.80)
ap.add_argument("--lag-max", type=float, default=10)
ap.add_argument("--once", action="store_true")
a = ap.parse_args()


def snapshot():
    ss = client.admin.command("serverStatus")
    wt = ss["wiredTiger"]["cache"]
    req = wt.get(REQ, 0)
    read = wt.get(READ, 0)
    hit_ratio = (1.0 - read / req) if req > 0 else 1.0

    rs = client.admin.command("replSetGetStatus")
    p_time = next((m["optimeDate"] for m in rs["members"] if m["stateStr"] == "PRIMARY"), None)
    members = []
    for m in rs["members"]:
        lag = max(0.0, (p_time - m["optimeDate"]).total_seconds()) if (p_time and "optimeDate" in m) else 0.0
        members.append({"name": m["name"], "state": m["stateStr"], "lag_s": lag})

    return {
        "connections": ss["connections"]["current"],
        "cache_hit_ratio": hit_ratio,
        "opcounters": ss["opcounters"],
        "members": members,
        "max_lag_s": max((m["lag_s"] for m in members), default=0.0),
    }


def table(s):
    ops = " ".join(f"{k}={v}" for k, v in s["opcounters"].items() if k in ("insert", "query", "update", "delete"))
    lines = [
        f"--- {datetime.now():%Y-%m-%d %H:%M:%S} ---",
        f"{'connections':<22}{s['connections']}",
        f"{'cache hit ratio':<22}{s['cache_hit_ratio']:.2%}",
        f"{'opcounters':<22}{ops}",
    ]
    lines += [f"{m['name']:<22}{m['state']:<11}lag={m['lag_s']:.0f}s" for m in s["members"]]
    return "\n".join(lines)


def alerts(s):
    out = []
    if s["cache_hit_ratio"] < a.cache_min:
        out.append(f"cache hit ratio {s['cache_hit_ratio']:.2%} is below {a.cache_min:.0%}")
    if s["max_lag_s"] > a.lag_max:
        out.append(f"replication lag {s['max_lag_s']:.0f}s is above {a.lag_max:.0f}s")
    return out


while True:
    s = snapshot()
    text = table(s)
    for msg in alerts(s):
        text += f"\nWARNING: {msg}"
        if WEBHOOK:
            try:
                requests.post(WEBHOOK, json={"text": msg, "content": msg}, timeout=5)
            except requests.RequestException as e:
                text += f"\n(webhook failed: {type(e).__name__})"
    print(text)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(text + "\n")
    if a.once:
        break
    time.sleep(a.interval)