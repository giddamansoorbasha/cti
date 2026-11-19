import os
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from neo4j import GraphDatabase
from pymongo import MongoClient, ReplaceOne

COUNT = 5_000
DIM = 384
TOP_K = 10
QUERY_COUNT = 100
WARMUP_COUNT = 10
MONGO_COLLECTION = "vectors_cross_engine"
MONGO_INDEX = "lab17_hnsw"
MONGO_INDEX_WIDE = "lab17_hnsw_wide"
INDEX_PARAMS = {MONGO_INDEX: (16, 100), MONGO_INDEX_WIDE: (32, 200)}
CANDIDATE_STEPS = (20, 50, 100, 200, 400)
NEO4J_INDEX = "lab17_2_vector"
BATCH_SIZE = 500

mongo_uri = os.environ["VECTOR_MONGO_URI"]
neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
neo4j_auth = (
    os.getenv("NEO4J_USER", "neo4j"),
    os.getenv("NEO4J_PASSWORD", "password"),
)


def ensure_mongo_index(collection, name, max_edges, edge_candidates):
    """Creates the HNSW index if missing. Returns build seconds, or None if it already existed."""
    started = time.monotonic()
    indexes = list(collection.aggregate([{"$listSearchIndexes": {"name": name}}]))
    existed = bool(indexes)
    if not existed:
        collection.database.command(
            {
                "createSearchIndexes": collection.name,
                "indexes": [
                    {
                        "name": name,
                        "type": "vectorSearch",
                        "definition": {
                            "fields": [
                                {
                                    "type": "vector",
                                    "path": "embedding",
                                    "numDimensions": DIM,
                                    "similarity": "cosine",
                                    "hnswOptions": {
                                        "maxEdges": max_edges,
                                        "numEdgeCandidates": edge_candidates,
                                    },
                                }
                            ]
                        },
                    }
                ],
            }
        )

    deadline = time.monotonic() + 180
    while time.monotonic() < deadline:
        indexes = list(
            collection.aggregate([{"$listSearchIndexes": {"name": name}}])
        )
        index = next(
            (item for item in indexes if item.get("name") == name), None
        )
        if index and index.get("status") == "READY" and index.get("queryable"):
            return None if existed else time.monotonic() - started
        if index and index.get("status") == "FAILED":
            raise RuntimeError(f"MongoDB HNSW index build failed: {index}")
        time.sleep(2)
    raise TimeoutError(f"MongoDB HNSW index {name} did not become queryable within 180 seconds.")


def seed_mongo(collection, vectors):
    collection.bulk_write(
        [
            ReplaceOne(
                {"_id": vector_id},
                {"_id": vector_id, "embedding": vector.tolist()},
                upsert=True,
            )
            for vector_id, vector in enumerate(vectors)
        ],
        ordered=False,
    )
    count = collection.count_documents({})
    if count != COUNT:
        raise RuntimeError(f"Expected {COUNT:,} MongoDB vectors; found {count:,}.")


def seed_neo4j(session, vectors):
    for start in range(0, COUNT, BATCH_SIZE):
        rows = [
            {"id": vector_id, "embedding": vector.tolist()}
            for vector_id, vector in enumerate(
                vectors[start : start + BATCH_SIZE], start=start
            )
        ]
        session.run(
            "UNWIND $rows AS row "
            "MERGE (v:Lab17Vector {id: row.id}) "
            "SET v.embedding = row.embedding",
            rows=rows,
        ).consume()

    count = session.run(
        "MATCH (v:Lab17Vector) RETURN count(v) AS count"
    ).single()["count"]
    if count != COUNT:
        raise RuntimeError(f"Expected {COUNT:,} Neo4j vectors; found {count:,}.")


def ensure_neo4j_index(session):
    session.run(
        f"CREATE VECTOR INDEX {NEO4J_INDEX} IF NOT EXISTS "
        "FOR (v:Lab17Vector) ON (v.embedding) "
        "OPTIONS {indexConfig: {"
        f"`vector.dimensions`: {DIM}, "
        "`vector.similarity_function`: 'cosine'}}"
    ).consume()

    deadline = time.monotonic() + 180
    while time.monotonic() < deadline:
        index = session.run(
            "SHOW VECTOR INDEXES YIELD name, state, populationPercent "
            "WHERE name = $name RETURN state, populationPercent",
            name=NEO4J_INDEX,
        ).single()
        if index and index["state"] == "ONLINE" and index["populationPercent"] == 100.0:
            return
        time.sleep(1)
    raise TimeoutError("Neo4j vector index did not become ONLINE within 180 seconds.")


def mongo_search(collection, query, index=MONGO_INDEX, candidates=100):
    return [
        row["_id"]
        for row in collection.aggregate(
            [
                {
                    "$vectorSearch": {
                        "index": index,
                        "path": "embedding",
                        "queryVector": query.tolist(),
                        "numCandidates": candidates,
                        "limit": TOP_K,
                    }
                },
                {"$project": {"_id": 1}},
            ]
        )
    ]


def neo4j_search(session, query):
    return [
        row["id"]
        for row in session.run(
            "CALL db.index.vector.queryNodes($index, $limit, $vector) "
            "YIELD node, score RETURN node.id AS id",
            index=NEO4J_INDEX,
            limit=TOP_K,
            vector=query.tolist(),
        )
    ]


def recall_at_k(result_ids, exact_ids):
    return len(set(result_ids) & exact_ids) / TOP_K


def measure_searches(mongo_collection, neo4j_session, queries, vectors):
    mongo_times = []
    neo4j_times = []
    mongo_recalls = []
    neo4j_recalls = []

    for query_number, query in enumerate(queries):
        exact_ids = set(
            np.argpartition(vectors @ query, -TOP_K)[-TOP_K:].tolist()
        )
        searches = (
            (mongo_search, mongo_collection, mongo_times, mongo_recalls),
            (neo4j_search, neo4j_session, neo4j_times, neo4j_recalls),
        )
        if query_number % 2:
            searches = tuple(reversed(searches))

        for search, target, times, recalls in searches:
            started = time.perf_counter()
            result_ids = search(target, query)
            times.append((time.perf_counter() - started) * 1000)
            if len(result_ids) != TOP_K:
                raise RuntimeError(
                    f"{search.__name__} returned {len(result_ids)} results, "
                    f"expected {TOP_K}."
                )
            recalls.append(recall_at_k(result_ids, exact_ids))

    return mongo_times, neo4j_times, mongo_recalls, neo4j_recalls


def sweep_mongo(collection, queries, vectors):
    exact = [
        set(np.argpartition(vectors @ query, -TOP_K)[-TOP_K:].tolist())
        for query in queries
    ]
    rows = []
    for index in (MONGO_INDEX, MONGO_INDEX_WIDE):
        for query in queries[:WARMUP_COUNT]:
            mongo_search(collection, query, index, 100)
        for candidates in CANDIDATE_STEPS:
            times = []
            recalls = []
            for query, truth in zip(queries, exact):
                started = time.perf_counter()
                result_ids = mongo_search(collection, query, index, candidates)
                times.append((time.perf_counter() - started) * 1000)
                recalls.append(recall_at_k(result_ids, truth))
            rows.append(
                (index, candidates, statistics.median(times), statistics.mean(recalls))
            )
    return rows


def main():
    rng = np.random.default_rng(42)
    vectors = rng.normal(size=(COUNT, DIM)).astype(np.float32)
    vectors /= np.maximum(np.linalg.norm(vectors, axis=1, keepdims=True), 1e-12)
    query_ids = rng.choice(COUNT, size=QUERY_COUNT, replace=False)
    queries = vectors[query_ids] + rng.normal(
        scale=0.05, size=(QUERY_COUNT, DIM)
    ).astype(np.float32)
    queries /= np.maximum(np.linalg.norm(queries, axis=1, keepdims=True), 1e-12)

    mongo = MongoClient(mongo_uri, serverSelectionTimeoutMS=10_000)
    neo4j = GraphDatabase.driver(neo4j_uri, auth=neo4j_auth)
    try:
        mongo.admin.command("ping")
        neo4j.verify_connectivity()
        collection = mongo["cti_lab17"][MONGO_COLLECTION]
        seed_mongo(collection, vectors)

        with neo4j.session() as session:
            seed_neo4j(session, vectors)
            ensure_neo4j_index(session)

            print(
                f"Loaded the same {COUNT:,} normalized {DIM}-dimensional vectors "
                "into MongoDB and Neo4j."
            )
            ensure_mongo_index(collection, MONGO_INDEX, *INDEX_PARAMS[MONGO_INDEX])
            wide_build_seconds = ensure_mongo_index(
                collection, MONGO_INDEX_WIDE, *INDEX_PARAMS[MONGO_INDEX_WIDE]
            )

            for query in queries[:WARMUP_COUNT]:
                mongo_search(collection, query)
                neo4j_search(session, query)

            print(
                f"Running {QUERY_COUNT} measured queries per engine "
                f"after {WARMUP_COUNT} warmups..."
            )
            mongo_times, neo4j_times, mongo_recalls, neo4j_recalls = (
                measure_searches(collection, session, queries, vectors)
            )

            sweep_rows = sweep_mongo(collection, queries, vectors)

            neo4j_version = session.run(
                "CALL dbms.components() YIELD versions "
                "RETURN versions[0] AS version"
            ).single()["version"]

        mongo_version = mongo.server_info()["version"]
        report = "\n".join(
            [
                "# Lab 17.2: Cross-Engine HNSW Vector Search",
                "",
                f"Run time (UTC): {datetime.now(timezone.utc).isoformat()}",
                f"Dataset: {COUNT:,} identical normalized vectors | dimensions: {DIM}",
                f"Queries: {QUERY_COUNT} measured per engine, plus {WARMUP_COUNT} warmups",
                f"Top K: {TOP_K} | metric: cosine similarity",
                f"MongoDB version: {mongo_version}",
                f"Neo4j version: {neo4j_version}",
                "",
                "| Engine | Index | Median latency | P95 latency | Mean recall@10 |",
                "|---|---|---:|---:|---:|",
                f"| MongoDB Atlas Local | HNSW (maxEdges=16; numCandidates=100) | "
                f"{statistics.median(mongo_times):.2f} ms | "
                f"{np.percentile(mongo_times, 95):.2f} ms | "
                f"{statistics.mean(mongo_recalls) * 100:.1f}% |",
                f"| Neo4j | HNSW (native vector index defaults) | "
                f"{statistics.median(neo4j_times):.2f} ms | "
                f"{np.percentile(neo4j_times, 95):.2f} ms | "
                f"{statistics.mean(neo4j_recalls) * 100:.1f}% |",
                "",
                "## MongoDB HNSW parameter experiment",
                "",
                "| Index | maxEdges | numEdgeCandidates (build) | numCandidates (query) | Median latency | Mean recall@10 |",
                "|---|---:|---:|---:|---:|---:|",
                *[
                    f"| {name} | {INDEX_PARAMS[name][0]} | {INDEX_PARAMS[name][1]} | "
                    f"{candidates} | {latency:.2f} ms | {recall * 100:.1f}% |"
                    for name, candidates, latency, recall in sweep_rows
                ],
                "",
                (
                    f"Build time of {MONGO_INDEX_WIDE}: {wide_build_seconds:.1f} s for {COUNT:,} vectors."
                    if wide_build_seconds is not None
                    else f"Build time of {MONGO_INDEX_WIDE} was not measured in this run because the index already existed."
                ),
                f"In this run, recall ranged from {min(r[3] for r in sweep_rows) * 100:.1f}% to "
                f"{max(r[3] for r in sweep_rows) * 100:.1f}%, while median latency stayed between "
                f"{min(r[2] for r in sweep_rows):.2f} and {max(r[2] for r in sweep_rows):.2f} ms. "
                f"With only {COUNT:,} vectors, round-trip time is probably most of the latency, "
                "so differences under about 1 ms are probably noise. "
                "maxEdges and numEdgeCandidates are MongoDB's HNSW build settings "
                "(similar to M and efConstruction in other HNSW libraries).",
                "",
                "## Why not IVF?",
                "MongoDB Vector Search indexes use HNSW (the default) or a flat full-scan method; "
                "IVF is not one of its documented index types. IVF exists in Azure Cosmos DB for "
                "MongoDB vCore, which is a different product. So this lab compares HNSW settings "
                "inside MongoDB, and MongoDB HNSW against Neo4j HNSW.",
                "",
                "The vectors are random, which usually makes approximate search harder than real "
                "text embeddings would; recall on real data may be higher (not tested).",
                "",
                "Method: both engines received the same deterministic vector dataset and "
                "query vectors. Exact cosine top-10 from NumPy is used only as the recall "
                "reference, not as a competing search engine. Query latency includes the "
                "client round trip and result transfer; both engines were warmed and query "
                "order was alternated. Engine-specific HNSW implementations and defaults "
                "differ, so timings describe this host and configuration rather than a "
                "hardware-independent ranking.",
                "",
                "The script upserts records in dedicated Lab 17.2 collections/labels and "
                "does not drop collections, delete graph nodes, or reset database volumes.",
            ]
        )
        print("\n" + report)
        report_path = Path(__file__).with_name("vector_benchmark_report.md")
        report_path.write_text(report + "\n", encoding="utf-8")
        print(f"Saved report: {report_path}")
    finally:
        mongo.close()
        neo4j.close()


if __name__ == "__main__":
    main()