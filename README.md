# 🛡️ CTI Platform (Cyber Threat Intelligence) & NoSQL Labs

A local, AI-powered Cyber Threat Intelligence (CTI) assistant paired with 18 hands-on NoSQL database labs covering MongoDB, Apache Cassandra, Neo4j, and local RAG/vector search. Everything runs locally via Docker and Ollama to keep your data 100% private.

---

## 📂 Repository Structure

- **CTI Platform (`cti-app`)**: FastAPI backend, vanilla HTML/CSS/JS frontend, local MongoDB storage, and Ollama-powered RAG chatbot + security scanner.
- **NoSQL Labs (`labs/`)**: 18 documented labs (`lab01`–`lab18`) covering CRUD, schema design, aggregation, indexing, replica sets, sharding, RBAC/TLS, transactions, polyglot persistence, HNSW vector search, and cross-database benchmarks. See **[labs/README.md](labs/README.md)** for full instructions and per-lab guides.

---

## 🌟 CTI Platform Features

- **AI Chatbot:** Ask natural-language questions about cyber threats, malware, and zero-days.
- **Platform Filtering:** Filter answers specifically for Windows, Linux, MacOS, Android, or iOS from the UI dropdown.
- **Exact CVE Search:** Query a CVE ID (e.g., `CVE-2024-6387`) for direct database lookup, bypassing AI guesswork.
- **Automated Feed Updates:** Fetches the latest cybersecurity advisories via RSS feeds and extracts IOCs (IPs, CVEs).
- **MongoDB Security Scanner:** Built-in `/scan` and `/fix` commands to detect weak credentials or exposed settings.
- **Role-Based Access Control (RBAC):** Separate permissions for Viewers (chat), Analysts (chat + scan), and Admins (full access).

---

## 🏗️ Architecture & Data Flow

1. **Data Ingestion:** The backend pulls security advisories (e.g., CISA, BleepingComputer) via RSS, cleans the text, and extracts Indicators of Compromise (IOCs).
2. **Vectorization:** Cleaned text is embedded locally via **Ollama** (`nomic-embed-text`).
3. **Storage:** Threat reports, extracted IOCs, and vector embeddings are stored in local **MongoDB** inside Docker.
4. **Chat Routing:**
   - **Exact CVE match:** Uses regex lookup directly against MongoDB.
   - **General query:** Runs semantic vector search with optional platform filtering.
5. **AI Generation:** Retrieved context is passed to local **Llama 3.2 (3B)** via Ollama to generate a grounded response.

---

## 💻 Tech Stack

- **Frontend:** HTML, CSS, JavaScript (Vanilla)
- **Backend:** Python, FastAPI
- **Databases:** MongoDB (Standalone, Replica Set, Sharded, Atlas Local), Apache Cassandra, Neo4j
- **AI Models (Ollama):** `hf.co/gmansoor/Llama-3.2-3B-CTI-GGUF:Q4_K_M`, `nomic-embed-text`
- **Infrastructure:** Docker & Docker Compose

---

## 🚀 Getting Started (CTI App)

### 1. Prerequisites
- **Docker** (Docker Desktop or Docker Engine)
- **Ollama** (installed locally from [ollama.com](https://ollama.com))

### 2. Pull the AI Models

```powershell
ollama pull hf.co/gmansoor/Llama-3.2-3B-CTI-GGUF:Q4_K_M
ollama pull nomic-embed-text
```

*(Linux users: start Ollama with `OLLAMA_HOST=0.0.0.0 ollama serve` so Docker containers can reach it.)*

### 3. Build & Run

```powershell
docker build -t cti-app .
docker run --rm -p 8000:8000 --add-host=host.docker.internal:host-gateway cti-app
```

Wait ~20 seconds for MongoDB to initialize and load seed data, then open **http://localhost:8000**.

---

## 🎮 Using the Platform

### Default Login
- **Username:** `admin`
- **Password:** `admin123`
*(New users can register via "Create viewer account" on the login page; Admins can upgrade roles.)*

### Example Prompts
1. *"What are the active threats on Windows?"* (select **Windows** in the dropdown)
2. *"Tell me about CVE-2024-6387"*
3. *"What is the Dirty Pipe vulnerability?"*

### Admin Slash Commands (set dropdown to **General**)
- `/scan` — Audits MongoDB for security issues (e.g., default credentials).
- `/fix 1` — Prepares an automatic fix for issue #1.
- `/yes` — Confirms and applies the fix.

---

## 🧪 Running the 18 NoSQL Labs

All 18 labs (`labs/lab01` through `labs/lab18`) include runnable scripts, saved outputs, and individual READMEs.

- **Labs 01–06:** Standalone MongoDB (`cti-labs1-6` on port `27015`) — NoSQL classification, CRUD, schema validation, aggregation, indexing.
- **Labs 07–14:** Replica sets, failover, write concerns, network partitions, ACID transactions, sharding, RBAC/TLS, keyFile auth, monitoring, backups.
- **Labs 15–18:** Multi-tenant API, polyglot persistence (MongoDB + Cassandra + Neo4j), local RAG + HNSW vector search, and cross-database benchmarking.

Full setup and execution instructions: **[labs/README.md](labs/README.md)**.