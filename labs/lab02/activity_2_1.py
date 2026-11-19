from pymongo import MongoClient
from dotenv import load_dotenv
import os
import json

load_dotenv()

atlas_uri = os.getenv("ATLAS_URI", "mongodb://localhost:27015/")
docker_uri = os.getenv("DOCKER_URI", "mongodb://localhost:27015/")

atlas_client = MongoClient(atlas_uri)
docker_client = MongoClient(docker_uri)

atlas_info = atlas_client.server_info()
docker_info = docker_client.server_info()

print("Atlas MongoDB version :", atlas_info["version"])
print("Docker MongoDB version:", docker_info["version"])

print("\nFull Atlas server_info():")
print(atlas_info)

print("\nFull Docker server_info():")
print(docker_info)

os.makedirs(".", exist_ok=True)
with open(r"lab02/server_info.json", "w") as f:
    json.dump({"atlas": atlas_info, "docker": docker_info}, f, default=str, indent=2)

print("\nSaved to server_info.json")