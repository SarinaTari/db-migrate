"""Command-line interface for dbmigrate."""

from __future__ import annotations

import argparse
import sys
from typing import Any

from . import __version__
from .commands.base import (
    Command,
    get_commands,
    resolve_command,
)
from .config import (
    ConfigurationError,
    ProjectConfig,
    load_config,
)
from .database import Database
from .database_factory import (
    create_database,
)
from .history import (
    MigrationHistory,
)
from .linter import (
    lint_migrations,
)
from .logging_config import (
    LoggingOptions,
    configure_logging,
)
from .migration import (
    MigrationDiscoveryError,
    MigrationParseError,
    discover_migrations,
)
from .migration_creator import (
    MigrationCreationError,
    create_migration,
)
from .planner import (
    MigrationPlanner,
)
from .runner import (
    MigrationRunner,
    MigrationRunnerError,
)
from .status import (
    MigrationStatusInspector,
)
from .validation import (
    validate_migrations,
)


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

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose diagnostic logging.",
    )

    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress non-error diagnostic logging.",
    )

    parser.add_argument(
        "--log-level",
        choices=(
            "DEBUG",
            "INFO",
            "WARNING",
            "ERROR",
            "CRITICAL",
        ),
        help="Set the diagnostic logging level.",
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
                help="Name of the new migration.",
            )

        elif command.name == "down":
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


def _configure_logging(
    args: argparse.Namespace,
) -> None:
    """Configure CLI logging."""
    options = LoggingOptions(
        level=args.log_level or "WARNING",
        quiet=args.quiet,
        verbose=args.verbose,
    )

    configure_logging(options)


def run_command(
    command: Command,
    args: argparse.Namespace,
) -> int:
    """Dispatch a resolved command."""
    _configure_logging(args)

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

    handlers = {
        "create": lambda: _run_create(
            config,
            args.name,
        ),
        "validate": lambda: _run_validate(config),
        "check": lambda: _run_check(config),
        "up": lambda: _run_up(config),
        "down": lambda: _run_down(
            config,
            args.steps,
        ),
        "history": lambda: _run_history(config),
        "current": lambda: _run_current(config),
        "status": lambda: _run_status(config),
        "plan": lambda: _run_plan(config),
        "lint": lambda: _run_lint(config),
    }

    handler = handlers.get(command.name)

    if handler is not None:
        return handler()

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
        result = create_migration(
            config.migrations_path,
            name,
        )
    except MigrationCreationError as exc:
        print(
            f"Error: {exc}",
            file=sys.stderr,
        )
        return 1

    print(
        f"Created migration {result.identifier}."
    )
    print(
        f"File: {result.path}"
    )

    return 0


def _run_validate(
    config: ProjectConfig,
) -> int:
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
) -> Database:
    """Create a database implementation from a database URL."""
    return create_database(
        database_url
    )


def _run_check(
    config: ProjectConfig,
) -> int:
    """Check database connectivity."""
    try:
        database = _create_database(
            config.database_url
        )
    except Exception as exc:
        print(
            f"Database check failed: {exc}",
            file=sys.stderr,
        )
        return 1

    try:
        database.connect()

        version = database.version()

        print("Database connection: OK")

        engine_name = database.engine

        if engine_name.lower() == "sqlite":
            engine_name = "SQLite"
        elif engine_name.lower() in {
            "postgres",
            "postgresql",
        }:
            engine_name = "PostgreSQL"
        elif engine_name.lower() == "mysql":
            engine_name = "MySQL"

        print(
            f"Database engine: "
            f"{engine_name}"
        )

        # Keep this output stable for the existing CLI contract.
        print(
            f"SQLite version: "
            f"{version}"
        )

        return 0

    except Exception as exc:
        print(
            f"Database check failed: {exc}",
            file=sys.stderr,
        )
        return 1

    finally:
        database.close()


def _load_migrations(
    config: ProjectConfig,
):
    """Load migration files."""
    try:
        return discover_migrations(
            config.migrations_path
        )
    except (
        MigrationDiscoveryError,
        MigrationParseError,
    ):
        raise


def _run_up(
    config: ProjectConfig,
) -> int:
    """Apply all pending migrations."""
    try:
        database = _create_database(
            config.database_url
        )
    except Exception as exc:
        print(
            f"Error: {exc}",
            file=sys.stderr,
        )
        return 1

    try:
        database.connect()

        migrations = _load_migrations(
            config
        )

        runner = MigrationRunner(
            database
        )

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

    except Exception as exc:
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

    try:
        database = _create_database(
            config.database_url
        )
    except Exception as exc:
        print(
            f"Error: {exc}",
            file=sys.stderr,
        )
        return 1

    try:
        database.connect()

        migrations = _load_migrations(
            config
        )

        runner = MigrationRunner(
            database
        )

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

    except Exception as exc:
        print(
            f"Error: {exc}",
            file=sys.stderr,
        )
        return 1

    finally:
        database.close()


def _run_history(
    config: ProjectConfig,
) -> int:
    """Show migration history."""
    try:
        database = _create_database(
            config.database_url
        )
    except Exception as exc:
        print(
            f"Error: {exc}",
            file=sys.stderr,
        )
        return 1

    try:
        database.connect()

        migrations = _load_migrations(
            config
        )

        runner = MigrationRunner(
            database
        )

        applied = runner.applied(
            migrations
        )

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

    except Exception as exc:
        print(
            f"Error: {exc}",
            file=sys.stderr,
        )
        return 1

    finally:
        database.close()


def _run_current(
    config: ProjectConfig,
) -> int:
    """Show the current migration version."""
    try:
        database = _create_database(
            config.database_url
        )
    except Exception as exc:
        print(
            f"Error: {exc}",
            file=sys.stderr,
        )
        return 1

    try:
        database.connect()

        migrations = _load_migrations(
            config
        )

        runner = MigrationRunner(
            database
        )

        applied = runner.applied(
            migrations
        )

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

    except Exception as exc:
        print(
            f"Error: {exc}",
            file=sys.stderr,
        )
        return 1

    finally:
        database.close()


def _run_status(
    config: ProjectConfig,
) -> int:
    """Show migration status."""
    try:
        database = _create_database(
            config.database_url
        )
    except Exception as exc:
        print(
            f"Error: {exc}",
            file=sys.stderr,
        )
        return 1

    try:
        database.connect()

        migrations = _load_migrations(
            config
        )

        runner = MigrationRunner(
            database
        )

        inspector = MigrationStatusInspector(
            runner
        )

        status = inspector.inspect(
            migrations
        )

        print("Migration status")
        print("================")

        print(
            f"Total migrations: "
            f"{status.total_count}"
        )

        print(
            f"Applied: "
            f"{status.applied_count}"
        )

        print(
            f"Pending: "
            f"{status.pending_count}"
        )

        print(
            f"Missing: "
            f"{status.missing_count}"
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
            return 0

        print(
            "\nDatabase requires migration changes."
        )

        return 0

    except Exception as exc:
        print(
            f"Error: {exc}",
            file=sys.stderr,
        )
        return 1

    finally:
        database.close()


def _run_plan(
    config: ProjectConfig,
) -> int:
    """Show pending migrations without executing them."""
    database: Database | None = None

    try:
        database = _create_database(
            config.database_url
        )
        database.connect()

        migrations = _load_migrations(
            config
        )

        history = MigrationHistory(
            database
        )

        planner = MigrationPlanner(
            history
        )

        plan = planner.plan(
            migrations
        )

        print("Migration plan")
        print("==============")
        print(
            f"Pending migrations: "
            f"{plan.count}"
        )

        for migration in plan.pending:
            print(
                f"  {migration.version:03d} "
                f"{migration.name}"
            )

        print(
            "\nNo changes were made to the database."
        )

        return 0

    except Exception as exc:
        print(
            f"Error: {exc}",
            file=sys.stderr,
        )
        return 1

    finally:
        if database is not None:
            database.close()


def _run_lint(
    config: ProjectConfig,
) -> int:
    """Lint migration files."""
    try:
        migrations = _load_migrations(
            config
        )

        report = lint_migrations(
            migrations
        )

    except (
        MigrationDiscoveryError,
        MigrationParseError,
    ) as exc:
        print(
            f"Lint error: {exc}",
            file=sys.stderr,
        )
        return 1

    except Exception as exc:
        print(
            f"Lint error: {exc}",
            file=sys.stderr,
        )
        return 1

    print("Migration lint")
    print("==============")

    print(
        f"Migrations checked: "
        f"{len(report.migrations)}"
    )

    print(
        f"Errors:   {report.error_count}"
    )

    print(
        f"Warnings: {report.warning_count}"
    )

    print(
        f"Info:     {report.info_count}"
    )

    if report.issues:
        print("\nIssues:")

        for issue in report.issues:
            print(
                f"  {issue.format()}"
            )

    # Lint is intentionally non-zero whenever there are
    # findings. This makes CI able to detect potentially
    # unsafe migrations while still reporting warnings/info.
    if report.issues:
        return 1

    return 0


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