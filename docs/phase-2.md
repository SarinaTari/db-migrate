# Phase 2 — CLI Foundation

## Purpose

Phase 2 establishes the command-line architecture of `dbmigrate`.

Phase 1 created a working Python package and a minimal executable.

Phase 2 turns that executable into an extensible command framework that later
phases can use to expose migration, database, schema, validation, and analysis
functionality.

No database behavior is implemented in this phase.

---

## Objectives

Phase 2 establishes:

- a top-level CLI parser
- subcommand support
- command definitions
- command lookup
- command dispatch
- consistent exit codes
- command-specific help
- a testable CLI architecture

---

## CLI Architecture

The CLI now follows this structure:

```text
User
 |
 v
dbmigrate
 |
 v
Argument Parser
 |
 v
Command Resolution
 |
 v
Command Handler
 |
 v
Future Application Services

The final architecture will eventually extend this to:

User
 |
 v
CLI
 |
 v
Command Layer
 |
 v
Application Services
 |
 +--> Migration Discovery
 +--> Planning
 +--> Validation
 +--> Execution
 +--> History
 +--> Schema Analysis
 |
 v
Database Layer

Phase 2 only implements the first part of this architecture.

Command Registry

The project introduces a central command definition.

Each command currently has:

a name
user-facing help text

Example:

Command(
    name="status",
    help="Show migration status.",
)

The registry is intentionally simple.

It should not become a complex plugin system unless future requirements justify
one.

Planned Commands

The CLI currently recognizes the planned command names:

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

These commands are registered so that the CLI interface can be established
early.

Their actual behavior will be implemented in later phases.

Command Behavior

At this stage, commands are placeholders.

For example:

$ dbmigrate status

Command 'status' is not implemented yet. This command will be introduced in a later phase.

This is intentional.

The CLI should not pretend to perform database operations before the
corresponding services exist.

Global Options

The CLI currently supports:

dbmigrate --help
dbmigrate --version

These options are handled by the top-level parser.

Command-Specific Help

Because commands are registered as real argparse subparsers, each command
already has its own help page.

For example:

dbmigrate status --help

or:

dbmigrate plan --help

Future phases can add command-specific arguments without redesigning the
entire CLI.

Error Handling

The project uses argparse for command-line syntax validation.

Therefore malformed commands and unknown commands receive non-zero exit
codes automatically.

Application-level errors will be introduced later when the migration services
exist.

Testing

Phase 2 tests:

parser construction
program name
version handling
help handling
no-command behavior
known command parsing
unknown command rejection
command resolution
command uniqueness
command help text
command dispatch

The CLI should be testable without requiring a database.

What Phase 2 Does Not Implement

Phase 2 intentionally does not implement:

project configuration
database connections
migration files
migration parsing
migration discovery
SQL execution
migration history
rollback
checksums
schema inspection
PostgreSQL
MySQL
locking
migration planning logic
linting logic
impact analysis

Those capabilities belong to later phases.

Design Principles
Keep the CLI thin

The CLI should eventually translate user input into application-level
operations.

Business logic should not accumulate inside cli.py.

Prefer explicit commands

Commands should have clear responsibilities.

Avoid premature abstraction

The command registry is deliberately small.

More sophisticated abstractions should only be introduced when the real
application requires them.

Keep commands testable

Command parsing should not require a real database.

Database-dependent behavior will be tested separately once implemented.

Completion Criteria

Phase 2 is complete when:

dbmigrate --help works.
dbmigrate --version works.
Planned commands are recognized.
Command-specific help works.
Unknown commands are rejected.
Command definitions are centralized.
The CLI remains independent of database behavior.
Automated tests pass.
The project can still be installed using pip install -e ".[dev]".
Result

Phase 2 establishes the interface through which future migration functionality
will be exposed.

The next phase can therefore focus on configuration rather than simultaneously
redesigning the CLI.