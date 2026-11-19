# Lab 16: Polyglot Persistence — Hybrid Query Service (MongoDB + Cassandra + Neo4j)

## Required Containers
* Replica Set `rs0`: `cti-mongo1` (`27117`), `cti-mongo2` (`27118`), `cti-mongo3` (`27119`)
* Cassandra: `cti-cassandra` (`9042`)
* Neo4j: `cti-neo4j` (`7474`, `7687`, auth `neo4j/password`)

## Prerequisites
* Python packages: `pymongo`, `cassandra-driver`, `pyasyncore` (Python 3.12+), `neo4j`.

## Scripts
* `01_model_and_seed.py`: Seeds shared threat records (`THREAT_COUNT`, default `10,000`) into MongoDB (`cti_hybrid.threats`), Cassandra (`cti.threats_by_platform`, `cti.threat_by_id`), and Neo4j (`Threat`, `Platform`, `IOC` graph).
* `02_query_service.py`: Implements `ThreatQueryService` with per-backend `CircuitBreaker` protection, merges document/partition/graph lookups (`analyze`), and benchmarks median query latency.
* `03_test_query_service.py`: Mocked unit test suite (7 tests) verifying query routing, circuit breaker tripping, 30s half-open recovery, and failure reset.

## Run from `labs/` (Save to `output.txt`)

    & { echo "=== 01_model_and_seed.py ==="; python -u -B lab16\01_model_and_seed.py; echo "`n=== 02_query_service.py ==="; python -u -B lab16\02_query_service.py; echo "`n=== 03_test_query_service.py ==="; python -u -B lab16\03_test_query_service.py 2>&1 | ForEach-Object { "$_" } } | Tee-Object -FilePath lab16\output.txt

## Latency Summary (Median of 10 runs)
| Query | Backend | Median Latency |
|---|---|---:|
| `get_threat` | MongoDB | 1.34 ms |
| `get_platform_threats` | Cassandra | 12.25 ms |
| `detect_threat_ring` (2 hops) | Neo4j | 7.97 ms |
| `detect_threat_ring` (4 hops) | Neo4j | 7.25 ms |

## Outputs
* `output.txt`