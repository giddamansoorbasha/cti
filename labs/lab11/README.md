# Lab 11: Sharding, Shard Key Selection & Hotspot Analysis

## Required Containers
* Config Servers: `cti-lab11-cfg1`, `cti-lab11-cfg2`, `cti-lab11-cfg3`
* Shards: `cti-lab11-shard1`, `cti-lab11-shard2`
* Router (`mongos` on `localhost:27217`): `cti-lab11-router`

## Shard Key Decision Matrix (E-Commerce Orders)

| Key | Cardinality | Distribution | Query Targeting | Verdict |
|---|---|---|---|---|
| `order_id` | High | Even | Poor: customer queries hit all shards | No |
| `customer_id` | High | Uneven (heavy buyers = jumbo chunks) | Good | Maybe |
| `order_date` | Low per day | Hot-spot: all new orders go to one shard | Good for ranges only | No |
| `hashed customer_id` | High | Even | Good: one customer = one shard | **Yes** |

* **Recommendation:** `hashed customer_id` — spreads writes evenly and targets a single shard for per-customer queries.
* **Trade-off:** Range queries on `customer_id` become scatter-gather across all shards.
* **Resharding (MongoDB 5.0+):** `reshardCollection` copies data into a new layout online, then briefly blocks writes at cutover; requires spare disk and I/O, so run off-peak.

## Scripts
* `01_hotspot.py`: Compares document distribution and query targeting (`explain()`) between a monotonic shard key (`ts: 1`) and a hashed shard key (`user_id: "hashed"`) across 10,000 documents each.

## Run from `labs/` (Auto-Start Cluster & Save to `output.txt`)

    docker start cti-lab11-cfg1 cti-lab11-cfg2 cti-lab11-cfg3 cti-lab11-shard1 cti-lab11-shard2; Start-Sleep -Seconds 5; docker start cti-lab11-router; Start-Sleep -Seconds 5; & { echo "=== 01_hotspot.py ==="; python -u -B lab11\01_hotspot.py } | Tee-Object -FilePath lab11\output.txt

## Outputs
* `output.txt`