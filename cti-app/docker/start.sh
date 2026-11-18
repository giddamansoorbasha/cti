#!/bin/bash
mkdir -p /data/db
LOG=/var/log/mongodb.log

wait_mongo() {
  for i in $(seq 1 40); do
    mongosh --quiet "$@" --eval "db.runCommand({ping:1})" >/dev/null 2>&1 && return 0
    sleep 1
  done
  return 1
}

echo "1) Starting MongoDB (setup mode)..."
mongod --fork --logpath $LOG --bind_ip 127.0.0.1
wait_mongo

echo "2) Creating Mongo root user..."
mongosh --quiet admin --eval "
if (!db.getUser('root')) {
  db.createUser({user: process.env.MONGO_ROOT_USER, pwd: process.env.MONGO_ROOT_PASSWORD, roles: ['root']});
}"

echo "3) Restarting MongoDB with auth ON..."
mongod --shutdown >/dev/null 2>&1
sleep 2
mongod --fork --auth --logpath $LOG --bind_ip 127.0.0.1
wait_mongo -u "$MONGO_ROOT_USER" -p "$MONGO_ROOT_PASSWORD" --authenticationDatabase admin

echo "4) Starting CTI app on :8000"
cd /app
exec uvicorn main:app --app-dir /app/app --host 0.0.0.0 --port 8000