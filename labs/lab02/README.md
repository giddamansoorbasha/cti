# Lab 02: Environment Setup, Server Info Comparison & Bulk Updates

## Required Container & Config
* Standalone MongoDB: `cti-labs1-6` (`localhost:27015`)
* Environment variables (`.env`, optional fallback to `mongodb://localhost:27015/`): `ATLAS_URI`, `DOCKER_URI`

## Overview
Compares MongoDB server metadata between Atlas and local Docker instances, then seeds a `bookstore.books` collection and performs aggregation-pipeline bulk price updates (`$multiply`).

## Operations & Generated Exports
* **Server Comparison** → `output1.json`: Compares `version`, `storageEngine`, `gitVersion`, and `javascriptEngine` between Atlas and Docker.
* **Full Server Info** → `server_info.json`: Captures complete `server_info()` output for both instances.
* **Price Increase (`year < 2010`)** → `books2.json`: Seeds 5 sample books (if empty) and increases prices by 10% for books published before 2010.
* **Price Decrease (`year >= 2015`)** → `output2.json`: Decreases prices by 5% for books published in 2015 or later.

## Run from `labs/`

    Get-ChildItem lab02\*.py | ForEach-Object { python -u -B $_.FullName }

## Outputs
* `output1.json`
* `server_info.json`
* `books2.json`
* `output2.json`