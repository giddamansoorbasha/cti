"""Lab 16.2: hybrid query service over MongoDB, Cassandra and Neo4j.

The lab sheet describes a fraud dataset; this project uses the shared threat
dataset seeded by 01_model_and_seed.py, so the three methods are:

  get_threat(threat_id)                  MongoDB    flexible document lookup
  get_platform_threats(platform, status) Cassandra  single-partition read
  detect_threat_ring(threat_id, hops)    Neo4j      multi-hop traversal over shared IOCs

Read-only. Run it directly for the integration demo and latency table.
"""
import os
import statistics
import time

FAILURE_LIMIT = 3      # consecutive failures before a backend is skipped
RETRY_AFTER = 30       # seconds before a skipped backend is tried again


class CircuitBreaker:
    def __init__(self, limit=FAILURE_LIMIT, retry_after=RETRY_AFTER, clock=time.monotonic):
        self.limit, self.retry_after, self.clock = limit, retry_after, clock
        self.failures, self.opened_at = 0, None

    @property
    def available(self):
        if self.opened_at is None:
            return True
        return self.clock() - self.opened_at >= self.retry_after   # half-open: allow one retry

    def call(self, fn, *args):
        if not self.available:
            return None
        try:
            result = fn(*args)
        except Exception:
            self.failures += 1
            if self.failures >= self.limit:
                self.opened_at = self.clock()
            return None
        self.failures, self.opened_at = 0, None
        return result


class ThreatQueryService:
    def __init__(self, mongo_db, cassandra_session, neo4j_driver, clock=time.monotonic):
        self.mongo_db, self.cassandra, self.neo4j = mongo_db, cassandra_session, neo4j_driver
        self.breakers = {name: CircuitBreaker(clock=clock) for name in ("mongo", "cassandra", "neo4j")}

    @classmethod
    def connect(cls):
        """Real connections, each with a bounded pool."""
        from cassandra.cluster import Cluster
        from neo4j import GraphDatabase
        from pymongo import MongoClient

        uri = os.getenv("CTI_MONGO_URI", os.getenv(
            "MONGO_URI", "mongodb://127.0.0.1:27117,127.0.0.1:27118,127.0.0.1:27119/?replicaSet=rs0"))
        mongo = MongoClient(uri, maxPoolSize=10, serverSelectionTimeoutMS=5000)
        cluster = Cluster([os.getenv("CASSANDRA_HOST", "127.0.0.1")],
                          port=int(os.getenv("CASSANDRA_PORT", "9042")), executor_threads=4)
        driver = GraphDatabase.driver(
            os.getenv("NEO4J_URI", "bolt://localhost:7687"),
            auth=(os.getenv("NEO4J_USER", "neo4j"), os.getenv("NEO4J_PASSWORD", "password")),
            max_connection_pool_size=10)
        service = cls(mongo["cti_hybrid"], cluster.connect("cti"), driver)
        service._closers = [mongo.close, cluster.shutdown, driver.close]
        return service

    def close(self):
        for closer in getattr(self, "_closers", []):
            closer()

    # ---- one method per database ----
    def get_threat(self, threat_id):
        return self.breakers["mongo"].call(self._get_threat, threat_id)

    def _get_threat(self, threat_id):
        return self.mongo_db.threats.find_one({"_id": threat_id})

    def get_platform_threats(self, platform, status, limit=10):
        return self.breakers["cassandra"].call(self._get_platform_threats, platform, status, limit)

    def _get_platform_threats(self, platform, status, limit):
        rows = self.cassandra.execute(
            "SELECT id, platform, status, severity FROM threats_by_platform "
            "WHERE platform=%s AND status=%s LIMIT %s", (platform, status, limit))
        return [{"id": r.id, "platform": r.platform, "status": r.status, "severity": r.severity} for r in rows]

    def detect_threat_ring(self, threat_id, max_hops=2):
        return self.breakers["neo4j"].call(self._detect_threat_ring, threat_id, max_hops)

    def _detect_threat_ring(self, threat_id, max_hops):
        hops = max(1, min(int(max_hops), 6))      # Cypher cannot take the hop bound as a parameter
        with self.neo4j.session() as session:
            rows = session.run(
                f"MATCH (t:Threat {{id: $id}})-[:HAS_IOC*1..{hops}]-(other:Threat) "
                "WHERE other.id <> $id RETURN DISTINCT other.id AS id LIMIT 50", id=threat_id)
            return [row["id"] for row in rows]

    # ---- merged workflow ----
    def analyze(self, threat_id, max_hops=2):
        threat = self.get_threat(threat_id)
        peers = self.get_platform_threats(threat["platform"], threat["status"]) if threat else None
        return {
            "threat": threat,
            "same_platform_and_status": peers,
            "ring": self.detect_threat_ring(threat_id, max_hops),
            "unavailable": [name for name, b in self.breakers.items() if not b.available],
        }


def median_ms(fn, runs=10):
    times = []
    for _ in range(runs):
        t0 = time.perf_counter()
        fn()
        times.append((time.perf_counter() - t0) * 1000)
    return statistics.median(times)


if __name__ == "__main__":
    service = ThreatQueryService.connect()
    try:
        sample = service.mongo_db.threats.find_one({}, {"_id": 1})
        if sample is None:
            raise SystemExit("cti_hybrid.threats is empty; run 01_model_and_seed.py first")
        tid = sample["_id"]
        result = service.analyze(tid)
        t = result["threat"]
        print("=== Integration: full analysis of one threat ===")
        print(f"MongoDB   threat   : {t['_id']} | {t['platform']} | {t['status']} | severity {t['severity']} | ioc {t['ioc']}")
        print(f"Cassandra partition: {len(result['same_platform_and_status'])} threats with the same platform and status")
        print(f"Neo4j     ring     : {len(result['ring'])} threats share an IOC with it (max 50 returned)")
        print(f"unavailable        : {result['unavailable'] or 'none'}")

        print("\n=== Latency, median of 10 runs (ms) ===")
        print(f"{'get_threat (MongoDB)':40}{median_ms(lambda: service.get_threat(tid)):>8.2f}")
        print(f"{'get_platform_threats (Cassandra)':40}"
              f"{median_ms(lambda: service.get_platform_threats(t['platform'], t['status'])):>8.2f}")
        for hops in (2, 4):
            print(f"{f'detect_threat_ring, {hops} hops (Neo4j)':40}"
                  f"{median_ms(lambda: service.detect_threat_ring(tid, hops)):>8.2f}")
    finally:
        service.close()
