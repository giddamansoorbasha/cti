"""Lab 16.2 unit tests: the three database drivers are mocked, so no database is needed."""
import importlib.util
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

spec = importlib.util.spec_from_file_location("query_service", Path(__file__).with_name("02_query_service.py"))
qs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(qs)

THREAT = {"_id": "t1", "platform": "Linux", "status": "Active", "severity": 7, "ioc": "192.168.1.5"}


class FakeClock:
    now = 0.0

    def __call__(self):
        return self.now


def make_service(clock=None):
    mongo_db, cassandra, neo4j = MagicMock(), MagicMock(), MagicMock()
    mongo_db.threats.find_one.return_value = THREAT
    cassandra.execute.return_value = [SimpleNamespace(id="t2", platform="Linux", status="Active", severity=4)]
    session = neo4j.session.return_value.__enter__.return_value
    session.run.return_value = [{"id": "t3"}, {"id": "t4"}]
    return qs.ThreatQueryService(mongo_db, cassandra, neo4j, clock=clock or FakeClock())


class ThreatQueryServiceTest(unittest.TestCase):
    def test_get_threat_reads_mongodb_by_id(self):
        service = make_service()
        self.assertEqual(service.get_threat("t1"), THREAT)
        service.mongo_db.threats.find_one.assert_called_once_with({"_id": "t1"})

    def test_get_platform_threats_queries_one_cassandra_partition(self):
        service = make_service()
        rows = service.get_platform_threats("Linux", "Active", limit=5)
        self.assertEqual(rows, [{"id": "t2", "platform": "Linux", "status": "Active", "severity": 4}])
        cql, params = service.cassandra.execute.call_args.args
        self.assertIn("WHERE platform=%s AND status=%s", cql)
        self.assertEqual(params, ("Linux", "Active", 5))

    def test_detect_threat_ring_uses_hop_limit(self):
        service = make_service()
        self.assertEqual(service.detect_threat_ring("t1", max_hops=4), ["t3", "t4"])
        session = service.neo4j.session.return_value.__enter__.return_value
        self.assertIn("[:HAS_IOC*1..4]", session.run.call_args.args[0])
        self.assertEqual(session.run.call_args.kwargs, {"id": "t1"})

    def test_analyze_merges_all_three_databases(self):
        result = make_service().analyze("t1")
        self.assertEqual(result["threat"], THREAT)
        self.assertEqual(result["same_platform_and_status"][0]["id"], "t2")
        self.assertEqual(result["ring"], ["t3", "t4"])
        self.assertEqual(result["unavailable"], [])

    def test_breaker_opens_after_three_failures_and_skips_the_backend(self):
        service = make_service()
        service.neo4j.session.side_effect = ConnectionError("neo4j down")
        for _ in range(3):
            self.assertIsNone(service.detect_threat_ring("t1"))
        self.assertEqual(service.neo4j.session.call_count, 3)
        self.assertIsNone(service.detect_threat_ring("t1"))          # skipped, driver not called
        self.assertEqual(service.neo4j.session.call_count, 3)
        result = service.analyze("t1")                                # other backends still answer
        self.assertEqual(result["threat"], THREAT)
        self.assertEqual(result["unavailable"], ["neo4j"])

    def test_breaker_retries_after_30_seconds_and_recovers(self):
        clock = FakeClock()
        service = make_service(clock)
        service.cassandra.execute.side_effect = ConnectionError("cassandra down")
        for _ in range(3):
            service.get_platform_threats("Linux", "Active")
        self.assertFalse(service.breakers["cassandra"].available)
        clock.now = 29
        self.assertFalse(service.breakers["cassandra"].available)
        clock.now = 31
        service.cassandra.execute.side_effect = None
        self.assertEqual(len(service.get_platform_threats("Linux", "Active")), 1)
        self.assertTrue(service.breakers["cassandra"].available)
        self.assertEqual(service.breakers["cassandra"].failures, 0)

    def test_success_resets_the_failure_count(self):
        service = make_service()
        service.mongo_db.threats.find_one.side_effect = [ConnectionError(), ConnectionError(), THREAT]
        service.get_threat("t1"); service.get_threat("t1")
        self.assertEqual(service.get_threat("t1"), THREAT)
        self.assertEqual(service.breakers["mongo"].failures, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
