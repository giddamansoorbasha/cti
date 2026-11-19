# Lab 05: Aggregation Framework — Grouping, Bucketing & `$lookup` Joins

## Required Container
* Standalone MongoDB: `cti-labs1-6` (`127.0.0.1:27015`, database `sales_analytics`)

## Overview
Demonstrates multi-stage MongoDB aggregation pipelines for sales analytics, value-range bucketing, basic cross-collection joins, and correlated subquery lookups.

## Activities
* **Sales Analytics (`sales_orders`)**: Seeds 12 dated orders and runs three pipelines—monthly revenue (`$dateToString` + `$multiply`), top 3 customers by total spending (`$sort` + `$limit`), and average order value by order status (`$addFields` + `$avg`).
* **Order Value Bucketing (`bucket_orders`)**: Computes `order_value` and groups 10 orders into `Small` (`0`–`50`), `Medium` (`50`–`200.01`), and `Large` (`200.01+`) tiers using `$bucket` and `$switch`.
* **Cross-Collection `$lookup` (`lookup_products`, `lookup_orders`)**: Joins orders with product details (`$lookup` + `$unwind` + `$project`) to compute `total_price`, and identifies products that were never ordered (`order_details == []`).
* **Correlated Pipeline `$lookup` (`pipeline_products`, `pipeline_orders`)**: Uses `$lookup` with `let`, `pipeline`, and `$expr` to return only products that have orders with `quantity >= 2`.

## Run from `labs/`

    Get-ChildItem lab05\*.py | ForEach-Object { python -u -B $_.FullName }