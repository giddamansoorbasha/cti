# Lab 07: Document Size, Embedding vs Referencing & WiredTiger Cache

## Required Containers
* `cti-mongo1`, `cti-mongo2`, `cti-mongo3`, `cti-mongo4-arbiter` (Replica Set `rs0`)

## Scripts
* `01_lab71_analyze.py`: Checks BSON document sizes against the 16 MB limit, benchmarks referenced (`$lookup`) vs embedded reads/updates, and tests unbounded IOC array growth.
* `02_lab72_generate.py`: Inserts 100,000 synthetic 2 KB documents into `reports_test` and indexes `seq`.
* `03_lab72_reads.py`: Measures WiredTiger cache hit ratio, range reads, and 150,000 random reads; saves metrics to `data/lab72_random_reads.csv`.
* `04_lab72_monitor.py`: Polls WiredTiger cache metrics every 10s and syncs new GitHub security reports into `annual_reports`; logs to `data/lab72_monitor.csv`.

## Run from `labs/` (Auto-Start DB & Save to `output.txt`)

    docker start cti-mongo1 cti-mongo2 cti-mongo3 cti-mongo4-arbiter; Start-Sleep -Seconds 5; & { echo "=== 01_lab71_analyze.py ==="; python -u -B lab07\01_lab71_analyze.py; echo "`n=== 02_lab72_generate.py ==="; python -u -B lab07\02_lab72_generate.py; echo "`n=== 03_lab72_reads.py ==="; python -u -B lab07\03_lab72_reads.py; echo "`n=== 04_lab72_monitor.py ==="; python -u -B lab07\04_lab72_monitor.py --ticks 2 } | Tee-Object -FilePath lab07\output.txt

## Outputs
* `output.txt`
* `data/lab72_random_reads.csv`
* `data/lab72_monitor.csv`