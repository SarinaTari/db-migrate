# 🗃️ db-migrate

> A Python-based database migration and schema-evolution CLI focused on **safety, integrity, explainability, and analysis**.

`db-migrate` is a database migration tool built from scratch in Python for managing versioned SQL migrations and evolving database schemas in a controlled and inspectable way.

The project is designed not only to execute migrations, but also to help developers **understand what a migration will do, validate migration state, detect inconsistencies, inspect schema changes, analyze potential impact, and verify migration integrity**.

It supports **SQLite, PostgreSQL, and MySQL** through a database abstraction layer with database-specific dialects and capabilities.

---

## ✨ Features

### 🔄 Migration Management

- Versioned SQL migration files
- Explicit `up` and `down` migration sections
- Automatic migration discovery
- Migration ordering
- Migration creation
- Migration history tracking
- Migration status inspection
- Forward and rollback execution

### 🧠 Migration Analysis

- Migration planning
- SQL migration linting
- Human-readable migration explanations
- Migration impact analysis
- Schema inspection
- Schema difference analysis
- Schema fingerprinting
- Migration reproducibility checks

### 🔐 Safety & Integrity

- Migration checksums
- Migration integrity verification
- Validation before execution
- Database capability checks
- Migration locking
- Concurrency protection
- Transaction-aware execution
- Production-oriented safety checks
- Diagnostic checks with `doctor`

### 🗄️ Multi-Database Support

- SQLite
- PostgreSQL
- MySQL
- Database abstraction layer
- Database-specific SQL dialect handling
- Database capability detection
- Database-specific locking strategies

### 🧪 Engineering & Tooling

- Extensive automated test suite
- CLI integration tests
- Database-specific tests
- GitHub Actions CI
- Logging abstraction
- Performance measurement
- Reproducibility testing
- Clean separation between CLI and application logic

---

# 🎯 Why db-migrate?

Database schema changes are easy to make and surprisingly difficult to manage safely.

A migration tool needs to answer more than:

> "What SQL should I execute?"

It should also answer:

- Which migrations have already been applied?
- What will happen if I run the pending migrations?
- Can the migration be reversed?
- Has a migration file been modified after execution?
- Does the database schema match the migration history?
- What objects will a migration affect?
- Is the migration compatible with the selected database?
- Can another process run migrations at the same time?
- Can a fresh database reproduce the expected schema?

`db-migrate` treats migration management as a combination of **execution, validation, analysis, and integrity management**.

---

# 🏗️ Architecture

The project uses a layered architecture:

```text
                    ┌──────────────────┐
                    │       CLI        │
                    └────────┬─────────┘
                             │
                    ┌────────▼─────────┐
                    │ Migration Service│
                    └────────┬─────────┘
                             │
          ┌──────────────────┼──────────────────┐
          │                  │                  │
          ▼                  ▼                  ▼
     Discovery          Planning          Validation
          │                  │                  │
          └──────────────────┼──────────────────┘
                             │
                    ┌────────▼─────────┐
                    │    Execution     │
                    └────────┬─────────┘
                             │
             ┌───────────────┼────────────────┐
             │               │                │
             ▼               ▼                ▼
        PostgreSQL         MySQL           SQLite
             │               │                │
             └───────────────┼────────────────┘
                             │
                    ┌────────▼─────────┐
                    │ History/Integrity│
                    └──────────────────┘
```

The database layer is intentionally separated from migration logic.

This allows migration planning, validation, integrity checks, and other higher-level services to work through a common database interface instead of depending directly on a specific database engine.

For more details:

📖 [`docs/architecture.md`](docs/architecture.md)

---

# 📝 Migration Format

Migrations are plain SQL files with explicit metadata and `up` / `down` sections.

Example:

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

A migration therefore contains:

- a version
- a name
- an `up` section
- a `down` section
- SQL controlled by the developer

Migration files are the source of truth for schema evolution.

For the complete migration format:

📖 [`docs/migration-format.md`](docs/migration-format.md)

---

# 🔄 Migration Lifecycle

A typical migration follows this lifecycle:

```text
Create
  │
  ▼
Discover
  │
  ▼
Validate
  │
  ▼
Plan
  │
  ▼
Analyze
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
Verify Integrity
```

The project deliberately separates **planning and analysis from execution**.

This makes it possible to inspect a migration before changing the database.

📖 [`docs/migration-lifecycle.md`](docs/migration-lifecycle.md)

---

# 🚀 Installation

Clone the repository:

```bash
git clone https://github.com/SarinaTari/db-migrate.git
cd db-migrate
```

Create a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the project:

```bash
pip install -e .
```

Verify the installation:

```bash
dbmigrate version
```

---

# ⚡ Quick Start

Initialize a migration project:

```bash
dbmigrate init
```

Create a migration:

```bash
dbmigrate create create_users
```

Validate migrations:

```bash
dbmigrate validate
```

Inspect the migration plan:

```bash
dbmigrate plan
```

Apply pending migrations:

```bash
dbmigrate up
```

Check migration status:

```bash
dbmigrate status
```

View migration history:

```bash
dbmigrate history
```

The exact behavior of each command is documented in:

📖 [`docs/commands.md`](docs/commands.md)

---

# 🔍 Analyze Before You Execute

One of the main design goals of `db-migrate` is to make migrations understandable before they are executed.

### Lint migrations

```bash
dbmigrate lint
```

### Explain migrations

```bash
dbmigrate explain
```

### Analyze migration impact

```bash
dbmigrate impact
```

### Inspect the current schema

```bash
dbmigrate schema
```

### Compare schemas

```bash
dbmigrate schema-diff
```

### Generate a schema fingerprint

```bash
dbmigrate fingerprint
```

These capabilities allow migration files to be treated as objects that can be **inspected and analyzed**, rather than simply executed as SQL.

📖 [`docs/schema-analysis.md`](docs/schema-analysis.md)

---

# 🔐 Safety & Integrity

Database migrations can permanently change data and schema state.

`db-migrate` therefore includes several mechanisms intended to reduce migration mistakes.

### Migration checksums

Migration files are hashed and their checksums are stored with migration history.

This allows the tool to detect situations where a previously applied migration has been modified.

### Validation

Migration structure and migration state are validated before execution.

### Locking

Migration execution uses database-aware locking to prevent concurrent migration processes from modifying the same database simultaneously.

### Transactions

Transaction behavior is determined according to database capabilities rather than assuming every database behaves identically.

### Integrity verification

The tool can compare migration information against database state and verify migration integrity.

### Diagnostics

The `doctor` functionality provides project and database diagnostics intended to identify configuration and migration-state problems.

📖 [`docs/safety-and-integrity.md`](docs/safety-and-integrity.md)

---

# 🗄️ Database Support

`db-migrate` uses a database abstraction layer so that migration services do not need to directly depend on a particular database engine.

| Database | Status |
|---|---|
| SQLite | ✅ Supported |
| PostgreSQL | ✅ Supported |
| MySQL | ✅ Supported |

The architecture separates:

```text
Database Interface
       │
       ├── Dialect
       ├── Capabilities
       └── Database Implementation
```

This allows database-specific behavior to remain explicit instead of hiding important differences behind unsafe assumptions.

📖 [`docs/database-support.md`](docs/database-support.md)

---

# 🧪 Testing

Testing is a major part of the project.

The test suite covers areas including:

- migration parsing
- migration discovery
- migration creation
- migration history
- checksums
- validation
- planning
- migration execution
- rollback
- schema inspection
- schema differences
- schema fingerprints
- migration impact analysis
- linting
- migration explanations
- locking
- reproducibility
- database abstractions
- SQLite behavior
- PostgreSQL behavior
- MySQL behavior
- CLI behavior
- logging
- CI
- performance

Run the complete test suite with:

```bash
pytest
```

Additional validation can be performed with:

```bash
python -m compileall src
```

The project reached a **300-test passing baseline** during the development process.

📖 [`docs/testing-and-ci.md`](docs/testing-and-ci.md)

---

# 🔁 Reproducibility

A migration system should not only work on an existing development database.

It should also be possible to build the schema from a clean database using the migration history.

Conceptually:

```text
Empty Database
      │
      ▼
Migration 001
      │
      ▼
Migration 002
      │
      ▼
Migration 003
      │
      ▼
Expected Schema
```

`db-migrate` includes reproducibility checks to help verify that the migration sequence can produce the expected schema.

The current reproducibility implementation is focused on SQLite.

---

# 🧠 Design Philosophy

The project follows several principles.

### Explicit over magical

The tool does not attempt to automatically rewrite arbitrary SQL or silently repair production databases.

### Analysis before execution

Developers should be able to understand a migration before applying it.

### Database differences should be visible

SQLite, PostgreSQL, and MySQL do not behave identically.

The project therefore uses explicit dialect and capability abstractions rather than pretending that every database has the same behavior.

### Migration files remain human-readable

Migrations are ordinary SQL files rather than an opaque internal representation.

### Integrity matters

Migration history is not merely a list of versions.

Checksums and verification are used to detect inconsistencies.

### Execution and analysis are separate

The same migration information can be used for planning, linting, explanation, impact analysis, validation, and execution.

---

# 📁 Project Structure

```text
db-migrate/
│
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
├── examples/
│   └── blog/
│       ├── README.md
│       └── migrations/
│           ├── 001_create_users.sql
│           ├── 002_create_posts.sql
│           └── 003_add_user_email.sql
│
├── migrations/
│   └── 001_create_users.sql
│
├── src/
│   └── dbmigrate/
│       ├── cli.py
│       ├── migration.py
│       ├── migration_creator.py
│       ├── migration_safety.py
│       ├── runner.py
│       ├── planner.py
│       ├── history.py
│       ├── validation.py
│       ├── checksum.py
│       ├── database.py
│       ├── database_factory.py
│       ├── database_capabilities.py
│       ├── database_dialect.py
│       ├── database_lock.py
│       ├── database_mysql.py
│       ├── database_postgres.py
│       ├── schema.py
│       ├── schema_diff.py
│       ├── impact.py
│       ├── linter.py
│       ├── explainer.py
│       ├── reproducibility.py
│       ├── doctor.py
│       ├── performance.py
│       ├── logging_config.py
│       └── ci.py
│
├── tests/
│
├── dbmigrate.toml.example
├── pyproject.toml
├── LICENSE
└── README.md
```

---

# 📚 Documentation

The README provides the overview. Detailed technical information is maintained separately.

| Document | Description |
|---|---|
| [`architecture.md`](docs/architecture.md) | System architecture and component responsibilities |
| [`migration-format.md`](docs/migration-format.md) | Migration file format and rules |
| [`migration-lifecycle.md`](docs/migration-lifecycle.md) | Migration lifecycle from creation to verification |
| [`database-support.md`](docs/database-support.md) | Database abstraction and supported engines |
| [`safety-and-integrity.md`](docs/safety-and-integrity.md) | Checksums, locking, validation, and safety |
| [`schema-analysis.md`](docs/schema-analysis.md) | Schema inspection, diffing, impact, and fingerprints |
| [`commands.md`](docs/commands.md) | CLI command reference |
| [`testing-and-ci.md`](docs/testing-and-ci.md) | Testing strategy and CI |
| [`design-decisions.md`](docs/design-decisions.md) | Important architectural decisions and trade-offs |
| [`limitations-and-future-work.md`](docs/limitations-and-future-work.md) | Current limitations and possible future directions |

---

# 🧪 Example Project

A small example application is included under:

```text
examples/blog/
```

It demonstrates a simple schema evolution:

```text
001_create_users
        │
        ▼
002_create_posts
        │
        ▼
003_add_user_email
```

The example is intentionally isolated from the project's own migration directory.

See:

📖 [`examples/blog/README.md`](examples/blog/README.md)

---

# 🚧 Scope & Limitations

`db-migrate` intentionally does **not** attempt to be a universal database automation platform.

Current limitations include:

- SQL parsing is intentionally limited.
- SQL dialects are not automatically translated.
- Reproducibility tooling is currently SQLite-focused.
- Schema diffing does not automatically generate migrations.
- The tool does not automatically repair production databases.
- Checksums detect migration-file changes but cannot prove migration correctness.
- Impact analysis cannot perfectly understand arbitrary SQL.
- Database-specific features may require database-specific SQL.
- The project does not provide distributed migration orchestration.
- Backup management is outside the project's scope.
- There is no automatic production approval system.
- Large-scale online migration strategies are outside the current scope.

These limitations are intentional boundaries rather than features that the project attempts to hide.

📖 [`docs/limitations-and-future-work.md`](docs/limitations-and-future-work.md)

---

# 🛠️ Technology Stack

### Language

- Python

### Database Systems

- SQLite
- PostgreSQL
- MySQL

### Development

- pytest
- Git
- GitHub Actions
- virtual environments
- standard Python tooling

### Architecture

- CLI application
- service-oriented internal structure
- database abstraction
- dialect abstraction
- capability abstraction
- migration history
- schema analysis
- integrity verification

---

# 📊 Project Status

**Status: Portfolio-ready**

The project has progressed through:

```text
Foundation
    ↓
Migration Management
    ↓
Database Abstraction
    ↓
Multi-Database Support
    ↓
Safety & Concurrency
    ↓
CI & Performance
    ↓
Architecture Review
    ↓
Documentation
    ↓
Final Portfolio Preparation
```

The implementation has been developed with an emphasis on:

- correctness
- maintainability
- explicit design
- testability
- database portability
- safety
- explainability

---

# 🎓 What This Project Demonstrates

`db-migrate` was built to demonstrate practical software-engineering concepts beyond basic CRUD or database scripting.

The project involves:

- Python application architecture
- CLI design
- SQL and database systems
- database abstraction
- schema evolution
- migration state management
- checksums and integrity
- transactions
- concurrency and locking
- database-specific behavior
- schema analysis
- static analysis of SQL
- automated testing
- CI
- logging
- performance measurement
- architectural trade-offs
- documentation

---

# 👩🏻‍💻 Author

**Sarina Tari**

Computer Engineering student interested in:

- systems programming
- software engineering
- databases
- developer tools
- version control systems
- Linux
- low-level and backend development

GitHub:

**https://github.com/SarinaTari**

---

# 📄 License

This project is licensed under the terms of the [MIT License](LICENSE).

---

⭐ If you find the project interesting, feel free to explore the source code and documentation.