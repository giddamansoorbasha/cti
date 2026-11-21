import hashlib
import html
import re
from datetime import datetime, timezone
import feedparser
import requests
from pymongo import UpdateOne
import llm
from classify import classify
from db import db
from seed_data import SEED

FEEDS = [
    ("BleepingComputer", "https://www.bleepingcomputer.com/feed/"),
    ("Krebs on Security", "https://krebsonsecurity.com/feed/"),
    ("The Hacker News", "https://feeds.feedburner.com/TheHackersNews"),
    ("Microsoft Security Blog", "https://www.microsoft.com/en-us/security/blog/feed/"),
    ("SecurityWeek", "https://feeds.feedburner.com/securityweek"),
    ("Cisco Talos", "https://blog.talosintelligence.com/rss/"),
    ("CISA Advisories", "https://www.cisa.gov/cybersecurity-advisories/all.xml"),
    ("SANS ISC", "https://isc.sans.edu/rssfeed.xml"),
    ("Dark Reading", "https://www.darkreading.com/rss.xml"),
    ("Unit 42", "https://unit42.paloaltonetworks.com/feed/"),
    ("Securelist (Kaspersky)", "https://securelist.com/feed/"),
    ("WeLiveSecurity (ESET)", "https://www.welivesecurity.com/en/rss/feed/"),
    ("Schneier on Security", "https://www.schneier.com/feed/atom/"),
    ("Rapid7 Blog", "https://www.rapid7.com/blog/rss/"),
]

CISA_KEV_URL = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
HEADERS = {"User-Agent": "Mozilla/5.0 (CTI-Platform student project)"}

# Ask each RSS source for up to 100 entries. The actual number depends on
# how many entries that source publishes in its feed.
PER_FEED_LIMIT = 100

def clean(text):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", text or ""))).strip()

def when(e):
    t = e.get("published_parsed") or e.get("updated_parsed")
    return datetime(*t[:6]) if t else datetime.now(timezone.utc).replace(tzinfo=None)

def indexes():
    db.threats.create_index([("published_at", -1)])
    db.threats.create_index("platforms")
    db.threats.create_index("status")
    db.threats.create_index("iocs.value")

def seed():
    indexes()
    ops = []
    for item in SEED:
        doc = dict(item)
        _id = doc.pop("_id")
        ops.append(UpdateOne({"_id": _id}, {"$set": doc}, upsert=True))
    if ops:
        db.threats.bulk_write(ops)

def fetch_cisa_kev(limit=250):
    try:
        r = requests.get(CISA_KEV_URL, headers=HEADERS, timeout=25)
        r.raise_for_status()
        vulns = r.json().get("vulnerabilities", [])
        # Sort newest first
        vulns.sort(key=lambda v: v.get("dateAdded", ""), reverse=True)
        ops = []
        for v in vulns[:limit]:
            cve = v.get("cveID", "").upper()
            if not cve:
                continue
            title = f"{cve}: {v.get('vulnerabilityName', 'Known Exploited Vulnerability')}"
            summary = f"{v.get('vendorProject', '')} {v.get('product', '')} - {v.get('shortDescription', '')}".strip()
            try:
                pub = datetime.strptime(v.get("dateAdded", ""), "%Y-%m-%d")
            except Exception:
                pub = datetime.now(timezone.utc).replace(tzinfo=None)

            meta = classify(title, summary)
            meta["status"] = "Active"
            meta["severity"] = "High"
            if not any(i["value"] == cve for i in meta["iocs"]):
                meta["iocs"].insert(0, {"type": "cve", "value": cve})

            doc = {
                "title": title,
                "url": f"https://nvd.nist.gov/vuln/detail/{cve}",
                "summary": summary[:1500],
                "mitigation": v.get("requiredAction", "Apply vendor patches immediately."),
                "source": "CISA KEV",
                "published_at": pub,
                **meta,
            }
            ops.append(UpdateOne({"_id": f"kev-{cve}"}, {"$set": doc}, upsert=True))
        if ops:
            db.threats.bulk_write(ops)
        return len(ops)
    except Exception as ex:
        return f"failed: {type(ex).__name__}: {ex}"

def fetch_all(per_feed=PER_FEED_LIMIT):
    report = {}
    for name, url in FEEDS:
        try:
            response = requests.get(url, headers=HEADERS, timeout=20)
            response.raise_for_status()
            feed = feedparser.parse(response.content)
            ops = []
            for entry in feed.entries[:per_feed]:
                link = entry.get("link")
                if not link:
                    continue
                title = clean(entry.get("title"))
                summary = clean(entry.get("summary"))[:1500]
                doc = {
                    "title": title,
                    "url": link,
                    "summary": summary,
                    "source": name,
                    "published_at": when(entry),
                    **classify(title, summary),
                }
                ops.append(UpdateOne(
                    {"_id": hashlib.sha1(link.encode()).hexdigest()},
                    {"$set": doc},
                    upsert=True,
                ))
            if ops:
                db.threats.bulk_write(ops)
            report[name] = len(ops)
        except Exception as ex:
            report[name] = f"failed: {type(ex).__name__}: {ex}"
    report["CISA KEV"] = fetch_cisa_kev(limit=250)
    return report

def embed_missing(batch=16):
    todo = list(db.threats.find(
        {"embedding": {"$exists": False}},
        {"title": 1, "summary": 1},
    ))
    for i in range(0, len(todo), batch):
        part = todo[i:i + batch]
        vectors = llm.embed([
            f"{item.get('title', '')}. {item.get('summary', '')[:600]}"
            for item in part
        ])
        db.threats.bulk_write([
            UpdateOne({"_id": item["_id"]}, {"$set": {"embedding": vector}})
            for item, vector in zip(part, vectors)
        ])
    return len(todo)

def refresh():
    report = fetch_all()
    try:
        embedded, error = embed_missing(), None
    except Exception as ex:
        embedded, error = 0, f"embedding failed (is Ollama running?): {ex}"
    return {
        "feeds": report,
        "total": db.threats.count_documents({}),
        "embedded_now": embedded,
        "error": error,
    }
