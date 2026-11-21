import re
from datetime import datetime
from db import db
import llm, rag, scanner

SYSTEM = ("You are a Cyber Threat Intelligence assistant. Answer ONLY from the threat context given. "
          "If the context does not contain the answer, say so. Give: what it is, affected platforms, status "
          "(Anticipated/Active/Evolving/Resolved), severity, and clear step-by-step mitigation. "
          "Cite sources like [1]. Keep it short and simple. "
          "STRICT RULE: Use plain text ONLY. Do NOT use markdown formatting, bolding, or asterisks (**).")

def save(user, role, content, **extra):
    db.history.insert_one({"user": user, "role": role, "content": content, "ts": datetime.utcnow(), **extra})

def history(user, n=2):
    docs = list(db.history.find({"user": user, "role": {"$in": ["user", "assistant"]}},
                                sort=[("ts", -1)], limit=n))[::-1]
    return [{"role": d["role"], "content": d["content"]} for d in docs]

def done(name, text, sources=None):
    save(name, "assistant", text)
    return {"answer": text, "sources": sources or []}

def handle(u, msg, platform="general"):
    name, role = u["username"], u["role"]
    low = msg.lower().strip()
    last = db.history.find_one({"user": name}, sort=[("ts", -1)])
    pending = last if last and last.get("kind") == "pending" else None
    past = history(name)
    save(name, "user", msg)

    # --- confirm a pending fix (Requires /yes or /confirm)
    if pending and platform == "general" and re.fullmatch(r"/(yes|y|confirm|ok)[.! ]*", low):
        if role != "admin":
            return done(name, "Only an admin can apply fixes.")
        return done(name, scanner.apply(pending["fix_id"]))

    # --- scan (Requires /scan or /audit)
    if platform == "general" and re.fullmatch(r"/(scan|audit)", low):
        if role not in ("analyst", "admin"):
            return done(name, "Scanning needs the analyst or admin role.")
        r = scanner.scan()
        lines = [f"MongoDB {r['version']} scan. Checked: {', '.join(r['checked'])}."]
        if not r["findings"]:
            lines.append("No issues found.")
        for i, f in enumerate(r["findings"], 1):
            lines.append(f"{i}. [{f['severity']}] {f['title']}" + ("  (fixable)" if f["fixable"] else "  (manual)"))
        if any(f["fixable"] for f in r["findings"]):
            lines.append('Type "/fix 1" to fix an item (admin only). I will ask you to confirm.')
        return done(name, "\n".join(lines))

    # --- request a fix (Requires /fix 1)
    m = re.match(r"/fix\s+#?(\d+)", low)
    if m and platform == "general":
        if role != "admin":
            return done(name, "Only an admin can apply fixes.")
        fs = scanner.scan()["findings"]
        i = int(m.group(1)) - 1
        if not 0 <= i < len(fs):
            return done(name, 'No such item. Type "/scan" first.')
        f = fs[i]
        if not f["fixable"]:
            return done(name, f"I cannot fix this automatically. Manual step: {f['manual']}")
        text = f"I will do this: {f['action']}\nType /yes to confirm, or anything else to cancel."
        out = done(name, text)
        save(name, "system", "pending", kind="pending", fix_id=f["id"])
        return out

    # --- normal threat question (RAG vs Exact CVE Lookup)
    cve_match = re.search(r"(cve-\d{4}-\d{4,7})", low)
    
    if cve_match:
        cve_id = cve_match.group(1).upper()
        docs = list(db.threats.find({
            "$or": [
                {"title": {"$regex": cve_id, "$options": "i"}},
                {"iocs.value": {"$regex": cve_id, "$options": "i"}},
                {"summary": {"$regex": cve_id, "$options": "i"}}
            ]
        }).limit(5))
    else:
        search_query = f"{platform} {msg}" if platform != "general" else msg
        docs = rag.retrieve(search_query)
    
    sources = [{"title": d.get("title", "Unknown"), "url": d.get("url", ""), 
                "status": d.get("status"), "severity": d.get("severity")} for d in docs]
                
    if not docs:
        return done(name, f"No threat intelligence found for '{msg}'.")
        
    system_prompt = SYSTEM
    if platform != "general":
        system_prompt += f" EXTREMELY IMPORTANT: Focus your answer exclusively on threats and mitigations related to the {platform.upper()} platform."

    try:
        ans = llm.chat([{"role": "system", "content": system_prompt}, *past,
                        {"role": "user", "content": f"Threat context:\n{rag.context(docs)}\n\nQuestion: {msg}"}])
    except Exception:
        ans = ("The AI model is not reachable. "
               "Here are the matching threats:\n" +
               "\n".join(f"- {d.get('title', 'Unknown')} [{d.get('status')}/{d.get('severity')}]" for d in docs))
               
    return done(name, ans, sources)