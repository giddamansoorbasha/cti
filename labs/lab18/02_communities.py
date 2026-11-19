"""Lab 18.1 activity: graph-based detection, cross-referenced with MongoDB.

Neo4j groups threats into communities by shared IOC: every threat linked to the
same IOC node is connected to every other one through it. A community is flagged
when its size is more than two standard deviations above the mean. Each flagged
community is then looked up in MongoDB for platform, status and severity details.

Neo4j Community edition here has no Graph Data Science plugin, so this is a
shared-neighbour (degree) grouping in plain Cypher, not Louvain. Read-only.
"""
import os
import statistics
import time

from neo4j import GraphDatabase
from pymongo import MongoClient

TOP = 5

mongo = MongoClient(os.getenv("CTI_MONGO_URI", os.getenv(
    "MONGO_URI", "mongodb://127.0.0.1:27117,127.0.0.1:27118,127.0.0.1:27119/?replicaSet=rs0")))
db = mongo["cti_hybrid"]
neo4j = GraphDatabase.driver(
    os.getenv("NEO4J_URI", "bolt://localhost:7687"),
    auth=(os.getenv("NEO4J_USER", "neo4j"), os.getenv("NEO4J_PASSWORD", "password")))

try:
    t0 = time.perf_counter()
    with neo4j.session() as session:
        sizes = {r["ioc"]: r["threats"] for r in session.run(
            "MATCH (i:IOC)<-[:HAS_IOC]-(t:Threat) RETURN i.value AS ioc, count(t) AS threats")}
    graph_ms = (time.perf_counter() - t0) * 1000
    if not sizes:
        raise SystemExit("No IOC communities in Neo4j; run the Lab 16 seed first")

    mean, sd = statistics.mean(sizes.values()), statistics.pstdev(sizes.values())
    threshold = mean + 2 * sd
    flagged = sorted((kv for kv in sizes.items() if kv[1] > threshold), key=lambda kv: -kv[1])

    print("=== 1. Neo4j: communities of threats that share an IOC ===")
    print(f"communities: {len(sizes):,} | mean size {mean:.1f} | std dev {sd:.1f} | query {graph_ms:.0f} ms")
    print(f"flag rule  : size > mean + 2 x std dev = {threshold:.1f}")
    print(f"flagged    : {len(flagged)} communities ({len(flagged) / len(sizes):.1%})")

    print(f"\n=== 2. MongoDB: details of the {min(TOP, len(flagged))} largest flagged communities ===")
    print(f"{'IOC':16}{'Neo4j':>7}{'Mongo':>7}{'avg sev':>9}{'not resolved':>14}  top platform")
    for ioc, size in flagged[:TOP]:
        rows = list(db.threats.aggregate([
            {"$match": {"ioc": ioc}},
            {"$group": {"_id": "$platform", "n": {"$sum": 1}, "severity": {"$sum": "$severity"},
                        "open": {"$sum": {"$cond": [{"$ne": ["$status", "Resolved"]}, 1, 0]}}}},
            {"$sort": {"n": -1}}]))
        total = sum(r["n"] for r in rows)
        print(f"{ioc:16}{size:>7}{total:>7}{sum(r['severity'] for r in rows) / total:>9.2f}"
              f"{sum(r['open'] for r in rows):>14}  {rows[0]['_id']} ({rows[0]['n']})")
    print("\nNeo4j and Mongo counts should match: both stores were seeded from the same rows.")
    print("The seed assigns IOCs at random, so flagged communities here are statistical outliers, not real campaigns.")
finally:
    neo4j.close()
    mongo.close()
