# Phase 8 — Migration Runner

## Goal

Introduce the migration runner responsible for executing pending migrations against the configured database.

Phase 8 connects:

- migration discovery
- migration validation
- database access
- migration history

The runner executes migrations in version order and records successful migrations in `schema_migrations`.

---

## Architecture

```text
Migration files
       |
       v
Migration parser
       |
       v
Migration discovery
       |
       v
Migration runner
       |
       +-------------------+
       |                   |
       v                   v
   Database          MigrationHistory
       |                   |
       v                   v
   Execute SQL       Record migration
       \                   /
        \                 /
         +-------+-------+
                 |
                 v
             COMMIT
Forward migration

The up operation performs:

1. Discover migrations
2. Determine which migrations are pending
3. Sort pending migrations by version
4. Execute each migration
5. Record the migration in schema_migrations
6. Commit the transaction
Transaction safety

A migration and its history record are executed inside the same transaction.

Conceptually:

BEGIN;

-- migration SQL

INSERT INTO schema_migrations (...);

COMMIT;

If migration execution fails:

ROLLBACK;

The database should therefore not contain a partially applied migration.

Migration runner

The main service is:

MigrationRunner

Its responsibilities include:

runner.initialize()
runner.pending(migrations)
runner.apply(migration)
runner.apply_all(migrations)
Applying one migration

When a migration is applied:

Migration
    |
    v
Check history
    |
    v
Not already applied?
    |
    v
BEGIN
    |
    v
Execute up SQL
    |
    v
Insert history record
    |
    v
COMMIT
Already-applied migrations

A migration that is already present in schema_migrations is not executed again by apply_all().

Attempting to directly apply an already-applied migration raises MigrationRunnerError.

Failed migrations

If migration SQL fails:

BEGIN
   |
   +-- SQL fails
   |
ROLLBACK

The migration history record is also rolled back.

This prevents the database from reporting a failed migration as successfully applied.

Migration order

Migrations are always executed in ascending version order.

For example:

003_add_orders
001_create_users
002_add_email

becomes:

001_create_users
002_add_email
003_add_orders
Checksums

Phase 8 calculates a deterministic checksum when a migration is applied.

The checksum is stored in schema_migrations.

Full checksum integrity verification is intentionally deferred to Phase 14.

CLI

Phase 8 introduces:

dbmigrate up

Expected behavior:

$ dbmigrate up

Applied 001_create_users.
Applied 002_add_email.

If everything is already applied:

$ dbmigrate up

No pending migrations.
Current limitations

Phase 8 does not yet implement:

rollback execution
migration status
migration history display
current migration display
checksum verification
dry-run
execution planning
migration locking
PostgreSQL execution
MySQL execution
migration dependency analysis

These are introduced in later phases.

Testing

Phase 8 tests cover:

applying one migration
applying multiple migrations
pending migration detection
skipping applied migrations
duplicate application protection
failed migration rollback
history rollback
version ordering
pending migration ordering
Result

At the end of Phase 8, dbmigrate can execute pending migrations against SQLite and persist successful migration state.

The project now moves from a migration-definition system to an actual migration-execution system.