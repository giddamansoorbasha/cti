# 🛡️ CTI Platform (Cyber Threat Intelligence)

A local, AI-powered cybersecurity assistant. This platform automatically collects threat reports (like zero-days, malware, and CVEs) from the internet, stores them securely in a local database, and lets you ask questions about them using an AI chatbot. Everything runs entirely locally on your laptop, keeping your data 100% private.

---

## 🌟 Features
* **AI Chatbot:** Ask natural language questions about cyber threats.
* **Platform Filtering:** Filter the AI's answers specifically for Windows, Linux, or Android using a UI dropdown.
* **Exact CVE Search:** Type a CVE ID (like `CVE-2024-6387`) to get precise details straight from the database, bypassing AI guesswork.
* **Automated Feed Updates:** Fetches the latest cybersecurity news via RSS feeds.
* **System Scanner:** Built-in MongoDB security scanner to find weak passwords or exposed ports.
* **Role-Based Access:** Different permissions for Viewers (chat only), Analysts (chat + scan), and Admins (all features).

---

## 🏗️ Architecture & Data Flow

Here is the exact step-by-step flow of how the system works behind the scenes:

1. **Data Ingestion (The Fetcher):** 
   The backend periodically reaches out to top security blogs (like CISA or BleepingComputer) via RSS. It cleans the text and extracts key Indicators of Compromise (IOCs), like IP addresses and CVE numbers.
2. **Vectorization (The Brain):** 
   The cleaned text is sent to **Ollama** (running the `nomic-embed-text` model). Ollama converts the text into mathematical vectors (embeddings), allowing the AI to understand the *meaning* of the reports.
3. **Storage (The Vault):** 
   The original text, extracted IOCs, and vectors are saved into a local **MongoDB** database running inside a Docker container.
4. **Chat Routing (The Gateway):** 
   When you type a question in the UI:
   * If you type a specific CVE (e.g., `CVE-2024-6387`), the system uses Regex to do a direct, exact database lookup.
   * If you ask a general question, it performs a semantic vector search to find the most relevant threat reports.
5. **AI Answer (The Output):** 
   The retrieved reports are sent to the local **Llama 3.2** model via Ollama. The AI reads them, respects your selected platform (Windows/Linux/Android), and types a clean, simple answer back to you in the chat.

---

## 💻 Tech Stack
* **Frontend:** HTML, CSS, JavaScript (Vanilla, lightweight)
* **Backend:** Python, FastAPI
* **Database:** MongoDB 8.0 (Local)
* **AI Models:** Ollama (Llama-3.2-3B for chat, Nomic-Embed-Text for search)
* **Deployment:** Docker

---

## 🚀 Getting Started (How to Run on Your Laptop)

### 1. Prerequisites
You need to install two things on your laptop:
* **Docker:** To run the database and the web app together.
* **Ollama:** To run the AI models locally (download from ollama.com).

### 2. Download the AI Models
Open your terminal or command prompt and run these two commands:

    ollama pull hf.co/gmansoor/Llama-3.2-3B-CTI-GGUF:Q4_K_M
    ollama pull nomic-embed-text

*(Note for Linux users: You must run `OLLAMA_HOST=0.0.0.0 ollama serve` so Docker can communicate with Ollama).*

### 3. Build and Run the App
Navigate to the project folder where your `Dockerfile` is located, and run:

    docker build -t cti-app .
    docker run --rm -p 8000:8000 --add-host=host.docker.internal:host-gateway cti-app

### 4. Open the App
Wait about 20 seconds for the database to start and load the initial seed data. Then open your web browser and go to:
**http://localhost:8000**

---

## 🎮 How to Use the Platform

### Default Login
* **Username:** `admin`
* **Password:** `admin123`
*(Other users can click "Create viewer account" on the login page to sign up. Admins can upgrade their roles later).*

### Chat Examples
Go to the **Ask CTI Assistant** page and try these:
1. *"What are the active threats on Windows?"* (Select "Windows" from the dropdown!)
2. *"Tell me about CVE-2024-6387"*
3. *"What is the Dirty Pipe vulnerability?"*

### Admin Slash Commands
If you are logged in as an Admin, set the platform dropdown to **General**, then type:
* `/scan` : Audits your MongoDB database for security issues (like the default admin123 password).
* `/fix 1` : Tells the system to automatically fix the first issue found in the scan.
* `/yes` : Confirms the fix.