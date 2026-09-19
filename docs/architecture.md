# Architecture

## Overview

`db-migrate` is designed as a layered database migration and schema-evolution system.

The architecture separates command-line interaction, migration management, database execution, and analysis.

---

## Current Architecture

At Phase 4, the implemented architecture is:

```text
CLI
 │
 ↓
Command Definitions
 │
 ↓
Configuration
 │
 ↓
Migration Discovery
 │
 ↓
Migration Parser
 │
 ↓
Migration Domain Model

Database execution has not yet been introduced.

Planned Architecture

The target architecture is:

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
Execution Layer
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

Each layer should have one primary responsibility.

The CLI should not contain SQL execution logic.

The parser should not connect to databases.

The database abstraction should not parse command-line arguments.

Explicit failure

Invalid migration files should fail clearly rather than being silently ignored.

Deterministic behavior

Migration discovery and ordering must be deterministic.

Migration version numbers define execution order.

Database independence

The migration engine should not be tightly coupled to a single database backend.

SQLite will be implemented first, but the architecture is intended to support PostgreSQL and MySQL later.

Safety first

The project will eventually prioritize:

validation
transactions
checksums
dry runs
planning
locking
integrity verification

before introducing advanced automation.

Current Modules
cli.py

Responsible for:

argument parsing
command resolution
command dispatch
config.py

Responsible for:

project discovery
configuration loading
configuration validation
migration.py

Responsible for:

migration representation
migration filename parsing
migration metadata parsing
migration section parsing
migration discovery
commands/base.py

Contains the command registry and command metadata.

Future Modules

Expected future responsibilities include:

database/
    base.py
    sqlite.py
    postgres.py
    mysql.py

history.py
runner.py
planner.py
validator.py
checksum.py
schema.py
lint.py
explain.py
impact.py
doctor.py

The exact module boundaries may evolve as the implementation grows.