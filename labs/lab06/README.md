# Lab 06: Indexing Strategies, `$indexStats`, Write Overhead & Covered Queries

## Required Container
* Standalone MongoDB: `cti-labs1-6` (`127.0.0.1:27015`, database `index_lab`)

## Overview
Evaluates single-field, compound, and multikey indexes on 50,000 documents using `explain()`, tracks index utilization with `$indexStats`, benchmarks insert slowdown caused by secondary indexes, and verifies zero-`FETCH` covered queries.

## Activities
* **Index Design & `explain()` Comparison (`products`)**: Seeds 50,000 products, runs `explain()` on 5 queries (category + price sort, price range, tag lookup, anchored name regex, rating range + sort) before indexing, creates 5 indexes (`category_price_idx`, `price_idx`, `tags_idx`, `name_idx`, `rating_idx`), and compares `totalDocsExamined` and `totalKeysExamined` after indexing.
* **Index Usage Tracking (`products`)**: Executes the 5 queries 10 times each and runs `$indexStats` to inspect per-index operation counts (`accesses.ops`).
* **Insert Overhead & Index Pruning (`products_benchmark`)**: Benchmarks inserting 10,000 products with only `_id_` versus with 5 secondary indexes, calculates the write slowdown percentage, drops all non-critical indexes except `category_price_idx`, and re-evaluates query plans.
* **Covered Query Verification (`products_covered`)**: Seeds 10,000 products, creates compound index `covered_query_idx` on `(category, price, name)`, executes a projected query excluding `_id`, and verifies via `explain()` that `totalDocsExamined` is `0` and the `FETCH` stage is eliminated.

## Run from `labs/`

    Get-ChildItem lab06\*.py | ForEach-Object { python -u -B $_.FullName }