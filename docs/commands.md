# Commands

## Overview

`dbmigrate` provides a command-line interface for creating, validating, planning, executing, inspecting, and analyzing database migrations.

The CLI is designed around the migration lifecycle:

```text
Create
  ↓
Validate
  ↓
Plan
  ↓
Analyze
  ↓
Execute
  ↓
Inspect
  ↓
Verify
```

Run:

```bash
dbmigrate --help
```

to see the commands and options available in the installed version.

---

# 1. `init`

Initializes a new `dbmigrate` project.

```bash
dbmigrate init
```

The command prepares the project structure required by the migration system.

A typical project contains:

```text
project/
├── migrations/
├── dbmigrate.toml
└── ...
```

Initialization is intended for starting a new migration project.

---

# 2. `create`

Creates a new migration file.

```bash
dbmigrate create <name>
```

Example:

```bash
dbmigrate create create_users
```

The migration creator assigns the next migration version and creates a migration file containing the expected structure.

Example:

```text
migrations/
└── 001_create_users.sql
```

The generated file contains:

```sql
-- migration: 001
-- name: create_users

-- +up

-- Migration SQL

-- +down

-- Rollback SQL
```

Creating a migration does not modify the database.

---

# 3. `up`

Applies pending migrations.

```bash
dbmigrate up
```

The command determines which migrations have not yet been recorded as applied and executes them in version order.

Conceptually:

```text
Migration Files
      │
      ▼
Migration History
      │
      ▼
Pending Migrations
      │
      ▼
Execute
      │
      ▼
Record History
```

The migration lock and database transaction behavior are applied according to the selected database backend.

---

# 4. `down`

Rolls back applied migrations.

```bash
dbmigrate down
```

The rollback uses the migration's `down` section.

For example:

```sql
-- +down

DROP TABLE users;
```

The most recently applied migration is rolled back first.

Where supported by the command interface, rollback can be controlled by the number of steps.

For example:

```bash
dbmigrate down --steps 2
```

would conceptually roll back the two most recent applied migrations.

---

# 5. `status`

Displays migration state.

```bash
dbmigrate status
```

The status command compares migration files with recorded migration history.

Example:

```text
Applied:
  001_create_users
  002_add_email

Pending:
  003_create_orders
```

This is useful for determining whether the database has pending migrations.

---

# 6. `history`

Displays migration history.

```bash
dbmigrate history
```

The history is stored in:

```text
schema_migrations
```

A history record contains information such as:

```text
version
name
checksum
applied_at
```

The command provides a view of migrations that have been recorded by the database.

---

# 7. `current`

Shows the current migration state.

```bash
dbmigrate current
```

The command is useful when you want to quickly determine the current migration position without manually inspecting the migration history table.

The current state is based on recorded migration information rather than assuming that migration files alone represent the database state.

---

# 8. `validate`

Validates migration files.

```bash
dbmigrate validate
```

Validation checks the migration collection for structural and consistency problems.

Examples include:

```text
Invalid migration metadata
Duplicate versions
Malformed migration definitions
Invalid ordering
Checksum-related inconsistencies
```

Validation is intended to detect problems before migration execution.

---

# 9. `plan`

Shows the migrations that would be applied.

```bash
dbmigrate plan
```

Planning is read-only.

It determines the pending migration sequence without applying it.

Example:

```text
Migration plan:

001_create_users
002_add_email
003_create_orders
```

This is useful for reviewing intended changes before executing:

```bash
dbmigrate up
```

---

# 10. `lint`

Analyzes migration SQL for potentially dangerous patterns.

```bash
dbmigrate lint
```

The linter can identify operations such as:

```sql
DROP TABLE
DROP COLUMN
DELETE without WHERE
UPDATE without WHERE
```

The command is designed to make potentially risky SQL visible.

It does not automatically rewrite the migration.

---

# 11. `explain`

Provides a human-readable explanation of migration operations.

```bash
dbmigrate explain
```

The explanation layer identifies supported SQL operations and describes their high-level effect.

For example:

```sql
CREATE TABLE users (...);
```

can be interpreted as:

```text
Create table: users
```

The purpose is to make migration behavior easier to understand during review.

---

# 12. `impact`

Analyzes the potential impact of migrations.

```bash
dbmigrate impact
```

The impact analyzer identifies operations such as:

```text
CREATE TABLE
DROP TABLE
ALTER TABLE
CREATE INDEX
DROP INDEX
```

and provides structured information about their potential effects.

A migration containing destructive operations can therefore be reviewed before execution.

---

# 13. `schema`

Inspects the current database schema.

```bash
dbmigrate schema
```

The schema inspection layer can expose structural information such as:

```text
Tables
Columns
Types
Nullability
Indexes
Constraints
```

The exact available information depends on the database backend and the schema information exposed by its implementation.

---

# 14. `schema-diff`

Compares schemas.

```bash
dbmigrate schema-diff
```

Schema differences can include:

```text
Added tables
Removed tables
Added columns
Removed columns
Changed columns
Added indexes
Removed indexes
```

The command is intended for schema analysis rather than automatic schema repair.

A detected difference does not automatically mean that the database should be modified.

---

# 15. `fingerprint`

Generates or inspects a schema fingerprint.

```bash
dbmigrate fingerprint
```

A schema fingerprint provides a compact representation of the schema.

Conceptually:

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

Fingerprints can be useful when comparing database states.

---

# 16. `doctor`

Runs diagnostic checks on the migration environment.

```bash
dbmigrate doctor
```

The diagnostic subsystem can check aspects of the environment and migration setup.

Typical areas include:

```text
Configuration
Database connectivity
Migration directory
Migration state
Database information
Migration integrity
```

The purpose is to make configuration and environment problems easier to identify.

---

# 17. `check`

Runs consistency-oriented checks.

```bash
dbmigrate check
```

The check functionality provides a higher-level way to inspect whether the migration environment is internally consistent.

It can be used as part of development or CI workflows before applying migrations.

---

# 18. `verify-schema`

Verifies schema state against the information available to the migration system.

```bash
dbmigrate verify-schema
```

The command is intended to help identify differences between expected and actual schema state.

Schema verification should be understood as an integrity check rather than an automatic repair mechanism.

---

# 19. `version`

Displays the installed `dbmigrate` version.

```bash
dbmigrate version
```

The package currently exposes its version through the project metadata and package version information.

---

# 20. `ci`

Runs migration checks in a CI-oriented workflow.

```bash
dbmigrate ci
```

The CI functionality is designed to make migration verification easier to integrate into automated environments.

A CI workflow can combine checks such as:

```text
Migration validation
       │
       ▼
Migration integrity
       │
       ▼
Reproducibility
       │
       ▼
Database checks
       │
       ▼
Exit status
```

A non-zero result can be used by a CI system to fail a pipeline.

---

# 21. Command Categories

The commands can be grouped by purpose.

## Project Setup

```text
init
create
```

## Migration State

```text
status
history
current
```

## Migration Execution

```text
up
down
```

## Validation and Review

```text
validate
plan
lint
explain
impact
```

## Schema Analysis

```text
schema
schema-diff
fingerprint
verify-schema
```

## Diagnostics

```text
doctor
check
version
```

## Automation

```text
ci
```

---

# 22. Typical Development Workflow

A typical development workflow can be:

```bash
dbmigrate init
```

Create a migration:

```bash
dbmigrate create create_users
```

Edit the generated migration:

```text
migrations/001_create_users.sql
```

Validate it:

```bash
dbmigrate validate
```

Inspect the plan:

```bash
dbmigrate plan
```

Review SQL:

```bash
dbmigrate lint
dbmigrate explain
dbmigrate impact
```

Apply it:

```bash
dbmigrate up
```

Check migration state:

```bash
dbmigrate status
```

Inspect the database:

```bash
dbmigrate schema
```

---

# 23. Reviewing Before Execution

A more safety-oriented workflow is:

```text
Create
  │
  ▼
Validate
  │
  ▼
Lint
  │
  ▼
Explain
  │
  ▼
Impact
  │
  ▼
Plan
  │
  ▼
Review
  │
  ▼
Up
```

This workflow separates migration review from migration execution.

The analysis commands are intended to help developers understand the consequences of a migration before changing the database.

---

# 24. Checking Migration State

After applying migrations, useful commands include:

```bash
dbmigrate status
```

and:

```bash
dbmigrate history
```

For schema inspection:

```bash
dbmigrate schema
```

For schema comparison:

```bash
dbmigrate schema-diff
```

For integrity-oriented analysis:

```bash
dbmigrate fingerprint
dbmigrate verify-schema
```

The exact combination depends on what is being investigated.

---

# 25. Rollback Workflow

A basic rollback workflow is:

```bash
dbmigrate status
```

Review the current migration state.

Then:

```bash
dbmigrate down
```

After rollback:

```bash
dbmigrate status
```

and optionally:

```bash
dbmigrate schema
```

can be used to inspect the resulting state.

Rollback should only be considered safe when the migration's `down` SQL correctly represents the desired reverse operation.

---

# 26. CI Workflow

A CI-oriented workflow can use:

```bash
dbmigrate ci
```

alongside the project's Python test suite.

For example:

```bash
python -m pytest
dbmigrate ci
```

The exact CI pipeline can be adapted to the project's environment.

The important principle is that migration validation and reproducibility should be testable automatically rather than relying exclusively on manual checks.

---

# 27. Command Design

The CLI follows several design principles.

### Commands Have Focused Responsibilities

Each command should answer a specific operational or analysis question.

### Analysis Commands Are Preferably Read-Only

Commands such as:

```text
status
history
validate
plan
lint
explain
impact
schema
schema-diff
fingerprint
doctor
check
```

are intended primarily for inspection or analysis rather than modifying application data.

### State-Changing Commands Are Explicit

The primary schema-changing commands are:

```text
up
down
```

This makes destructive state changes explicit.

---

# 28. CLI and Application Architecture

The CLI is a presentation layer over the underlying services.

Conceptually:

```text
Command Line
     │
     ▼
CLI Command
     │
     ▼
Application Service
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

The CLI should therefore not contain the complete implementation of migration behavior.

Instead, it coordinates the appropriate application components.

---

# 29. Error Handling

CLI commands report errors when an operation cannot safely complete.

Examples include:

```text
Invalid migration
Database connection failure
Migration checksum mismatch
Lock failure
SQL execution failure
Configuration error
Schema-analysis failure
```

Errors should result in a clear command failure rather than silently continuing with an uncertain migration state.

---

# 30. Exit Status

The CLI's exit status is important for automation.

Conceptually:

```text
Success
   │
   └── exit code 0

Failure
   │
   └── non-zero exit code
```

This allows commands such as:

```bash
dbmigrate ci
```

to be used inside CI systems and shell scripts.

---

# 31. Database-Specific Commands

The high-level CLI is database-independent where possible.

For example:

```bash
dbmigrate status
```

does not need a different command name for:

```text
SQLite
PostgreSQL
MySQL
```

The database factory selects the appropriate implementation.

Database-specific behavior is handled below the CLI layer through:

```text
Database Implementation
Dialect
Capabilities
Locking
Schema Inspection
```

---

# 32. Command Reference

| Command | Purpose | Changes Database |
|---|---|---|
| `init` | Initialize migration project | No |
| `create` | Create migration file | No |
| `up` | Apply pending migrations | Yes |
| `down` | Roll back migrations | Yes |
| `status` | Show migration state | No |
| `history` | Show recorded history | No |
| `current` | Show current migration state | No |
| `validate` | Validate migrations | No |
| `plan` | Show planned migrations | No |
| `lint` | Analyze migration SQL | No |
| `explain` | Explain migration operations | No |
| `impact` | Analyze migration impact | No |
| `schema` | Inspect database schema | No |
| `schema-diff` | Compare schemas | No |
| `fingerprint` | Inspect schema fingerprint | No |
| `doctor` | Diagnose environment | No |
| `check` | Run consistency checks | No |
| `verify-schema` | Verify schema state | No |
| `version` | Show application version | No |
| `ci` | Run CI-oriented checks | Normally No |

`up` and `down` are the primary commands that intentionally change database state.

---

# Summary

The `dbmigrate` CLI is organized around the complete migration lifecycle.

The main workflow is:

```text
init
  ↓
create
  ↓
validate
  ↓
plan
  ↓
lint / explain / impact
  ↓
up
  ↓
status / history
  ↓
schema / schema-diff / fingerprint
```

For rollback:

```text
status
  ↓
down
  ↓
status
  ↓
schema
```

For automation:

```text
validate
  ↓
checks
  ↓
reproducibility
  ↓
ci
```

The CLI intentionally separates state-changing commands from analysis and diagnostic commands, making the migration process easier to understand, review, automate, and operate safely.