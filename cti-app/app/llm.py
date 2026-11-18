import os
import requests

URL = os.getenv("OLLAMA_URL", "http://host.docker.internal:11434")
CHAT = os.getenv("OLLAMA_CHAT_MODEL")
EMB = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")

def embed(texts):
    r = requests.post(f"{URL}/api/embed", json={"model": EMB, "input": texts}, timeout=120)
    r.raise_for_status()
    return r.json()["embeddings"]

def chat(messages):
    r = requests.post(f"{URL}/api/chat", timeout=300, json={
        "model": CHAT, "messages": messages, "stream": False,
        "options": {"temperature": 0.2}})
    r.raise_for_status()
    return r.json()["message"]["content"]