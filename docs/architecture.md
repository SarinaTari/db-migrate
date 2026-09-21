# Architecture

## Overview

`dbmigrate` is a Python-based database migration and schema-evolution tool focused on safety, integrity, explainability, and database portability.

The project uses a layered architecture that separates the command-line interface from configuration, migration management, database access, execution, validation, safety checks, and schema analysis.

At a high level:

```text
CLI
 │
 ▼
Command / Service Layer
 │
 ├── Configuration
 ├── Migration Discovery
 ├── Planning
 ├── Validation
 ├── Safety Checks
 ├── Execution
 └── Analysis
       │
       ▼
Database Abstraction
 │
 ├── SQLite
 ├── PostgreSQL
 └── MySQL
```

## Architectural Goals

### Safety

Migration execution should minimize the risk of destructive or inconsistent database changes.

The project therefore includes:

- migration validation
- migration safety analysis
- checksums
- transactions where supported
- migration locking
- database diagnostics

### Integrity

Migration history and migration files should remain consistent.

The project uses:

- migration checksums
- persistent migration history
- schema fingerprints
- schema comparison
- reproducibility checks

### Explainability

Database changes should be understandable before they are executed.

The project provides:

- migration planning
- SQL linting
- SQL explanations
- impact analysis
- schema differences

### Portability

The migration engine is built around a database abstraction rather than being tied to a single database engine.

The current architecture supports:

- SQLite
- PostgreSQL
- MySQL

---

# Project Structure

```text
db-migrate/
├── .github/
│   └── workflows/
│       └── ci.yml
│
├── docs/
│   ├── architecture.md
│   ├── migration-format.md
│   ├── migration-lifecycle.md
│   ├── database-support.md
│   ├── safety-and-integrity.md
│   ├── schema-analysis.md
│   ├── commands.md
│   ├── testing-and-ci.md
│   ├── design-decisions.md
│   └── limitations-and-future-work.md
│
├── migrations/
│   └── 001_create_users.sql
│
├── src/
│   └── dbmigrate/
│       ├── database.py
│       ├── database_capabilities.py
│       ├── database_dialect.py
│       ├── database_factory.py
│       ├── database_lock.py
│       ├── database_mysql.py
│       ├── database_postgres.py
│       ├── migration.py
│       ├── migration_creator.py
│       ├── migration_safety.py
│       ├── history.py
│       ├── planner.py
│       ├── runner.py
│       ├── status.py
│       ├── validation.py
│       ├── checksum.py
│       ├── reproducibility.py
│       ├── schema.py
│       ├── schema_diff.py
│       ├── impact.py
│       ├── linter.py
│       ├── explainer.py
│       ├── doctor.py
│       ├── performance.py
│       ├── ci.py
│       ├── config.py
│       ├── logging_config.py
│       ├── cli.py
│       └── __init__.py
│
├── tests/
├── pyproject.toml
├── dbmigrate.toml.example
├── README.md
└── LICENSE
```

---

# Architectural Layers

## 1. CLI Layer

The CLI is primarily implemented in:

```text
src/dbmigrate/cli.py
```

Its responsibilities include:

- parsing command-line arguments
- loading project configuration
- configuring logging
- creating the appropriate database implementation
- dispatching commands
- formatting user-facing output
- handling command-level errors

The CLI does not contain the core migration algorithms.

This keeps command-line behavior separate from the underlying migration engine and makes the core functionality easier to test.

---

## 2. Configuration Layer

Configuration is implemented in:

```text
src/dbmigrate/config.py
```

The configuration system is responsible for:

- discovering the project root
- locating the migrations directory
- loading `dbmigrate.toml`
- providing database configuration
- validating configuration values

A template is provided as:

```text
dbmigrate.toml.example
```

The local `dbmigrate.toml` is environment-specific and is intentionally excluded from version control.

---

## 3. Migration Layer

Migration management is centered around:

```text
migration.py
migration_creator.py
validation.py
checksum.py
history.py
planner.py
runner.py
status.py
```

This layer is responsible for:

- discovering migration files
- parsing migration files
- creating migrations
- ordering migrations
- validating migration structure
- detecting duplicate versions
- calculating checksums
- determining migration state
- planning pending migrations
- executing migrations
- maintaining migration history

The general flow is:

```text
Migration Files
      │
      ▼
Discovery
      │
      ▼
Parsing
      │
      ▼
Validation
      │
      ▼
Checksum Verification
      │
      ▼
Planning
      │
      ▼
Execution
      │
      ▼
Migration History
```

---

## 4. Database Abstraction Layer

Database access is implemented through:

```text
database.py
database_factory.py
database_capabilities.py
database_dialect.py
database_mysql.py
database_postgres.py
```

The main `Database` abstraction defines the common database operations required by the migration system.

Concrete implementations provide database-specific behavior.

The factory selects the appropriate implementation from the configured database URL.

---

## 5. Database Dialect Layer

Different database engines use different SQL conventions.

The `DatabaseDialect` abstraction isolates these differences.

It provides database-specific information such as:

- parameter placeholders
- identifier quoting
- database version queries

For example:

```text
SQLite       ?
PostgreSQL   %s
MySQL        %s
```

Identifier quoting is also handled by the dialect.

This prevents database-specific SQL conventions from being duplicated throughout the migration system.

---

## 6. Database Capability Layer

Different database engines do not provide exactly the same features.

`DatabaseCapabilities` represents database-specific capabilities such as:

- transactional DDL
- `DROP COLUMN`
- schemas
- advisory locks

Higher-level components can therefore inspect capabilities instead of making assumptions about a particular database engine.

Current capability definitions are:

| Capability | SQLite | PostgreSQL | MySQL |
|------------|:------:|:----------:|:-----:|
| Transactional DDL | Yes | Yes | No |
| Drop column | Yes | Yes | Yes |
| Schemas | No | Yes | Yes |
| Advisory locks | No | Yes | Yes |

---

## 7. Database Factory

The database factory converts a database URL into the appropriate database implementation.

Supported URL schemes include:

```text
sqlite:///
postgresql://
postgres://
mysql://
```

The factory normalizes equivalent PostgreSQL schemes and validates required connection information for server-based databases.

This keeps connection construction outside the rest of the application.

---

## 8. Migration History Layer

Migration history is stored in the database using the:

```text
schema_migrations
```

table.

The table records:

- migration version
- migration name
- migration checksum
- application timestamp

The history component provides operations for:

- recording applied migrations
- removing migration records
- checking whether a migration is applied
- retrieving applied migrations
- determining the latest applied migration
- retrieving applied migration versions

Migration history is used by the planner and status system to determine migration state.

---

## 9. Planning Layer

The planner compares migration files against recorded migration history.

Conceptually:

```text
Migration Files
       │
       ▼
Applied History
       │
       ▼
Pending Migrations
```

Planning is read-only.

It does not:

- execute migration SQL
- modify schema state
- modify migration history

This makes it safe to inspect what `dbmigrate` intends to execute before applying changes.

---

## 10. Execution Layer

Migration execution is handled by:

```text
runner.py
```

The runner is responsible for:

- applying migrations
- rolling back migrations
- applying multiple pending migrations
- rolling back multiple migrations
- verifying migration checksums
- updating migration history

The conceptual execution flow is:

```text
Migration
    │
    ▼
Acquire Migration Lock
    │
    ▼
Begin Transaction
    │
    ├── Execute Migration SQL
    │
    └── Update Migration History
    │
    ▼
Commit
    │
    ▼
Release Migration Lock
```

The exact transactional behavior depends on the capabilities of the selected database engine.

---

## 11. Validation Layer

Migration validation is implemented in:

```text
validation.py
```

Validation checks migration structure and consistency before execution.

Examples include:

- valid migration numbering
- valid migration names
- duplicate versions
- duplicate migration identifiers
- malformed migration files
- checksum mismatches

Validation produces structured issues that can be inspected by higher-level commands.

---

## 12. Safety Layer

Migration safety is implemented in:

```text
migration_safety.py
```

and supported by:

```text
impact.py
linter.py
```

The safety system identifies potentially dangerous migration operations.

Examples include:

```sql
DROP TABLE
DROP COLUMN
DELETE without WHERE
UPDATE without WHERE
```

The safety system is separate from execution so migrations can be analyzed before SQL is executed.

---

## 13. Schema Layer

Schema inspection is implemented in:

```text
schema.py
```

The schema system represents database structures such as:

- tables
- columns
- indexes
- foreign keys
- views

Schema information is converted into structured Python representations rather than being handled as raw database output throughout the application.

This provides a foundation for:

- schema fingerprints
- schema differences
- impact analysis
- reproducibility checks

---

## 14. Schema Difference Layer

Schema comparison is implemented in:

```text
schema_diff.py
```

It compares two schema representations and identifies changes such as:

- added tables
- removed tables
- modified tables
- added columns
- removed columns
- modified columns
- added indexes
- removed indexes
- foreign-key changes
- view changes

The result is represented as structured schema differences.

---

## 15. Analysis Layer

Migration analysis is implemented through:

```text
impact.py
linter.py
explainer.py
```

### Impact Analysis

Impact analysis examines migration operations and classifies their potential effect.

### Linter

The linter identifies potentially dangerous SQL patterns before execution.

### Explainer

The explainer identifies supported SQL operations and produces human-readable explanations of what a migration does.

These components are analysis tools rather than execution components.

---

## 16. Reproducibility Layer

Reproducibility checking is implemented in:

```text
reproducibility.py
```

The basic workflow is:

```text
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
Compare Target Schema
```

This can be used to determine whether a database schema can be reproduced from the migration history.

The current reproducibility implementation operates with SQLite.

---

## 17. Locking Layer

Migration locking is implemented in:

```text
database_lock.py
```

The locking abstraction provides database-specific mechanisms to prevent concurrent migration processes from operating on the same migration state.

### SQLite

SQLite uses a filesystem lock:

```text
.dbmigrate.lock
```

with an exclusive non-blocking file lock.

### PostgreSQL

PostgreSQL uses advisory locking.

### MySQL

MySQL uses:

```sql
GET_LOCK(...)
```

and:

```sql
RELEASE_LOCK(...)
```

The rest of the migration system uses the common lock abstraction rather than depending directly on one locking mechanism.

---

## 18. Diagnostics Layer

Database diagnostics are implemented in:

```text
doctor.py
```

The doctor system checks important environment and database information, including:

- database connectivity
- database engine
- database version
- database capabilities
- safety-related conditions

The goal is to expose configuration and environment problems before migration execution.

---

## 19. Performance Layer

Performance utilities are implemented in:

```text
performance.py
```

The module provides lightweight measurement helpers for timing operations.

The performance system is intentionally small and independent from the migration execution engine.

---

## 20. CI Layer

CI functionality is implemented in:

```text
ci.py
```

The project also contains a GitHub Actions workflow that:

1. checks out the repository
2. installs Python
3. installs the project and development dependencies
4. runs the automated test suite
5. runs the migration CI command

The workflow currently tests Python 3.12 and Python 3.13.

---

# Dependency Direction

The architecture follows a generally layered dependency direction:

```text
CLI
 │
 ├── Configuration
 │
 ▼
Migration / Service Logic
 │
 ├── Validation
 ├── Safety
 ├── Planning
 ├── Analysis
 └── Execution
       │
       ▼
Database Abstraction
       │
       ├── SQLite
       ├── PostgreSQL
       └── MySQL
```

Lower-level database components do not depend on the CLI.

This separation makes the system easier to test and maintain.

---

# Error Handling

The project uses domain-specific exceptions for different failure categories.

Examples include errors related to:

- database operations
- migration parsing
- migration discovery
- migration execution
- validation
- checksums
- locking
- configuration

Lower-level components raise meaningful application-specific errors.

The CLI provides the final user-facing error boundary and converts application failures into readable messages and appropriate command results.

---

# Testing Architecture

The test suite is organized around the project's architectural layers.

It covers:

- database behavior
- database abstraction
- database capabilities
- database dialects
- database factory
- migration locking
- migration parsing
- migration history
- migration planning
- migration execution
- migration status
- migration validation
- checksums
- migration creation
- migration safety
- reproducibility
- schema inspection
- schema differences
- impact analysis
- linting
- explanations
- diagnostics
- performance
- CI
- configuration
- logging
- CLI behavior

The final Phase 23 baseline contains:

```text
300 passing tests
```

---

# Architectural Summary

The system separates the major responsibilities of a database migration tool:

```text
User Command
     │
     ▼
CLI
     │
     ▼
Configuration
     │
     ▼
Migration Discovery
     │
     ▼
Validation
     │
     ▼
Planning / Analysis
     │
     ▼
Safety Checks
     │
     ▼
Migration Execution
     │
     ├── Database Lock
     ├── Transaction
     ├── SQL Execution
     └── Migration History
     │
     ▼
Database
```

The architecture is intentionally modular so that database-specific behavior remains isolated while migration management, safety, analysis, and CLI functionality remain reusable across supported database engines.