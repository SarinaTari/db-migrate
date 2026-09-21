# Migration Lifecycle

## Overview

A migration in `dbmigrate` moves a database from one schema state to another through a controlled, versioned process.

The complete lifecycle is:

```text
Create
  │
  ▼
Discover
  │
  ▼
Parse
  │
  ▼
Validate
  │
  ▼
Analyze
  │
  ▼
Plan
  │
  ▼
Lock
  │
  ▼
Execute
  │
  ▼
Record History
  │
  ▼
Verify
```

The lifecycle is designed to keep migration files, migration history, and database state synchronized.

---

# 1. Create

A migration begins as a SQL file in the configured migrations directory.

A migration can be created with:

```bash
dbmigrate create <name>
```

For example:

```bash
dbmigrate create create_users
```

The migration creator determines an appropriate version and creates a migration file.

A generated migration follows the project's standard structure:

```sql
-- migration: 001
-- name: create_users

-- +up

-- Write migration SQL here.

-- +down

-- Write rollback SQL here.
```

At this stage, the migration exists only as a file.

The database has not been modified.

---

# 2. Discover

When a migration-related command is executed, `dbmigrate` discovers migration files in the configured migrations directory.

For example:

```text
migrations/
├── 001_create_users.sql
├── 002_add_email.sql
└── 003_create_orders.sql
```

The discovery process identifies the available migration files and loads their contents.

Discovery is handled by the migration subsystem.

---

# 3. Parse

Each migration file is parsed into a structured migration object.

The parser extracts:

```text
version
name
up SQL
down SQL
```

For example:

```text
001_create_users.sql

        │
        ▼

Migration
├── version = 1
├── name = create_users
├── up_sql = ...
└── down_sql = ...
```

Malformed migration files result in parsing errors.

The purpose of parsing is to transform migration files from raw text into structured data that can be used by the rest of the system.

---

# 4. Validate

After parsing, the migration set can be validated.

Validation checks the structure and consistency of the migration collection.

Examples include:

- valid versions
- valid names
- duplicate versions
- duplicate identifiers
- migration ordering
- malformed migration definitions
- checksum consistency

The goal is to detect problems before SQL is executed.

Conceptually:

```text
Migration Files
      │
      ▼
Parsed Migrations
      │
      ▼
Validation
      │
      ├── Valid
      │
      └── Invalid
```

Invalid migrations should be corrected before execution.

---

# 5. Check Migration Safety

Migration safety analysis can be performed before execution.

The project includes analysis for potentially dangerous SQL operations.

Examples include:

```sql
DROP TABLE
DROP COLUMN
DELETE without WHERE
UPDATE without WHERE
```

The linter and impact-analysis systems provide additional information about potentially destructive operations.

This creates an important separation:

```text
Migration
   │
   ├── Can it be parsed?
   │
   ├── Is it structurally valid?
   │
   └── Does it contain risky operations?
```

The migration can therefore be inspected before it changes the database.

---

# 6. Calculate and Verify Checksums

Migration checksums provide an integrity mechanism.

A checksum is derived from the migration's:

```text
version
name
up SQL
down SQL
```

using SHA-256.

Conceptually:

```text
Migration
    │
    ▼
SHA-256
    │
    ▼
Checksum
```

When a migration is recorded in the database, its checksum is stored in:

```text
schema_migrations
```

Later, the current migration checksum can be compared with the recorded checksum.

If they differ, the migration file has changed since it was recorded.

---

# 7. Determine Migration State

The migration planner compares:

```text
Migration Files
```

with:

```text
schema_migrations
```

For example:

```text
Migration Files:

001
002
003
004

Applied:

001
002
003
```

The planner determines:

```text
Pending:

004
```

This allows `dbmigrate` to determine what remains to be applied.

---

# 8. Plan

The plan represents the migrations that would be executed.

For example:

```text
Pending migrations:

004_create_indexes
005_add_status
```

The planning operation is read-only.

It does not:

- execute migration SQL
- modify the schema
- modify migration history

This allows developers to inspect the intended changes before execution.

---

# 9. Acquire the Migration Lock

Before changing migration state, the migration process obtains an appropriate lock.

The locking mechanism depends on the database.

### SQLite

A filesystem lock is used:

```text
.dbmigrate.lock
```

### PostgreSQL

A PostgreSQL advisory lock is used.

### MySQL

MySQL's locking mechanism is used through:

```sql
GET_LOCK(...)
```

The purpose of the lock is to prevent multiple migration processes from changing migration state concurrently.

Conceptually:

```text
Migration Process A
       │
       ▼
   Acquire Lock
       │
       ▼
   Execute
```

while:

```text
Migration Process B
       │
       ▼
   Try Lock
       │
       ▼
     Blocked
```

or receives a lock failure according to the database-specific implementation.

---

# 10. Begin Transaction

Where supported by the database implementation, migration execution is performed inside a transaction.

The conceptual flow is:

```text
BEGIN
  │
  ▼
Execute Migration SQL
  │
  ▼
Update Migration History
  │
  ▼
COMMIT
```

If execution fails:

```text
BEGIN
  │
  ▼
Execute Migration SQL
  │
  ▼
Failure
  │
  ▼
ROLLBACK
```

Transactional behavior depends on the capabilities of the selected database engine.

For example, the project represents whether the database supports transactional DDL through `DatabaseCapabilities`.

---

# 11. Execute the Up Migration

When applying a migration, the `up` SQL is executed.

For example:

```sql
-- +up

CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);
```

The database schema changes from:

```text
Before:

No users table
```

to:

```text
After:

users
├── id
└── name
```

The migration itself is still not considered fully recorded until the history update succeeds.

---

# 12. Record Migration History

After successful migration execution, the migration is recorded in:

```text
schema_migrations
```

The record contains information such as:

```text
version
name
checksum
applied_at
```

Conceptually:

```text
Execute SQL
    │
    ▼
Migration Succeeds
    │
    ▼
Record History
    │
    ▼
Commit
```

This allows future commands to determine that the migration has already been applied.

---

# 13. Commit

If the migration and history update succeed, the transaction is committed where transactional behavior is supported.

```text
BEGIN
 │
 ├── Migration SQL
 │
 ├── History Update
 │
 ▼
COMMIT
```

At this point the migration becomes part of the recorded migration state.

---

# 14. Release the Lock

After migration processing finishes, the migration lock is released.

The general lifecycle is:

```text
Acquire Lock
     │
     ▼
Execute Migration
     │
     ▼
Update History
     │
     ▼
Commit / Rollback
     │
     ▼
Release Lock
```

This allows another migration process to operate after the current operation has completed.

---

# 15. Rollback Lifecycle

Rolling back a migration follows the reverse direction.

For an applied migration:

```text
Applied Migration
       │
       ▼
Acquire Lock
       │
       ▼
Begin Transaction
       │
       ▼
Execute Down SQL
       │
       ▼
Remove History Record
       │
       ▼
Commit
       │
       ▼
Release Lock
```

For example:

```sql
-- +up

CREATE TABLE users (
    id INTEGER PRIMARY KEY
);

-- +down

DROP TABLE users;
```

Applying the migration creates:

```text
users
```

Rolling it back removes:

```text
users
```

---

# 16. Multiple Migration Execution

When multiple migrations are pending, they are processed in version order.

For example:

```text
001
002
003
```

The execution order is:

```text
001
 ↓
002
 ↓
003
```

This preserves the dependency implied by migration versions.

The migration runner can apply all pending migrations or a controlled number of steps.

---

# 17. Rollback by Steps

The migration runner also supports rolling back a specified number of migrations.

For example, if the applied history is:

```text
001
002
003
004
```

rolling back two steps conceptually produces:

```text
001
002
```

The rollback order is reverse chronological order:

```text
004
 ↓
003
```

rather than:

```text
001
 ↓
002
```

This ensures that the most recently applied migration is rolled back first.

---

# 18. Status Tracking

The status system compares migration files with migration history.

For example:

```text
Migration Files:

001
002
003
004

History:

001
002
003
```

The status can identify:

```text
Applied:
001
002
003

Pending:
004
```

It can also identify inconsistencies such as migration history that no longer matches the available migration files.

---

# 19. Schema Verification

Migration history alone does not necessarily prove that the physical database schema matches expectations.

The project therefore provides schema-related analysis capabilities.

A schema can be inspected and represented structurally.

This information can then be used for:

- schema comparison
- schema fingerprints
- reproducibility checks
- impact analysis

The conceptual relationship is:

```text
Migration History
       │
       ├──────────────┐
       ▼              ▼
Migration Files    Database
       │              │
       └──────┬───────┘
              ▼
       Schema Analysis
```

---

# 20. Reproducibility

The reproducibility system can test whether migrations can recreate a target schema.

The process is conceptually:

```text
Existing / Target Schema
          │
          ▼
     Target Fingerprint

Migration Files
          │
          ▼
     Fresh Database
          │
          ▼
     Apply Migrations
          │
          ▼
     Inspect Schema
          │
          ▼
  Generated Fingerprint
          │
          ▼
       Compare
```

If the generated schema matches the target schema, the migration set reproduces that schema.

The current implementation performs this reproducibility workflow with SQLite.

---

# 21. Failure Handling

Migration execution can fail for many reasons.

Examples include:

- invalid SQL
- database connection failures
- checksum mismatches
- invalid migration state
- lock acquisition failures
- unsupported database operations
- transaction failures

The general failure path is:

```text
Migration Operation
       │
       ▼
Failure
       │
       ▼
Rollback where supported
       │
       ▼
Do not record unsuccessful migration
       │
       ▼
Release Lock
       │
       ▼
Report Error
```

The exact rollback behavior depends on the database implementation and its capabilities.

---

# 22. Migration State Model

The migration system can be viewed as maintaining three related states:

```text
Migration Files
      │
      ▼
Expected Migration State

Migration History
      │
      ▼
Recorded Migration State

Database Schema
      │
      ▼
Actual Database State
```

A healthy migration workflow keeps these states aligned:

```text
Migration Files
       │
       ▼
Migration History
       │
       ▼
Database Schema
```

Analysis tools exist to detect differences between these representations.

---

# 23. Complete Lifecycle

Putting everything together:

```text
                  ┌──────────────┐
                  │    Create    │
                  └──────┬───────┘
                         │
                         ▼
                  ┌──────────────┐
                  │   Discover   │
                  └──────┬───────┘
                         │
                         ▼
                  ┌──────────────┐
                  │     Parse    │
                  └──────┬───────┘
                         │
                         ▼
                  ┌──────────────┐
                  │   Validate   │
                  └──────┬───────┘
                         │
                         ▼
                  ┌──────────────┐
                  │    Analyze   │
                  └──────┬───────┘
                         │
                         ▼
                  ┌──────────────┐
                  │     Plan     │
                  └──────┬───────┘
                         │
                         ▼
                  ┌──────────────┐
                  │ Acquire Lock │
                  └──────┬───────┘
                         │
                         ▼
                  ┌──────────────┐
                  │ Begin Tx     │
                  └──────┬───────┘
                         │
                         ▼
                  ┌──────────────┐
                  │ Execute SQL  │
                  └──────┬───────┘
                         │
                         ▼
                  ┌──────────────┐
                  │ Update       │
                  │ History      │
                  └──────┬───────┘
                         │
                         ▼
                  ┌──────────────┐
                  │ Commit       │
                  └──────┬───────┘
                         │
                         ▼
                  ┌──────────────┐
                  │ Release Lock │
                  └──────┬───────┘
                         │
                         ▼
                  ┌──────────────┐
                  │    Verify    │
                  └──────────────┘
```

---

# Lifecycle Summary

The migration lifecycle can be summarized as:

```text
Create
  ↓
Discover
  ↓
Parse
  ↓
Validate
  ↓
Analyze
  ↓
Plan
  ↓
Lock
  ↓
Execute
  ↓
Record
  ↓
Commit
  ↓
Release
  ↓
Verify
```

The separation of these stages allows `dbmigrate` to inspect and validate migrations before execution while maintaining a persistent record of applied migration state.