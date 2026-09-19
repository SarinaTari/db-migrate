"""Tests for migration execution."""

from pathlib import Path

import pytest

from dbmigrate.database import SQLiteDatabase
from dbmigrate.history import MigrationHistory
from dbmigrate.migration import Migration
from dbmigrate.runner import (
    MigrationRunner,
    MigrationRunnerError,
)


def create_database(tmp_path: Path) -> SQLiteDatabase:
    """Create and connect a temporary SQLite database."""
    database = SQLiteDatabase(tmp_path / "test.db")
    database.connect()
    return database


def make_migration(
    tmp_path: Path,
    version: int,
    name: str,
    up_sql: str,
    down_sql: str = "SELECT 1;",
) -> Migration:
    """Create an in-memory Migration object."""
    path = tmp_path / f"{version:03d}_{name}.sql"

    return Migration(
        version=version,
        name=name,
        up_sql=up_sql,
        down_sql=down_sql,
        path=path,
    )


def test_apply_migration(tmp_path: Path) -> None:
    database = create_database(tmp_path)

    try:
        migration = make_migration(
            tmp_path,
            1,
            "create_users",
            """
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL
            );
            """,
        )

        runner = MigrationRunner(database)

        result = runner.apply(migration)

        assert result.migration == migration
        assert result.checksum

        table = database.fetch_one(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name = 'users'
            """
        )

        assert table == ("users",)

        record = MigrationHistory(database).get(1)

        assert record is not None
        assert record.version == 1
        assert record.name == "create_users"
        assert record.checksum == result.checksum
    finally:
        database.close()


def test_apply_all_applies_pending_migrations(
    tmp_path: Path,
) -> None:
    database = create_database(tmp_path)

    try:
        migrations = [
            make_migration(
                tmp_path,
                1,
                "create_users",
                """
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY
                );
                """,
            ),
            make_migration(
                tmp_path,
                2,
                "add_email",
                """
                ALTER TABLE users
                ADD COLUMN email TEXT;
                """,
            ),
        ]

        runner = MigrationRunner(database)

        results = runner.apply_all(migrations)

        assert [result.migration.version for result in results] == [
            1,
            2,
        ]

        records = MigrationHistory(database).list_applied()

        assert [record.version for record in records] == [1, 2]
    finally:
        database.close()


def test_apply_all_skips_applied_migrations(
    tmp_path: Path,
) -> None:
    database = create_database(tmp_path)

    try:
        migrations = [
            make_migration(
                tmp_path,
                1,
                "create_users",
                """
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY
                );
                """,
            ),
            make_migration(
                tmp_path,
                2,
                "add_email",
                """
                ALTER TABLE users
                ADD COLUMN email TEXT;
                """,
            ),
        ]

        runner = MigrationRunner(database)

        first_run = runner.apply_all(migrations)
        second_run = runner.apply_all(migrations)

        assert len(first_run) == 2
        assert second_run == []
    finally:
        database.close()


def test_pending_returns_only_unapplied_migrations(
    tmp_path: Path,
) -> None:
    database = create_database(tmp_path)

    try:
        migrations = [
            make_migration(
                tmp_path,
                1,
                "create_users",
                """
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY
                );
                """,
            ),
            make_migration(
                tmp_path,
                2,
                "add_email",
                """
                ALTER TABLE users
                ADD COLUMN email TEXT;
                """,
            ),
        ]

        runner = MigrationRunner(database)

        runner.apply(migrations[0])

        pending = runner.pending(migrations)

        assert [migration.version for migration in pending] == [2]
    finally:
        database.close()


def test_apply_already_applied_migration_fails(
    tmp_path: Path,
) -> None:
    database = create_database(tmp_path)

    try:
        migration = make_migration(
            tmp_path,
            1,
            "create_users",
            """
            CREATE TABLE users (
                id INTEGER PRIMARY KEY
            );
            """,
        )

        runner = MigrationRunner(database)

        runner.apply(migration)

        with pytest.raises(MigrationRunnerError, match="already applied"):
            runner.apply(migration)
    finally:
        database.close()


def test_failed_migration_is_rolled_back(
    tmp_path: Path,
) -> None:
    database = create_database(tmp_path)

    try:
        migration = make_migration(
            tmp_path,
            1,
            "broken_migration",
            """
            CREATE TABLE users (
                id INTEGER PRIMARY KEY
            );

            THIS IS INVALID SQL;
            """,
        )

        runner = MigrationRunner(database)

        with pytest.raises(MigrationRunnerError):
            runner.apply(migration)

        table = database.fetch_one(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name = 'users'
            """
        )

        assert table is None

        record = MigrationHistory(database).get(1)

        assert record is None
    finally:
        database.close()


def test_history_record_is_rolled_back_with_migration(
    tmp_path: Path,
) -> None:
    database = create_database(tmp_path)

    try:
        migration = make_migration(
            tmp_path,
            1,
            "broken_migration",
            """
            CREATE TABLE users (
                id INTEGER PRIMARY KEY
            );

            INVALID SQL;
            """,
        )

        runner = MigrationRunner(database)

        with pytest.raises(MigrationRunnerError):
            runner.apply(migration)

        history = MigrationHistory(database)

        assert history.list_applied() == []
    finally:
        database.close()


def test_apply_all_runs_in_version_order(
    tmp_path: Path,
) -> None:
    database = create_database(tmp_path)

    try:
        migrations = [
            make_migration(
                tmp_path,
                2,
                "add_email",
                """
                ALTER TABLE users
                ADD COLUMN email TEXT;
                """,
            ),
            make_migration(
                tmp_path,
                1,
                "create_users",
                """
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY
                );
                """,
            ),
        ]

        runner = MigrationRunner(database)

        results = runner.apply_all(migrations)

        assert [result.migration.version for result in results] == [
            1,
            2,
        ]
    finally:
        database.close()


def test_pending_preserves_version_order(
    tmp_path: Path,
) -> None:
    database = create_database(tmp_path)

    try:
        migrations = [
            make_migration(
                tmp_path,
                3,
                "third",
                "SELECT 3;",
            ),
            make_migration(
                tmp_path,
                1,
                "first",
                "SELECT 1;",
            ),
            make_migration(
                tmp_path,
                2,
                "second",
                "SELECT 2;",
            ),
        ]

        runner = MigrationRunner(database)

        pending = runner.pending(migrations)

        assert [migration.version for migration in pending] == [
            1,
            2,
            3,
        ]
    finally:
        database.close()