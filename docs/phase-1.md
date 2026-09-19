# Phase 1 — Professional Python Project Foundation

## Purpose

Phase 1 transforms the conceptual Phase 0 project structure into a real,
installable Python project.

The goal is not to implement database migration behavior yet.

The goal is to establish a professional foundation on which the migration
engine, database layer, CLI commands, testing infrastructure, and analysis
features can be built.

---

## Objectives

By the end of Phase 1, the project should have:

- A valid Python package.
- A `src/` package layout.
- A working `pyproject.toml`.
- A real CLI entry point.
- Package version information.
- A development dependency configuration.
- A pytest test suite.
- A reproducible local installation.
- A clear separation between source code, tests, documentation, and migration files.

---

## Project Identity

Repository:

    db-migrate

Python distribution:

    dbmigrate

Python package:

    dbmigrate

CLI:

    dbmigrate

Human-readable project name:

    Database Migration Tool

---

## Architecture at This Stage

The project currently has only the foundation layer:

    User
      |
      v
    dbmigrate CLI
      |
      v
    Python package
      |
      v
    Future migration services

The actual migration system does not exist yet.

Future phases will add:

- configuration
- migration discovery
- migration parsing
- database connections
- migration history
- execution
- rollback
- validation
- checksums
- planning
- analysis
- schema inspection
- multiple database backends

---

## Source Layout

The project uses the `src` layout:

    src/
        dbmigrate/
            __init__.py
            cli.py

This prevents the project root from being accidentally treated as the
importable package during development.

The package is installed through the project metadata in `pyproject.toml`.

---

## CLI

Phase 1 introduces the first working command:

    dbmigrate --help

and:

    dbmigrate --version

The CLI currently does not perform database operations.

That behavior will be introduced incrementally in later phases.

---

## Versioning

The project currently uses:

    0.1.0

The version is defined in:

    src/dbmigrate/__init__.py

The CLI obtains the version from the package instead of maintaining a
separate hard-coded CLI version.

This prevents the package and CLI from silently reporting different versions.

---

## Packaging

The project uses `pyproject.toml` as its primary packaging configuration.

The build backend is setuptools.

The package is discovered from:

    src/

This allows the project to be installed in editable mode during development.

---

## Development Dependencies

The project currently uses pytest for automated testing.

Development dependencies are declared under:

    [project.optional-dependencies]
    dev = [...]

The intended development installation is:

    python -m pip install -e ".[dev]"

---

## Testing

Phase 1 introduces basic tests for:

- CLI program name
- version handling
- successful CLI execution

Run the test suite with:

    pytest

or:

    python -m pytest

The project should eventually have extensive unit, integration, and
end-to-end testing.

---

## What Phase 1 Does Not Implement

Phase 1 intentionally does not implement:

- database connections
- migration files
- migration discovery
- migration execution
- rollback
- migration history
- schema inspection
- checksums
- schema fingerprints
- migration planning
- PostgreSQL
- MySQL
- locking
- CI analysis

Those features are intentionally introduced in later phases.

---

## Completion Criteria

Phase 1 is complete when:

1. The package can be installed.
2. `dbmigrate --help` works.
3. `dbmigrate --version` works.
4. The package imports successfully.
5. pytest runs successfully.
6. The project uses the `src/` layout.
7. The repository contains no generated build artifacts.
8. The project can be cloned and installed on another machine using the
   documented setup process.

---

## Engineering Principle

Do not implement future functionality early simply because the final tool
will eventually need it.

Each phase should introduce a coherent engineering capability while keeping
the architecture understandable and testable.

Phase 1 establishes the foundation for the actual migration engine.