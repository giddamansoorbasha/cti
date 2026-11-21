#!/bin/bash
set -e

echo "1) Starting MongoDB (setup mode)..."
mongod --dbpath /data/db --logpath /var/log/mongodb/mongod.log --bind_ip 127.0.0.1 --fork

sleep 3

echo "2) Creating Mongo root user..."
mongosh --quiet --eval "
const adminDb = db.getSiblingDB('admin');
if (!adminDb.getUser('${MONGO_ROOT_USER}')) {
  printjson(adminDb.createUser({
    user: '${MONGO_ROOT_USER}',
    pwd: '${MONGO_ROOT_PASS}',
    roles: [{ role: 'root', db: 'admin' }]
  }));
}
"

echo "3) Restarting MongoDB with auth ON..."
mongod --dbpath /data/db --shutdown
sleep 2
mongod --dbpath /data/db --logpath /var/log/mongodb/mongod.log --bind_ip 127.0.0.1 --auth --fork

sleep 2

echo "4) Starting CTI app on :8000 (using host Ollama)..."
cd /app/app
exec uvicorn main:app --host 0.0.0.0 --port 8000