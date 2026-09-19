# Architecture

## Overview

dbmigrate is organized as a layered database migration and schema-evolution tool.

```text
CLI
 |
 v
Command Layer
 |
 v
Configuration
 |
 v
Migration Discovery / Validation
 |
 v
Migration Service
 |
 v
Database Abstraction
 |
 +---- SQLite
 |
 +---- PostgreSQL      (future)
 |
 +---- MySQL          (future)
 |
 v
Database
CLI Layer

Responsible for:

argument parsing
command dispatch
user-facing output
exit codes

The CLI should remain thin.

Business logic should not be implemented directly inside argument parsing.

Configuration Layer

Responsible for:

locating the project root
loading dbmigrate.toml
validating configuration
resolving migration directories
resolving the configured database URL
Migration Layer

Responsible for:

migration filename parsing
migration metadata
up/down SQL extraction
migration discovery
migration ordering
Validation Layer

Responsible for:

duplicate migration versions
migration gaps
duplicate migration names
migration structure validation
Database Layer

The database layer isolates database-specific behavior.

The abstract Database interface defines operations needed by higher layers.

SQLite is the first implementation.

Future database implementations should conform to the same abstraction.

Transaction Handling

Transactions belong to the database implementation.

The migration runner will later use the database transaction interface when applying migrations.

Current Responsibility Boundary

Phase 6 does not execute migrations.

The current system can:

discover migration files
parse migrations
validate migrations
connect to SQLite
execute arbitrary SQL through the database abstraction
manage transactions

The system cannot yet:

track migration history
apply migrations automatically
roll back migrations
calculate migration checksums
plan pending migrations

## Migration history

Migration history is managed through the `MigrationHistory` service.

```text
MigrationHistory
       |
       v
Database interface
       |
       +---- SQLiteDatabase
       |
       +---- PostgreSQLDatabase (future)
       |
       +---- MySQLDatabase (future)

The history service does not depend directly on SQLite.

This keeps database-specific behavior inside the database abstraction layer.

The history table is:

CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    checksum TEXT NOT NULL,
    applied_at TEXT NOT NULL
);

Migration execution is deliberately separate from history management.

The future migration runner will coordinate:

Migration
    |
    v
Database transaction
    |
    v
Execute SQL
    |
    v
Record history

---

# `commands/base.py`

For Phase 7, **don't add `history` as a CLI command yet**.

The roadmap says:

- Phase 7 → history infrastructure
- Phase 8 → migration runner
- Phase 11 → `status`, `history`, `current`

So adding a user-facing `history` command now would blur the phase boundaries.

Keep your existing `commands/base.py` unchanged for Phase 7.

---

# `cli.py`

Likewise, **do not change `cli.py` for Phase 7**.

There is no Phase 7 command to expose yet.

---

# Phase 7 test expectation

After adding:

```text
src/dbmigrate/history.py
tests/test_history.py

## Migration runner

The migration runner coordinates migration execution and history management.

```text
MigrationRunner
      |
      +---- Database
      |
      +---- MigrationHistory
      |
      +---- Migration

The runner does not implement SQL parsing or database-specific connection logic.

Its responsibility is orchestration:

discover
   |
validate
   |
determine pending migrations
   |
execute in version order
   |
record successful migration

Migration SQL and its history record are written inside the same database transaction.

This prevents migration history from becoming inconsistent with actual database state.