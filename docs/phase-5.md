# Phase 5 — Discovery and Validation

## Objective

Phase 5 extends the migration system from individual-file parsing to project-level migration validation.

Phase 4 answered:

> Is this migration file structurally valid?

Phase 5 asks:

> Is the migration collection consistent?

---

## Validation Layers

The migration system now has two validation levels.

### File-level validation

Handled by `migration.py`.

Checks:

- filename
- version
- name
- metadata
- up section
- down section
- section ordering
- filename/metadata consistency

### Project-level validation

Handled by `validation.py`.

Checks:

- migration sequence
- duplicate names
- migration collection discovery
- parser/discovery failures

---

## Validation Report

Validation produces a `ValidationReport`.

It contains:

```text
migrations
issues

The report also provides:

is_valid
migration_count

This makes validation useful both for the CLI and future programmatic consumers.

Validation Issues

Each issue contains:

code
message
path
version

Examples:

MIGRATION_GAP
DUPLICATE_NAME
MIGRATION_PARSE_ERROR
MIGRATION_DISCOVERY_ERROR
Migration Sequence

The current validation policy expects migration versions to form a continuous sequence beginning at:

001

For example:

001_create_users.sql
002_add_email.sql
003_create_posts.sql

is valid.

But:

001_create_users.sql
003_create_posts.sql

produces:

MIGRATION_GAP

because version 002 is missing.

Duplicate Names

Migration versions must be unique.

Migration names must also be unique.

For example:

001_create_users.sql
002_create_users.sql

is rejected because the migration name is duplicated.

Validation CLI

Phase 5 introduces the first functional command:

dbmigrate validate

Successful output looks conceptually like:

Migration directory: /project/migrations
Validation successful: 3 migration(s) found.
  001_create_users.sql
  002_add_email.sql
  003_create_posts.sql

An invalid collection reports the problem and returns a non-zero exit code.

Important Boundary

Phase 5 still does not execute SQL.

Validation checks the migration files and their organization.

It does not verify whether:

CREATE TABLE users (...)

is valid for SQLite, PostgreSQL, or MySQL.

Database-aware validation will become relevant after the database abstraction is introduced.

Why This Phase Exists

Separating discovery and validation from execution provides an important safety boundary.

The intended future flow is:

Discover
   ↓
Parse
   ↓
Validate
   ↓
Plan
   ↓
Execute

Execution should never be the first step.

Testing

Phase 5 adds tests for:

empty migration directories
valid contiguous migrations
missing migration versions
duplicate versions
duplicate names
malformed migration files
missing migration directories
deterministic ordering
validation issue formatting
successful CLI validation
failed CLI validation
configuration errors
Completion Criteria

Phase 5 is complete when:

project-level migration validation exists
migration gaps are detected
duplicate names are detected
parser failures are surfaced through validation
validation results are structured
dbmigrate validate works
invalid migration collections return non-zero status
tests cover the validation system
Next Phase

Phase 6 introduces the database abstraction and the first actual backend:

SQLite

The next major architectural transition will be:

Migration
   ↓
Database Interface
   ↓
SQLite

At that point, the project will be able to execute real SQL against a real database.