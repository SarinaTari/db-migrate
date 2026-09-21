# Design Decisions

## Overview

`dbmigrate` was designed as a database migration system with an emphasis on:

- safety
- integrity
- explainability
- portability
- testability
- maintainability

The architecture deliberately avoids trying to solve every possible database-management problem.

This document explains the main design decisions and the reasoning behind them.

---

# 1. Python as the Implementation Language

`dbmigrate` is implemented primarily in Python.

Python was selected because it provides:

- strong standard-library support
- mature database drivers
- straightforward CLI development
- fast development and iteration
- excellent testing tools
- readable code suitable for an educational portfolio project

The project also benefits from Python's ecosystem for:

```text
SQLite
PostgreSQL
MySQL
CLI tooling
Testing
Configuration
Logging
```

---

# 2. CLI-First Design

The project is designed primarily as a command-line tool.

The CLI provides a direct interface for:

```text
Creating migrations
Validating migrations
Planning changes
Applying migrations
Rolling back migrations
Inspecting schemas
Analyzing migration impact
Running diagnostics
Running CI checks
```

A CLI-first design keeps the tool:

- scriptable
- automatable
- easy to test
- suitable for CI
- independent of a graphical interface

---

# 3. Migration Files as Source of Truth

Migration definitions are stored as files.

For example:

```text
migrations/
├── 001_create_users.sql
├── 002_add_email.sql
└── 003_create_orders.sql
```

This was chosen because migrations should be:

- version-controlled
- reviewable
- reproducible
- portable between development environments

A migration is therefore part of the project's source code rather than being stored only inside a database.

---

# 4. Explicit `up` and `down` Sections

Each migration contains:

```text
up
down
```

The `up` section describes the forward schema change.

The `down` section describes the reverse operation.

For example:

```sql
-- +up

CREATE TABLE users (
    id INTEGER PRIMARY KEY
);

-- +down

DROP TABLE users;
```

This makes migration direction explicit.

It also makes rollback behavior visible during code review.

---

# 5. No Automatic Reverse-SQL Generation

The project does not attempt to automatically generate `down` SQL from `up` SQL.

For example:

```sql
CREATE TABLE users (...);
```

does not automatically produce:

```sql
DROP TABLE users;
```

The migration author explicitly defines the rollback operation.

This decision avoids pretending that arbitrary SQL can always be safely reversed.

For example, a migration might contain:

```sql
DELETE FROM users WHERE id = 10;
```

The inverse operation cannot necessarily recover the deleted row.

Explicit rollback SQL makes this limitation visible.

---

# 6. Versioned Migrations

Migrations use explicit numeric versions.

For example:

```text
001
002
003
```

This provides deterministic ordering.

The migration system can therefore construct:

```text
001
  ↓
002
  ↓
003
```

rather than relying on filesystem ordering or creation timestamps.

---

# 7. Migration History Table

Applied migrations are recorded in:

```text
schema_migrations
```

The table contains information such as:

```text
version
name
checksum
applied_at
```

This was chosen instead of relying only on the filesystem because the database needs a persistent record of which migrations it has already processed.

---

# 8. History Is Separate From Migration Files

Migration files and migration history represent different concepts.

Migration files describe:

```text
What migrations exist.
```

Migration history describes:

```text
What migrations the database has recorded as applied.
```

This distinction allows the planner to compare:

```text
Available migrations
        vs.
Applied migrations
```

and determine the pending migration set.

---

# 9. Checksums for Migration Integrity

Each applied migration stores a checksum.

The checksum protects against silent modification of migration files after they have been applied.

The project uses SHA-256.

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

The checksum is stored in migration history and can later be compared with the current migration contents.

---

# 10. Why SHA-256

SHA-256 was selected because it is:

- widely available
- deterministic
- well understood
- suitable for integrity checking
- available through Python's standard library

The checksum is used for detecting content changes, not for password storage or cryptographic authentication.

---

# 11. Database Abstraction

Migration logic is separated from database-specific implementation.

The architecture uses a database abstraction layer:

```text
Migration Logic
      │
      ▼
Database Interface
      │
      ├── SQLite
      ├── PostgreSQL
      └── MySQL
```

This allows the same migration lifecycle to operate across supported database engines.

---

# 12. Database Factory

Database implementations are selected through a factory.

Conceptually:

```text
Configuration
      │
      ▼
Database Factory
      │
      ├── SQLite
      ├── PostgreSQL
      └── MySQL
```

This prevents database selection logic from being duplicated throughout the application.

---

# 13. Dialect Abstraction

The project separates database-specific SQL conventions into a dialect layer.

This is necessary because databases can use different syntax for otherwise similar operations.

For example, parameter placeholders can differ:

```text
SQLite / MySQL:
?

PostgreSQL:
%s
```

Generic components should not hard-code one database's parameter syntax.

---

# 14. Capability Abstraction

Dialect differences are not enough to describe database behavior.

The project therefore has a separate capability layer.

Capabilities describe properties such as:

```text
Transactional behavior
Locking support
Schema inspection
Database information
```

This allows higher-level code to ask what a database supports instead of assuming that all database engines behave identically.

---

# 15. Why Dialect and Capability Are Separate

These two concepts answer different questions.

### Dialect

> How should a database-specific query be written?

### Capability

> What behavior does this database provide?

Keeping them separate prevents SQL syntax concerns from becoming mixed with behavioral assumptions.

---

# 16. Database-Specific Locking

Migration concurrency requires locking, but database engines provide different mechanisms.

The project therefore uses database-specific locking behind a common abstraction.

Conceptually:

```text
SQLite
  └── Application/filesystem locking

PostgreSQL
  └── Advisory locking

MySQL
  └── Named locking
```

This allows the migration runner to use one conceptual locking API while the implementation remains database-specific.

---

# 17. Lock Before Migration

The migration lock is acquired before the critical migration operation.

The general lifecycle is:

```text
Acquire Lock
      │
      ▼
Determine State
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

This reduces the possibility of concurrent processes applying the same migration or modifying migration state simultaneously.

---

# 18. Transactions

Migration execution uses transactions where supported.

The intended model is:

```text
BEGIN
  │
  ├── Execute migration
  ├── Update history
  │
  ▼
COMMIT
```

On failure:

```text
BEGIN
  │
  ├── Execute migration
  ├── Failure
  │
  ▼
ROLLBACK
```

This helps keep migration execution and migration history consistent.

---

# 19. Why Transactional Behavior Is Capability-Driven

Database engines differ in how they handle transactions and DDL.

The project therefore avoids assuming that every database provides identical transactional behavior.

Instead:

```text
Database
    │
    ▼
Capabilities
    │
    ▼
Migration Runner
```

The runner can make execution decisions based on the selected database's capabilities.

---

# 20. Planner Separate From Runner

The planner and runner are intentionally separate.

The planner determines:

```text
What should be executed?
```

The runner performs:

```text
Execute it.
```

This separation allows:

```text
dbmigrate plan
```

to inspect pending work without changing the database.

It also makes the execution layer easier to test independently.

---

# 21. Validation Before Execution

Migration validation is separated from execution.

The general workflow is:

```text
Migration
   │
   ▼
Parse
   │
   ▼
Validate
   │
   ▼
Plan
   │
   ▼
Execute
```

This prevents malformed migration files from reaching the database unnecessarily.

---

# 22. Linter Instead of Automatic SQL Modification

The project includes SQL analysis, but it does not automatically rewrite migration SQL.

For example:

```sql
DROP TABLE users;
```

can be identified as destructive.

The tool can report this fact, but it does not silently replace the statement.

This preserves developer control over migration semantics.

---

# 23. Explainability as a Separate Layer

Migration explanation is implemented separately from migration execution.

The explanation system answers:

> What does this migration appear to do?

rather than:

> Should this migration be executed?

This distinction is important because the tool should provide information without hiding the underlying SQL.

---

# 24. Impact Analysis

Impact analysis provides another view of migration changes.

Instead of only reporting raw SQL, it can identify operations such as:

```text
CREATE TABLE
DROP TABLE
ALTER TABLE
CREATE INDEX
DROP INDEX
```

The purpose is to make potentially important changes easier to review.

The analysis system does not automatically approve or reject migrations.

---

# 25. Schema Analysis Separate From Migration History

The project deliberately distinguishes:

```text
Migration History
```

from:

```text
Actual Database Schema
```

History answers:

```text
What has been recorded as applied?
```

Schema inspection answers:

```text
What objects actually exist?
```

This separation is important because external database changes can cause the two states to diverge.

---

# 26. Schema Diff

Schema comparison is implemented separately from migration execution.

The schema-diff system identifies structural differences such as:

```text
Added table
Removed table
Added column
Removed column
Changed column
Added index
Removed index
```

It does not automatically apply the differences.

This keeps analysis separate from modification.

---

# 27. Schema Fingerprinting

Schema fingerprints provide a compact way to compare schema states.

The general design is:

```text
Schema
  │
  ▼
Canonical Representation
  │
  ▼
SHA-256
  │
  ▼
Fingerprint
```

Canonicalization is important because logically equivalent schema structures should not receive different fingerprints merely because metadata was returned in a different order.

---

# 28. Reproducibility as a First-Class Concept

A migration chain should ideally be capable of recreating the intended schema from an empty database.

The project therefore includes reproducibility analysis.

Conceptually:

```text
Empty Database
      │
      ▼
Apply Migration Chain
      │
      ▼
Inspect Schema
      │
      ▼
Compare Result
```

The current reproducibility workflow is implemented using SQLite.

---

# 29. Why Reproducibility Matters

A migration history can appear correct while the migration chain itself contains problems.

For example:

```text
Production Database
       │
       ├── Historical manual changes
       ├── Old migrations
       └── Current migrations
```

may hide a migration that fails on a clean database.

Testing from an empty database removes that historical state.

This makes reproducibility a valuable integrity check.

---

# 30. No Automatic Production Repair

The project deliberately avoids automatically repairing arbitrary schema differences.

For example:

```text
History:
001
002
003

Actual schema:
001
002
```

does not automatically tell the tool exactly what should be done.

Possible causes include:

- manual database changes
- incomplete restoration
- failed external operation
- incorrect migration history
- another migration system

Automatically changing the database could make the situation worse.

Therefore, the project reports inconsistencies rather than inventing a repair strategy.

---

# 31. No Automatic SQL Dialect Translation

The project supports multiple database engines, but it does not attempt to automatically translate arbitrary SQL between them.

For example:

```text
PostgreSQL SQL
      ≠
Automatically generated SQLite SQL
```

This decision keeps the scope realistic and avoids pretending that SQL dialect translation is universally safe.

Migration authors remain responsible for database-specific SQL.

---

# 32. No ORM

`dbmigrate` is intentionally not an ORM.

The tool operates directly on migration SQL and database metadata.

This provides:

- explicit SQL
- predictable migration behavior
- database-level control
- independence from application models

It also keeps the project's scope focused on migration infrastructure rather than object-relational mapping.

---

# 33. SQL Files Instead of Python Migrations

Migrations are stored as SQL rather than Python code.

For example:

```sql
-- +up

CREATE TABLE users (...);

-- +down

DROP TABLE users;
```

This makes migrations:

- easy to inspect
- database-oriented
- portable
- understandable without learning a migration-specific programming API

It also makes the actual database operation visible during code review.

---

# 34. Explicit SQL Over Abstraction

The project intentionally does not hide SQL behind a high-level schema builder.

For example, developers write:

```sql
ALTER TABLE users
ADD COLUMN email TEXT;
```

rather than:

```text
migration.add_column(...)
```

This keeps the tool close to the database and makes its behavior transparent.

---

# 35. Separate Analysis From Execution

A recurring architectural principle is:

```text
Analyze
   ≠
Execute
```

For example:

```text
plan
lint
explain
impact
schema
schema-diff
fingerprint
doctor
```

are primarily analysis or diagnostic operations.

State-changing operations are explicit:

```text
up
down
```

This separation improves safety and makes commands easier to reason about.

---

# 36. Separate Core Services From CLI

The CLI should not contain the complete implementation of migration logic.

Instead:

```text
CLI
 │
 ▼
Services
 │
 ├── Migration
 ├── Planner
 ├── Runner
 ├── History
 ├── Validation
 ├── Schema
 └── Analysis
 │
 ▼
Database Layer
```

This makes the application easier to test without invoking the CLI.

It also keeps the command layer focused on user interaction.

---

# 37. Testability as a Design Requirement

Components are designed so that important behavior can be tested independently.

Examples include:

```text
Migration parser
Planner
History
Runner
Schema inspector
Linter
Explainer
Impact analyzer
Database implementations
CLI
```

This is one reason responsibilities are separated into multiple modules instead of placing everything in one large command implementation.

---

# 38. Standard Library Where Practical

The project uses Python's standard library where it provides a suitable solution.

Examples include:

```text
sqlite3
hashlib
pathlib
tempfile
logging
```

External dependencies are used where they provide necessary database or testing functionality.

This keeps the project relatively lightweight.

---

# 39. Logging Abstraction

Logging is centralized rather than scattered through direct logging configuration in every component.

The logging layer provides consistent configuration for:

```text
log level
quiet mode
verbose mode
handlers
```

This prevents individual components from having incompatible logging behavior.

---

# 40. CI as a Development Tool

Continuous integration is treated as part of the architecture rather than an afterthought.

The repository contains:

```text
.github/workflows/ci.yml
```

The CI system provides a clean environment where automated tests and project checks can run.

This helps detect problems that may not appear on a developer's local machine.

---

# 41. Performance Utilities Without Premature Optimization

The project includes performance-related functionality, but performance measurement is separated from normal migration logic.

This keeps the main code focused on correctness.

Performance can then be measured when needed without introducing optimization complexity throughout the system.

The design principle is:

```text
Correctness first
       ↓
Measure
       ↓
Optimize where justified
```

rather than optimizing based only on assumptions.

---

# 42. Explicit Scope

The project deliberately excludes several areas that could make a migration tool much larger.

It does not attempt to provide:

```text
Automatic SQL translation
Universal schema repair
ORM functionality
Distributed migration orchestration
Backup management
Kubernetes orchestration
Perfect SQL parsing
```

These exclusions help keep the project focused on:

```text
Migration
Safety
Integrity
Analysis
Portability
Developer tooling
```

---

# 43. Design Trade-offs

Every architectural decision introduces trade-offs.

For example:

### Explicit SQL

**Advantage:**

Developers see exactly what will execute.

**Trade-off:**

Migrations are more database-specific.

### Explicit Down SQL

**Advantage:**

Rollback behavior is visible and controllable.

**Trade-off:**

Developers must write and maintain rollback SQL.

### Database Abstraction

**Advantage:**

Supports multiple databases.

**Trade-off:**

The abstraction must account for genuine database differences.

### Schema Abstraction

**Advantage:**

Enables cross-database analysis.

**Trade-off:**

Some engine-specific schema features may not fit perfectly into a common representation.

### Safety Analysis

**Advantage:**

Makes potentially dangerous changes visible.

**Trade-off:**

Analysis cannot determine the developer's intent with complete certainty.

---

# 44. Human Review Remains Important

The project is designed to assist developers rather than replace their judgment.

For example:

```text
DROP TABLE users;
```

can be identified as destructive.

But the tool cannot know whether:

```text
users
```

is intentionally being removed as part of a planned feature.

Therefore, analysis produces information rather than making arbitrary decisions for the developer.

---

# 45. Overall Architectural Principle

The main design principle can be summarized as:

```text
Make database changes:

Explicit
     +
Inspectable
     +
Versioned
     +
Traceable
     +
Testable
     +
Protected
```

The architecture is structured around achieving these properties without hiding the actual database operations from the developer.

---

# Summary

The major design decisions in `dbmigrate` are centered around explicitness and separation of responsibilities.

The architecture intentionally uses:

```text
SQL Migration Files
Versioned Migrations
Migration History
Checksums
Database Abstraction
Database Dialects
Database Capabilities
Database-Specific Locking
Transactions
Planning
Validation
Linting
Impact Analysis
Schema Analysis
Fingerprints
Reproducibility
Automated Testing
CI
```

At the same time, it intentionally avoids:

```text
Automatic SQL Translation
Automatic Production Repair
ORM Behavior
Distributed Orchestration
Universal SQL Parsing
```

The result is a migration tool that focuses on understanding and controlling schema evolution rather than hiding database behavior behind a large abstraction.