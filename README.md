# db-migrate

A Python-based database migration and schema-evolution CLI focused on safety, integrity, explainability, and migration analysis.

## Current Status

The project is under active development.

Completed phases:

- Phase 0 — Database Migration Concepts
- Phase 1 — Professional Python Project
- Phase 2 — CLI Foundation
- Phase 3 — Configuration
- Phase 4 — Migration Format
- Phase 5 — Discovery and Validation
- Phase 6 — Database Interface + SQLite
- Phase 7 — Migration History
- Phase 8 — Migration Runner
- Phase 9 — Transaction and Failure Semantics
- Phase 10 — Down/Rollback
- Phase 11 — Status/History/Current
- Phase 12 — Create Command

Current capabilities include:

- project configuration
- migration file creation
- migration file parsing
- migration discovery
- migration validation
- SQLite database connectivity
- SQLite SQL execution
- transaction handling
- migration history
- migration application
- migration rollback
- migration status inspection
- database connectivity checks
- safe migration file generation
- migration version generation

The project currently supports SQLite. PostgreSQL and MySQL support are planned for later phases.

## Installation

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate