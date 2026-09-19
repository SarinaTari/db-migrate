"""Command definitions and command resolution."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Command:
    """A dbmigrate CLI command."""

    name: str
    description: str


_COMMANDS = (
    Command(
        "init",
        "Initialize a new dbmigrate project.",
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
        "Show the current migration version.",
    ),
    Command(
        "validate",
        "Validate migration files.",
    ),
    Command(
        "plan",
        "Show the planned migration operations.",
    ),
    Command(
        "lint",
        "Analyze migrations for common problems.",
    ),
    Command(
        "explain",
        "Explain a migration.",
    ),
    Command(
        "impact",
        "Analyze the impact of a migration.",
    ),
    Command(
        "schema",
        "Inspect the current database schema.",
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
        "Diagnose project and database problems.",
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


def resolve_command(name: str) -> Command | None:
    """Resolve a command by name."""
    for command in _COMMANDS:
        if command.name == name:
            return command

    return None