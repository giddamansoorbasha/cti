# Lab 10: Multi-Document ACID Transactions & Concurrency Control

## Required Containers
* `cti-mongo1`, `cti-mongo2`, `cti-mongo3`, `cti-mongo4-arbiter` (Replica Set `rs0`)

## Scripts
* `01_transfer.py`: Demonstrates atomic account transfers across `accounts` and `transfer_history` with automatic rollback on insufficient funds and retry on `TransientTransactionError`.
* `02_inventory.py`: Tests concurrent stock reservations (8 threads vs 5 items) and benchmarks multi-document transaction throughput against single-document `find_one_and_update`.

## Run from `labs/` (Auto-Start DB & Save to `output.txt`)

    docker start cti-mongo1 cti-mongo2 cti-mongo3 cti-mongo4-arbiter; Start-Sleep -Seconds 5; & { echo "=== 01_transfer.py ==="; python -u -B lab10\01_transfer.py; echo "`n=== 02_inventory.py ==="; python -u -B lab10\02_inventory.py } | Tee-Object -FilePath lab10\output.txt

## Outputs
* `output.txt`