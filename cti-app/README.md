# Cyber Threat Intelligence (CTI) Platform

An LLM-backed Cyber Threat Intelligence web application and automated vulnerability scanner built with **FastAPI**, **MongoDB 8**, and **Ollama**. MongoDB serves as the operational threat database, vector store for RAG retrieval, and persistent conversation memory store.

---

## Features

- **Threat Intelligence Dashboard:** Filter and search threats by platform (`Windows`, `Linux`, `Android`, `macOS`, `iOS`), lifecycle status (`Active`, `Evolving`, `Anticipated`, `Resolved`), severity, type, and IOCs/CVEs.
- **Auto-Seeding & Live Feeds:** Automatically seeds baseline threats on startup and ingests live threat intelligence from 14+ RSS feeds and CISA KEV, generating vector embeddings in the background.
- **RAG Chatbot + Exact CVE Lookup:** Retrieves relevant threats using cosine similarity over MongoDB-stored embeddings (with exact CVE ID lookup and keyword fallback) and answers using a local Ollama LLM.
- **Interactive Security Scanner Bot:** Run `/scan` or `/audit` in chat to detect vulnerabilities, `/fix <n>` to stage a remediation, and `/yes` to apply it with conversational confirmation.
- **Role-Based Access Control (RBAC):** JWT authentication supporting `viewer`, `analyst`, and `admin` roles, plus rate limiting and a `/health` endpoint.

---

## Prerequisites

1. **Docker** installed and running.
2. **Ollama** installed and running on the host machine (`ollama serve`).
3. Pull the required models on the host machine:

```bash
ollama pull hf.co/gmansoor/Llama-3.2-3B-CTI-GGUF:Q4_K_M
ollama pull nomic-embed-text
```

---

## Quick Start (Docker Hub)

Run the single self-contained image (includes MongoDB 8 with auth + FastAPI web app):

```bash
docker run --rm --name cti-app -p 8000:8000 --add-host=host.docker.internal:host-gateway gmansoorbasha/cti-project:latest
```

Open **`http://localhost:8000`** in your browser.

---

## Build & Run Locally

```bash
docker build -t cti-app:latest .
docker run --rm --name cti-app -p 8000:8000 --add-host=host.docker.internal:host-gateway cti-app:latest
```

---

## Default Credentials & Roles

- **Admin Account (auto-created on startup):**
  - **Username:** `admin`
  - **Password:** `admin123`
- **New Users:** Register via `/login` (assigned `viewer` role by default). Admins can promote users via `/api/admin/role`.

| Role | Dashboard & Chat | `/scan` & `/audit` | `/fix` & `/yes` | Refresh Feeds & Manage Roles |
| :--- | :---: | :---: | :---: | :---: |
| **viewer** | Yes | No | No | No |
| **analyst** | Yes | Yes | No | No |
| **admin** | Yes | Yes | Yes | Yes |

---

## Chat Commands

- **Threat Queries:** Ask naturally (e.g., *"Active threats on Windows"*, *"Tell me about CVE-2024-6387"*).
- **`/scan`** or **`/audit`**: Scans for security issues *(analyst/admin)*.
- **`/fix 1`**: Prepares the fix for finding #1 *(admin only)*.
- **`/yes`**: Confirms and applies the pending fix *(admin only)*.

---

## MongoDB Collections (`cti` database)

- `threats`: Threat reports, IOCs, classifications, mitigations, and vector embeddings.
- `users`: Hashed user credentials and RBAC roles.
- `history`: Multi-turn conversation memory and pending scanner fix states.

---

## Environment Variables

| Variable | Default | Description |
| :--- | :--- | :--- |
| `MONGO_URI` | `mongodb://admin:admin123@127.0.0.1:27017/?authSource=admin` | Internal MongoDB connection string |
| `OLLAMA_URL` | `http://host.docker.internal:11434` | Host Ollama API endpoint |
| `OLLAMA_CHAT_MODEL` | `hf.co/gmansoor/Llama-3.2-3B-CTI-GGUF:Q4_K_M` | Chat model name |
| `OLLAMA_EMBEDDING_MODEL` | `nomic-embed-text` | Embedding model name |
| `ADMIN_PASSWORD` | `admin123` | Initial admin password |