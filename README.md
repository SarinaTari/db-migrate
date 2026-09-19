# db-migrate

A Python-based database migration and schema-evolution CLI focused on safety, integrity, explainability, and migration analysis.

## Current Status

The project is under active development.

Completed phases:

- Phase 0 — Database Migration Concepts
- Phase 1 — Professional Python Project
- Phase 2 — CLI Foundation
- Phase 3 — Configuration
- Phase 4 — Migration Format
- Phase 5 — Discovery and Validation
- Phase 6 — Database Interface + SQLite

Current capabilities include:

- project configuration
- migration file parsing
- migration discovery
- migration validation
- SQLite database connectivity
- SQLite SQL execution
- transaction handling
- database connectivity checks

Migration execution and migration history are intentionally not implemented yet.

## Example Migration

```sql
-- migration: 001
-- name: create_users

-- +up

CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);

-- +down

DROP TABLE users;
Configuration

Create dbmigrate.toml:

[migrations]
directory = "migrations"

[database]
url = "sqlite:///dbmigrate.db"
Database Check

Run:

dbmigrate check
Testing

Run:

pytest
Roadmap
Database Migration Concepts
Professional Python Project
CLI Foundation
Configuration
Migration Format
Discovery and Validation
Database Interface + SQLite
Migration History
Migration Runner
Transaction and Failure Semantics
Down/Rollback
Status/History/Current
Create Command
Validation
Checksums
Dry Run and Planning
Migration Linter
Explain and Impact
Schema Inspection/Fingerprints
Schema Diff/Reproducibility
Database Abstraction Review
PostgreSQL
MySQL
SQL Dialect/Capability System
Locking/Concurrency
Safety and Doctor
CI Mode
Logging
Performance
Full Integration Testing
Architecture Review
Documentation
Example Project
Portfolio Finalization