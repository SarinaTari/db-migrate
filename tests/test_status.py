"""Tests for migration status inspection."""

from pathlib import Path

from dbmigrate.database import SQLiteDatabase
from dbmigrate.migration import Migration
from dbmigrate.runner import MigrationRunner
from dbmigrate.status import MigrationStatusInspector


def create_database(tmp_path: Path) -> SQLiteDatabase:
    """Create and connect a temporary SQLite database."""
    database = SQLiteDatabase(
        tmp_path / "test.db"
    )
    database.connect()
    return database


def make_migration(
    tmp_path: Path,
    version: int,
    name: str,
    sql: str,
) -> Migration:
    """Create a migration object for testing."""
    path = (
        tmp_path
        / f"{version:03d}_{name}.sql"
    )

    path.write_text(
        f"""-- migration: {version}
-- name: {name}

-- +up

{sql}

-- +down

DROP TABLE IF EXISTS {name};
""",
        encoding="utf-8",
    )

    return Migration(
        version=version,
        name=name,
        up_sql=sql.strip(),
        down_sql=f"DROP TABLE IF EXISTS {name};",
        path=path,
    )


def test_status_reports_all_pending(
    tmp_path: Path,
) -> None:
    database = create_database(tmp_path)

    try:
        migrations = [
            make_migration(
                tmp_path,
                1,
                "users",
                "CREATE TABLE users (id INTEGER);",
            ),
            make_migration(
                tmp_path,
                2,
                "posts",
                "CREATE TABLE posts (id INTEGER);",
            ),
        ]

        runner = MigrationRunner(database)
        inspector = MigrationStatusInspector(runner)

        status = inspector.inspect(migrations)

        assert status.total_count == 2
        assert status.applied_count == 0
        assert status.pending_count == 2
        assert status.missing_count == 0
        assert status.current is None
        assert len(status.pending) == 2
        assert status.is_up_to_date is False

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
                "users",
                "CREATE TABLE users (id INTEGER);",
            ),
            make_migration(
                tmp_path,
                2,
                "posts",
                "CREATE TABLE posts (id INTEGER);",
            ),
        ]

        runner = MigrationRunner(database)
        runner.apply(migrations[0])

        inspector = MigrationStatusInspector(runner)

        status = inspector.inspect(migrations)

        assert status.total_count == 2
        assert status.applied_count == 1
        assert status.pending_count == 1
        assert status.missing_count == 0
        assert status.current == migrations[0]
        assert status.pending == [migrations[1]]
        assert status.is_up_to_date is False

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
                "users",
                "CREATE TABLE users (id INTEGER);",
            ),
            make_migration(
                tmp_path,
                2,
                "posts",
                "CREATE TABLE posts (id INTEGER);",
            ),
        ]

        runner = MigrationRunner(database)
        runner.apply_all(migrations)

        inspector = MigrationStatusInspector(runner)

        status = inspector.inspect(migrations)

        assert status.total_count == 2
        assert status.applied_count == 2
        assert status.pending_count == 0
        assert status.missing_count == 0
        assert status.current == migrations[1]
        assert status.pending == []
        assert status.is_up_to_date is True

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
            "users",
            "CREATE TABLE users (id INTEGER);",
        )

        runner = MigrationRunner(database)
        runner.apply(migration)

        migration.path.unlink()

        inspector = MigrationStatusInspector(runner)

        status = inspector.inspect([])

        assert status.total_count == 0
        assert status.applied_count == 0
        assert status.pending_count == 0
        assert status.missing_count == 1
        assert status.current is None
        assert status.pending == []
        assert status.is_up_to_date is False

        assert status.missing[0].version == 1
        assert status.missing[0].name == "users"

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
                "users",
                "CREATE TABLE users (id INTEGER);",
            ),
            make_migration(
                tmp_path,
                2,
                "posts",
                "CREATE TABLE posts (id INTEGER);",
            ),
            make_migration(
                tmp_path,
                3,
                "comments",
                "CREATE TABLE comments (id INTEGER);",
            ),
        ]

        runner = MigrationRunner(database)
        runner.apply(migrations[0])

        inspector = MigrationStatusInspector(runner)

        status = inspector.inspect(migrations)

        assert (
            status.applied_count
            + status.pending_count
            == status.total_count
        )

        assert status.applied_count == 1
        assert status.pending_count == 2

    finally:
        database.close()