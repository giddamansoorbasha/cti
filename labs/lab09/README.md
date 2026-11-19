# Lab 09: Write Concerns & Network Partition Tolerance

## Required Containers
* `cti-mongo1`, `cti-mongo2`, `cti-mongo3`, `cti-mongo4-arbiter` (Replica Set `rs0`)

## Scripts
* `01_write_concern.py`: Benchmarks 1,000 inserts across `w=(1, "majority", 3)` and `j=(False, True)`; saves results to `results.csv`.
* `02_partition.py`: Simulates a network partition by disconnecting secondaries from `replica-set_default`, tests `w=1` vs `w="majority"` under quorum loss, and reconnects nodes with their DNS aliases intact.

## Run from `labs/` (Auto-Start DB & Save to `output.txt`)

    docker start cti-mongo1 cti-mongo2 cti-mongo3 cti-mongo4-arbiter; Start-Sleep -Seconds 5; & { echo "=== 01_write_concern.py ==="; python -u -B lab09\01_write_concern.py; echo "`n=== 02_partition.py ==="; python -u -B lab09\02_partition.py } | Tee-Object -FilePath lab09\output.txt

## Outputs
* `output.txt`
* `results.csv`