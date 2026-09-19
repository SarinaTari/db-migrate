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

Those responsibilities belong to later phases.