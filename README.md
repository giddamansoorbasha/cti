# 🛡️ CTI Platform (Cyber Threat Intelligence) & NoSQL Labs

A local, AI-powered Cyber Threat Intelligence (CTI) platform paired with 18 hands-on NoSQL database labs covering MongoDB, Apache Cassandra, Neo4j, and local RAG/vector search. Everything runs locally via Docker and Ollama to keep your data 100% private.

- **GitHub Repository:** [github.com/giddamansoorbasha/cti](https://github.com/giddamansoorbasha/cti)
- **Docker Hub Image:** [hub.docker.com/r/gmansoorbasha/cti-app](https://hub.docker.com/repository/docker/gmansoorbasha/cti-app)

---

## 📂 Repository Structure

- **CTI Platform (`cti-app/`)**: Self-contained Docker image bundling **MongoDB 8** (with authentication enabled) and a **FastAPI** web app (`login.html`, `dashboard.html`, `chat.html`) connected to host **Ollama** for local RAG chat and security auditing.
- **NoSQL Labs (`labs/`)**: 18 documented labs (`lab01`–`lab18`) covering CRUD, schema design, aggregation, indexing, replica sets, sharding, RBAC/TLS, transactions, polyglot persistence, HNSW vector search, and cross-database benchmarks. See **[labs/README.md](labs/README.md)** for full instructions and per-lab guides.

---

## 🌟 CTI Platform Features

- **Threat Intelligence Dashboard (`/`):** Real-time statistics and paginated search/filtering by keyword, CVE/IOC, threat type, severity (`Critical`, `High`, `Medium`, `Low`), platform (`Windows`, `Linux`, `macOS`, `Android`, `iOS`), lifecycle status (`Active`, `Evolving`, `Anticipated`, `Resolved`), and source.
- **Automated Seeding & Live Feeds:** Automatically seeds baseline threats on startup and pulls live advisories in the background from **14 security RSS feeds** (BleepingComputer, Krebs on Security, The Hacker News, Microsoft Security, CISA, Cisco Talos, Unit 42, etc.) plus **CISA KEV**, extracting IOCs (CVEs, IPs) and generating embeddings automatically.
- **AI Chatbot (`/chat-ui`):** Ask natural-language questions about cyber threats, malware, and mitigations with platform-focused context filtering and persistent multi-turn conversation memory.
- **Exact CVE Search:** Query any CVE ID (e.g., `CVE-2024-6387`) for deterministic regex lookup directly against MongoDB before invoking the LLM.
- **MongoDB Security Scanner Bot:** Built-in `/scan` (or `/audit`), `/fix <n>`, and `/yes` chat commands to detect and remediate security misconfigurations with conversational confirmation.
- **Role-Based Access Control (RBAC) & Hardening:** JWT authentication for `viewer`, `analyst`, and `admin` roles, per-endpoint rate limiting, and a `/health` monitoring endpoint.

---

## 🏗️ Architecture & Data Flow

1. **Startup & Seeding:** On container boot, `docker/start.sh` starts MongoDB 8, initializes root authentication, and launches FastAPI. On startup, FastAPI creates the default `admin` account, seeds baseline threats, and spawns a background thread to ingest live RSS/CISA KEV feeds.
2. **Vectorization:** Cleaned threat titles and summaries are embedded locally via host **Ollama** (`nomic-embed-text`) and stored alongside metadata in MongoDB.
3. **MongoDB Collections (`cti` database):**
   - `threats` — Threat reports, IOCs, classifications, mitigations, and vector embeddings.
   - `users` — Hashed user credentials and RBAC roles.
   - `history` — Persistent multi-turn chat memory and pending scanner remediation states.
4. **Hybrid Chat Routing:**
   - **Slash commands (`/scan`, `/audit`, `/fix`, `/yes`):** Routed to `scanner.py` with role checks.
   - **Exact CVE match:** Direct regex lookup against `db.threats`.
   - **General query:** Platform/status-filtered cosine similarity retrieval over MongoDB embeddings (with keyword fallback).
5. **Grounded AI Generation:** Retrieved threat context and recent history are sent to local **Llama 3.2 (3B)** via Ollama (`http://host.docker.internal:11434`) to produce concise, source-cited answers.

---

## 💻 Tech Stack

- **Frontend:** HTML5, CSS3, Vanilla JavaScript
- **Backend:** Python 3.11, FastAPI, Uvicorn, PyMongo, NumPy, Feedparser
- **Databases:** MongoDB 8 (Standalone, Replica Set, Sharded, Atlas Local), Apache Cassandra, Neo4j
- **AI Models (Ollama):** `hf.co/gmansoor/Llama-3.2-3B-CTI-GGUF:Q4_K_M`, `nomic-embed-text`
- **Infrastructure:** Docker & Docker Compose

---

## 🚀 Getting Started (CTI App)

### 1. Prerequisites
- **Docker** (Docker Desktop or Docker Engine)
- **Ollama** installed and running on the host machine ([ollama.com](https://ollama.com))

### 2. Pull the AI Models on the Host

```powershell
ollama pull hf.co/gmansoor/Llama-3.2-3B-CTI-GGUF:Q4_K_M
ollama pull nomic-embed-text
```

*(Linux users: start Ollama with `OLLAMA_HOST=0.0.0.0 ollama serve` so Docker containers can reach it.)*

### 3. Quick Start (Pre-Built Docker Hub Image)

```powershell
docker run --rm --name cti-app -p 8000:8000 --add-host=host.docker.internal:host-gateway gmansoorbasha/cti-app:latest
```

### 4. Or Build & Run Locally

```powershell
cd cti-app
docker build -t cti-app:latest .
docker run --rm --name cti-app -p 8000:8000 --add-host=host.docker.internal:host-gateway cti-app:latest
```

Wait ~10–20 seconds for MongoDB to initialize and seed data, then open **http://localhost:8000** (or verify readiness at **http://localhost:8000/health**).

---

## 🎮 Using the Platform

### Default Login & Roles
- **Username:** `admin`
- **Password:** `admin123`
*(New users can register via "Create viewer account" on `/login`; Admins can promote roles via `/api/admin/role`.)*

| Role | Dashboard & Chat | `/scan` & `/audit` | `/fix` & `/yes` | Refresh Feeds & Manage Roles |
| :--- | :---: | :---: | :---: | :---: |
| **viewer** | Yes | No | No | No |
| **analyst** | Yes | Yes | No | No |
| **admin** | Yes | Yes | Yes | Yes |

### Example Prompts
1. *"Active threats on Windows"* (select **Windows** in the dropdown)
2. *"Tell me about CVE-2024-6387"*
3. *"Resolved Linux threats"*

### Security Scanner Slash Commands (set dropdown to **General**)
- `/scan` or `/audit` — Audits MongoDB for security issues *(analyst / admin)*.
- `/fix 1` — Prepares an automatic remediation for finding #1 *(admin only)*.
- `/yes` — Confirms and applies the pending fix *(admin only)*.

---

## ⚙️ Environment Variables

| Variable | Default | Description |
| :--- | :--- | :--- |
| `MONGO_URI` | `mongodb://admin:admin123@127.0.0.1:27017/?authSource=admin` | Internal authenticated MongoDB URI |
| `MONGO_DB` | `cti` | MongoDB database name |
| `OLLAMA_URL` | `http://host.docker.internal:11434` | Host Ollama API endpoint |
| `OLLAMA_CHAT_MODEL` | `hf.co/gmansoor/Llama-3.2-3B-CTI-GGUF:Q4_K_M` | Local SLM for grounded chat |
| `OLLAMA_EMBEDDING_MODEL` | `nomic-embed-text` | Local embedding model |
| `ADMIN_PASSWORD` | `admin123` | Initial admin account password |

---

## 🧪 Running the 18 NoSQL Labs

All 18 labs (`labs/lab01` through `labs/lab18`) include runnable scripts, saved outputs, and individual READMEs.

- **Labs 01–06:** Standalone MongoDB (`cti-labs1-6` on port `27015`) — NoSQL classification, CRUD, schema validation, aggregation, indexing.
- **Labs 07–14:** Replica sets, failover, write concerns, network partitions, ACID transactions, sharding, RBAC/TLS, keyFile auth, monitoring, backups.
- **Labs 15–18:** Multi-tenant API, polyglot persistence (MongoDB + Cassandra + Neo4j), local RAG + HNSW vector search, and cross-database benchmarking.

Full setup and execution instructions: **[labs/README.md](labs/README.md)**.