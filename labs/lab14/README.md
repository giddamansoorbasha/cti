# Lab 14: Cluster Monitoring, Alerting & Backup/Restore Verification

## Required Containers
* Replica Set `rs0`: `cti-mongo1` (`27117`), `cti-mongo2` (`27118`), `cti-mongo3` (`27119`), `cti-mongo4` (`27120`, arbiter)

## Scripts
* `01_monitor.py`: Captures replica set health (connections, WiredTiger cache hit ratio, opcounters, member replication lag), appends to `metrics.log`, and triggers threshold warnings.
* `02_backup_verify.py`: Automates `mongodump`/`mongorestore` via `cti-mongo1`, verifies restore integrity (`verify`), benchmarks 1k–100k docs (`benchmark`), and enforces 7-day cleanup (`retention`).
* `common.py`: Shared MongoDB connection (`rs0`) and WiredTiger cache metric keys.

## Run from `labs/` (Auto-Start DB & Save to `output.txt`)

    docker start cti-mongo1 cti-mongo2 cti-mongo3; Start-Sleep -Seconds 5; & { echo "=== 01_monitor.py --once ==="; python -u -B lab14\01_monitor.py --once; echo "`n=== 02_backup_verify.py verify ==="; python -u -B lab14\02_backup_verify.py verify; echo "`n=== 02_backup_verify.py benchmark ==="; python -u -B lab14\02_backup_verify.py benchmark; echo "`n=== 02_backup_verify.py retention ==="; python -u -B lab14\02_backup_verify.py retention } | Tee-Object -FilePath lab14\output.txt

## Backup & Restore Benchmark
| Documents | Backup (s) | Restore (s) |
|---:|---:|---:|
| 1,000 | 0.2 | 0.3 |
| 10,000 | 0.2 | 0.3 |
| 100,000 | 0.6 | 4.2 |

* **RPO:** Backup interval (1 hour).
* **RTO:** Restore time + app restart time.

## Outputs
* `output.txt`
* `metrics.log`