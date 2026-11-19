import base64
import hashlib
import hmac
import json
import time
from collections import defaultdict
from datetime import datetime, timezone
from bson import ObjectId
from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel
from common import db

SECRET = b"cti-lab15-secret"
RATE_LIMIT = 30
RATE_WINDOW = 60.0
_hits = defaultdict(list)

app = FastAPI()


def hash_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()


def ensure_indexes():
    db.users.create_index("username", unique=True)
    db.tasks.create_index([("tenant_id", 1), ("created_at", -1)])


def make_token(payload: dict) -> str:
    raw = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()
    sig = hmac.new(SECRET, raw.encode(), hashlib.sha256).hexdigest()
    return f"{raw}.{sig}"


def read_token(token: str) -> dict:
    try:
        raw, sig = token.split(".", 1)
        if not hmac.compare_digest(sig, hmac.new(SECRET, raw.encode(), hashlib.sha256).hexdigest()):
            raise ValueError
        return json.loads(base64.urlsafe_b64decode(raw.encode()).decode())
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")


def current_user(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Bearer token")
    return read_token(authorization.split(" ", 1)[1])


def check_rate(user: dict):
    now = time.time()
    key = user["username"]
    _hits[key] = [t for t in _hits[key] if now - t < RATE_WINDOW]
    if len(_hits[key]) >= RATE_LIMIT:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    _hits[key].append(now)


class LoginReq(BaseModel):
    username: str
    password: str


class TaskReq(BaseModel):
    title: str


@app.post("/api/auth/login")
def login(req: LoginReq):
    u = db.users.find_one({"username": req.username, "password": hash_pw(req.password)})
    if not u:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"access_token": make_token({"username": u["username"], "tenant_id": u["tenant_id"], "role": u["role"]})}


@app.get("/api/tasks")
def list_tasks(user: dict = Depends(current_user)):
    check_rate(user)
    q = {"tenant_id": user["tenant_id"]}
    if user["role"] != "admin":
        q["owner"] = user["username"]
    docs = list(db.tasks.find(q).sort("created_at", -1))
    for d in docs:
        d["id"] = str(d.pop("_id"))
    return docs


@app.post("/api/tasks")
def create_task(req: TaskReq, user: dict = Depends(current_user)):
    doc = {
        "tenant_id": user["tenant_id"],
        "owner": user["username"],
        "title": req.title,
        "status": "open",
        "created_at": datetime.now(timezone.utc),
    }
    res = db.tasks.insert_one(doc)
    return {"id": str(res.inserted_id)}


@app.delete("/api/tasks/{tid}")
def delete_task(tid: str, user: dict = Depends(current_user)):
    q = {"_id": ObjectId(tid), "tenant_id": user["tenant_id"]}
    if user["role"] != "admin":
        q["owner"] = user["username"]
    res = db.tasks.delete_one(q)
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Not found")
    return {"deleted": True}