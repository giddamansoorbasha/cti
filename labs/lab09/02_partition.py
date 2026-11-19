import subprocess
import time
from pymongo.write_concern import WriteConcern
from helpers import client

NET = "replica-set_default"


def try_insert(w):
    col = client.cti.get_collection("lab9_partition", write_concern=WriteConcern(w=w, wtimeout=5000))
    t0 = time.time()
    try:
        col.insert_one({"t": t0})
        print(f"  w={w!s:<8} | OK     | {time.time() - t0:.1f}s")
    except Exception as e:
        print(f"  w={w!s:<8} | FAILED | {time.time() - t0:.1f}s | {type(e).__name__}")


def net(action, node):
    cmd = ["docker", "network", action]
    if action == "connect":
        cmd += ["--alias", node]
    cmd += [NET, "cti-" + node]
    subprocess.run(cmd, check=False, capture_output=True)


deadline = time.monotonic() + 10
primary = client.primary
while primary is None and time.monotonic() < deadline:
    client.admin.command("ping")
    time.sleep(0.2)
    primary = client.primary
if primary is None:
    raise RuntimeError("No discoverable primary.")

primary = primary[0]
secs = [n for n in ("mongo1", "mongo2", "mongo3") if n != primary]
members = client.admin.command("replSetGetConfig")["config"]["members"]
voting = sum(m.get("votes", 1) for m in members)
data_nodes = sum(not m.get("arbiterOnly") for m in members)
print(f"primary={primary} | isolating={secs} | voting={voting} | data_nodes={data_nodes} | majority_needed={voting // 2 + 1}")

try:
    print(f"\n[1] Disconnect {secs[0]} (1 secondary left)")
    net("disconnect", secs[0])
    time.sleep(5)
    try_insert(1)
    try_insert("majority")

    print(f"\n[2] Disconnect {secs[1]} (primary isolated)")
    net("disconnect", secs[1])
    time.sleep(3)
    try_insert(1)
    try_insert("majority")

    print("  waiting 15s for primary step-down...")
    time.sleep(15)
    try_insert(1)
finally:
    print("\n[3] Reconnect both with DNS aliases")
    for n in secs:
        net("connect", n)
    time.sleep(15)
    client.admin.command("ping")
    print(f"  primary_now={client.primary}")