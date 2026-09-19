# Phase 7 — Migration History

## Goal

Introduce persistent migration history so dbmigrate can determine which migrations have been applied to a database.

Phase 7 establishes the history layer required by the migration runner.

Migration execution itself is intentionally deferred to Phase 8.

---

## What was added

- Migration history database table
- `MigrationRecord`
- `MigrationHistory`
- Record applied migrations
- Remove migration records
- Check whether a migration is applied
- Retrieve a migration by version
- List applied migrations
- Retrieve the latest applied migration
- History initialization
- History-specific error handling
- Automated tests

---

## History table

The database contains:

```sql
CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    checksum TEXT NOT NULL,
    applied_at TEXT NOT NULL
);
Fields
version

The migration version.

Example:

1
2
3

The version is the primary key.

name

The migration name.

Example:

create_users
add_email
create_orders
checksum

A checksum associated with the migration.

Phase 7 stores this value but does not yet verify it.

Checksum calculation and integrity enforcement are introduced later.

applied_at

The UTC timestamp at which the migration was recorded as applied.

Architecture

The Phase 7 architecture is:

CLI
 |
 v
Configuration
 |
 v
Database
 |
 v
MigrationHistory
 |
 v
schema_migrations

The history layer depends on the abstract Database interface rather than directly depending on SQLite.

This allows PostgreSQL and MySQL implementations to use the same history service later.

Important design decision

Phase 7 does not execute migration SQL.

For example, this phase does not implement:

dbmigrate up
dbmigrate down

The history layer only provides the persistent state needed by the future migration runner.

This separation keeps migration execution and migration state management independent.

Migration record lifecycle

Eventually the migration runner will perform operations similar to:

Migration discovered
       |
       v
Migration selected for execution
       |
       v
Migration SQL executed
       |
       v
History record inserted

For rollback:

Migration selected for rollback
       |
       v
Down SQL executed
       |
       v
History record removed

Those execution semantics belong to Phase 8 and later.

History API

The main interface is:

history.initialize()
history.record(...)
history.remove(version)
history.is_applied(version)
history.get(version)
history.list_applied()
history.latest()
Error handling

History-specific failures are represented by:

HistoryError

Database-specific errors are converted into HistoryError at the history boundary.

This prevents higher layers from needing to know implementation-specific database exceptions.

Duplicate versions

The database primary key prevents two records from existing for the same migration version.

Therefore:

version = 1

can only occur once in schema_migrations.

Current limitations

Phase 7 does not yet:

execute migration files
calculate migration checksums
verify existing checksums
detect modified migrations
run migrations forward
roll migrations backward
provide migration status
provide migration history CLI output
support PostgreSQL
support MySQL
provide migration locking

These features belong to later phases.

Testing

Phase 7 tests cover:

history table creation
idempotent initialization
recording migrations
retrieving migrations
applied-state checks
ordered history listing
latest migration lookup
empty history
removing records
duplicate versions
invalid versions
invalid names
invalid checksums
Result

At the end of Phase 7, dbmigrate has a persistent representation of migration state.

The project now has a clear separation between:

Migration definition
Migration discovery
Migration validation
Database access
Migration history

The next phase introduces the migration runner that connects these components.