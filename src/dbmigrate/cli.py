"""Command-line interface for dbmigrate."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from . import __version__
from .commands.base import Command, get_commands, resolve_command
from .config import ConfigurationError, load_config
from .database import DatabaseError, SQLiteDatabase
from .migration import (
    MigrationDiscoveryError,
    MigrationParseError,
)
from .runner import MigrationRunner, MigrationRunnerError
from .validation import validate_migrations


def build_parser() -> argparse.ArgumentParser:
    """Build the dbmigrate argument parser."""
    parser = argparse.ArgumentParser(
        prog="dbmigrate",
        description=(
            "Database migration and schema-evolution tool."
        ),
    )

    parser.add_argument(
        "--version",
        action="version",
        version=__version__,
    )

    subparsers = parser.add_subparsers(
        dest="command",
        title="commands",
        metavar="COMMAND",
    )

    for command in get_commands():
        subparsers.add_parser(
            command.name,
            help=command.description,
            description=command.description,
        )

    return parser


def parse_args(
    argv: list[str] | None = None,
) -> argparse.Namespace:
    """Parse command-line arguments."""
    return build_parser().parse_args(argv)


def run_command(command: Command) -> int:
    """Dispatch a resolved command."""
    if command.name == "init":
        return _run_init()

    try:
        config = load_config()
    except ConfigurationError as exc:
        print(
            f"Configuration error: {exc}",
            file=sys.stderr,
        )
        return 1

    if command.name == "validate":
        return _run_validate(config)

    if command.name == "check":
        return _run_check(config)

    if command.name == "up":
        return _run_up(config)

    print(
        f"Command '{command.name}' is not implemented yet. "
        "This command will be introduced in a later phase."
    )

    return 0


def _run_init() -> int:
    """Run the init command."""
    print(
        "Command 'init' is not implemented yet. "
        "Project initialization will be introduced in a later phase."
    )

    return 0


def _run_validate(config) -> int:
    """Run migration validation."""
    try:
        report = validate_migrations(config.migrations_path)
    except OSError as exc:
        print(
            f"Validation error: could not access migrations directory: "
            f"{exc}",
            file=sys.stderr,
        )
        return 1

    print(f"Migration directory: {config.migrations_path}")

    if report.migrations:
        print(
            f"Migrations discovered: "
            f"{len(report.migrations)}"
        )

        for migration in report.migrations:
            print(
                f"  {migration.version:03d} "
                f"{migration.name}"
            )
    else:
        print("Migrations discovered: 0")

    if report.errors:
        print("\nValidation failed:")

        for error in report.errors:
            print(f"  - {error}")

        return 1

    print("\nMigration validation passed.")

    return 0


def _run_check(config) -> int:
    """Check database connectivity."""
    database = _create_database(config.database_url)

    if database is None:
        return 1

    try:
        database.connect()

        row = database.fetch_one(
            "SELECT sqlite_version()"
        )

        if row is None:
            raise DatabaseError(
                "SQLite did not return a version."
            )

        print("Database connection: OK")
        print("Database engine: SQLite")
        print(f"SQLite version: {row[0]}")
        print(f"Database path: {database.path}")

        return 0

    except DatabaseError as exc:
        print(
            f"Database check failed: {exc}",
            file=sys.stderr,
        )
        return 1

    finally:
        database.close()


def _create_database(
    database_url: str,
) -> SQLiteDatabase | None:
    """Create a database implementation from a database URL."""
    prefix = "sqlite:///"

    if not database_url.startswith(prefix):
        print(
            "Configuration error: Phase 6 supports only "
            "sqlite:/// database URLs.",
            file=sys.stderr,
        )
        return None

    raw_path = database_url[len(prefix):]

    if not raw_path:
        print(
            "Configuration error: SQLite database path is empty.",
            file=sys.stderr,
        )
        return None

    path = Path(raw_path)

    if not path.is_absolute():
        path = Path.cwd() / path

    return SQLiteDatabase(path)


def _run_up(config) -> int:
    """Apply all pending migrations."""
    database = _create_database(config.database_url)

    if database is None:
        return 1

    try:
        database.connect()

        report = validate_migrations(
            config.migrations_path
        )

        if report.errors:
            print(
                "Migration validation failed:",
                file=sys.stderr,
            )

            for error in report.errors:
                print(
                    f"  - {error}",
                    file=sys.stderr,
                )

            return 1

        runner = MigrationRunner(database)

        applied = runner.apply_all(
            report.migrations
        )

        if not applied:
            print("No pending migrations.")
            return 0

        for result in applied:
            print(
                f"Applied {result.migration.identifier}."
            )

        return 0

    except (
        DatabaseError,
        MigrationRunnerError,
    ) as exc:
        print(
            f"Error: {exc}",
            file=sys.stderr,
        )
        return 1

    finally:
        database.close()


def main(argv: list[str] | None = None) -> int:
    """Run the dbmigrate command-line interface."""
    try:
        args = parse_args(argv)
    except SystemExit as exc:
        return int(exc.code)

    if args.command is None:
        build_parser().print_help()
        return 0

    command = resolve_command(args.command)

    if command is None:
        print(
            f"Unknown command: {args.command}",
            file=sys.stderr,
        )
        return 2

    return run_command(command)


if __name__ == "__main__":
    raise SystemExit(main())