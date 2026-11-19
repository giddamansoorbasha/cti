from pymongo import MongoClient
from dotenv import load_dotenv
import os
import json

load_dotenv()

# Fallback to local Docker URI if env vars are missing
atlas_uri = os.getenv("ATLAS_URI", "mongodb://localhost:27015/")
docker_uri = os.getenv("DOCKER_URI", "mongodb://localhost:27015/")

atlas_client = MongoClient(atlas_uri)
docker_client = MongoClient(docker_uri)

atlas_info = atlas_client.server_info()
docker_info = docker_client.server_info()

comparison = {
    "version": (atlas_info.get("version"), docker_info.get("version")),
    "storageEngine": (atlas_info.get("storageEngine", {}).get("name"), docker_info.get("storageEngine", {}).get("name")),
    "gitVersion": (atlas_info.get("gitVersion"), docker_info.get("gitVersion")),
    "javascriptEngine": (atlas_info.get("javascriptEngine"), docker_info.get("javascriptEngine")),
}

print(f"{'Field':<20}{'Atlas':<25}{'Docker':<25}")
print("-" * 70)
for field, (a_val, d_val) in comparison.items():
    print(f"{field:<20}{str(a_val):<25}{str(d_val):<25}")
    if a_val != d_val:
        print(f"    -> Difference found in '{field}'")

# Ensure output directory exists before writing
os.makedirs(".", exist_ok=True)
with open(r"lab02/output1.json", "w") as f:
    json.dump({k: {"atlas": v[0], "docker": v[1]} for k, v in comparison.items()}, f, indent=2)

print("\nSaved to output.json")