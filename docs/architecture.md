# Architecture

## Overview

`db-migrate` is a layered database migration and schema-evolution system.

The architecture separates:

- command-line interaction
- configuration
- migration discovery
- parsing
- validation
- execution
- database access
- analysis

---

## Current Architecture

At Phase 5:

```text
CLI
 │
 ↓
Command Layer
 │
 ├── Configuration
 │
 └── Validation
       │
       ↓
Migration Discovery
       │
       ↓
Migration Parser
       │
       ↓
Migration Domain Model

The database execution layer has not yet been introduced.

Planned Architecture
CLI
 │
 ↓
Command Layer
 │
 ↓
Migration Service
 │
 ├── Discovery
 ├── Parsing
 ├── Validation
 └── Planning
 │
 ↓
Execution
 │
 ↓
History / Integrity
 │
 ↓
Database Interface
 │
 ├── SQLite
 ├── PostgreSQL
 └── MySQL

Analysis components will eventually include:

Analysis
├── Linter
├── Explainer
└── Impact Analyzer

Schema
├── Inspector
├── Diff
├── Fingerprint
└── Reproducibility
Design Principles
Separation of responsibilities

The CLI should coordinate operations rather than contain business logic.

The parser should not connect to databases.

Validation should not execute SQL.

Database implementations should not parse command-line arguments.

Explicit failure

Invalid migrations should fail clearly.

The tool should prefer explicit errors over silent behavior.

Deterministic behavior

Migration discovery and ordering must be deterministic.

Version numbers define migration order.

Database independence

The migration service should remain independent from the database backend.

SQLite will be implemented first.

PostgreSQL and MySQL will be added later.

Safety

The future execution system will prioritize:

validation
planning
transactions
checksums
locking
integrity checks
Current Modules
cli.py

Handles:

argument parsing
command resolution
command dispatch
validation output
config.py

Handles:

project discovery
configuration loading
configuration validation
migration.py

Handles:

migration model
filename parsing
metadata parsing
section parsing
migration discovery
validation.py

Handles:

project-level validation
migration sequence checks
duplicate-name checks
validation reports
commands/base.py

Contains command metadata and the command registry.

Future Modules

Expected future components include:

database/
    base.py
    sqlite.py
    postgres.py
    mysql.py

history.py
runner.py
planner.py
checksum.py
schema.py
lint.py
explain.py
impact.py
doctor.py

The exact module boundaries may evolve as the project develops.