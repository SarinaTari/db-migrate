"""Tests for migration status inspection."""

from pathlib import Path

from dbmigrate.database import SQLiteDatabase
from dbmigrate.migration import Migration
from dbmigrate.runner import MigrationRunner
from dbmigrate.status import MigrationStatusInspector


def create_database(
    tmp_path: Path,
) -> SQLiteDatabase:
    """Create a connected SQLite database."""
    database = SQLiteDatabase(
        tmp_path / "test.db"
    )
    database.connect()
    return database


def make_migration(
    tmp_path: Path,
    version: int,
    name: str,
    up_sql: str = "SELECT 1;",
    down_sql: str = "SELECT 1;",
) -> Migration:
    """Create a migration object for testing."""
    path = (
        tmp_path
        / f"{version:03d}_{name}.sql"
    )

    return Migration(
        version=version,
        name=name,
        up_sql=up_sql,
        down_sql=down_sql,
        path=path,
    )


def test_status_reports_pending_migrations(
    tmp_path: Path,
) -> None:
    database = create_database(tmp_path)

    try:
        migrations = [
            make_migration(
                tmp_path,
                1,
                "first",
            ),
            make_migration(
                tmp_path,
                2,
                "second",
            ),
        ]

        runner = MigrationRunner(database)
        inspector = MigrationStatusInspector(
            runner
        )

        status = inspector.inspect(
            migrations
        )

        assert status.applied == []
        assert [
            migration.version
            for migration in status.pending
        ] == [1, 2]

        assert status.missing == []
        assert status.current is None
        assert not status.is_up_to_date

    finally:
        database.close()


def test_status_reports_applied_and_pending(
    tmp_path: Path,
) -> None:
    database = create_database(tmp_path)

    try:
        migrations = [
            make_migration(
                tmp_path,
                1,
                "first",
            ),
            make_migration(
                tmp_path,
                2,
                "second",
            ),
        ]

        runner = MigrationRunner(database)

        runner.apply(migrations[0])

        inspector = MigrationStatusInspector(
            runner
        )

        status = inspector.inspect(
            migrations
        )

        assert [
            migration.version
            for migration in status.applied
        ] == [1]

        assert [
            migration.version
            for migration in status.pending
        ] == [2]

        assert status.current is not None
        assert status.current.version == 1
        assert not status.is_up_to_date

    finally:
        database.close()


def test_status_reports_up_to_date(
    tmp_path: Path,
) -> None:
    database = create_database(tmp_path)

    try:
        migrations = [
            make_migration(
                tmp_path,
                1,
                "first",
            ),
            make_migration(
                tmp_path,
                2,
                "second",
            ),
        ]

        runner = MigrationRunner(database)
        runner.apply_all(migrations)

        inspector = MigrationStatusInspector(
            runner
        )

        status = inspector.inspect(
            migrations
        )

        assert status.applied_count == 2
        assert status.pending_count == 0
        assert status.missing_count == 0
        assert status.current is not None
        assert status.current.version == 2
        assert status.is_up_to_date

    finally:
        database.close()


def test_status_detects_missing_migration_file(
    tmp_path: Path,
) -> None:
    database = create_database(tmp_path)

    try:
        migration = make_migration(
            tmp_path,
            1,
            "first",
        )

        runner = MigrationRunner(database)
        runner.apply(migration)

        inspector = MigrationStatusInspector(
            runner
        )

        status = inspector.inspect([])

        assert status.applied == []
        assert status.pending == []
        assert len(status.missing) == 1
        assert status.missing[0].version == 1
        assert status.missing[0].name == "first"
        assert not status.is_up_to_date

    finally:
        database.close()


def test_status_counts_are_consistent(
    tmp_path: Path,
) -> None:
    database = create_database(tmp_path)

    try:
        migrations = [
            make_migration(
                tmp_path,
                1,
                "first",
            ),
            make_migration(
                tmp_path,
                2,
                "second",
            ),
            make_migration(
                tmp_path,
                3,
                "third",
            ),
        ]

        runner = MigrationRunner(database)
        runner.apply(migrations[0])

        inspector = MigrationStatusInspector(
            runner
        )

        status = inspector.inspect(
            migrations
        )

        assert (
            status.applied_count
            + status.pending_count
            == len(migrations)
        )

        assert status.missing_count == 0

    finally:
        database.close()