"""Command-line interface for dbmigrate."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Sequence

from . import __version__
from .commands.base import (
    get_commands,
    resolve_command,
)
from .config import (
    ConfigurationError,
    load_config,
)
from .database import DatabaseError
from .database_factory import create_database
from .database_lock import (
    MigrationLockError,
    create_migration_lock,
)
from .doctor import DatabaseDoctor
from .history import (
    HistoryError,
    MigrationHistory,
)
from .migration import (
    MigrationDiscoveryError,
    MigrationParseError,
    discover_migrations,
)
from .migration_safety import (
    MigrationSafetyChecker,
    MigrationSafetyError,
)
from .runner import (
    MigrationRunner,
    MigrationRunnerError,
)
from .status import (
    MigrationStatusError,
    MigrationStatusInspector,
)
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
        command_parser = subparsers.add_parser(
            command.name,
            help=command.description,
            description=command.description,
        )

        if command.name == "create":
            command_parser.add_argument(
                "name",
                help="Migration name.",
            )

        if command.name == "down":
            command_parser.add_argument(
                "--steps",
                type=int,
                default=1,
                help="Number of migrations to roll back.",
            )

    return parser


def _create_database(
    database_url: str,
):
    """Create a database implementation."""
    try:
        return create_database(
            database_url
        )

    except DatabaseError as exc:
        print(
            f"Configuration error: {exc}",
            file=sys.stderr,
        )
        return None


def _load_migrations(
    config,
):
    """Discover and parse migration files."""
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


def _run_init(
    config,
) -> int:
    """Initialize a migration project."""
    print(
        "The project is already initialized."
    )
    return 0


def _run_validate(
    config,
) -> int:
    """Validate migration files."""
    try:
        migrations = _load_migrations(
            config
        )

        errors = validate_migrations(
            migrations
        )

        print(
            f"Migration directory: "
            f"{config.migrations_path}"
        )

        print(
            f"Discovered migrations: "
            f"{len(migrations)}"
        )

        if errors:
            print(
                "Migration validation failed:",
                file=sys.stderr,
            )

            for error in errors:
                print(
                    f"- {error}",
                    file=sys.stderr,
                )

            return 1

        print(
            "Migration validation: OK"
        )

        return 0

    except MigrationRunnerError as exc:
        print(
            f"Migration validation failed: {exc}",
            file=sys.stderr,
        )
        return 1


def _run_check(config) -> int:
    """Check database connectivity."""
    database = _create_database(
        config.database_url
    )

    if database is None:
        return 1

    try:
        database.connect()

        version = database.version()

        engine_names = {
            "sqlite": "SQLite",
            "postgresql": "PostgreSQL",
            "mysql": "MySQL",
        }

        engine_name = engine_names.get(
            database.engine,
            database.engine,
        )

        print("Database connection: OK")
        print(
            f"Database engine: {engine_name}"
        )

        if database.engine == "sqlite":
            print(
                f"SQLite version: {version}"
            )
        elif database.engine == "postgresql":
            print(
                f"PostgreSQL version: {version}"
            )
        elif database.engine == "mysql":
            print(
                f"MySQL version: {version}"
            )
        else:
            print(
                f"Database version: {version}"
            )

        if hasattr(database, "path"):
            print(
                f"Database path: {database.path}"
            )

        return 0

    except DatabaseError as exc:
        print(
            f"Database check failed: {exc}",
            file=sys.stderr,
        )
        return 1

    finally:
        database.close()


def _run_up(
    config,
) -> int:
    """Apply pending migrations."""
    database = _create_database(
        config.database_url
    )

    if database is None:
        return 1

    try:
        database.connect()

        migrations = _load_migrations(
            config
        )

        safety_checker = MigrationSafetyChecker(
            database
        )

        safety_checker.require_safe(
            migrations
        )

        lock = create_migration_lock(
            database
        )

        with lock:
            runner = MigrationRunner(
                database
            )

            applied = runner.apply_all(
                migrations
            )

        if not applied:
            print(
                "No pending migrations."
            )
            return 0

        for migration in applied:
            print(
                f"Applied {migration.identifier}."
            )

        return 0

    except (
        MigrationRunnerError,
        MigrationSafetyError,
        MigrationLockError,
        DatabaseError,
    ) as exc:
        print(
            f"Migration failed: {exc}",
            file=sys.stderr,
        )
        return 1

    finally:
        database.close()


def _run_down(
    config,
    steps: int,
) -> int:
    """Roll back migrations."""
    if steps <= 0:
        print(
            "The number of rollback steps must be "
            "greater than zero.",
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

        migrations = _load_migrations(
            config
        )

        safety_checker = MigrationSafetyChecker(
            database
        )

        safety_checker.require_safe(
            migrations
        )

        lock = create_migration_lock(
            database
        )

        with lock:
            runner = MigrationRunner(
                database
            )

            rolled_back = runner.rollback_steps(
                migrations,
                steps,
            )

        if not rolled_back:
            print(
                "No applied migrations."
            )
            return 0

        for migration in rolled_back:
            print(
                f"Rolled back "
                f"{migration.identifier}."
            )

        return 0

    except (
        MigrationRunnerError,
        MigrationSafetyError,
        MigrationLockError,
        DatabaseError,
    ) as exc:
        print(
            f"Rollback failed: {exc}",
            file=sys.stderr,
        )
        return 1

    finally:
        database.close()


def _run_history(
    config,
) -> int:
    """Display migration history."""
    database = _create_database(
        config.database_url
    )

    if database is None:
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

    except (
        MigrationRunnerError,
        DatabaseError,
    ) as exc:
        print(
            f"Could not read migration history: {exc}",
            file=sys.stderr,
        )
        return 1

    finally:
        database.close()


def _run_current(
    config,
) -> int:
    """Display the current migration."""
    database = _create_database(
        config.database_url
    )

    if database is None:
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
            f"Current migration: "
            f"{current.version:03d} "
            f"{current.name}"
        )

        return 0

    except (
        MigrationRunnerError,
        DatabaseError,
    ) as exc:
        print(
            f"Could not determine current migration: "
            f"{exc}",
            file=sys.stderr,
        )
        return 1

    finally:
        database.close()


def _run_status(
    config,
) -> int:
    """Display migration status."""
    database = _create_database(
        config.database_url
    )

    if database is None:
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
            print(
                "Current migration: none"
            )
        else:
            print(
                f"Current migration: "
                f"{status.current.version:03d} "
                f"{status.current.name}"
            )

        if status.pending:
            print("Pending migrations:")

            for migration in status.pending:
                print(
                    f"{migration.version:03d} "
                    f"{migration.name}"
                )

        if (
            status.pending_count == 0
            and status.missing_count == 0
        ):
            print(
                "Database is up to date."
            )
        else:
            print(
                "Database requires migration changes."
            )

        return 0

    except (
        MigrationRunnerError,
        MigrationStatusError,
        DatabaseError,
    ) as exc:
        print(
            f"Could not determine migration status: "
            f"{exc}",
            file=sys.stderr,
        )
        return 1

    finally:
        database.close()


def _run_doctor(
    config,
) -> int:
    """Run database and migration health diagnostics."""
    database = _create_database(
        config.database_url
    )

    if database is None:
        return 1

    try:
        database.connect()

        migrations = _load_migrations(
            config
        )

        report = DatabaseDoctor(
            database
        ).inspect(
            migrations
        )

        for issue in report.issues:
            print(
                issue.format()
            )

        if report.healthy:
            print(
                "Doctor: database is healthy."
            )
            return 0

        print(
            "Doctor: database health checks "
            "reported errors.",
            file=sys.stderr,
        )

        return 1

    except (
        MigrationRunnerError,
        DatabaseError,
    ) as exc:
        print(
            f"Doctor failed: {exc}",
            file=sys.stderr,
        )
        return 1

    finally:
        database.close()


def _run_create(
    config,
    args,
) -> int:
    """Create a new migration file."""

    from .migration_creator import (
        MigrationCreationError,
        create_migration,
    )

    try:
        migration = create_migration(
            config.migrations_path,
            args.name,
        )

        print(
            f"Created migration "
            f"{migration.identifier}."
        )

        print(
            f"File: {migration.path}"
        )

        return 0

    except MigrationCreationError as exc:
        print(
            str(exc),
            file=sys.stderr,
        )
        return 1


def _run_plan(
    config,
) -> int:
    """Display the migrations that would be applied."""
    database = _create_database(
        config.database_url
    )

    if database is None:
        return 1

    try:
        database.connect()

        migrations = _load_migrations(
            config
        )

        from .planner import MigrationPlanner

        planner = MigrationPlanner(
            MigrationHistory(database)
        )

        plan = planner.plan(
            migrations
        )

        print("Migration plan")

        if plan.is_empty:
            print(
                "No pending migrations."
            )
            print(
                "No changes were made "
                "to the database."
            )
            return 0

        print(
            f"Pending migrations: "
            f"{plan.count}"
        )

        for migration in plan.pending:
            print(
                f"{migration.version:03d} "
                f"{migration.name}"
            )

        print(
            "No changes were made "
            "to the database."
        )

        return 0

    except (
        DatabaseError,
        MigrationDiscoveryError,
        MigrationParseError,
    ) as exc:
        print(
            str(exc),
            file=sys.stderr,
        )
        return 1

    finally:
        database.close()


def _run_lint(
    config,
) -> int:
    """Lint migration files for potentially dangerous SQL."""
    try:
        migrations = _load_migrations(
            config
        )

        from .linter import lint_migrations

        report = lint_migrations(
            migrations
        )

        print("Migration lint")

        for issue in report.issues:
            print(
                issue.format()
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

        if report.is_clean:
            print(
                "No migration issues found."
            )
            return 0

        return 1

    except (
        MigrationDiscoveryError,
        MigrationParseError,
    ) as exc:
        print(
            str(exc),
            file=sys.stderr,
        )
        return 1


def run_command(
    args,
    config,
) -> int:
    """Run the selected command."""
    command = resolve_command(
        args.command
    )

    if command is None:
        print(
            "No command specified.",
            file=sys.stderr,
        )
        return 1

    command_name = command.name

    if command_name == "init":
        return _run_init(
            config
        )

    if command_name == "create":
        return _run_create(
            config,
            args,
        )

    if command_name == "up":
        return _run_up(
            config
        )

    if command_name == "down":
        return _run_down(
            config,
            args.steps,
        )

    if command_name == "status":
        return _run_status(
            config
        )

    if command_name == "history":
        return _run_history(
            config
        )

    if command_name == "current":
        return _run_current(
            config
        )

    if command_name == "validate":
        return _run_validate(
            config
        )

    if command_name == "plan":
        return _run_plan(
            config
        )

    if command_name == "lint":
        return _run_lint(
            config
        )

    if command_name == "explain":
        return _run_explain(
            config,
            args,
        )

    if command_name == "impact":
        return _run_impact(
            config,
            args,
        )

    if command_name == "schema":
        return _run_schema(
            config
        )

    if command_name == "schema-diff":
        return _run_schema_diff(
            config
        )

    if command_name == "fingerprint":
        return _run_fingerprint(
            config
        )

    if command_name == "doctor":
        return _run_doctor(
            config
        )

    if command_name == "check":
        return _run_check(
            config
        )

    if command_name == "verify-schema":
        return _run_verify_schema(
            config
        )

    print(
        f"Command '{command_name}' is not implemented.",
        file=sys.stderr,
    )
    return 1


def main(
    argv: Sequence[str] | None = None,
) -> int:
    """Run the dbmigrate command-line interface."""
    parser = build_parser()

    try:
        args = parser.parse_args(
            argv
        )
    except SystemExit as exc:
        return int(exc.code)

    if args.command is None:
        parser.print_help()
        return 0

    try:
        config = load_config()
    except ConfigurationError as exc:
        print(
            f"Configuration error: {exc}",
            file=sys.stderr,
        )
        return 1

    try:
        return run_command(
            args,
            config,
        )
    except (
        MigrationDiscoveryError,
        MigrationParseError,
        MigrationRunnerError,
        HistoryError,
        MigrationStatusError,
        DatabaseError,
    ) as exc:
        print(
            str(exc),
            file=sys.stderr,
        )
        return 1