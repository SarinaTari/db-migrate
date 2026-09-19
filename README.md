# db-migrate

A Python-based database migration and schema-evolution CLI focused on
safety, integrity, and explainability.

The project is being built from scratch as a serious software-engineering
project rather than as a simple migration script.

---

## Project Goal

`db-migrate` is designed to manage versioned database schema changes while
making migrations understandable, testable, reproducible, and safe.

The project will begin with SQLite and later introduce PostgreSQL and MySQL.

The long-term goal is not simply to execute SQL files.

The tool will provide:

- migration discovery
- migration validation
- migration execution
- rollback
- migration history
- integrity verification
- checksums
- migration planning
- migration linting
- migration explanation
- schema inspection
- schema comparison
- schema fingerprints
- reproducibility checks
- impact analysis
- safety diagnostics
- CI-oriented validation

Only features that have actually been implemented will be advertised as
available functionality.

---

## Project Identity

| Item | Value |
|---|---|
| Repository | `db-migrate` |
| Python package | `dbmigrate` |
| CLI | `dbmigrate` |
| Language | Python |
| Initial database | SQLite |
| Later databases | PostgreSQL, MySQL |
| License | MIT |

---

## Current Status

The project is currently in **Phase 3 — Configuration**.

### Phase 0 — Database Migration Concepts

Established:

- database migration concepts
- migration lifecycle
- architecture
- safety principles
- reproducibility principles
- project scope

### Phase 1 — Professional Python Project

Established:

- Python package
- `src/` layout
- packaging configuration
- CLI entry point
- version handling
- pytest configuration
- initial automated tests

### Phase 2 — CLI Foundation

Established:

- top-level CLI parser
- CLI subcommands
- command registry
- command resolution
- command dispatch
- command-specific help
- CLI tests

### Phase 3 — Configuration

Established:

- project configuration
- TOML configuration loading
- project-root discovery
- configurable migration directory
- configuration validation
- configuration-specific errors

The migration engine has not been implemented yet.

---

## Configuration

A dbmigrate project uses:

```text
dbmigrate.toml

A minimal configuration is:

[migrations]
directory = "migrations"

The directory setting is optional and defaults to:

migrations

The configuration file is discovered by searching upward from the current
working directory.

For example:

my-project/
├── dbmigrate.toml
├── migrations/
└── src/
    └── application/

Running:

dbmigrate status

from inside src/application/ will locate the project's configuration.

CLI

Global commands:

dbmigrate --help
dbmigrate --version

The planned command interface is:

dbmigrate init
dbmigrate create
dbmigrate up
dbmigrate down
dbmigrate status
dbmigrate history
dbmigrate current
dbmigrate validate
dbmigrate plan
dbmigrate lint
dbmigrate explain
dbmigrate impact
dbmigrate schema
dbmigrate schema-diff
dbmigrate fingerprint
dbmigrate doctor
dbmigrate check
dbmigrate verify-schema

The commands are currently placeholders except for the configuration-aware
CLI foundation.

Only implemented behavior will be documented as available functionality.

Architecture

The current architecture is:

User
 |
 v
CLI
 |
 v
Argument Parser
 |
 v
Command Layer
 |
 v
Configuration

The intended application architecture will eventually become:

CLI
 |
 v
Command Layer
 |
 v
Migration Service
 |
 +--> Discovery
 |
 +--> Planning
 |
 +--> Validation
 |
 +--> Execution
 |
 +--> History
 |
 +--> Integrity
 |
 v
Database Interface
 |
 +--> SQLite
 +--> PostgreSQL
 +--> MySQL

Additional analysis layers will eventually provide:

Migration Analysis
 |
 +--> Linter
 +--> Explainer
 +--> Impact Analyzer

Schema Analysis
 |
 +--> Inspector
 +--> Diff
 +--> Fingerprint
 +--> Reproducibility

The architecture will evolve as implementation reveals real requirements.

The project deliberately avoids unnecessary abstraction before it is justified.

Migration Model

The planned migration format is:

-- migration: 001
-- name: create_users

-- +up

CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);

-- +down

DROP TABLE users;

Migrations will be versioned and applied in a deterministic order.

The migration history will eventually be tracked inside the target database.

A conceptual history table is:

CREATE TABLE schema_migrations (
    version INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    checksum TEXT NOT NULL,
    applied_at TIMESTAMP NOT NULL
);

The actual implementation will be introduced in later phases.

Safety Principles

Database migration software can modify important persistent state.

The project therefore prioritizes:

deterministic execution
transaction safety where supported
explicit planning
dry-run behavior
validation
migration checksums
history integrity
failure visibility
reproducibility
clear error messages
conservative behavior

The tool should prefer making potentially dangerous behavior visible before
performing it.

Development Philosophy

The project is being developed incrementally.

Each phase should:

introduce a coherent capability
explain the underlying engineering concept
implement the capability
test the implementation
document the result
leave the repository in a working state

The project should not become a collection of unrelated features.

Development Setup

Python 3.12 or newer is required.

Create a virtual environment:

python3 -m venv .venv

Activate it on macOS/Linux:

source .venv/bin/activate

Install the project with development dependencies:

python -m pip install -e ".[dev]"
Running the CLI

Check the version:

dbmigrate --version

Expected:

dbmigrate 0.1.0

Show help:

dbmigrate --help

Project-dependent commands require a dbmigrate.toml configuration file.

Running Tests

Run the complete test suite:

pytest

or:

python -m pytest
Project Structure
db-migrate/
├── README.md
├── LICENSE
├── .gitignore
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
│   └── phase-3.md
│
├── migrations/
│   └── .gitkeep
│
├── src/
│   └── dbmigrate/
│       ├── __init__.py
│       ├── cli.py
│       ├── config.py
│       └── commands/
│           ├── __init__.py
│           └── base.py
│
└── tests/
    ├── test_cli.py
    ├── test_commands.py
    └── test_config.py
Roadmap
Phase 0  Database Migration Concepts                 ✓
Phase 1  Professional Python Project               ✓
Phase 2  CLI Foundation                             ✓
Phase 3  Configuration                              ✓
Phase 4  Migration Format                            →
Phase 5  Discovery and Validation
Phase 6  Database Interface + SQLite
Phase 7  Migration History
Phase 8  Migration Runner
Phase 9  Transaction and Failure Semantics
Phase 10 Down/Rollback
Phase 11 Status/History/Current
Phase 12 Create Command
Phase 13 Validation
Phase 14 Checksums
Phase 15 Dry Run and Planning
Phase 16 Migration Linter
Phase 17 Explain and Impact
Phase 18 Schema Inspection/Fingerprints
Phase 19 Schema Diff/Reproducibility
Phase 20 Database Abstraction Review
Phase 21 PostgreSQL
Phase 22 MySQL
Phase 23 SQL Dialect/Capability System
Phase 24 Locking/Concurrency
Phase 25 Safety and Doctor
Phase 26 CI Mode
Phase 27 Logging
Phase 28 Performance
Phase 29 Full Integration Testing
Phase 30 Architecture Review
Phase 31 Documentation
Phase 32 Example Project
Phase 33 Portfolio Finalization
License

This project is licensed under the MIT License.