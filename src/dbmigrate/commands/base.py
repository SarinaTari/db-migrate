"""Base command definitions for the dbmigrate CLI."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Command:
    """Description of a dbmigrate CLI command."""

    name: str
    help: str


COMMANDS: tuple[Command, ...] = (
    Command(
        name="init",
        help="Initialize a new dbmigrate project.",
    ),
    Command(
        name="create",
        help="Create a new migration.",
    ),
    Command(
        name="up",
        help="Apply pending migrations.",
    ),
    Command(
        name="down",
        help="Roll back the latest applied migration.",
    ),
    Command(
        name="status",
        help="Show migration status.",
    ),
    Command(
        name="history",
        help="Show migration execution history.",
    ),
    Command(
        name="current",
        help="Show the current migration version.",
    ),
    Command(
        name="validate",
        help="Validate migration files.",
    ),
    Command(
        name="plan",
        help="Show the migration execution plan.",
    ),
    Command(
        name="lint",
        help="Analyze migrations for potential problems.",
    ),
    Command(
        name="explain",
        help="Explain what a migration does.",
    ),
    Command(
        name="impact",
        help="Analyze the potential impact of a migration.",
    ),
    Command(
        name="schema",
        help="Inspect the current database schema.",
    ),
    Command(
        name="schema-diff",
        help="Compare database schemas.",
    ),
    Command(
        name="fingerprint",
        help="Calculate a schema fingerprint.",
    ),
    Command(
        name="doctor",
        help="Diagnose project and database problems.",
    ),
    Command(
        name="check",
        help="Run project consistency checks.",
    ),
    Command(
        name="verify-schema",
        help="Verify the database schema against migrations.",
    ),
)


def get_commands() -> tuple[Command, ...]:
    """Return all registered CLI commands."""
    return COMMANDS