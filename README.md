# db-migrate

A Python-based database migration and schema-evolution CLI focused on safety, integrity, and explainability.

The project is being built from scratch as a serious software-engineering project rather than as a simple migration script.

---

## Project Goal

`db-migrate` is designed to manage versioned database schema changes while making migrations understandable, testable, reproducible, and safe.

The project will begin with SQLite and later introduce PostgreSQL and MySQL.

The long-term goal is not simply to execute SQL files.

The tool will provide:

* migration discovery
* migration validation
* migration execution
* rollback
* migration history
* integrity verification
* checksums
* migration planning
* migration linting
* migration explanation
* schema inspection
* schema comparison
* schema fingerprints
* reproducibility checks
* impact analysis
* safety diagnostics
* CI-oriented validation

Only features that have actually been implemented will be advertised as available functionality.

---

## Project Identity

| Item             | Value             |
| ---------------- | ----------------- |
| Repository       | `db-migrate`      |
| Python package   | `dbmigrate`       |
| CLI              | `dbmigrate`       |
| Language         | Python            |
| Initial database | SQLite            |
| Later databases  | PostgreSQL, MySQL |
| License          | MIT               |

---

## Current Status

The project is currently in **Phase 1 — Professional Python Project Foundation**.

Phase 0 established the project's conceptual model, architecture, migration lifecycle, safety principles, and documentation.

Phase 1 establishes:

* the Python package
* the `src/` layout
* project packaging
* CLI entry point
* version handling
* pytest configuration
* initial automated tests

The migration engine has not been implemented yet.

---

## Planned Commands

The planned CLI will eventually include commands such as:

```text
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
dbmigrate version
```

These commands are part of the project's planned roadmap and should not be interpreted as already implemented.

---

## Architecture

The intended architecture is:

```text
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
```

Additional analysis layers will eventually provide:

```text
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
```

The architecture will evolve as implementation reveals real requirements.

The project deliberately avoids unnecessary abstraction before it is justified.

---

## Migration Model

The planned migration format is:

```sql
-- migration: 001
-- name: create_users

-- +up

CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);

-- +down

DROP TABLE users;
```

Migrations will be versioned and applied in a deterministic order.

The migration history will eventually be tracked inside the target database.

A conceptual history table is:

```sql
CREATE TABLE schema_migrations (
    version INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    checksum TEXT NOT NULL,
    applied_at TIMESTAMP NOT NULL
);
```

The actual implementation will be introduced in later phases.

---

## Safety Principles

Database migration software can modify important persistent state.

The project therefore prioritizes:

* deterministic execution
* transaction safety where supported
* explicit planning
* dry-run behavior
* validation
* migration checksums
* history integrity
* failure visibility
* reproducibility
* clear error messages
* conservative behavior

The tool should prefer making potentially dangerous behavior visible before performing it.

---

## Development Philosophy

The project is being developed incrementally.

Each phase should:

1. introduce a coherent capability
2. explain the underlying engineering concept
3. implement the capability
4. test the implementation
5. document the result
6. leave the repository in a working state

The project should not become a collection of unrelated features.

---

## Development Setup

Python 3.12 or newer is required.

Create a virtual environment:

```bash
python3 -m venv .venv
```

Activate it on macOS/Linux:

```bash
source .venv/bin/activate
```

Install the project with development dependencies:

```bash
python -m pip install -e ".[dev]"
```

---

## Running the CLI

After installation:

```bash
dbmigrate --help
```

Check the version:

```bash
dbmigrate --version
```

Expected:

```text
dbmigrate 0.1.0
```

---

## Running Tests

Run the complete test suite:

```bash
pytest
```

or:

```bash
python -m pytest
```

---

## Project Structure

```text
db-migrate/
├── README.md
├── LICENSE
├── .gitignore
├── pyproject.toml
│
├── docs/
│   ├── architecture.md
│   ├── database-migrations.md
│   ├── migration-lifecycle.md
│   ├── phase-0.md
│   └── phase-1.md
│
├── migrations/
│   └── .gitkeep
│
├── src/
│   └── dbmigrate/
│       ├── __init__.py
│       └── cli.py
│
└── tests/
    └── test_cli.py
```

---

## Roadmap

```text
Phase 0  Database Migration Concepts                 ✓
Phase 1  Professional Python Project               ✓
Phase 2  CLI Foundation                             →
Phase 3  Configuration
Phase 4  Migration Format
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
```

---

## License

This project is licensed under the MIT License.
