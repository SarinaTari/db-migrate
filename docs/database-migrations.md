# Database Migrations

## 1. What Is a Database Schema?

A database schema describes the structure of a database.

For a relational database, this includes objects such as:

* tables
* columns
* data types
* primary keys
* foreign keys
* unique constraints
* indexes
* views
* triggers

For example:

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE
);
```

The schema describes the structure of the `users` table.

It does not represent the individual rows stored in that table.

---

## 2. Schema vs Data

This distinction is fundamental.

### Schema

Describes structure:

```text
users
├── id
├── name
└── email
```

### Data

Represents actual records:

```text
1 | Alice | alice@example.com
2 | Bob   | bob@example.com
```

A migration tool primarily manages **schema evolution**.

It may execute SQL that changes data, but its primary responsibility is tracking changes to database structure.

---

## 3. Why Schemas Change

Applications evolve.

Suppose the first version of an application contains:

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);
```

Later, the application needs email addresses.

We could change the schema:

```sql
ALTER TABLE users
ADD COLUMN email TEXT;
```

Later we might add:

```text
projects
tasks
indexes
foreign keys
constraints
```

The database schema therefore evolves alongside the application.

This process is called:

> Schema evolution.

---

## 4. What Is a Migration?

A migration is a **recorded, ordered database change**.

For example:

```text
001_create_users
002_add_email
003_create_projects
```

Each migration represents a known point in the evolution of the database schema.

Conceptually:

```text
Schema 0
   │
   │ Migration 001
   ▼
Schema 1
   │
   │ Migration 002
   ▼
Schema 2
   │
   │ Migration 003
   ▼
Schema 3
```

The migration history therefore describes how the schema evolved.

---

## 5. Why Not Just Modify the Database Manually?

Suppose one developer runs:

```sql
ALTER TABLE users ADD COLUMN email TEXT;
```

directly against a development database.

Another developer does not know that this happened.

The production database does not contain the change.

A migration provides a reproducible record:

```text
002_add_email.sql
```

Now the change can be:

* reviewed
* committed to Git
* applied to another database
* tested
* reproduced
* tracked

This is one of the fundamental reasons migration systems exist.

---

## 6. Migrations as Versioned History

A migration system creates a relationship between:

```text
Application version
```

and:

```text
Database schema state
```

For example:

```text
Migration 001
    ↓
Migration 002
    ↓
Migration 003
    ↓
Migration 004
```

A database that has applied migrations 001–004 should correspond to the schema produced by those changes.

---

## 7. Up Migration

An `up` migration moves the database forward.

Example:

```sql
-- +up

CREATE TABLE projects (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);
```

Applying this migration changes:

```text
Schema N
   ↓
Schema N + 1
```

---

## 8. Down Migration

A `down` migration reverses a migration.

For example:

```sql
-- +down

DROP TABLE projects;
```

Conceptually:

```text
Schema N + 1
     ↓
Schema N
```

However, rollback is not always equivalent to perfectly recovering the previous state.

For example:

```sql
DROP TABLE users;
```

may destroy data.

Therefore, "down" does not automatically mean "safe."

---

## 9. Migration History

The database needs to know which migrations have already been applied.

A migration history table can contain:

```text
version
name
checksum
applied_at
```

For example:

```text
001 | create_users    | abc123 | ...
002 | add_email       | def456 | ...
003 | create_projects | 789abc | ...
```

The migration engine can then compare:

```text
Migration files on disk
```

against:

```text
Migration records in the database
```

to determine the current state.

---

## 10. Pending Migrations

Suppose the repository contains:

```text
001_create_users
002_add_email
003_create_projects
004_create_tasks
005_add_indexes
```

but the database history contains:

```text
001
002
003
```

Then:

```text
Current version:
003

Pending:

004
005
```

The migration runner can execute those migrations in order.

---

## 11. Migration Ordering

Migration order matters.

Suppose:

```text
001_create_users
002_create_projects
003_create_tasks
```

Migration `003` might depend on the table created by `002`.

Therefore:

```text
001 → 002 → 003
```

is not equivalent to:

```text
003 → 001 → 002
```

The migration engine must therefore have a deterministic ordering mechanism.

---

## 12. Sequential Versions

One possible strategy is:

```text
001
002
003
004
```

Advantages:

* easy to understand
* readable
* deterministic

Potential problems:

* two developers may both create migration `005`

This becomes important when multiple developers create migrations independently.

---

## 13. Timestamp Versions

Another strategy is:

```text
202609191130_create_users
202609191145_add_email
```

Advantages include reduced collision probability.

However, timestamps introduce their own considerations:

* clock differences
* readability
* ordering
* branch merges

The project will evaluate the tradeoffs before implementation.

---

## 14. Migration Files and Git

Migration files are normal project files.

For example:

```text
migrations/
├── 001_create_users.sql
├── 002_add_email.sql
└── 003_create_projects.sql
```

They should normally be committed to Git.

This gives the migration history a relationship with application source history:

```text
Git commit
    │
    ├── application changes
    │
    └── migration changes
```

A feature that requires a database schema change should normally include the corresponding migration in the same development history.

---

## 15. Transactions

A migration may perform several operations.

For example:

```sql
CREATE TABLE projects (...);

CREATE INDEX idx_projects_name
ON projects(name);
```

If the database supports transactional execution for those operations, we ideally want:

```text
BEGIN
   │
   ├── operation 1
   │
   ├── operation 2
   │
   ▼
COMMIT
```

If something fails:

```text
BEGIN
   │
   ├── operation 1
   │
   ├── operation 2
   │      X
   │
   ▼
ROLLBACK
```

This prevents a partially completed migration where the database is left in an unintended intermediate state.

---

## 16. ACID

Transactions are commonly discussed using the ACID properties.

### Atomicity

A transaction is treated as a unit.

Conceptually:

```text
all operations succeed
```

or:

```text
none of the transaction's changes remain
```

subject to the database's actual behavior and supported operations.

### Consistency

A successful transaction should preserve the database's defined integrity constraints.

### Isolation

Concurrent operations should interact according to the database's isolation rules.

### Durability

Committed changes should survive according to the database's durability guarantees.

The exact behavior depends on the database engine and configuration.

---

## 17. DDL vs DML

Two important SQL categories are:

### DDL

Data Definition Language.

Examples:

```sql
CREATE TABLE
ALTER TABLE
DROP TABLE
CREATE INDEX
```

DDL primarily changes database structure.

### DML

Data Manipulation Language.

Examples:

```sql
INSERT
UPDATE
DELETE
```

DML primarily changes stored data.

Migration systems can execute both.

---

## 18. Why DDL Transactions Matter

A critical database-engineering issue is that DDL does not behave identically across database engines.

For example, SQLite, PostgreSQL, and MySQL have different transactional behavior for various schema operations.

Therefore, the project must never assume:

```text
All databases
+
All DDL
+
All operations
=
identical transaction semantics
```

The actual behavior must be investigated and documented for each supported database.

---

## 19. Rollback Is Not Magic

Consider:

```sql
DROP TABLE users;
```

If the operation permanently removes data and the database cannot roll it back in the particular situation, a down migration cannot magically recover the lost records.

Therefore:

```text
Migration reversal
```

and:

```text
Data recovery
```

are different concepts.

This is one reason destructive migrations require special treatment.

---

## 20. Migration Integrity

Suppose migration `002` was already applied:

```text
002_add_email.sql
```

Later someone edits the file.

The database still represents the original version of migration `002`, but the repository now contains different SQL.

This creates a dangerous mismatch.

The tool should therefore eventually calculate a checksum:

```text
Original:
abc123

Current:
def456
```

and report:

```text
Migration 002 has been modified after application.
```

---

## 21. Why Applied Migrations Should Be Immutable

Once a migration has been applied to an environment, its contents should generally be treated as immutable.

Instead of changing:

```text
002_add_email.sql
```

we create:

```text
003_change_email_constraint.sql
```

This preserves the historical record.

Conceptually:

```text
001
  ↓
002
  ↓
003
```

rather than rewriting:

```text
002
```

after it has already been used.

---

## 22. Reproducibility

A strong migration system should make it possible to construct a database from an empty state:

```text
Empty database
      │
      ▼
001
      │
      ▼
002
      │
      ▼
003
      │
      ▼
004
      │
      ▼
Current schema
```

This is extremely important.

If the migration history cannot reproduce the current schema, then the migration history is not a reliable representation of the system.

---

## 23. Schema Fingerprints

The project will eventually create a normalized representation of the schema.

For example:

```text
users(
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT
)

projects(
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL
)
```

That normalized representation can be hashed:

```text
SHA-256(normalized_schema)
```

producing something like:

```text
8f1d3e...
```

This becomes a schema fingerprint.

It can help detect:

```text
same schema
```

versus:

```text
different schema
```

without comparing raw database files.

---

## 24. Schema Drift

Schema drift occurs when the actual database schema differs from the expected schema.

For example:

```text
Migration history says:

users:
    id
    name
    email
```

but the actual database contains:

```text
users:
    id
    name
    email
    debug_flag
```

The database has drifted from the expected state.

A future `schema-diff` feature will help detect such differences.

---

## 25. Planning Before Execution

A migration tool should not necessarily jump directly from:

```text
command
```

to:

```text
database modification
```

A better conceptual pipeline is:

```text
Discover
   ↓
Validate
   ↓
Plan
   ↓
Show plan
   ↓
Execute
```

For example:

```text
Current version: 003

Pending:

004_add_projects
005_add_tasks
006_add_indexes

No changes have been made.
```

This provides the user with visibility before modification.

---

## 26. Migration Analysis

Later phases will analyze migration SQL.

For example:

```sql
DROP TABLE users;
```

The analyzer can identify:

```text
Detected operation:
DROP TABLE users

Potential concern:
Existing data may be removed.
```

The analyzer should not claim:

```text
This migration is definitely unsafe.
```

because it cannot know the complete operational context.

---

## 27. Migration Linting

Linting means checking migration files for known patterns and potential problems.

Examples:

```text
DROP TABLE
DROP COLUMN
ADD COLUMN ... NOT NULL
```

A linter might report:

```text
WARNING:
Migration adds a NOT NULL column without an obvious default.
```

The warning should describe the detected condition.

---

## 28. Migration Impact Analysis

Impact analysis answers:

> Which database objects does this migration affect?

For example:

```text
Migration:
005_add_project_owner

Affected:

Table:
projects

Column:
owner_id

Referenced table:
users

Index:
idx_projects_owner
```

This feature will be implemented progressively.

---

## 29. Migration Doctor

A doctor command can combine several diagnostics:

```text
Configuration
Database connection
Migration files
Ordering
Checksums
History
Schema
```

Example:

```text
Database Migration Doctor

[OK] Configuration
[OK] Database connection
[OK] Migration directory
[OK] Migration ordering
[OK] Applied migration checksums
[WARNING] Schema differs from expected state
```

The doctor should diagnose problems rather than automatically modifying the database.

---

## 30. Core Mental Model

The most important mental model for this project is:

```text
Migration files
       │
       ▼
Migration history
       │
       ▼
Expected schema
       │
       │
       ├───────────────┐
       │               │
       ▼               ▼
Actual database    Schema analysis
```

The migration tool exists to keep these representations understandable, reproducible, and consistent.

---

## Phase 0 Summary

At the end of Phase 0, I should be able to explain:

* what a database schema is
* what schema evolution means
* what a migration is
* why migrations are versioned
* how migration history works
* what up/down migrations mean
* why migration ordering matters
* what transactions are
* what commit and rollback mean
* what ACID means
* the difference between DDL and DML
* why database engines behave differently
* why applied migrations should be immutable
* why checksums matter
* what schema drift is
* why reproducibility matters
* what migration planning means
* what migration linting means
* what schema diff means

Only after these concepts are understood should implementation begin.
