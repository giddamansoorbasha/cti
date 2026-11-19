# Lab 01: NoSQL Database Classification & Polyglot Family Mapping

## Required Container
* Standalone MongoDB: `cti-labs1-6` (`localhost:27015`, database `nosql_exercise`)

## Overview
Classifies major NoSQL products across the four core data models (Key-Value, Document, Column-Family, Graph) plus multi-model/time-series engines, and maps real-world application domains to their optimal NoSQL families.

## Collections & Generated Exports
* `db_classification` → `db_classification.json`: Classifies Amazon S3, Couchbase, Apache HBase, Amazon Neptune, and Memcached with reasoning, best-use cases, and limitations.
* `db_classification_tryit` → `db_classification_tryit.json`: Classifies ScyllaDB, InfluxDB, and ArangoDB, noting which engines span multiple NoSQL families.
* `app_family_mapping` → `app_family_mapping.json`: Maps Ride-sharing (driver locations, user profiles, ride history, relationship graph) and Social Media Analytics (raw posts, real-time trending) to NoSQL families.
* `healthcare_family_mapping` → `healthcare_family_mapping.json`: Maps Hospital Patient Management domains (live vitals, medical records, lab history, referral network) to NoSQL families.

## Run from `labs/`

    Get-ChildItem lab01\*.py | ForEach-Object { python -u -B $_.FullName }

## Outputs
* `db_classification.json`
* `db_classification_tryit.json`
* `app_family_mapping.json`
* `healthcare_family_mapping.json`