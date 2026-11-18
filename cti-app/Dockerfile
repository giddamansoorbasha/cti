FROM python:3.11-slim

RUN apt-get update && apt-get install -y gnupg curl wget && \
    curl -fsSL https://www.mongodb.org/static/pgp/server-8.0.asc | \
    gpg -o /usr/share/keyrings/mongodb-server-8.0.gpg --dearmor && \
    echo "deb [ signed-by=/usr/share/keyrings/mongodb-server-8.0.gpg ] http://repo.mongodb.org/apt/debian bookworm/mongodb-org/8.0 main" | \
    tee /etc/apt/sources.list.d/mongodb-org-8.0.list && \
    apt-get update && apt-get install -y mongodb-org && \
    rm -rf /var/lib/apt/lists/* && mkdir -p /data/db

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN sed -i 's/\r$//' /app/docker/start.sh && chmod +x /app/docker/start.sh

ENV OLLAMA_CHAT_MODEL="hf.co/gmansoor/Llama-3.2-3B-CTI-GGUF:Q4_K_M" \
    OLLAMA_EMBEDDING_MODEL="nomic-embed-text" \
    OLLAMA_URL="http://host.docker.internal:11434" \
    MONGO_ROOT_USER="root" \
    MONGO_ROOT_PASSWORD="Root-Change-Me-1" \
    MONGO_DB="chatbot" \
    ADMIN_PASSWORD="admin123" \
    JWT_SECRET="change-this-secret" \
    PYTHONUNBUFFERED=1

EXPOSE 8000
CMD ["/app/docker/start.sh"]