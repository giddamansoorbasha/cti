# Lab 18: Cross-Database Benchmark & Graph-Document Community Detection

## Required Containers
* Replica Set `rs0`: `cti-mongo1` (`27117`), `cti-mongo2` (`27118`), `cti-mongo3` (`27119`)
* Cassandra: `cti-cassandra` (`9042`)
* Neo4j: `cti-neo4j` (`7474`, `7687`, auth `neo4j/password`)

## Prerequisites
* Dataset seeded by Lab 16 (`10,000` shared threats across MongoDB `cti_hybrid.threats`, Cassandra `cti`, and Neo4j).

## Scripts
* `01_benchmark.py`: Syncs a 30-day `day` field across all three databases and benchmarks 6 workloads (ID lookup, platform+status filter, shared-IOC spread, platform target, 7-day volume, and 500-row insert throughput) over 10 median runs.
* `02_communities.py`: Groups threats by shared IOC in Neo4j, flags statistical outliers (`size > mean + 2 * sd`), and cross-references the top 5 flagged communities against MongoDB for severity, unresolved count, and top platform.

## Run from `labs/` (Save to `output.txt`)

    & { echo "=== 01_benchmark.py ==="; python -u -B lab18\01_benchmark.py; echo "`n=== 02_communities.py ==="; python -u -B lab18\02_communities.py } | Tee-Object -FilePath lab18\output.txt

## Benchmark Summary (10,000 Threats, Median of 10 Runs)
| Query | MongoDB | Cassandra | Neo4j | Fastest |
|---|---:|---:|---:|---|
| Q1: Lookup by ID | 1.03 ms | 13.12 ms | N/A | MongoDB |
| Q2: Platform + status | 1.73 ms | 12.43 ms | N/A | MongoDB |
| Q3: Threats sharing an IOC | 1.02 ms | N/A | 7.05 ms | MongoDB |
| Q4: Threats by platform | 1.78 ms | N/A | 10.59 ms | MongoDB |
| Q5: Daily volume (7 days) | 3.15 ms | 122.36 ms | 11.14 ms | MongoDB |
| Q6: Insert throughput | 17,723.28 /s | 2,639.16 /s | 4,081.74 /s | MongoDB |

## Outputs
* `output.txt`