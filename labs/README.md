# Labs 1 to 18: Guide & Index

Run commands from the project root (the folder with `docker-compose.yml`) or `labs/` in PowerShell.
Each lab folder (`lab01/`–`lab18/`) has its own `README.md` with exact commands and saved outputs (`output.txt` or `.json` files). Results for Labs 7–18 are also served at <http://localhost:8000/lab-results>.

## One-Time Setup

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
```

Ensure the Windows hosts file contains `127.0.0.1 mongo1 mongo2 mongo3 mongo4`.

Start the main stack (replica set `rs0`, Atlas Local, Cassandra, Neo4j, and the app):

```powershell
docker compose --profile app --profile vector --profile graph --profile tls up -d
```

> **Thermal / RAM tip:** Stop unused containers between labs (`docker stop $(docker ps -q)`) and start only the containers listed in each lab's `README.md`.

## Where Each Lab Runs

- **Host** = local Windows `.venv`: `python -u -B labs\labNN\script.py` (uses `pyasyncore` for `cassandra-driver` on Python 3.12+).
- **Container** = inside the app container (optional for Labs 13 and 15–18): `docker exec cti-platform-app python /app/labs/labNN/script.py`.
  After editing a script, rebuild the app container if running inside Docker:
  `docker compose --profile app --profile vector --profile tls up -d --build app`

## Labs 1 to 6 (Standalone MongoDB — `cti-labs1-6` on `localhost:27015`)

| Lab | Topic | Key Files | Details |
|---|---|---|---|
| 01 | NoSQL Classification & Family Mapping | 4 scripts + `.json` exports | [lab01/README.md](lab01/README.md) |
| 02 | Environment Setup, Server Info & Bulk Updates | 4 scripts + `.json` exports | [lab02/README.md](lab02/README.md) |
| 03 | Schema Design (Embedding vs. Referencing & `$jsonSchema`) | 4 scripts + `output.json` | [lab03/README.md](lab03/README.md) |
| 04 | CRUD Operators, Pagination, Regex Indexing & Bulk Writes | 4 scripts + `output1–4.json` | [lab04/README.md](lab04/README.md) |
| 05 | Aggregation Framework (`$group`, `$bucket`, `$lookup`) | 4 scripts | [lab05/README.md](lab05/README.md) |
| 06 | Indexing Strategies, `$indexStats`, Write Overhead & Covered Queries | 4 scripts | [lab06/README.md](lab06/README.md) |

## Labs 7 to 18 (CTI Platform, Sharding, Security, Polyglot & Vector Search)

| Lab | Script | Runs on | Needs | Changes data? |
|---|---|---|---|---|
| 7.1 | `lab07/01_lab71_analyze.py` | Host | `rs0` with ingested threats | Rebuilds scratch `threats_embedded` |
| 7.2 | `lab07/02_lab72_generate.py` | Host | `rs0` | Recreates `reports_test` (100,000 docs) |
| 7.2 | `lab07/03_lab72_reads.py` | Host | `reports_test` from generate step | No |
| 7.2 | `lab07/04_lab72_monitor.py --ticks 6` | Host | `rs0`, internet for GitHub list | Adds new entries to `annual_reports` |
| 8.1 | `lab08/01_replication_check.py` | Host | `rs0` | Inserts one test document |
| 8.2 | `lab08/02_failover_observer.py` | Host | `rs0` | No (runs until Ctrl+C) |
| 8.2 | `lab08/03_priority_demo.py` | Host | `rs0` | **Changes member priorities and steps down primary** |
| 9.1 | `lab09/01_write_concern.py` | Host | `rs0` | Recreates scratch `lab9_wc`, rewrites `results.csv` |
| 9.2 | `lab09/02_partition.py` | Host | `rs0`, Docker CLI | **Disconnects two members ~1 min, then reconnects** |
| 10.1 | `lab10/01_transfer.py` | Host | `rs0` | Recreates scratch `accounts`, `transfer_history` |
| 10.2 | `lab10/02_inventory.py` | Host | `rs0` | Recreates scratch `inventory`, `orders` |
| 11.1 | `lab11/01_shard_key_matrix.md` | (document) | — | — |
| 11.2 | `lab11/02_hotspot.py` | Host | Sharding stack (below) | Recreates database `lab11` on sharded cluster |
| 12.1 | `lab12/01_rbac_views.py` | Host | Auth/TLS stack (below) | Recreates database `cti_auth` on `mongo-auth` |
| 12.2 | `lab12/02_tls_test.py` | Host | Auth/TLS stack, certificates | Inserts one test document |
| 13.1 | `lab13/01_failover_auth.py` | Host or Container | keyFile stack (below) | Inserts test documents (runs until Ctrl+C) |
| 13.2 | `docker/k8s/mongo.yaml` | `kubectl` | Kubernetes in Docker Desktop | See main README |
| 14.1 | `lab14/01_monitor.py --once` | Host | `rs0` | Appends to `metrics.log` |
| 14.2 | `lab14/02_backup_verify.py verify` | Host | `rs0`, Docker CLI | Recreates scratch `backup_test`, adds backup folder |
| 14.2 | `lab14/02_backup_verify.py benchmark` | Host | `rs0`, Docker CLI | Same, at 1,000 / 10,000 / 100,000 docs |
| 15.1 | `lab15/01_seed.py` | Host or Container | `rs0` | **Deletes all users and tasks, then reseeds** |
| 15.1 | `lab15/02_test_api.py` | Host or Container | Seeded users, app running | Creates and deletes one task |
| 15.2 | `lab15/03_migrate.py` | Host or Container | Seeded tasks | Recreates `tasks_tenant_*` copies |
| 16.1 | `lab16/01_model_and_seed.py` | Host or Container | `rs0`, Cassandra, Neo4j | **Clears and reseeds shared threats (`THREAT_COUNT`, default `10,000`)** |
| 16.2 | `lab16/02_query_service.py` | Host or Container | Lab 16 data | No |
| 16.2 | `lab16/03_test_query_service.py` | Host or Container | Nothing (drivers mocked) | No |
| 17.1 | `lab17/01_rag_pipeline.py` | Host or Container | Atlas Local (`27777` + auth), Ollama | Upserts labeled chunks |
| 17.2 | `lab17/02_hnsw_vs_ivf.py` | Host or Container | Atlas Local (`27777` + auth), Neo4j | Upserts 5,000 benchmark vectors |
| 18.1 | `lab18/01_benchmark.py` | Host or Container | Lab 16 data | Inserts and removes its own benchmark rows |
| 18.1 | `lab18/02_communities.py` | Host or Container | Lab 16 data | No |

## Extra Stacks

These do not restart on their own after a reboot.

```powershell
# Lab 11: sharded cluster on localhost:27217
$s = "docker\sharding\docker-compose.yml"
docker compose -f $s up -d cfg1 cfg2 cfg3 shard1 shard2
docker compose -f $s --profile init run --rm bootstrap
docker compose -f $s up -d router
docker compose -f $s --profile init run --rm register
```

If the router shows `unhealthy` (started while config servers were stopped), run `docker restart cti-lab11-router`.

```powershell
# Lab 12: auth server on localhost:27200, TLS server on localhost:27201
python -B docker\tls\gen_certs.py      # only if docker\tls\certs is empty
docker compose -f docker\tls\docker-compose.yml up -d
```

```powershell
# Lab 13.1: keyFile replica set rs1 (prod1, prod2, prod3) with Prometheus exporter on localhost:9216
docker compose -f docker\replica-set\docker-compose.prod.yml up -d
```

First-time initialization of `rs1` and the Kubernetes steps for Lab 13.2 are in the main project README.

## Container Names

Every container starts with `cti-`, and the name states its role.

| Container | Used by | Purpose |
|---|---|---|
| `cti-platform-app` | project, Labs 15 to 18 | FastAPI app |
| `cti-mongo1`, `cti-mongo2`, `cti-mongo3` | project, Labs 7 to 10, 14–16, 18 | Replica set `rs0` (primary data) |
| `cti-mongo4-arbiter` | Lab 8 | Votes in elections, stores no data |
| `cti-atlas-local` | project chat, Lab 17 | Vector search (`27777`, auth enabled) |
| `cti-https-proxy` | project | HTTPS on port `8443` |
| `cti-replica-init` | project | Initializes `rs0` once, then exits |
| `cti-cassandra`, `cti-neo4j` | Labs 16 to 18 | Wide-column & graph databases |
| `cti-lab11-cfg1..3`, `cti-lab11-shard1..2`, `cti-lab11-router` | Lab 11 | Sharded cluster |
| `cti-lab12-auth`, `cti-lab12-tls` | Lab 12 | Auth and TLS servers |
| `cti-lab13-prod1..3`, `cti-lab13-exporter` | Lab 13 | keyFile replica set and metrics |
| `cti-labs1-6` | Labs 1 to 6 | Standalone MongoDB on port `27015` |

Inside Docker, databases still answer to their short service names (`mongo1`, `prod1`, `cfg1`), so internal connection strings do not change.

## Shared Code

Lab scripts import the MongoDB connection from `backend/common.py` and the monitoring snapshot from `backend/monitor.py`. Lab 7 keeps its own helpers (cache counters, GitHub report list) in `labs/lab07/helpers.py`.

The lab results page consists of `backend/lab_results.py`, `frontend/lab-results.html`, and two lines in `backend/main.py` (the router include and the `/lab-results` route). Delete those to remove the page from the app.