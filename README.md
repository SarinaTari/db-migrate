# db-migrate

A Python-based database migration and schema-evolution CLI focused on safety, integrity, explainability, and migration analysis.

## Project Status

**Current phase: Phase 4 — Migration Format**

The project is being developed as a serious portfolio-quality software engineering project.

The current implementation provides:

- Professional Python project structure
- `dbmigrate` command-line interface
- Project configuration
- Automatic project-root discovery
- Migration file format
- Migration parsing
- Migration validation
- Migration discovery
- Deterministic migration ordering
- Duplicate migration-version detection
- Automated tests

Database execution has not been implemented yet.

SQLite will be introduced in Phase 6.

---

## Project Goal

`db-migrate` is designed to manage database schema evolution through versioned migration files.

Instead of manually applying schema changes, developers will eventually be able to use commands such as:

```bash
dbmigrate create add_email_to_users
dbmigrate up
dbmigrate down
dbmigrate status
dbmigrate history
dbmigrate plan

The project will progressively add:

migration execution
rollback
migration history
checksums
transactions
dry-run planning
migration linting
migration explanation
impact analysis
schema inspection
schema fingerprints
schema diffing
reproducibility checks
SQLite support
PostgreSQL support
MySQL support
locking and concurrency protection
CI-oriented validation
project diagnostics

Only implemented features will be advertised as available.

Migration Model

A migration represents one versioned change to a database schema.

A migration contains:

migration version
migration name
up SQL
down SQL

Example:

-- migration: 001
-- name: create_users

-- +up

CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);

-- +down

DROP TABLE users;

The up section describes how to apply the migration.

The down section describes how to reverse it.

Migration Filenames

Migration files use the following convention:

<version>_<name>.sql

Examples:

001_create_users.sql
002_add_email.sql
003_create_posts.sql

Names use lowercase letters, numbers, underscores, and hyphens.

Migration versions must be positive integers.

Migration Metadata

The filename and internal metadata must agree.

For example:

001_create_users.sql

must contain:

-- migration: 001
-- name: create_users

This prevents a migration from accidentally identifying itself differently from its filename.

Migration Sections

Every migration must contain exactly one:

-- +up

and exactly one:

-- +down

The order must be:

metadata

-- +up

UP SQL

-- +down

DOWN SQL

Both SQL sections must contain content.

Phase 4 Architecture

Migration processing currently follows:

Migration Directory
        │
        ↓
File Discovery
        │
        ↓
Filename Validation
        │
        ↓
Metadata Parsing
        │
        ↓
Section Parsing
        │
        ↓
Migration Object
        │
        ↓
Migration Collection

The resulting migration objects are immutable domain objects.

Configuration

Project configuration is stored in:

dbmigrate.toml

Example:

[migrations]
directory = "migrations"

A template is provided:

dbmigrate.toml.example

Local dbmigrate.toml files are ignored by Git because they may eventually contain environment-specific database configuration.

CLI

The CLI is already established, but most commands are intentionally placeholders until their corresponding phases.

dbmigrate --help
dbmigrate --version

Available command names include:

init
create
up
down
status
history
current
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
verify-schema

The commands will be implemented progressively.

Current Limitations

Phase 4 does not yet:

connect to a database
execute SQL
create a migration history table
apply migrations
roll back migrations
calculate migration checksums
inspect a database schema
support SQLite execution
support PostgreSQL
support MySQL

These features belong to later phases.

Architecture Direction

The intended architecture is:

CLI
 │
 ↓
Command Layer
 │
 ↓
Migration Service
 │
 ├── Discovery
 ├── Parsing
 ├── Validation
 └── Planning
 │
 ↓
Execution
 │
 ↓
History / Integrity
 │
 ↓
Database Interface
 │
 ├── SQLite
 ├── PostgreSQL
 └── MySQL

Analysis capabilities will eventually sit alongside the migration engine:

Migration Analysis
├── Linter
├── Explainer
└── Impact Analyzer

Schema Analysis
├── Schema Inspector
├── Schema Diff
├── Fingerprint
└── Reproducibility Checks
Safety Philosophy

The project is designed around several principles:

validate before execution
make migration order explicit
never silently ignore malformed migrations
preserve migration history
detect modified migrations
use transactions where supported
provide dry-run and planning capabilities
distinguish database capabilities
make potentially dangerous operations visible
prefer explicit failure over silent corruption
Testing

The project uses pytest.

Run:

pytest

The Phase 4 tests cover:

migration filename parsing
migration metadata parsing
version consistency
name consistency
up section validation
down section validation
empty-section detection
section ordering
migration discovery
migration ordering
duplicate versions
invalid paths
non-SQL files
configuration
CLI behavior
Development Setup

Create a virtual environment:

python3 -m venv .venv

Activate it:

source .venv/bin/activate

Install the project in editable mode:

python -m pip install -e ".[dev]"

Run the tests:

pytest
Project Structure
db-migrate/
├── .gitignore
├── LICENSE
├── README.md
├── pyproject.toml
├── dbmigrate.toml.example
│
├── docs/
│   ├── architecture.md
│   ├── database-migrations.md
│   ├── migration-lifecycle.md
│   ├── phase-0.md
│   ├── phase-1.md
│   ├── phase-2.md
│   ├── phase-3.md
│   └── phase-4.md
│
├── migrations/
│   └── .gitkeep
│
├── src/
│   └── dbmigrate/
│       ├── __init__.py
│       ├── cli.py
│       ├── config.py
│       ├── migration.py
│       └── commands/
│           ├── __init__.py
│           └── base.py
│
└── tests/
    ├── test_cli.py
    ├── test_commands.py
    ├── test_config.py
    └── test_migration.py
Roadmap
Phase 0   Database Migration Concepts             ✓
Phase 1   Professional Python Project             ✓
Phase 2   CLI Foundation                          ✓
Phase 3   Configuration                           ✓
Phase 4   Migration Format                        ✓
Phase 5   Discovery and Validation                →
Phase 6   Database Interface + SQLite
Phase 7   Migration History
Phase 8   Migration Runner
Phase 9   Transaction and Failure Semantics
Phase 10  Down / Rollback
Phase 11  Status / History / Current
Phase 12  Create Command
Phase 13  Validation
Phase 14  Checksums
Phase 15  Dry Run and Planning
Phase 16  Migration Linter
Phase 17  Explain and Impact
Phase 18  Schema Inspection / Fingerprints
Phase 19  Schema Diff / Reproducibility
Phase 20  Database Abstraction Review
Phase 21  PostgreSQL
Phase 22  MySQL
Phase 23  SQL Dialect / Capability System
Phase 24  Locking / Concurrency
Phase 25  Safety and Doctor
Phase 26  CI Mode
Phase 27  Logging
Phase 28  Performance
Phase 29  Full Integration Testing
Phase 30  Architecture Review
Phase 31  Documentation
Phase 32  Example Project
Phase 33  Portfolio Finalization
Portfolio Description

db-migrate is a Python-based database migration and schema-evolution CLI designed to manage versioned database changes with an emphasis on safety, integrity, explainability, and migration analysis.

As development progresses, the project will support SQLite, PostgreSQL, and MySQL while maintaining a database-independent migration architecture.