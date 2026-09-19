"""Foundational command abstractions for the dbmigrate CLI."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class Command:
    """Describe a command exposed by the CLI."""

    name: str
    help: str


COMMANDS: tuple[Command, ...] = (
    Command(
        name="init",
        help="Initialize a migration project.",
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
        help="Roll back migrations.",
    ),
    Command(
        name="status",
        help="Show migration status.",
    ),
    Command(
        name="history",
        help="Show migration history.",
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
        help="Explain a migration.",
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
        help="Run migration safety checks.",
    ),
    Command(
        name="verify-schema",
        help="Verify schema reproducibility.",
    ),
)


def get_commands() -> Sequence[Command]:
    """Return the commands exposed by the CLI."""
    return COMMANDS