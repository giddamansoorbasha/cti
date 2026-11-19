# Lab 03: Schema Design — Embedding vs. Referencing & JSON Schema Validation

## Required Container
* Standalone MongoDB: `cti-labs1-6` (`localhost:27015`, databases `university` and `blogsystem`)

## Overview
Demonstrates MongoDB schema design patterns: enforcing `$jsonSchema` validation, embedding bounded arrays (rosters, schedules, prerequisites), referencing unbounded relationships with `$lookup`, migrating referenced data to embedded documents via `$out`, and analyzing the 16 MB document size limit.

## Activities
* **University Courses & Schema Validation (`university.courses`)**: Creates a `$jsonSchema`-validated `courses` collection with embedded `schedule` and `roster`, inserts 3 courses, and queries Monday courses and students enrolled under `Dr. Sharma`.
* **Course Prerequisites (`university.courses`)**: Embeds a bounded `prerequisites` array of course codes into each course document and documents the design justification for embedding over referencing.
* **Blog System — Referenced vs. Embedded (`blogsystem`)**: Seeds 5 `posts` and 10 referenced `comments`, joins them in one query using `$lookup`, migrates them into `posts_embedded` using `$out`, and compares query counts.
* **Unbounded Array Analysis (`blogsystem`)**: Simulates a post with 10,000 embedded comments, measures its approximate size against MongoDB's 16 MB document cap, and recommends the extended-reference / hybrid pattern.

## Run from `labs/`

    Get-ChildItem lab03\*.py | ForEach-Object { python -u -B $_.FullName }

## Outputs
* `output.json`