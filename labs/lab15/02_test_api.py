import os
import requests

BASE = os.getenv("API_BASE_URL", "http://127.0.0.1:8000/api")


def login(u):
    r = requests.post(f"{BASE}/auth/login", json={"username": u, "password": "pass123"})
    return {"Authorization": "Bearer " + r.json()["access_token"]}


h = login("user_windows")
mine = requests.get(f"{BASE}/tasks", headers=h).json()
print("user_windows sees", len(mine), "tasks (expect 80) | tenants seen:", {t["tenant_id"] for t in mine})
adm = requests.get(f"{BASE}/tasks", headers=login("admin_windows")).json()
print("admin_windows sees", len(adm), "tasks (expect 100)")

tid = requests.post(f"{BASE}/tasks", json={"title": "test"}, headers=h).json()["id"]
print("admin of ANOTHER tenant deletes it:", requests.delete(f"{BASE}/tasks/{tid}", headers=login("admin_linux")).status_code, "(expect 404)")
print("owner deletes it:", requests.delete(f"{BASE}/tasks/{tid}", headers=h).status_code, "(expect 200)")

codes = [requests.get(f"{BASE}/tasks", headers=h).status_code for _ in range(40)]
print("rate limit (30/min): 200s =", codes.count(200), "| 429s =", codes.count(429), "(expect some 429)")