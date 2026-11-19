# Lab 12: Role-Based Access Control (RBAC), Views & Mutual TLS

## Required Containers
* `cti-lab12-auth` (MongoDB with authentication on `localhost:27200`)
* `cti-lab12-tls` (MongoDB with mutual TLS on `localhost:27201`)

## Scripts
* `01_rbac_views.py`: Creates custom roles (`reader_role`, `writer_role`, `hr_role`), a redacted view (`staff_public` hiding `salary`), and verifies least-privilege access per user.
* `02_tls_test.py`: Verifies plain connections are rejected on the TLS port, connects using client/CA certificates (`lab12/certs/`), and prints the X.509 certificate chain.

## Run from `labs/` (Auto-Start DB & Save to `output.txt`)

    docker start cti-lab12-auth cti-lab12-tls; Start-Sleep -Seconds 5; & { echo "=== 01_rbac_views.py ==="; python -u -B lab12\01_rbac_views.py; echo "`n=== 02_tls_test.py ==="; python -u -B lab12\02_tls_test.py } | Tee-Object -FilePath lab12\output.txt

## Outputs
* `output.txt`