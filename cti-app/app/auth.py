import os
import time
import bcrypt
import jwt
from fastapi import Depends, Header, HTTPException
from db import db

SECRET = os.getenv("JWT_SECRET", "change-this-secret")
ROLES = {"viewer": 1, "analyst": 2, "admin": 3}

def hash_pw(p):
    return bcrypt.hashpw(p.encode()[:72], bcrypt.gensalt()).decode()

def check_pw(p, h):
    try:
        return bcrypt.checkpw(p.encode()[:72], h.encode())
    except Exception:
        return False

def make_token(u):
    return jwt.encode({"sub": u["username"], "exp": int(time.time()) + 8 * 3600}, SECRET, algorithm="HS256")

def current_user(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Login required")
    try:
        data = jwt.decode(authorization[7:], SECRET, algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(401, "Invalid or expired token")
    u = db.users.find_one({"username": data["sub"]}, {"password": 0})
    if not u:
        raise HTTPException(401, "User not found")
    return u

def need(role):
    def dep(u=Depends(current_user)):
        if ROLES[u["role"]] < ROLES[role]:
            raise HTTPException(403, f"{role} role required")
        return u
    return dep