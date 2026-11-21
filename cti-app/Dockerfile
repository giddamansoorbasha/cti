FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends gnupg curl ca-certificates && \
    curl -fsSL https://www.mongodb.org/static/pgp/server-8.0.asc | \
    gpg -o /usr/share/keyrings/mongodb-server-8.0.gpg --dearmor && \
    echo "deb [ signed-by=/usr/share/keyrings/mongodb-server-8.0.gpg ] http://repo.mongodb.org/apt/debian bookworm/mongodb-org/8.0 main" | \
    tee /etc/apt/sources.list.d/mongodb-org-8.0.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends mongodb-org && \
    rm -rf /var/lib/apt/lists/* && \
    mkdir -p /data/db /var/log/mongodb

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN sed -i 's/\r$//' /app/docker/start.sh && chmod +x /app/docker/start.sh

ENV MONGO_ROOT_USER="admin" \
    MONGO_ROOT_PASS="admin123" \
    MONGO_URI="mongodb://admin:admin123@127.0.0.1:27017/?authSource=admin" \
    OLLAMA_URL="http://host.docker.internal:11434" \
    OLLAMA_BASE_URL="http://host.docker.internal:11434" \
    OLLAMA_HOST="http://host.docker.internal:11434" \
    OLLAMA_CHAT_MODEL="hf.co/gmansoor/Llama-3.2-3B-CTI-GGUF:Q4_K_M" \
    OLLAMA_EMBEDDING_MODEL="nomic-embed-text" \
    PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["/app/docker/start.sh"]