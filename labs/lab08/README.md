# Lab 08: Replica Set Replication, Failover Monitoring & Priority Elections

## Required Containers
* `cti-mongo1`, `cti-mongo2`, `cti-mongo3`, `cti-mongo4-arbiter` (Replica Set `rs0`)

## Scripts
* `01_replication_check.py`: Inserts a document into `lab8test` and verifies replication across `mongo1`, `mongo2`, and `mongo3`.
* `02_failover_observer.py`: Polls `threats` count and active primary every second (`--ticks 0` for continuous failover testing).
* `03_priority_demo.py`: Reconfigures member priorities (`mongo2=5`, `mongo3=3`, `mongo1=1`) and tests `replSetStepDown` election behavior.

## Run from `labs/` (Auto-Start DB & Save to `output.txt`)

    docker start cti-mongo1 cti-mongo2 cti-mongo3 cti-mongo4-arbiter; Start-Sleep -Seconds 5; & { echo "=== 01_replication_check.py ==="; python -u -B lab08\01_replication_check.py; echo "`n=== 02_failover_observer.py ==="; python -u -B lab08\02_failover_observer.py --ticks 5; echo "`n=== 03_priority_demo.py ==="; python -u -B lab08\03_priority_demo.py } | Tee-Object -FilePath lab08\output.txt

## Outputs
* `output.txt`