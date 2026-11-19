# Lab 04: CRUD Operators, Pagination, Regex Indexing & Bulk Writes

## Required Container
* Standalone MongoDB: `cti-labs1-6` (`localhost:27015`, database `inventory`, collection `products`)

## Overview
Covers `$jsonSchema` validation, comparison/logical/array query operators, cursor pagination, safe case-insensitive regex search with `explain()` index analysis, `$setOnInsert` upserts, and idempotent `bulk_write` operations.

## Activities & Generated Exports
* **Schema Validation, Queries & Pagination** → `output2.json`: Creates a `$jsonSchema`-validated `products` collection, seeds 10 products (SKUs `A`–`J`), demonstrates `$gte`/`$lte`, `$or`/`$and`, `$all`/`$size`, and implements `sort`/`skip`/`limit` pagination.
* **Safe Regex Search & Index Analysis** → `output1.json`: Escapes user input with `re.escape()` for case-insensitive `$regex` searches, indexes `name`, and inspects `explain()` bounds (`["", {})`) to show why case-insensitive regexes still scan the full index.
* **Idempotent Bulk Import** → `output3.json`: Runs `UpdateOne(..., upsert=True)` via `bulk_write` twice on SKUs `K` and `L`, verifying zero duplicates and zero modifications on the second run.
* **Upserts & Mixed Bulk Updates** → `output4.json`: Uses `$setOnInsert` to update existing SKU `A` and insert new SKU `Z` with defaults, then executes 5 simultaneous `UpdateOne` operations (`$inc` stock on `A`–`C`, `$set` `is_active: False` on `D`–`E`).

## Run from `labs/`

    Get-ChildItem lab04\*.py | ForEach-Object { python -u -B $_.FullName }

## Outputs
* `output1.json`
* `output2.json`
* `output3.json`
* `output4.json`