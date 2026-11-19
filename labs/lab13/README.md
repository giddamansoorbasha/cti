# Lab 13: Production Keyfile Replica Set & Failover Testing

## Required Containers
* Replica Set `rs1` (Keyfile Auth): `cti-lab13-prod1` (`27317`), `cti-lab13-prod2` (`27318`), `cti-lab13-prod3` (`27319`)
* Metrics Exporter: `cti-lab13-exporter` (`9216`)

## Prerequisites
* Windows `hosts` entry mapping `127.0.0.1 prod1 prod2 prod3`.

## Scripts
* `01_failover_test.py`: Inserts timestamped documents into `cti.failover_test` on the keyfile-authenticated `rs1` replica set and logs the active primary (`--ticks 5` for verification, `--ticks 0` for continuous live failover testing).

## Run from `labs/` (Auto-Start Cluster & Save to `output.txt`)

    docker start cti-lab13-prod1 cti-lab13-prod2 cti-lab13-prod3 cti-lab13-exporter; Start-Sleep -Seconds 8; & { echo "=== 01_failover_test.py ==="; python -u -B lab13\01_failover_test.py --ticks 5 } | Tee-Object -FilePath lab13\output.txt

## Outputs
* `output.txt`