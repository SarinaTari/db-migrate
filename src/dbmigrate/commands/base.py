"""Command definitions for dbmigrate."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Command:
    """Describe a CLI command."""

    name: str
    description: str


_COMMANDS = (
    Command(
        "init",
        "Initialize a migration project.",
    ),
    Command(
        "create",
        "Create a new migration.",
    ),
    Command(
        "up",
        "Apply pending migrations.",
    ),
    Command(
        "down",
        "Roll back applied migrations.",
    ),
    Command(
        "status",
        "Show migration status.",
    ),
    Command(
        "history",
        "Show migration history.",
    ),
    Command(
        "current",
        "Show the current migration.",
    ),
    Command(
        "validate",
        "Validate migration files.",
    ),
    Command(
        "plan",
        "Show the migrations that would be applied.",
    ),
    Command(
        "lint",
        "Analyze migrations for potential problems.",
    ),
    Command(
        "explain",
        "Explain migration behavior.",
    ),
    Command(
        "impact",
        "Analyze migration impact.",
    ),
    Command(
        "schema",
        "Inspect the database schema.",
    ),
    Command(
        "schema-diff",
        "Compare migration and database schemas.",
    ),
    Command(
        "fingerprint",
        "Calculate a database schema fingerprint.",
    ),
    Command(
        "doctor",
        "Check project health.",
    ),
    Command(
        "check",
        "Check database connectivity.",
    ),
    Command(
        "verify-schema",
        "Verify the database schema.",
    ),
)


def get_commands() -> tuple[Command, ...]:
    """Return all registered commands."""
    return _COMMANDS


def resolve_command(
    name: str,
) -> Command | None:
    """Resolve a command by name."""
    for command in _COMMANDS:
        if command.name == name:
            return command

    return None