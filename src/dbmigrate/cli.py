"""Command-line interface for dbmigrate."""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from . import __version__
from .commands.base import Command, get_commands
from .config import ConfigurationError, load_config
from .validation import validate_migrations


def build_parser() -> argparse.ArgumentParser:
    """Build the top-level CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="dbmigrate",
        description=(
            "Database migration and schema-evolution tool "
            "focused on safety, integrity, and explainability."
        ),
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"dbmigrate {__version__}",
    )

    subparsers = parser.add_subparsers(
        dest="command",
        title="commands",
        metavar="COMMAND",
    )

    for command in get_commands():
        subparsers.add_parser(
            command.name,
            help=command.help,
            description=command.help,
        )

    return parser


def resolve_command(name: str | None) -> Command | None:
    """Resolve a command name to its command definition."""
    if name is None:
        return None

    for command in get_commands():
        if command.name == name:
            return command

    return None


def _run_validate() -> int:
    """Run migration validation."""
    try:
        config = load_config()
    except ConfigurationError as exc:
        print(f"Configuration error: {exc}")
        return 1

    print(f"Migration directory: {config.migrations_path}")

    report = validate_migrations(config.migrations_path)

    if report.is_valid:
        print(
            f"Validation successful: "
            f"{report.migration_count} migration(s) found."
        )

        for migration in report.migrations:
            print(
                f"  {migration.version:03d}_{migration.name}.sql"
            )

        return 0

    print(
        f"Validation failed: "
        f"{len(report.issues)} issue(s) found."
    )

    for issue in report.issues:
        print(f"  {issue.format()}")

    return 1


def run_command(command: Command) -> int:
    """Run a command."""
    if command.name == "init":
        print(
            "Command 'init' is not implemented yet. "
            "This command will be introduced in a later phase."
        )
        return 0

    if command.name == "validate":
        return _run_validate()

    try:
        config = load_config()
    except ConfigurationError as exc:
        print(f"Configuration error: {exc}")
        return 1

    print(f"Project root: {config.project_root}")
    print(
        f"Command '{command.name}' is not implemented yet. "
        "This command will be introduced in a later phase."
    )

    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Run the dbmigrate CLI."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    command = resolve_command(args.command)

    if command is None:
        parser.error(f"unknown command: {args.command}")

    return run_command(command)