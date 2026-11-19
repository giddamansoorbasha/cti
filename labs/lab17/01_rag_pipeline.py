import os
import time, requests
from pymongo import MongoClient

# FIX: Added &directConnection=true to bypass internal Docker hostnames
client = MongoClient(os.environ["VECTOR_MONGO_URI"])
db = client["cti_lab17"]
col = db["threat_chunks"]

docs = [
    {
        "_id": "lab17-windows-apt",
        "text": "Advanced Persistent Threat (APT) groups use spear-phishing to gain initial access to Windows networks.",
        "platform": "Windows",
        "status": "Active",
    },
    {
        "_id": "lab17-windows-ransomware",
        "text": "Ransomware can disable Windows Defender before encrypting files and demanding payment.",
        "platform": "Windows",
        "status": "Evolving",
    },
    {
        "_id": "lab17-linux-cryptomining",
        "text": "Linux servers are targeted by crypto-mining malware exploiting unpatched vulnerabilities.",
        "platform": "Linux",
        "status": "Active",
    },
    {
        "_id": "lab17-macos-infostealer",
        "text": "MacOS information stealers have been reported in pirated software that bypasses Gatekeeper.",
        "platform": "MacOS",
        "status": "Anticipated",
    },
    {
        "_id": "lab17-android-banking-trojan",
        "text": "Android banking trojans can abuse accessibility services to intercept SMS-based authentication.",
        "platform": "Android",
        "status": "Evolving",
    },
    {
        "_id": "lab17-ios-patched-vulnerability",
        "text": "A previously reported iOS vulnerability has been patched; keep devices on supported updates.",
        "platform": "iOS",
        "status": "Resolved",
    },
]

def get_embedding(text):
    r = requests.post(
        f"{os.getenv('OLLAMA_URL', 'http://localhost:11434')}/api/embed",
        json={"model": "nomic-embed-text", "input": text},
        timeout=120,
    )
    r.raise_for_status()
    embeddings = r.json().get("embeddings")
    if not embeddings or not embeddings[0]:
        raise RuntimeError("Ollama returned no embedding for the text.")
    return embeddings[0]

print("1. Embedding and inserting document chunks...")
for doc in docs:
    col.replace_one({"_id": doc["_id"]}, {**doc, "embedding": get_embedding(doc["text"])}, upsert=True)

print("2. Creating or updating the filtered Atlas Vector Search Index...")
index_definition = {
    "fields": [
        {"type": "vector", "path": "embedding", "numDimensions": 768, "similarity": "cosine"},
        {"type": "filter", "path": "platform"},
        {"type": "filter", "path": "status"},
    ]
}
search_indexes = list(col.aggregate([{"$listSearchIndexes": {}}]))
if any(index.get("name") == "vector_index_lifecycle" for index in search_indexes):
    db.command({
        "updateSearchIndex": "threat_chunks",
        "name": "vector_index_lifecycle",
        "definition": index_definition,
    })
else:
    db.command({
        "createSearchIndexes": "threat_chunks",
        "indexes": [{
            "name": "vector_index_lifecycle",
            "type": "vectorSearch",
            "definition": index_definition,
        }],
    })

print("Waiting 10 seconds for the index to build in the background...")
time.sleep(10)

query = "How do Android and MacOS threats operate?"
print(f"3. Searching for: '{query}'")
results = list(col.aggregate([
    {
        "$vectorSearch": {
            "index": "vector_index_lifecycle",
            "path": "embedding",
            "queryVector": get_embedding(query),
            "numCandidates": 10,
            "limit": 2,
            "filter": {"platform": {"$in": ["Android", "MacOS"]}},
        }
    },
    {"$project": {"text": 1, "platform": 1, "status": 1, "score": {"$meta": "vectorSearchScore"}, "_id": 0}}
]))

context = ""
for r in results:
    print(f" - Match ({r['platform']}, {r['status']}; score {r['score']:.4f}): {r['text']}")
    context += r['text'] + " "

print("\n4. Sending context to LLM (llama3.2:3b)...")
prompt = f"Answer the query strictly based on these documents: {context}\nQuestion: {query}"
llm_resp = requests.post(
    f"{os.getenv('OLLAMA_URL', 'http://localhost:11434')}/api/generate",
    json={"model": "llama3.2:3b", "prompt": prompt, "stream": False},
    timeout=300,
)
llm_resp.raise_for_status()
print("\n[LLM RESPONSE]:\n" + llm_resp.json()["response"])