# Phase 6 — Database Interface + SQLite

## Goal

Introduce the first real database backend for dbmigrate.

The project now has a database abstraction that separates migration logic from database-specific implementation details.

## Implemented

- Abstract `Database` interface.
- SQLite database implementation.
- SQLite connection management.
- SQL execution.
- Parameterized queries.
- Single-row queries.
- Multi-row queries.
- Explicit transactions.
- Transaction commit.
- Transaction rollback.
- SQLite foreign-key enforcement.
- Database configuration through `dbmigrate.toml`.
- `dbmigrate check` command.
- SQLite-specific integration tests.

## Database configuration

Example:

```toml
[database]
url = "sqlite:///dbmigrate.db"

Phase 6 supports SQLite only.

PostgreSQL and MySQL will be introduced in later phases.

Architecture
CLI
 |
 v
Configuration
 |
 v
Database Factory
 |
 v
Database
 |
 +---- SQLiteDatabase
 |
 +---- PostgreSQLDatabase   (future)
 |
 +---- MySQLDatabase        (future)
Important design decision

Migration execution is intentionally not implemented yet.

The database layer only provides the infrastructure required by the future migration runner.

This keeps responsibilities separated:

Database layer manages connections and transactions.
Migration layer parses migration files.
Validation layer validates migration collections.
Migration runner will later coordinate migrations and database operations.
Database check

Run:

dbmigrate check

Expected output resembles:

Database connection: OK
Database engine: SQLite
SQLite version: 3.x.x
Database path: /path/to/dbmigrate.db
Testing

Run:

pytest

The tests verify:

connection creation
database file creation
SQL execution
parameterized queries
query results
transactions
rollback behavior
foreign keys
database errors
CLI database checks