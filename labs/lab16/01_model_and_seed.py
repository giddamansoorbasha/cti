import os
import random
import time
import uuid

from cassandra.cluster import Cluster, NoHostAvailable
from cassandra.concurrent import execute_concurrent_with_args
from neo4j import GraphDatabase
from pymongo import MongoClient

THREAT_COUNT = int(os.getenv("THREAT_COUNT", "10000"))
BATCH_SIZE = 1_000

mongo_uri = os.getenv(
    "CTI_MONGO_URI",
    os.getenv(
        "MONGO_URI",
        "mongodb://127.0.0.1:27117,127.0.0.1:27118,127.0.0.1:27119/?replicaSet=rs0",
    ),
)
mongo = MongoClient(mongo_uri)
db = mongo["cti_hybrid"]
db.threats.drop()

print("Connecting to Cassandra...")
cassandra_cluster = None
session = None
for _ in range(20):
    try:
        cassandra_cluster = Cluster(
            [os.getenv("CASSANDRA_HOST", "127.0.0.1")],
            port=int(os.getenv("CASSANDRA_PORT", "9042")),
        )
        session = cassandra_cluster.connect()
        break
    except NoHostAvailable:
        if cassandra_cluster:
            cassandra_cluster.shutdown()
        time.sleep(5)
if session is None:
    raise RuntimeError("Cassandra did not boot in time. Check Docker.")

session.execute(
    "CREATE KEYSPACE IF NOT EXISTS cti "
    "WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1}"
)
session.set_keyspace("cti")
session.execute(
    "CREATE TABLE IF NOT EXISTS threats_by_platform "
    "(platform text, status text, id text, severity int, "
    "PRIMARY KEY ((platform, status), id))"
)
session.execute(
    "CREATE TABLE IF NOT EXISTS threat_by_id "
    "(id text PRIMARY KEY, platform text, status text, severity int)"
)
session.execute("TRUNCATE threats_by_platform")
session.execute("TRUNCATE threat_by_id")
insert_by_platform = session.prepare(
    "INSERT INTO threats_by_platform (platform, status, id, severity) "
    "VALUES (?, ?, ?, ?)"
)
insert_by_id = session.prepare(
    "INSERT INTO threat_by_id (id, platform, status, severity) "
    "VALUES (?, ?, ?, ?)"
)

print("Connecting to Neo4j and clearing the Lab 16 graph...")
neo4j = GraphDatabase.driver(
    os.getenv("NEO4J_URI", "bolt://localhost:7687"),
    auth=(os.getenv("NEO4J_USER", "neo4j"), os.getenv("NEO4J_PASSWORD", "password")),
)
with neo4j.session() as graph_session:
    while (
        graph_session.run(
            "MATCH (n) WITH n LIMIT 10000 DETACH DELETE n RETURN count(n) AS c"
        ).single()["c"]
        > 0
    ):
        pass
    graph_session.run(
        "CREATE CONSTRAINT IF NOT EXISTS FOR (t:Threat) REQUIRE t.id IS UNIQUE"
    ).consume()
    graph_session.run(
        "CREATE CONSTRAINT IF NOT EXISTS FOR (p:Platform) REQUIRE p.name IS UNIQUE"
    ).consume()
    graph_session.run(
        "CREATE CONSTRAINT IF NOT EXISTS FOR (i:IOC) REQUIRE i.value IS UNIQUE"
    ).consume()


def write_graph_batch(tx, rows):
    tx.run(
        """
        UNWIND $rows AS row
        MERGE (t:Threat {id: row.id})
        MERGE (p:Platform {name: row.platform})
        MERGE (i:IOC {value: row.ioc})
        MERGE (t)-[:TARGETS]->(p)
        MERGE (t)-[:HAS_IOC]->(i)
        """,
        rows=rows,
    ).consume()


platforms = ["Windows", "Linux", "MacOS", "Android", "iOS"]
statuses = ["Anticipated", "Active", "Evolving", "Resolved"]
iocs = [f"192.168.1.{i}" for i in range(1_000)]

print(f"Seeding {THREAT_COUNT:,} shared threats in batches of {BATCH_SIZE:,}...")
with neo4j.session() as graph_session:
    for start in range(0, THREAT_COUNT, BATCH_SIZE):
        mongo_docs = []
        platform_rows = []
        id_rows = []
        graph_rows = []

        for _ in range(min(BATCH_SIZE, THREAT_COUNT - start)):
            threat_id = str(uuid.uuid4())
            platform = random.choice(platforms)
            status = random.choice(statuses)
            severity = random.randint(1, 10)
            ioc = random.choice(iocs)

            mongo_docs.append(
                {
                    "_id": threat_id,
                    "platform": platform,
                    "status": status,
                    "severity": severity,
                    "ioc": ioc,
                }
            )
            platform_rows.append((platform, status, threat_id, severity))
            id_rows.append((threat_id, platform, status, severity))
            graph_rows.append(
                {"id": threat_id, "platform": platform, "ioc": ioc}
            )

        db.threats.insert_many(mongo_docs, ordered=False)
        execute_concurrent_with_args(
            session,
            insert_by_platform,
            platform_rows,
            concurrency=100,
            raise_on_first_error=True,
        )
        execute_concurrent_with_args(
            session,
            insert_by_id,
            id_rows,
            concurrency=100,
            raise_on_first_error=True,
        )
        graph_session.execute_write(write_graph_batch, graph_rows)

        completed = start + len(mongo_docs)
        if completed % 10_000 == 0:
            print(f" - Inserted {completed:,} / {THREAT_COUNT:,}")

print("Creating MongoDB query indexes...")
db.threats.create_index([("platform", 1), ("status", 1)])
db.threats.create_index("ioc")

print(
    "Seed complete:",
    db.threats.count_documents({}),
    "MongoDB threats;",
    session.execute("SELECT COUNT(*) FROM threat_by_id").one().count,
    "Cassandra threats.",
)

neo4j.close()
cassandra_cluster.shutdown()
mongo.close()