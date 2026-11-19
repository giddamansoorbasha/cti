import os
import re
import requests
from pymongo import MongoClient

MONGO_URI = os.getenv(
    "MONGO_URI",
    "mongodb://mongo1:27117,mongo2:27118,mongo3:27119/?replicaSet=rs0",
)
client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
db = client["cti"]

LIMIT = 16 * 1024 * 1024
REQ = "pages requested from the cache"
READ = "pages read into cache"
INUSE = "bytes currently in the cache"
MAX = "maximum bytes configured"

GITHUB_API = "https://api.github.com/repos/jacobdjwilson/awesome-annual-security-reports/readme"
GH_HEADERS = {"Accept": "application/vnd.github.raw+json", "User-Agent": "cti-lab07"}
SKIP_HOSTS = ("shields.io", "awesome.re", "linkedin.com", "github.com", "githubusercontent.com")
LINK_RE = re.compile(r"(?<!!)\[([^\]]+)\]\((https?://[^)\s]+)\)")


def cache():
    return db.command("serverStatus")["wiredTiger"]["cache"]


def fetch_readme(etag=None):
    h = dict(GH_HEADERS)
    if etag:
        h["If-None-Match"] = etag
    r = requests.get(GITHUB_API, headers=h, timeout=20)
    if r.status_code == 304:
        return None, etag
    r.raise_for_status()
    return r.content.decode("utf-8", errors="replace"), r.headers.get("ETag")


def parse_reports(text):
    if "<!-- BADGES_END -->" in text:
        text = text.split("<!-- BADGES_END -->", 1)[1]
    found = {}
    for title, url in LINK_RE.findall(text):
        if any(h in url for h in SKIP_HOSTS):
            continue
        found.setdefault(url, title.strip())
    return found