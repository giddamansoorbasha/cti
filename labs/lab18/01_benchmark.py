import os
import random
import statistics
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from cassandra.cluster import Cluster
from cassandra.concurrent import execute_concurrent_with_args
from neo4j import GraphDatabase
from pymongo import MongoClient, UpdateOne

REQUIRED_THREATS = int(os.getenv("REQUIRED_THREATS", "10000"))
RUNS = 10
LIMIT = 100
INSERTS_PER_RUN = 500
DAY_WINDOW = 30

mongo_uri = os.getenv(
    "CTI_MONGO_URI",
    os.getenv(
        "MONGO_URI",
        "mongodb://127.0.0.1:27117,127.0.0.1:27118,127.0.0.1:27119/?replicaSet=rs0",
    ),
)
mongo = MongoClient(mongo_uri)
db = mongo["cti_hybrid"]
count = db.threats.count_documents({})
if count < REQUIRED_THREATS:
    raise RuntimeError(
        f"Lab 18 requires at least {REQUIRED_THREATS:,} threats; found {count:,}. "
        "Run the Lab 16 seed first."
    )

cluster = Cluster(
    [os.getenv("CASSANDRA_HOST", "127.0.0.1")],
    port=int(os.getenv("CASSANDRA_PORT", "9042")),
)
cass_session = cluster.connect("cti")
neo4j = GraphDatabase.driver(
    os.getenv("NEO4J_URI", "bolt://localhost:7687"),
    auth=(os.getenv("NEO4J_USER", "neo4j"), os.getenv("NEO4J_PASSWORD", "password")),
)
cass_count = cass_session.execute(
    "SELECT COUNT(*) FROM threat_by_id"
).one().count
with neo4j.session() as session:
    neo4j_count = session.run(
        "MATCH (t:Threat) RETURN count(t) AS total"
    ).single()["total"]
if cass_count < REQUIRED_THREATS or neo4j_count < REQUIRED_THREATS:
    raise RuntimeError(
        "Lab 18 requires at least 100,000 records in each database; "
        f"found MongoDB={count:,}, Cassandra={cass_count:,}, Neo4j={neo4j_count:,}."
    )

sample = db.threats.find_one({}, {"_id": 1, "ioc": 1, "platform": 1})
if sample is None:
    raise RuntimeError("Lab 18 dataset is empty.")
sample_id = sample["_id"]
sample_ioc = sample["ioc"]
sample_platform = sample["platform"]

PLATFORMS = ["Windows", "Linux", "MacOS", "Android", "iOS"]
STATUSES = ["Anticipated", "Active", "Evolving", "Resolved"]


# ---- Daily volume setup: adds a 'day' field. Nothing is deleted or replaced. ----
def ensure_mongo_days():
    rng = random.Random(18)
    today = datetime.now(timezone.utc).date()
    pool = [(today - timedelta(days=i)).isoformat() for i in range(DAY_WINDOW)]
    missing = [d["_id"] for d in db.threats.find({"day": {"$exists": False}}, {"_id": 1})]
    for start in range(0, len(missing), 5000):
        db.threats.bulk_write(
            [
                UpdateOne({"_id": threat_id}, {"$set": {"day": rng.choice(pool)}})
                for threat_id in missing[start:start + 5000]
            ],
            ordered=False,
        )
    db.threats.create_index("day")
    return len(missing)


def ensure_cassandra_days():
    cass_session.execute(
        "CREATE TABLE IF NOT EXISTS threats_by_day "
        "(day text, id text, platform text, PRIMARY KEY ((day), id))"
    )
    insert_day = cass_session.prepare(
        "INSERT INTO threats_by_day (day, id, platform) VALUES (?, ?, ?)"
    )
    expected = {
        row["_id"]: row["n"]
        for row in db.threats.aggregate([{"$group": {"_id": "$day", "n": {"$sum": 1}}}])
    }
    stale = [
        day
        for day, n in expected.items()
        if cass_session.execute(
            "SELECT COUNT(*) FROM threats_by_day WHERE day=%s", (day,)
        ).one().count != n
    ]
    if stale:
        rows = [
            (row["day"], row["_id"], row["platform"])
            for row in db.threats.find({"day": {"$in": stale}}, {"day": 1, "platform": 1})
        ]
        execute_concurrent_with_args(
            cass_session, insert_day, rows, concurrency=100, raise_on_first_error=True
        )
    return len(stale)


def write_neo4j_days(tx, rows):
    tx.run(
        "UNWIND $rows AS r MATCH (t:Threat {id: r.id}) SET t.day = r.day",
        rows=rows,
    ).consume()


def ensure_neo4j_days():
    with neo4j.session() as session:
        session.run(
            "CREATE INDEX threat_day IF NOT EXISTS FOR (t:Threat) ON (t.day)"
        ).consume()
        missing = session.run(
            "MATCH (t:Threat) WHERE t.day IS NULL RETURN count(t) AS n"
        ).single()["n"]
        if missing:
            rows = [{"id": d["_id"], "day": d["day"]} for d in db.threats.find({}, {"day": 1})]
            for start in range(0, len(rows), 5000):
                session.execute_write(write_neo4j_days, rows[start:start + 5000])
    return missing


print("Preparing daily-volume data (adds a 'day' field only if missing)...")
print(f" - MongoDB documents updated: {ensure_mongo_days():,}")
print(f" - Cassandra day partitions synced: {ensure_cassandra_days():,}")
print(f" - Neo4j nodes missing a day before sync: {ensure_neo4j_days():,}")
sample_days = sorted(db.threats.distinct("day"))[-7:]

insert_by_id = cass_session.prepare(
    "INSERT INTO threat_by_id (id, platform, status, severity) VALUES (?, ?, ?, ?)"
)
insert_by_platform = cass_session.prepare(
    "INSERT INTO threats_by_platform (platform, status, id, severity) VALUES (?, ?, ?, ?)"
)
insert_by_day = cass_session.prepare(
    "INSERT INTO threats_by_day (day, id, platform) VALUES (?, ?, ?)"
)
delete_by_id = cass_session.prepare("DELETE FROM threat_by_id WHERE id=?")
delete_by_platform = cass_session.prepare(
    "DELETE FROM threats_by_platform WHERE platform=? AND status=? AND id=?"
)
delete_by_day = cass_session.prepare("DELETE FROM threats_by_day WHERE day=? AND id=?")


def median_ms(func, *args):
    timings = []
    for _ in range(RUNS):
        started = time.perf_counter()
        func(*args)
        timings.append((time.perf_counter() - started) * 1000)
    return statistics.median(timings)


# ---- Q1 / Q2: threat history ----
def q1_mongo(threat_id):
    list(db.threats.find({"_id": threat_id}))


def q1_cassandra(threat_id):
    list(cass_session.execute(
        "SELECT * FROM threat_by_id WHERE id=%s", (threat_id,)
    ))


def q2_mongo():
    list(
        db.threats.find({"platform": "Windows", "status": "Active"}).limit(LIMIT)
    )


def q2_cassandra():
    list(
        cass_session.execute(
            "SELECT * FROM threats_by_platform "
            "WHERE platform=%s AND status=%s LIMIT 100",
            ("Windows", "Active"),
        )
    )


# ---- Q3 / Q4: target and spread ----
def q3_mongo(ioc):
    list(db.threats.find({"ioc": ioc}))


def q3_neo4j(threat_id):
    with neo4j.session() as session:
        list(
            session.run(
                "MATCH (t1:Threat {id: $id})-[:HAS_IOC]->(i:IOC)"
                "<-[:HAS_IOC]-(t2:Threat) RETURN t2.id LIMIT 100",
                id=threat_id,
            )
        )


def q4_mongo(platform):
    list(db.threats.find({"platform": platform}).limit(LIMIT))


def q4_neo4j(platform):
    with neo4j.session() as session:
        list(
            session.run(
                "MATCH (p:Platform {name: $platform})"
                "<-[:TARGETS]-(t:Threat) RETURN t.id LIMIT 100",
                platform=platform,
            )
        )


# ---- Q5: daily volume (threats per day, newest 7 days) ----
def q5_mongo(days):
    list(
        db.threats.aggregate(
            [
                {"$match": {"day": {"$in": days}}},
                {"$group": {"_id": "$day", "total": {"$sum": 1}}},
                {"$sort": {"_id": 1}},
            ]
        )
    )


def q5_cassandra(days):
    for day in days:
        cass_session.execute(
            "SELECT COUNT(*) FROM threats_by_day WHERE day=%s", (day,)
        ).one()


def q5_neo4j(days):
    with neo4j.session() as session:
        list(
            session.run(
                "MATCH (t:Threat) WHERE t.day IN $days "
                "RETURN t.day AS day, count(t) AS total ORDER BY day",
                days=days,
            )
        )


# ---- Q6: real-time insert throughput (test rows are deleted after each run) ----
def make_rows():
    day = sample_days[-1]
    return [
        {
            "id": str(uuid.uuid4()),
            "platform": random.choice(PLATFORMS),
            "status": random.choice(STATUSES),
            "severity": random.randint(1, 10),
            "ioc": sample_ioc,
            "day": day,
        }
        for _ in range(INSERTS_PER_RUN)
    ]


def insert_mongo(rows):
    db.threats.insert_many(
        [
            {
                "_id": r["id"], "platform": r["platform"], "status": r["status"],
                "severity": r["severity"], "ioc": r["ioc"], "day": r["day"],
            }
            for r in rows
        ],
        ordered=False,
    )


def cleanup_mongo(rows):
    db.threats.delete_many({"_id": {"$in": [r["id"] for r in rows]}})


def insert_cassandra(rows):
    for statement, params in (
        (insert_by_id, [(r["id"], r["platform"], r["status"], r["severity"]) for r in rows]),
        (insert_by_platform, [(r["platform"], r["status"], r["id"], r["severity"]) for r in rows]),
        (insert_by_day, [(r["day"], r["id"], r["platform"]) for r in rows]),
    ):
        execute_concurrent_with_args(
            cass_session, statement, params, concurrency=100, raise_on_first_error=True
        )


def cleanup_cassandra(rows):
    for statement, params in (
        (delete_by_id, [(r["id"],) for r in rows]),
        (delete_by_platform, [(r["platform"], r["status"], r["id"]) for r in rows]),
        (delete_by_day, [(r["day"], r["id"]) for r in rows]),
    ):
        execute_concurrent_with_args(
            cass_session, statement, params, concurrency=100, raise_on_first_error=True
        )


def write_neo4j_rows(tx, rows):
    tx.run(
        "UNWIND $rows AS row "
        "CREATE (t:Threat {id: row.id, severity: row.severity, day: row.day}) "
        "WITH t, row "
        "MATCH (p:Platform {name: row.platform}) "
        "MATCH (i:IOC {value: row.ioc}) "
        "CREATE (t)-[:TARGETS]->(p), (t)-[:HAS_IOC]->(i)",
        rows=rows,
    ).consume()


def insert_neo4j(rows):
    with neo4j.session() as session:
        session.execute_write(write_neo4j_rows, rows)


def cleanup_neo4j(rows):
    with neo4j.session() as session:
        session.run(
            "UNWIND $ids AS id MATCH (t:Threat {id: id}) DETACH DELETE t",
            ids=[r["id"] for r in rows],
        ).consume()


def median_insert_rate(insert, cleanup):
    rates = []
    for _ in range(RUNS):
        rows = make_rows()
        try:
            started = time.perf_counter()
            insert(rows)
            elapsed = time.perf_counter() - started
        finally:
            cleanup(rows)
        rates.append(len(rows) / elapsed)
    return statistics.median(rates)


results = {
    "q1_mongo": median_ms(q1_mongo, sample_id),
    "q1_cassandra": median_ms(q1_cassandra, sample_id),
    "q2_mongo": median_ms(q2_mongo),
    "q2_cassandra": median_ms(q2_cassandra),
    "q3_mongo": median_ms(q3_mongo, sample_ioc),
    "q3_neo4j": median_ms(q3_neo4j, sample_id),
    "q4_mongo": median_ms(q4_mongo, sample_platform),
    "q4_neo4j": median_ms(q4_neo4j, sample_platform),
    "q5_mongo": median_ms(q5_mongo, sample_days),
    "q5_cassandra": median_ms(q5_cassandra, sample_days),
    "q5_neo4j": median_ms(q5_neo4j, sample_days),
    "q6_mongo": median_insert_rate(insert_mongo, cleanup_mongo),
    "q6_cassandra": median_insert_rate(insert_cassandra, cleanup_cassandra),
    "q6_neo4j": median_insert_rate(insert_neo4j, cleanup_neo4j),
}

# Confirm the test rows were removed, so the 100,000-record dataset is unchanged.
final_counts = (
    db.threats.count_documents({}),
    cass_session.execute("SELECT COUNT(*) FROM threat_by_id").one().count,
)

stats = db.command("collStats", "threats")
bytes_per_doc = (stats["size"] + stats["totalIndexSize"]) / stats["count"]


def cell(value, unit):
    return "N/A" if value is None else f"{value:,.2f} {unit}"


def best_of(values, higher_is_better=False):
    found = {k: v for k, v in values.items() if v is not None}
    return (max if higher_is_better else min)(found, key=found.get)


def table_row(label, values, unit, higher_is_better=False):
    best = best_of(values, higher_is_better)
    cells = " | ".join(cell(values.get(name), unit) for name in ("MongoDB", "Cassandra", "Neo4j"))
    return f"| {label} | {cells} | {best} |"


specs = [
    ("Q1: Threat history, lookup by ID",
     {"MongoDB": results["q1_mongo"], "Cassandra": results["q1_cassandra"]}, "ms", False),
    ("Q2: Threat history, platform + status",
     {"MongoDB": results["q2_mongo"], "Cassandra": results["q2_cassandra"]}, "ms", False),
    ("Q3: Spread, threats sharing an IOC",
     {"MongoDB": results["q3_mongo"], "Neo4j": results["q3_neo4j"]}, "ms", False),
    ("Q4: Target, threats by platform",
     {"MongoDB": results["q4_mongo"], "Neo4j": results["q4_neo4j"]}, "ms", False),
    ("Q5: Daily volume, newest 7 days",
     {"MongoDB": results["q5_mongo"], "Cassandra": results["q5_cassandra"], "Neo4j": results["q5_neo4j"]}, "ms", False),
    ("Q6: Insert throughput",
     {"MongoDB": results["q6_mongo"], "Cassandra": results["q6_cassandra"], "Neo4j": results["q6_neo4j"]}, "inserts/s", True),
]
winners = [best_of(values, better) for _, values, _, better in specs]
win_counts = {name: winners.count(name) for name in ("MongoDB", "Cassandra", "Neo4j")}


def projection(n):
    return f"| {n:,} | {bytes_per_doc * n / 1e9:,.2f} GB |"


report = "\n".join(
    [
        "# Lab 18: Cross-Database Comparative Report",
        "",
        "## 1. Executive Summary",
        "Use MongoDB as the main operational database (flexible filters, easy to run). "
        "Cassandra is built to scale writes across many machines; that was not tested here "
        "because this test used only one node. "
        "Neo4j is built for multi-hop relationship questions; only one-hop questions were tested here. "
        f"In this run MongoDB was fastest in {win_counts['MongoDB']} of 6 tests, "
        f"Cassandra in {win_counts['Cassandra']}, and Neo4j in {win_counts['Neo4j']}. "
        "These numbers change a little on every run and are not production capacity claims.",
        "",
        "## 2. Methodology",
        f"- Data: {REQUIRED_THREATS:,} threats in each database "
        f"(verified MongoDB={count:,}, Cassandra={cass_count:,}, Neo4j={neo4j_count:,}).",
        f"- Each query: median of {RUNS} measured runs, result cap {LIMIT} where applicable.",
        f"- Insert test: {INSERTS_PER_RUN} threats per run, median of {RUNS} runs. "
        "Test rows are deleted after every run "
        f"(counts after the test: MongoDB={final_counts[0]:,}, Cassandra={final_counts[1]:,}).",
        "- Environment: one local machine, Docker containers, one Cassandra node, one Neo4j instance.",
        f"- Daily volume uses the newest 7 days ({sample_days[0]} to {sample_days[-1]}). "
        "The day values are generated test dates, not real report dates.",
        "",
        "## 3. Schema Design",
        "- MongoDB: one document per threat (platform, status, severity, ioc, day). "
        "Indexes on (platform, status), ioc, and day.",
        "- Cassandra: one table per query. threat_by_id for lookups, "
        "threats_by_platform partitioned by (platform, status), threats_by_day partitioned by day. "
        "Every threat is written to all three tables.",
        "- Neo4j: Threat, Platform, and IOC nodes with TARGETS and HAS_IOC relationships. "
        "Index on Threat.day.",
        "",
        "## 4. Query Performance",
        "",
        "| Query | MongoDB | Cassandra | Neo4j | Fastest |",
        "|---|---:|---:|---:|---|",
        *[table_row(label, values, unit, better) for label, values, unit, better in specs],
        "",
        "Q1 to Q5: lower is better. Q6: higher is better. "
        "N/A means that database was not designed for that query. "
        "Cassandra writes 3 tables per threat and Neo4j creates 2 relationships per threat, "
        "so Q6 compares each database's normal design, not identical work. "
        "Cassandra daily volume needs one query per day (7 queries), which adds time.",
        "",
        "## 5. Ergonomics",
        "- MongoDB: easiest to learn; one query language for lookups, filters, and grouping.",
        "- Cassandra: you must design a table for each query first; fast and predictable, less flexible.",
        "- Neo4j: Cypher makes relationship questions short and clear.",
        "",
        "## 6. Scalability Assessment",
        f"MongoDB size measured here: about {bytes_per_doc:,.0f} bytes per threat (data + indexes). "
        "The table is a straight-line estimate from that number, not a measurement.",
        "",
        "| Threats | Estimated MongoDB data + indexes |",
        "|---:|---:|",
        projection(1_000_000),
        projection(10_000_000),
        projection(100_000_000),
        "",
        "- MongoDB: scale out with sharding (Lab 11). Keep indexes in RAM. "
        "A good shard key matters more than extra hardware.",
        "- Cassandra: add nodes to the ring; data and writes spread by partition key. "
        "Designed for high write volume across many nodes (not tested here).",
        "- Neo4j: Community edition runs on one machine, so you scale up (more RAM and CPU). "
        "Clustering is an Enterprise feature.",
        "- Operations: MongoDB has mongodump (Lab 14). Cassandra needs snapshots and repairs. "
        "Neo4j needs its own backup tool. Three databases means three skill sets to maintain.",
        "",
        "## 7. Recommendation by Access Pattern",
        f"- Threat lookups and filters: fastest this run was {winners[0]} (by ID) and {winners[1]} (platform + status).",
        f"- Insert speed on one node: {winners[5]} was fastest this run. "
        "Cassandra's advantage needs many nodes and was not tested.",
        f"- Daily counts: {winners[4]} was fastest this run. "
        "Cassandra needed one query per day.",
        f"- Shared-IOC and platform questions (one hop): fastest this run was {winners[2]} (IOC) and {winners[3]} (platform). "
        "Neo4j should be tested with multi-hop chains before choosing it.",
        "- For this project: MongoDB alone is enough. Add the others only when a specific need appears.",
        "",
        "## Limitations",
        "Medians of 10 runs on one local machine, with a single Cassandra node and a single Neo4j instance. "
        "Results are workload-specific and are not production capacity claims.",
    ]
)

print(report)
report_path = Path(__file__).with_name("benchmark_report.md")
report_path.write_text(report + "\n", encoding="utf-8")
print(f"Saved report: {report_path}")

neo4j.close()
cluster.shutdown()
mongo.close()
