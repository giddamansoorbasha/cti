import os
import re
import time
import threading
from collections import defaultdict, deque
from datetime import datetime
from fastapi import Depends, FastAPI, HTTPException, Request, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from pymongo.errors import DuplicateKeyError
import auth, chat, ingest
from db import client, db

WEB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "web")
app = FastAPI(title="CTI Platform")
hits = defaultdict(deque)

def limit(key, n, sec=60):
    now, q = time.time(), hits[key]
    while q and now - q[0] > sec:
        q.popleft()
    if len(q) >= n:
        raise HTTPException(429, "Too many requests. Slow down.")
    q.append(now)

class Cred(BaseModel):
    username: str = Field(max_length=30)
    password: str = Field(max_length=100)

class Msg(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    platform: str = "general"  # <-- Added to accept UI dropdown

class RoleSet(BaseModel):
    username: str
    role: str

def embed_loop():
    for _ in range(60):
        try:
            ingest.embed_missing()
            return
        except Exception:
            time.sleep(10)

@app.on_event("startup")
def startup():
    for _ in range(30):
        try:
            client.admin.command("ping")
            break
        except Exception:
            time.sleep(1)
    db.users.create_index("username", unique=True)
    db.history.create_index([("user", 1), ("ts", -1)])
    if not db.users.find_one({"username": "admin"}):
        db.users.insert_one({"username": "admin", "role": "admin", "created": datetime.utcnow(),
                             "password": auth.hash_pw(os.getenv("ADMIN_PASSWORD", "admin123"))})
    ingest.seed()
    threading.Thread(target=embed_loop, daemon=True).start()

@app.on_event("shutdown")
def shutdown():
    client.close()

# ---------- pages
@app.get("/")
def index():
    return FileResponse(f"{WEB}/dashboard.html")

@app.get("/login")
def login_page():
    return FileResponse(f"{WEB}/login.html")

@app.get("/chat-ui")
def chat_page():
    return FileResponse(f"{WEB}/chat.html")

@app.get("/health")
def health():
    try:
        client.admin.command("ping")
        return {"status": "ok", "threats": db.threats.count_documents({})}
    except Exception:
        raise HTTPException(503, "database down")

# ---------- dashboard statistics
@app.get("/api/dashboard")
def dashboard(u=Depends(auth.need("viewer"))):
    total = db.threats.count_documents({})

    def count_status(status):
        return db.threats.count_documents({
            "status": {"$regex": f"^{re.escape(status)}$", "$options": "i"}
        })

    def count_severity(severity):
        return db.threats.count_documents({
            "severity": {"$regex": f"^{re.escape(severity)}$", "$options": "i"}
        })

    return {
        "total": total,
        "active": count_status("Active"),
        "evolving": count_status("Evolving"),
        "anticipated": count_status("Anticipated"),
        "resolved": count_status("Resolved"),
        "critical": count_severity("Critical"),
        "high": count_severity("High"),
        "searchable": db.threats.count_documents({
            "embedding": {"$exists": True}
        }),
        "sources_monitored": len(ingest.FEEDS),
        "platforms": sorted({
                            p for p in db.threats.distinct("platforms")
                            if isinstance(p, str) and p.strip()
                        }),
        "sources": sorted(db.threats.distinct("source"))
    }

# ---------- threat reports
@app.get("/api/threats")
def get_threats(
    q: str = "",
    type: str = "",
    severity: str = "",
    platform: str = "",
    status: str = "",
    source: str = "",
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    u=Depends(auth.need("viewer"))
):
    filters = {}

    if q.strip():
        term = re.escape(q.strip())
        filters["$or"] = [
            {"title": {"$regex": term, "$options": "i"}},
            {"summary": {"$regex": term, "$options": "i"}},
            {"iocs.value": {"$regex": term, "$options": "i"}}
        ]

    if type:
        filters["type"] = {"$regex": f"^{re.escape(type)}$", "$options": "i"}
    if severity:
        filters["severity"] = {"$regex": f"^{re.escape(severity)}$", "$options": "i"}
    if platform:
        filters["platforms"] = platform
    if status:
        filters["status"] = {"$regex": f"^{re.escape(status)}$", "$options": "i"}
    if source:
        filters["source"] = source

    total = db.threats.count_documents(filters)
    cursor = db.threats.find(
        filters,
        {
            "_id": 0, "title": 1, "summary": 1, "type": 1, "severity": 1,
            "status": 1, "platforms": 1, "source": 1, "url": 1,
            "published_at": 1, "iocs": 1
        }
    ).sort("published_at", -1).skip((page - 1) * limit).limit(limit)

    reports = []
    for doc in cursor:
        published = doc.get("published_at")
        doc["published_at"] = (
            published.isoformat() if hasattr(published, "isoformat")
            else str(published or "")
        )
        reports.append(doc)

    return {
        "reports": reports,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit
    }

# ---------- auth
@app.post("/api/register")
def register(c: Cred, request: Request):
    limit("reg:" + request.client.host, 5)
    if not re.fullmatch(r"[A-Za-z0-9_]{3,20}", c.username) or not 8 <= len(c.password) <= 72:
        raise HTTPException(400, "Username: 3-20 letters/digits/_. Password: 8-72 characters.")
    try:
        db.users.insert_one({"username": c.username, "password": auth.hash_pw(c.password),
                             "role": "viewer", "created": datetime.utcnow()})
    except DuplicateKeyError:
        raise HTTPException(409, "Username already taken")
    return {"ok": True}

@app.post("/api/login")
def login(c: Cred, request: Request):
    limit("login:" + request.client.host, 10)
    u = db.users.find_one({"username": c.username})
    if not u or not auth.check_pw(c.password, u["password"]):
        raise HTTPException(401, "Wrong username or password")
    return {"token": auth.make_token(u), "username": u["username"], "role": u["role"]}

# ---------- chat
@app.post("/api/chat")
def chat_api(m: Msg, u=Depends(auth.need("viewer"))):
    limit("chat:" + u["username"], 20)
    # <-- Updated to pass m.platform down to your chat handler
    return chat.handle(u, m.message, m.platform) 

@app.get("/api/history")
def get_history(u=Depends(auth.need("viewer"))):
    docs = db.history.find({"user": u["username"], "role": {"$in": ["user", "assistant"]}},
                           {"role": 1, "content": 1}, sort=[("ts", -1)], limit=40)
    return [{"role": d["role"], "content": d["content"]} for d in list(docs)[::-1]]

# ---------- admin
@app.get("/api/admin/users")
def users(u=Depends(auth.need("admin"))):
    return list(db.users.find({}, {"_id": 0, "username": 1, "role": 1}))

@app.post("/api/admin/role")
def set_role(r: RoleSet, u=Depends(auth.need("admin"))):
    if r.role not in auth.ROLES:
        raise HTTPException(400, "Role must be viewer, analyst or admin")
    if r.username == u["username"]:
        raise HTTPException(400, "You cannot change your own role")
    if not db.users.update_one({"username": r.username}, {"$set": {"role": r.role}}).matched_count:
        raise HTTPException(404, "User not found")
    return {"ok": True}

@app.post("/api/admin/refresh")
def refresh(u=Depends(auth.need("admin"))):
    return ingest.refresh()