import random, sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from common import db
from saas import ensure_indexes, hash_pw

TENANTS = ["windows", "linux", "macos", "android", "ios"]   # tenant = platform

db.tasks.drop(); db.users.drop()
ensure_indexes()
now = datetime.now(timezone.utc)
for t in TENANTS:
    db.users.insert_many([
        {"username": f"admin_{t}", "password": hash_pw("pass123"), "tenant_id": t, "role": "admin"},
        {"username": f"user_{t}", "password": hash_pw("pass123"), "tenant_id": t, "role": "user"}])
    db.tasks.insert_many([{"tenant_id": t, "owner": f"admin_{t}" if i % 5 == 0 else f"user_{t}",
                           "title": f"Mitigate {t} threat #{i}", "status": random.choice(["open", "done"]),
                           "created_at": now - timedelta(minutes=i)} for i in range(100)])
print("tenants:", len(TENANTS), "| tasks:", db.tasks.count_documents({}), "| users:", db.users.count_documents({}))