# Phase 3 — Configuration

## Purpose

Phase 3 introduces project configuration.

The CLI established in Phase 2 needs a reliable way to determine which
migration project it is operating on and where migration files are located.

This phase introduces:

- `dbmigrate.toml`
- configuration loading
- project-root discovery
- migration-directory configuration
- configuration validation
- configuration-specific errors

Database connection configuration is intentionally deferred until the
database layer is introduced.

---

## Why Configuration Matters

A migration tool cannot safely operate on an implicit project structure.

The tool needs to know:

- which directory represents the project
- where migration files are stored
- which configuration belongs to the project

Configuration also gives the project a stable place for future settings.

---

## Configuration File

The default project configuration filename is:

```text
dbmigrate.toml

A minimal configuration is:

[migrations]
directory = "migrations"

The migration directory defaults to:

migrations/

if the setting is omitted.

Project Discovery

When a command requires project configuration, the tool searches upward
from the current working directory.

For example:

project/
├── dbmigrate.toml
├── migrations/
└── src/
    └── application/
        └── feature/

If the user runs:

dbmigrate status

from:

project/src/application/feature/

the configuration loader searches the current directory and its parents until
it finds:

project/dbmigrate.toml

That directory becomes the project root.

Explicit Configuration

The configuration layer also supports loading a specific configuration file
directly.

This is useful for testing and will become useful for future CLI options.

Example conceptually:

load_config(Path("dbmigrate.toml"))
Configuration Object

The loaded configuration is represented by an immutable ProjectConfig
object.

It contains:

project root
migrations directory
configuration file path

The migrations path is derived from the project root and migrations directory.

Validation

Configuration is validated when loaded.

Invalid configuration should fail early.

Examples of invalid configuration include:

missing configuration file
invalid TOML syntax
empty migration directory
non-string migration directory
migration directory outside the project root
Security and Safety

The migration directory is required to remain inside the project root.

For example:

[migrations]
directory = "../somewhere"

is rejected.

This prevents configuration from silently redirecting migration discovery to
an unrelated filesystem location.

Why TOML?

Python 3.11 introduced the standard-library tomllib module for reading TOML.

This means the project can use TOML configuration without adding another
runtime dependency.

TOML is also already closely associated with modern Python project
configuration through pyproject.toml.

The project uses:

pyproject.toml for package/build metadata
dbmigrate.toml for application/project configuration

These files have different responsibilities.

pyproject.toml vs dbmigrate.toml
pyproject.toml

Describes the Python project itself.

It contains information such as:

package name
package version
Python requirement
dependencies
build configuration
CLI entry point
dbmigrate.toml

Describes a specific dbmigrate project.

It will eventually contain settings related to:

migration directory
database configuration
migration behavior
safety options
project-specific settings

Keeping these responsibilities separate prevents application configuration
from being mixed with Python packaging metadata.

CLI Behavior

Global commands continue to work without a project:

dbmigrate --help
dbmigrate --version

Project-dependent commands require configuration.

For example:

dbmigrate status

without a dbmigrate.toml produces a configuration error.

The init command is currently a placeholder and does not yet require an
existing configuration file.

What Phase 3 Does Not Implement

This phase intentionally does not implement:

database URLs
SQLite connections
PostgreSQL connections
MySQL connections
migration parsing
migration discovery
migration execution
migration history
rollback
checksums
schema inspection
schema fingerprints
locking

These will be introduced only when their corresponding architectural layers
are ready.

Testing

Phase 3 tests:

default migration directory
custom migration directory
project-root discovery
missing configuration
invalid TOML
invalid migration directory values
directories outside the project root
CLI behavior without configuration

The configuration layer is testable independently of any real database.

Completion Criteria

Phase 3 is complete when:

A project can be configured with dbmigrate.toml.
The configuration can be discovered from nested directories.
Configuration errors are reported clearly.
Migration paths are resolved relative to the project root.
Invalid paths outside the project root are rejected.
The CLI can distinguish global commands from project-dependent commands.
Automated tests pass.
No external TOML dependency is required.
Result

Phase 3 gives the migration tool a defined project context.