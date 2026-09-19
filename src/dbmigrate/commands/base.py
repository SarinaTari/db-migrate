"""Command definitions for the dbmigrate CLI."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Command:
    """Describe a dbmigrate CLI command."""

    name: str
    description: str


COMMANDS = (
    Command(
        name="init",
        description="Initialize a dbmigrate project.",
    ),
    Command(
        name="create",
        description="Create a new migration.",
    ),
    Command(
        name="up",
        description="Apply pending migrations.",
    ),
    Command(
        name="down",
        description="Roll back a migration.",
    ),
    Command(
        name="status",
        description="Show migration status.",
    ),
    Command(
        name="history",
        description="Show migration history.",
    ),
    Command(
        name="current",
        description="Show the current migration.",
    ),
    Command(
        name="validate",
        description="Validate migration files.",
    ),
    Command(
        name="plan",
        description="Show the migration execution plan.",
    ),
    Command(
        name="lint",
        description="Analyze migrations for problems.",
    ),
    Command(
        name="explain",
        description="Explain a migration.",
    ),
    Command(
        name="impact",
        description="Analyze migration impact.",
    ),
    Command(
        name="schema",
        description="Inspect the database schema.",
    ),
    Command(
        name="schema-diff",
        description="Compare database schemas.",
    ),
    Command(
        name="fingerprint",
        description="Calculate a database schema fingerprint.",
    ),
    Command(
        name="doctor",
        description="Check project and database health.",
    ),
    Command(
        name="check",
        description="Check database connectivity.",
    ),
    Command(
        name="verify-schema",
        description="Verify database schema state.",
    ),
    Command(
        name="version",
        description="Show the dbmigrate version.",
    ),
)


def get_commands() -> tuple[Command, ...]:
    """Return all registered commands."""
    return COMMANDS


def resolve_command(name: str) -> Command | None:
    """Resolve a command by name."""
    for command in COMMANDS:
        if command.name == name:
            return command

    return None