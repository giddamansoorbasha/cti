import time
from helpers import client

PRIORITY = {"mongo1:27117": 1, "mongo2:27118": 5, "mongo3:27119": 3}

print("[1] Reconfig priorities -> expect mongo2:27118 (priority 5)")
conf = client.admin.command("replSetGetConfig")["config"]
for m in conf["members"]:
    if m["host"] in PRIORITY:
        m["priority"] = PRIORITY[m["host"]]
conf["version"] += 1

try:
    client.admin.command("replSetReconfig", conf)
except Exception as e:
    print(f"  reconfig closed connection: {type(e).__name__}")

time.sleep(15)
client.admin.command("ping")
print(f"  actual_primary={client.primary}")

print("\n[2] StepDown primary (60s) -> expect mongo3:27119 (priority 3)")
try:
    client.admin.command("replSetStepDown", 60)
except Exception as e:
    print(f"  stepDown closed connection: {type(e).__name__}")

time.sleep(15)
client.admin.command("ping")
print(f"  actual_primary={client.primary}")