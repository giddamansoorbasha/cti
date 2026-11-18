import secrets
from db import db, client
from auth import check_pw, hash_pw

WEAK = ["admin123", "password", "123456", "12345678", "admin", "qwerty", "letmein", "changeme"]

def scan():
    findings, checked = [], []
    opts = client.admin.command("getCmdLineOpts").get("parsed", {})
    version = client.server_info()["version"]

    # 1. Mongo authentication
    checked.append("MongoDB authentication")
    if opts.get("security", {}).get("authorization") != "enabled":
        findings.append({"id": "mongo_noauth", "severity": "High", "fixable": False,
                         "title": "MongoDB authentication is OFF",
                         "manual": "Restart mongod with --auth and create a root user."})
    # 2. Network exposure
    checked.append("MongoDB bind address")
    bind = str(opts.get("net", {}).get("bindIp", "127.0.0.1"))
    if "0.0.0.0" in bind or "::" in bind:
        findings.append({"id": "mongo_bind", "severity": "High", "fixable": False,
                         "title": f"MongoDB listens on all interfaces ({bind})",
                         "manual": "Restart mongod with --bind_ip 127.0.0.1 (or a private IP) and firewall port 27017."})
    # 3. Weak app passwords
    checked.append("Weak user passwords")
    for u in db.users.find({}, {"username": 1, "password": 1}):
        if any(check_pw(w, u["password"]) for w in WEAK):
            findings.append({"id": f"weak_pwd:{u['username']}", "severity": "High", "fixable": True,
                             "title": f"User '{u['username']}' has a weak or default password",
                             "action": f"Reset the password of '{u['username']}' to a strong random one (shown once)."})
    # 4. Threats without embeddings
    checked.append("Threat embeddings")
    n = db.threats.count_documents({"embedding": {"$exists": False}})
    if n:
        findings.append({"id": "no_embeddings", "severity": "Medium", "fixable": True,
                         "title": f"{n} threat records have no embedding (semantic search weaker)",
                         "action": "Generate the missing embeddings with Ollama."})
    return {"version": version, "checked": checked, "findings": findings}

def apply(fid):
    if fid.startswith("weak_pwd:"):
        name = fid.split(":", 1)[1]
        new = secrets.token_urlsafe(10)
        r = db.users.update_one({"username": name}, {"$set": {"password": hash_pw(new)}})
        if not r.matched_count:
            return f"User '{name}' not found."
        return f"Done. New password for '{name}': {new}\nSave it now. It is shown only once."
    if fid == "no_embeddings":
        import ingest
        try:
            return f"Done. Embedded {ingest.embed_missing()} records."
        except Exception as ex:
            return f"Failed. Is Ollama running? {ex}"
    return "Unknown fix."