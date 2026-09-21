# Safety and Integrity

## Overview

Database migrations modify persistent data and schema state. A migration tool therefore needs to treat correctness, integrity, and failure handling as first-class concerns.

`dbmigrate` approaches migration safety through several layers:

```text
Migration Validation
        │
        ▼
SQL Analysis
        │
        ▼
Checksum Verification
        │
        ▼
Planning
        │
        ▼
Concurrency Locking
        │
        ▼
Transactional Execution
        │
        ▼
Migration History
        │
        ▼
Schema Verification
```

No single mechanism can guarantee complete safety. Instead, the project combines multiple independent protections.

---

# 1. Safety Principles

The safety architecture is based on several principles.

### Validate Before Execution

Problems should be detected before SQL is sent to the database whenever possible.

### Make State Explicit

Migration history should clearly describe which migrations have been applied.

### Detect Modification

A migration that changes after being applied should be detectable.

### Prevent Concurrent Migration Runs

Multiple processes should not modify migration state simultaneously.

### Preserve Atomicity Where Supported

Migration changes and history updates should be grouped into transactions where the database supports the required behavior.

### Make Risk Visible

Potentially destructive SQL should be identifiable before execution.

### Prefer Explicit Failure

When the system cannot safely determine the correct state, it should report the problem rather than silently modifying the database.

---

# 2. Migration Validation

Migration validation is the first safety layer.

Before execution, migrations can be checked for structural problems such as:

- malformed metadata
- invalid versions
- duplicate versions
- invalid migration names
- missing migration sections
- inconsistent migration ordering

Conceptually:

```text
Migration Files
      │
      ▼
    Parse
      │
      ▼
   Validate
      │
      ├── Valid ──────► Continue
      │
      └── Invalid ────► Stop
```

The purpose is to prevent malformed migration files from reaching the execution stage.

---

# 3. SQL Linting

The project includes a migration linter that analyzes SQL before execution.

The linter can identify potentially dangerous patterns such as:

```sql
DROP TABLE
DROP COLUMN
DELETE without WHERE
UPDATE without WHERE
```

These operations are not automatically prohibited.

Instead, the linter provides information that allows the developer to review potentially destructive operations.

For example:

```text
Migration:
003_remove_old_users

Warnings:
- DROP TABLE detected
- Destructive schema operation
```

This is intentionally different from automatically modifying or rewriting the migration.

---

# 4. SQL Parsing for Analysis

The linter and explainer do not treat SQL as an undifferentiated string.

The analysis layer separates SQL statements while taking comments and quoted strings into account.

This is important because SQL text can contain keywords that are not actually SQL operations.

For example:

```sql
-- DROP TABLE users;

SELECT 'DROP TABLE users';
```

Neither occurrence should automatically be interpreted as a destructive SQL operation.

The analysis layer therefore masks comments and string literals before detecting operations.

---

# 5. Migration Impact Analysis

Impact analysis provides a higher-level view of possible schema effects.

A migration may contain operations such as:

```text
CREATE TABLE
ALTER TABLE
DROP TABLE
CREATE INDEX
DROP INDEX
```

The impact-analysis system can classify these operations and identify potentially significant changes.

The goal is not to automatically determine whether a migration is acceptable.

Instead, it provides structured information for human review.

---

# 6. Explainability

The project includes an explanation layer that converts migration operations into human-readable descriptions.

For example, instead of only seeing:

```sql
DROP TABLE users;
```

the developer can receive an explanation indicating that the migration removes the `users` table.

This is useful during migration review because the developer does not have to inspect every SQL statement manually to understand its high-level effect.

---

# 7. Planning Before Execution

The migration planner separates deciding what should happen from actually changing the database.

For example:

```text
Migration Files
      │
      ▼
   Planner
      │
      ▼
Pending Migrations
```

The plan can be inspected before execution.

This reduces accidental execution of unexpected migrations.

Planning is therefore a read-oriented operation, while execution is the state-changing operation.

---

# 8. Checksums

Migration checksums protect the integrity of migration files after they have been applied.

When a migration is recorded, its checksum is stored with its history record.

Conceptually:

```text
Migration File
      │
      ▼
 SHA-256
      │
      ▼
 Recorded Checksum
```

Later:

```text
Current Migration
      │
      ▼
 SHA-256
      │
      ▼
Current Checksum
      │
      ▼
Compare With History
```

If the values differ, the migration file has changed.

---

# 9. What a Checksum Protects

A checksum provides evidence that the migration file currently on disk matches the migration that was previously recorded.

For example:

```text
Applied migration:

001_create_users
checksum = ABC123...
```

If someone later modifies the migration:

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    name TEXT,
    email TEXT
);
```

the checksum changes.

The system can then identify:

```text
Recorded checksum != Current checksum
```

This prevents a modified migration from silently appearing identical to the originally recorded migration.

---

# 10. What a Checksum Does Not Protect

A checksum does not prove that the database schema is correct.

For example, a migration file can have a valid checksum while:

- the database was modified manually
- another application changed the schema
- a migration partially succeeded outside a transaction
- the database was restored from another source

Therefore:

```text
Checksum Integrity
        ≠
Schema Integrity
```

They are complementary mechanisms.

---

# 11. Migration History

Applied migrations are recorded in:

```text
schema_migrations
```

The history includes information such as:

```text
version
name
checksum
applied_at
```

This provides a persistent record of migration state.

Conceptually:

```text
Migration Files
      │
      ▼
Migration Runner
      │
      ▼
schema_migrations
```

Future migration operations use this information to determine which migrations have already been applied.

---

# 12. History and Schema Are Different

Migration history is an application-level record.

The physical database schema is the actual database state.

These two states can theoretically diverge.

For example:

```text
History:

001 applied
002 applied
003 applied

Database:

001 changes exist
002 changes exist
003 changes missing
```

A migration tool should therefore avoid treating history as absolute proof of physical schema correctness.

This distinction is important for diagnostic and verification functionality.

---

# 13. Transactions

Transactions provide an important execution-safety mechanism.

A migration can conceptually be processed as:

```text
BEGIN
  │
  ├── Execute migration SQL
  │
  ├── Record migration history
  │
  ▼
COMMIT
```

If an error occurs:

```text
BEGIN
  │
  ├── Execute migration SQL
  │
  ├── Error
  │
  ▼
ROLLBACK
```

Where supported, this prevents an unsuccessful migration from leaving the database in the same partially committed state.

---

# 14. Transactional DDL

Not every database handles schema-changing statements identically.

DDL includes operations such as:

```sql
CREATE TABLE
ALTER TABLE
DROP TABLE
```

The database capability layer therefore represents transactional behavior instead of assuming that all databases provide identical semantics.

This distinction matters because:

```text
Transaction support
```

and:

```text
Transactional DDL behavior
```

are related but not necessarily identical concepts.

The migration runner uses database capabilities when determining how execution should be handled.

---

# 15. Concurrency Protection

Two migration processes should not normally execute migrations against the same database simultaneously.

Without coordination, a race could occur:

```text
Process A                    Process B

Read history                 Read history
     │                            │
     ▼                            ▼
See migration 004 pending     See migration 004 pending
     │                            │
     ▼                            ▼
Execute 004                   Execute 004
```

This can cause duplicate execution or conflicting schema changes.

The locking layer prevents this class of concurrent migration race.

---

# 16. Locking Strategy

The project uses database-specific locking mechanisms.

```text
SQLite
  └── Application/filesystem locking

PostgreSQL
  └── Advisory locking

MySQL
  └── Named database locking
```

The migration runner interacts with a common locking abstraction rather than implementing every database-specific mechanism itself.

---

# 17. Lock Lifecycle

The lock should cover the critical migration operation.

Conceptually:

```text
Acquire Lock
     │
     ▼
Determine Migration State
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

The lock is therefore part of the migration lifecycle rather than an unrelated utility.

---

# 18. Failure Handling

Failures are expected to occur in real database systems.

Examples include:

```text
Connection failure
SQL syntax error
Constraint violation
Lock failure
Checksum mismatch
Invalid migration
Transaction failure
Unsupported operation
```

The system should surface these failures rather than hiding them.

The general execution model is:

```text
Operation
   │
   ▼
Success ─────────► Continue
   │
Failure
   │
   ▼
Rollback where supported
   │
   ▼
Do not record failed migration
   │
   ▼
Release resources
   │
   ▼
Report error
```

---

# 19. Resource Cleanup

Database connections, transactions, and locks are resources that must be cleaned up correctly.

A failure should not leave:

- an open database connection
- an unreleased application lock
- an active transaction
- stale migration state

The database and locking abstractions centralize this behavior where possible.

---

# 20. Migration History Consistency

Migration history should satisfy basic consistency properties.

For example:

```text
version
```

should uniquely identify a migration.

The migration history should not contain multiple records for the same migration version.

Migration execution therefore follows the principle:

```text
One Migration Version
        │
        ▼
One History Record
```

This gives the planner a deterministic representation of applied migrations.

---

# 21. Checksum Verification

Checksum verification compares the migration files currently available with the checksums stored in migration history.

Conceptually:

```text
Current Files
     │
     ▼
Calculate Checksums
     │
     ▼
Compare
     │
     ├── Match ──────► Integrity OK
     │
     └── Mismatch ───► Report Change
```

A mismatch should be investigated before relying on the migration history as an accurate representation of the migration files.

---

# 22. Fresh Database Reproducibility

One of the strongest practical integrity checks is reproducing a schema from an empty database.

The process is:

```text
Fresh Database
      │
      ▼
Apply All Migrations
      │
      ▼
Inspect Schema
      │
      ▼
Compare With Expected Schema
```

If the migration chain cannot recreate the expected schema, the migration set has a reproducibility problem.

This catches classes of errors that checksum verification alone cannot detect.

---

# 23. Schema Integrity

Schema inspection and schema comparison provide another layer of verification.

A schema can be represented structurally:

```text
Database
├── Tables
├── Columns
├── Types
├── Nullability
├── Indexes
└── Constraints
```

Two schema representations can then be compared.

For example:

```text
Expected Schema
      │
      ├── users
      ├── orders
      └── products

Actual Schema
      │
      ├── users
      └── orders
```

The difference indicates that the actual database does not contain the expected `products` table.

---

# 24. Safety Is Layered

No individual feature provides complete migration safety.

The project instead uses layered protection:

```text
                 ┌────────────────────┐
                 │ Migration Format   │
                 └─────────┬──────────┘
                           │
                           ▼
                 ┌────────────────────┐
                 │    Validation      │
                 └─────────┬──────────┘
                           │
                           ▼
                 ┌────────────────────┐
                 │      Linting       │
                 └─────────┬──────────┘
                           │
                           ▼
                 ┌────────────────────┐
                 │ Impact / Explain   │
                 └─────────┬──────────┘
                           │
                           ▼
                 ┌────────────────────┐
                 │     Planning       │
                 └─────────┬──────────┘
                           │
                           ▼
                 ┌────────────────────┐
                 │     Checksum       │
                 └─────────┬──────────┘
                           │
                           ▼
                 ┌────────────────────┐
                 │      Locking       │
                 └─────────┬──────────┘
                           │
                           ▼
                 ┌────────────────────┐
                 │   Transactions     │
                 └─────────┬──────────┘
                           │
                           ▼
                 ┌────────────────────┐
                 │ Migration History  │
                 └─────────┬──────────┘
                           │
                           ▼
                 ┌────────────────────┐
                 │ Schema Verification│
                 └────────────────────┘
```

Each layer addresses a different class of failure.

---

# 25. Safety Boundaries

`dbmigrate` is designed to improve migration safety, but it does not guarantee that every database operation is reversible or risk-free.

For example:

```sql
DROP TABLE users;
```

can remove data permanently.

Even if the migration is syntactically valid and successfully recorded, the operation may still be destructive.

Similarly:

```sql
DELETE FROM users;
```

can permanently remove rows.

The tool can identify and explain potentially dangerous operations, but it does not replace database backups, operational procedures, or human review.

---

# 26. No Automatic Production Repair

The project intentionally does not attempt to automatically repair arbitrary schema inconsistencies.

For example, if the migration history says:

```text
001
002
003
```

but the database is missing a table from migration `002`, the tool should not silently invent a repair strategy.

Instead, the inconsistency should be surfaced for investigation.

This avoids making irreversible assumptions about the intended production state.

---

# 27. No Automatic SQL Rewriting

The safety architecture also avoids automatically rewriting arbitrary SQL to make it "safer."

For example, the tool does not silently transform:

```sql
DROP TABLE users;
```

into another operation.

The migration author remains responsible for the SQL.

The analysis system provides information; it does not silently change migration semantics.

---

# 28. Integrity Model

The project's integrity model can be summarized through four questions:

### 1. Is the migration valid?

Handled through parsing and validation.

### 2. Has the migration changed?

Handled through checksums.

### 3. Is another migration process running?

Handled through locking.

### 4. Does the resulting schema match expectations?

Handled through schema inspection, comparison, and reproducibility checks.

Together:

```text
Validity
   +
File Integrity
   +
Concurrency Protection
   +
Schema Verification
   =
Migration Integrity
```

---

# 29. Recommended Review Workflow

A careful migration workflow can be:

```text
1. Create migration
        │
        ▼
2. Review SQL
        │
        ▼
3. Validate migration
        │
        ▼
4. Run lint / impact / explain
        │
        ▼
5. Inspect migration plan
        │
        ▼
6. Verify checksums
        │
        ▼
7. Execute migration
        │
        ▼
8. Verify resulting state
        │
        ▼
9. Run tests
```

For production environments, additional operational controls should be applied outside the migration tool as appropriate.

---

# 30. Safety Summary

`dbmigrate` treats migration safety as a layered engineering problem.

The major protections are:

```text
Validation
Linting
Impact Analysis
Explainability
Planning
Checksums
History Tracking
Locking
Transactions
Schema Inspection
Schema Comparison
Reproducibility
Failure Handling
```

These mechanisms are intentionally separated so that each addresses a different aspect of migration reliability.

The central principle is:

> A migration should be understandable, validated, traceable, and protected against avoidable integrity failures before and during execution.

At the same time, the tool does not claim to make arbitrary database changes completely safe. Destructive SQL, external schema modifications, data loss, operational mistakes, and database-specific limitations remain outside the guarantees of the migration framework.