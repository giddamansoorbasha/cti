# Lab 15: Multi-Tenant SaaS Isolation, RBAC, Rate Limiting & Collection Migration

## Required Containers
* Replica Set `rs0`: `cti-mongo1` (`27117`), `cti-mongo2` (`27118`), `cti-mongo3` (`27119`)

## Scripts
* `saas.py`: Self-contained FastAPI service implementing HMAC-signed bearer tokens, tenant isolation, role-based access (`admin` vs `user`), and 30 req/min per-user rate limiting.
* `01_seed.py`: Creates indexes and seeds 5 tenants (`windows`, `linux`, `macos`, `android`, `ios`) with 10 users and 500 tasks.
* `02_test_api.py`: Verifies tenant isolation, cross-tenant delete rejection (`404`), owner delete (`200`), and rate limiting (`429`).
* `03_migrate.py`: Migrates shared `tasks` into per-tenant `tasks_tenant_<name>` collections, checks for cross-tenant leaks, and benchmarks single-collection vs. per-tenant queries.
* `common.py`: Shared MongoDB connection (`rs0`).

## Run from `labs/` (Auto-Start API & Save to `output.txt`)

    $srv = Start-Process python -ArgumentList "-m", "uvicorn", "saas:app", "--app-dir", "lab15", "--host", "127.0.0.1", "--port", "8000" -PassThru -WindowStyle Hidden; Start-Sleep -Seconds 3; try { & { echo "=== 01_seed.py ==="; python -u -B lab15\01_seed.py; echo "`n=== 02_test_api.py ==="; python -u -B lab15\02_test_api.py; echo "`n=== 03_migrate.py ==="; python -u -B lab15\03_migrate.py } | Tee-Object -FilePath lab15\output.txt } finally { Stop-Process -Id $srv.Id -Force -ErrorAction SilentlyContinue }

## Benchmark Summary (Median ms, 20 runs)
| Operation | One Collection | Per Tenant |
|---|---:|---:|
| List one tenant | 1.34 ms | 1.02 ms |
| Create one task | 5.77 ms | 5.48 ms |
| Cross-tenant analytics | 1.22 ms | 3.71 ms |

## Outputs
* `output.txt`