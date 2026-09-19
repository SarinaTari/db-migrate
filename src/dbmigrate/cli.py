"""Command-line interface for dbmigrate."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from . import __version__
from .commands.base import Command, get_commands, resolve_command
from .config import ConfigurationError, ProjectConfig, load_config
from .database import DatabaseError, SQLiteDatabase
from .history import HistoryError
from .migration import (
    MigrationDiscoveryError,
    MigrationParseError,
    discover_migrations,
)
from .migration_creator import (
    MigrationCreationError,
    create_migration,
)
from .runner import MigrationRunner, MigrationRunnerError
from .status import (
    MigrationStatusError,
    MigrationStatusInspector,
)
from .validation import validate_migrations


def build_parser() -> argparse.ArgumentParser:
    """Build the dbmigrate argument parser."""
    parser = argparse.ArgumentParser(
        prog="dbmigrate",
        description="Database migration and schema-evolution tool.",
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
        command_parser = subparsers.add_parser(
            command.name,
            help=command.description,
            description=command.description,
        )

        if command.name == "create":
            command_parser.add_argument(
                "name",
                help="Name of the migration to create.",
            )

        if command.name == "down":
            command_parser.add_argument(
                "--steps",
                type=int,
                default=1,
                help="Number of migrations to roll back.",
            )

    return parser


def parse_args(
    argv: list[str] | None = None,
) -> argparse.Namespace:
    """Parse command-line arguments."""
    return build_parser().parse_args(argv)


def run_command(
    command: Command,
    args: argparse.Namespace,
) -> int:
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

    if command.name == "create":
        return _run_create(
            config,
            args.name,
        )

    if command.name == "validate":
        return _run_validate(config)

    if command.name == "check":
        return _run_check(config)

    if command.name == "up":
        return _run_up(config)

    if command.name == "down":
        return _run_down(config, args.steps)

    if command.name == "history":
        return _run_history(config)

    if command.name == "current":
        return _run_current(config)

    if command.name == "status":
        return _run_status(config)

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


def _run_create(
    config: ProjectConfig,
    name: str,
) -> int:
    """Create a new migration."""
    try:
        migration = create_migration(
            config.migrations_path,
            name,
        )
    except MigrationCreationError as exc:
        print(
            f"Migration creation error: {exc}",
            file=sys.stderr,
        )
        return 1

    print(
        f"Created migration "
        f"{migration.identifier}."
    )

    print(
        f"File: {migration.path}"
    )

    return 0


def _run_validate(config: ProjectConfig) -> int:
    """Run migration validation."""
    try:
        report = validate_migrations(
            config.migrations_path
        )
    except OSError as exc:
        print(
            "Validation error: could not access "
            f"migrations directory: {exc}",
            file=sys.stderr,
        )
        return 1

    print(
        f"Migration directory: "
        f"{config.migrations_path}"
    )

    print(
        f"Migrations discovered: "
        f"{len(report.migrations)}"
    )

    for migration in report.migrations:
        print(
            f"  {migration.version:03d} "
            f"{migration.name}"
        )

    if report.errors:
        print("\nValidation failed:")

        for error in report.errors:
            print(f"  - {error}")

        return 1

    print("\nMigration validation passed.")

    return 0


def _create_database(
    database_url: str,
) -> SQLiteDatabase | None:
    """Create the configured database implementation."""
    prefix = "sqlite:///"

    if not database_url.startswith(prefix):
        print(
            "Configuration error: only sqlite:/// database URLs "
            "are currently supported.",
            file=sys.stderr,
        )
        return None

    raw_path = database_url[len(prefix):]

    if not raw_path:
        print(
            "Configuration error: "
            "SQLite database path is empty.",
            file=sys.stderr,
        )
        return None

    path = Path(raw_path).expanduser()

    if not path.is_absolute():
        path = Path.cwd() / path

    return SQLiteDatabase(path)


def _run_check(config: ProjectConfig) -> int:
    """Check database connectivity."""
    database = _create_database(
        config.database_url
    )

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


def _load_migrations(config: ProjectConfig):
    """Load migration files."""
    try:
        return discover_migrations(
            config.migrations_path
        )
    except (
        MigrationDiscoveryError,
        MigrationParseError,
    ) as exc:
        raise MigrationRunnerError(
            f"Could not load migrations: {exc}"
        ) from exc


def _run_up(config: ProjectConfig) -> int:
    """Apply all pending migrations."""
    database = _create_database(
        config.database_url
    )

    if database is None:
        return 1

    try:
        database.connect()

        migrations = _load_migrations(config)

        runner = MigrationRunner(database)

        applied = runner.apply_all(
            migrations
        )

        if not applied:
            print("No pending migrations.")
            return 0

        for result in applied:
            print(
                f"Applied "
                f"{result.migration.identifier}."
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


def _run_down(
    config: ProjectConfig,
    steps: int,
) -> int:
    """Roll back applied migrations."""
    if steps < 1:
        print(
            "Error: --steps must be greater than zero.",
            file=sys.stderr,
        )
        return 1

    database = _create_database(
        config.database_url
    )

    if database is None:
        return 1

    try:
        database.connect()

        migrations = _load_migrations(config)

        runner = MigrationRunner(database)

        results = runner.rollback_steps(
            migrations,
            steps,
        )

        if not results:
            print("No applied migrations.")
            return 0

        for result in results:
            print(
                f"Rolled back "
                f"{result.migration.identifier}."
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


def _run_history(config: ProjectConfig) -> int:
    """Show migration history."""
    database = _create_database(
        config.database_url
    )

    if database is None:
        return 1

    try:
        database.connect()

        migrations = _load_migrations(config)

        runner = MigrationRunner(database)

        applied = runner.applied(migrations)

        if not applied:
            print(
                "No migrations have been applied."
            )
            return 0

        for migration in applied:
            print(
                f"{migration.version:03d} "
                f"{migration.name}"
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


def _run_current(config: ProjectConfig) -> int:
    """Show the current migration version."""
    database = _create_database(
        config.database_url
    )

    if database is None:
        return 1

    try:
        database.connect()

        migrations = _load_migrations(config)

        runner = MigrationRunner(database)

        applied = runner.applied(migrations)

        if not applied:
            print(
                "No migrations have been applied."
            )
            return 0

        current = applied[-1]

        print(
            f"{current.version:03d} "
            f"{current.name}"
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


def _run_status(config: ProjectConfig) -> int:
    """Show migration status."""
    database = _create_database(
        config.database_url
    )

    if database is None:
        return 1

    try:
        database.connect()

        migrations = _load_migrations(config)

        runner = MigrationRunner(database)
        inspector = MigrationStatusInspector(
            runner
        )

        status = inspector.inspect(
            migrations
        )

        print("Migration status")
        print("================")
        print(
            f"Total migrations: {status.total_count}"
        )
        print(
            f"Applied: {status.applied_count}"
        )
        print(
            f"Pending: {status.pending_count}"
        )
        print(
            f"Missing: {status.missing_count}"
        )

        if status.current is None:
            print("Current: none")
        else:
            print(
                "Current: "
                f"{status.current.version:03d} "
                f"{status.current.name}"
            )

        if status.pending:
            print("\nPending migrations:")

            for migration in status.pending:
                print(
                    f"  {migration.version:03d} "
                    f"{migration.name}"
                )

        if status.missing:
            print(
                "\nMissing migration files:"
            )

            for record in status.missing:
                print(
                    f"  {record.version:03d} "
                    f"{record.name}"
                )

        if status.is_up_to_date:
            print(
                "\nDatabase is up to date."
            )
        else:
            print(
                "\nDatabase requires migration changes."
            )

        return 0

    except (
        DatabaseError,
        MigrationRunnerError,
        MigrationStatusError,
        HistoryError,
    ) as exc:
        print(
            f"Error: {exc}",
            file=sys.stderr,
        )
        return 1

    finally:
        database.close()


def main(
    argv: list[str] | None = None,
) -> int:
    """Run the dbmigrate CLI."""
    try:
        args = parse_args(argv)
    except SystemExit as exc:
        return int(exc.code)

    if args.command is None:
        build_parser().print_help()
        return 0

    command = resolve_command(
        args.command
    )

    if command is None:
        print(
            f"Unknown command: {args.command}",
            file=sys.stderr,
        )
        return 2

    return run_command(
        command,
        args,
    )


if __name__ == "__main__":
    raise SystemExit(main())