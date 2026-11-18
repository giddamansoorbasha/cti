import re
import numpy as np
from db import db
from classify import PLATFORMS
import llm

FIELDS = {"title": 1, "summary": 1, "url": 1, "source": 1, "type": 1, "severity": 1, "status": 1,
          "platforms": 1, "published_at": 1, "embedding": 1, "iocs": 1, "mitigation": 1}

def retrieve(q, k=5):
    flt = {}
    plats = [p for p, rx in PLATFORMS.items() if re.search(rx, q, re.I)]
    if plats:
        flt["platforms"] = {"$in": plats}
    m = re.search(r"\b(anticipated|active|evolving|resolved)\b", q, re.I)
    if m:
        flt["status"] = m.group(1).capitalize()

    docs = list(db.threats.find(flt, FIELDS)) or list(db.threats.find({}, FIELDS))

    # exact CVE match goes first
    cves = {c.upper() for c in re.findall(r"CVE-\d{4}-\d{4,7}", q, re.I)}
    exact = [d for d in docs if cves & {i["value"] for i in d.get("iocs", [])}]
    if cves and not exact:
        exact = list(db.threats.find({"iocs.value": {"$in": list(cves)}}, FIELDS))

    emb = [d for d in docs if d.get("embedding") and d not in exact]
    try:
        qv = np.array(llm.embed([q])[0])
        M = np.array([d["embedding"] for d in emb]) if emb else None
        if M is not None:
            scores = (M @ qv) / (np.linalg.norm(M, axis=1) * np.linalg.norm(qv) + 1e-9)
            ranked = [emb[i] for i in np.argsort(-scores)]
        else:
            ranked = []
    except Exception:
        words = set(re.findall(r"\w{4,}", q.lower()))
        ranked = sorted(docs, key=lambda d: -len(words & set(re.findall(r"\w{4,}", (d["title"] + d["summary"]).lower()))))
    out = (exact + ranked)[:k]
    for d in out:
        d.pop("embedding", None)
    return out

def context(docs):
    parts = []
    for i, d in enumerate(docs, 1):
        cves = ", ".join(x["value"] for x in d.get("iocs", []) if x["type"] == "cve")
        parts.append(f"[{i}] {d['title']} | status={d.get('status')} | severity={d.get('severity')} | "
                     f"platforms={','.join(d.get('platforms', [])) or 'unknown'} | source={d.get('source')}\n"
                     f"{d['summary'][:700]}\nCVEs: {cves or 'none'}\nMitigation: {d.get('mitigation', 'not listed')}")
    return "\n\n".join(parts)