"""Command-line interface for dbmigrate."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from . import __version__
from .commands.base import Command, get_commands, resolve_command
from .config import ConfigurationError, load_config
from .database import DatabaseError, SQLiteDatabase
from .history import HistoryError, MigrationHistory
from .migration import (
    MigrationDiscoveryError,
    MigrationParseError,
    discover_migrations,
)
from .migration_creator import (
    MigrationCreationError,
    create_migration,
)
from .planner import MigrationPlanner, MigrationPlanningError
from .runner import MigrationRunner, MigrationRunnerError
from .status import (
    MigrationStatusError,
    MigrationStatusInspector,
)
from .validation import validate_migrations
from .linter import lint_migrations
from .explainer import explain_migrations
from .impact import analyze_migrations


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

    if command.name == "create":
        return _run_create(
            args.name
        )

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

    if command.name == "plan":
        return _run_plan(config)

    if command.name == "lint":
        return _run_lint(config)

    if command.name == "up":
        return _run_up(config)

    if command.name == "down":
        return _run_down(
            config,
            args.steps,
        )

    if command.name == "history":
        return _run_history(config)

    if command.name == "current":
        return _run_current(config)

    if command.name == "status":
        return _run_status(config)

    if command.name == "explain":
        return _run_explain(config)

    if command.name == "impact":
        return _run_impact(config)

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
    name: str,
) -> int:
    """Create a new migration."""
    try:
        config = load_config()
    except ConfigurationError as exc:
        print(
            f"Configuration error: {exc}",
            file=sys.stderr,
        )
        return 1

    try:
        migration = create_migration(
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
        f"Created migration "
        f"{migration.identifier}."
    )
    print(
        f"File: "
        f"{migration.path}"
    )

    return 0


def _run_validate(config) -> int:
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

    database = _create_database(
        config.database_url
    )

    if database is None:
        return 1

    try:
        database.connect()

        history = MigrationHistory(
            database
        )

        records = history.list_applied()

        report = validate_migrations(
            config.migrations_path,
            records=records,
        )

    except (
        DatabaseError,
        HistoryError,
    ) as exc:
        print(
            f"Validation error: {exc}",
            file=sys.stderr,
        )
        return 1

    finally:
        database.close()

    print(
        "Migration directory: "
        f"{config.migrations_path}"
    )

    print(
        "Migrations discovered: "
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
            print(
                f"  - {error}"
            )

        return 1

    print(
        "\nMigration validation passed."
    )

    return 0


def _create_database(
    database_url: str,
):
    """Create a database implementation."""
    prefix = "sqlite:///"

    if not database_url.startswith(
        prefix
    ):
        print(
            "Configuration error: Phase 10 supports only "
            "sqlite:/// database URLs.",
            file=sys.stderr,
        )
        return None

    raw_path = database_url[
        len(prefix):
    ]

    if not raw_path:
        print(
            "Configuration error: "
            "SQLite database path is empty.",
            file=sys.stderr,
        )
        return None

    path = Path(raw_path)

    if not path.is_absolute():
        path = Path.cwd() / path

    return SQLiteDatabase(path)


def _load_migrations(config):
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


def _run_plan(config) -> int:
    """Show the migrations that would be applied."""
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

        history = MigrationHistory(
            database
        )

        planner = MigrationPlanner(
            history
        )

        plan = planner.plan(
            migrations
        )

        print(
            "Migration plan"
        )
        print(
            "==============="
        )

        if plan.is_empty:
            print(
                "\nNo pending migrations."
            )
            print(
                "No changes would be made to the database."
            )
            return 0

        print(
            f"\nPending migrations: "
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

    except (
        DatabaseError,
        MigrationRunnerError,
        MigrationPlanningError,
    ) as exc:
        print(
            f"Error: {exc}",
            file=sys.stderr,
        )
        return 1

    finally:
        database.close()


def _run_check(config) -> int:
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

        print(
            "Database connection: OK"
        )
        print(
            "Database engine: SQLite"
        )
        print(
            f"SQLite version: {row[0]}"
        )
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


def _run_up(config) -> int:
    """Apply all pending migrations."""
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

        applied = runner.apply_all(
            migrations
        )

        if not applied:
            print(
                "No pending migrations."
            )
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
    config,
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
            print(
                "No applied migrations."
            )
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


def _run_history(config) -> int:
    """Show migration history."""
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


def _run_current(config) -> int:
    """Show the current migration version."""
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


def _run_status(config) -> int:
    """Show migration status."""
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

        print(
            "Migration status"
        )
        print(
            "================"
        )
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
                "Current: none"
            )
        else:
            print(
                "Current: "
                f"{status.current.version:03d} "
                f"{status.current.name}"
            )

        if status.pending:
            print(
                "\nPending migrations:"
            )

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


def _run_lint(config) -> int:
    """Lint migration SQL for potentially dangerous operations."""
    try:
        migrations = _load_migrations(
            config
        )

        report = lint_migrations(
            migrations
        )

        print("Migration lint")
        print("===============")

        if report.is_clean:
            print("\nNo lint issues found.")
            print(
                f"Checked {len(report.migrations)} "
                "migration(s)."
            )
            return 0

        for migration in report.migrations:
            migration_issues = [
                issue
                for issue in report.issues
                if issue.migration == migration
            ]

            if not migration_issues:
                continue

            print()
            print(migration.identifier)

            for issue in migration_issues:
                print(
                    f"  {issue.severity} "
                    f"[{issue.code}]"
                )
                print(
                    f"  {issue.section}: "
                    f"line {issue.line}"
                )
                print(
                    f"  {issue.message}"
                )

        print()
        print("Summary")
        print("-------")
        print(
            f"Errors:   {report.error_count}"
        )
        print(
            f"Warnings: {report.warning_count}"
        )
        print(
            f"Info:     {report.info_count}"
        )

        return 1 if not report.is_valid else 0

    except MigrationRunnerError as exc:
        print(
            f"Error: {exc}",
            file=sys.stderr,
        )
        return 1

def _run_explain(config) -> int:
    """Explain recognized operations in migrations."""
    try:
        migrations = _load_migrations(
            config
        )

        explanations = explain_migrations(
            migrations
        )

        print("Migration explanation")
        print("=====================")

        for explanation in explanations:
            print()
            print(
                explanation.migration.identifier
            )

            if explanation.is_empty:
                print(
                    "  No recognized SQL operations."
                )
                continue

            for item in explanation.explanations:
                print()
                print(
                    f"  {item.section.upper()}"
                )
                print(
                    f"    {item.operation}"
                )
                print(
                    f"      line: {item.line}"
                )
                print(
                    f"      {item.description}"
                )

        if not explanations:
            print(
                "\nNo migrations found."
            )

        return 0

    except MigrationRunnerError as exc:
        print(
            f"Error: {exc}",
            file=sys.stderr,
        )
        return 1

def _run_impact(config) -> int:
    """Analyze the apparent impact of migrations."""
    try:
        migrations = _load_migrations(
            config
        )

        impacts = analyze_migrations(
            migrations
        )

        print("Migration impact")
        print("================")

        for impact in impacts:
            print()
            print(
                impact.migration.identifier
            )

            print()
            print("  Tables:")

            if impact.tables:
                for table in impact.tables:
                    print(
                        f"    {table}"
                    )
            else:
                print(
                    "    None detected"
                )

            print()
            print("  Indexes:")

            if impact.indexes:
                for index in impact.indexes:
                    print(
                        f"    {index}"
                    )
            else:
                print(
                    "    None detected"
                )

            print()
            print("  Operations:")

            if impact.operations:
                for operation in impact.operations:
                    print(
                        f"    {operation}"
                    )
            else:
                print(
                    "    None detected"
                )

            print()
            print(
                f"  Risk: {impact.risk}"
            )

        if not impacts:
            print(
                "\nNo migrations found."
            )

        return 0

    except MigrationRunnerError as exc:
        print(
            f"Error: {exc}",
            file=sys.stderr,
        )
        return 1

    
def main(
    argv: list[str] | None = None,
) -> int:
    """Run the dbmigrate CLI."""
    try:
        args = parse_args(
            argv
        )
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
    raise SystemExit(
        main()
    )