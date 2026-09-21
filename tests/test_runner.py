"""Tests for migration execution."""

from pathlib import Path

import pytest

from dbmigrate.database import SQLiteDatabase
from dbmigrate.history import MigrationHistory
from dbmigrate.migration import Migration, parse_migration
from dbmigrate.runner import (
    MigrationRunner,
    MigrationRunnerError,
)


def create_database(
    tmp_path: Path,
) -> SQLiteDatabase:
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
    up_sql: str,
    down_sql: str = "SELECT 1;",
) -> Migration:
    """Create and parse a temporary migration."""
    path = (
        tmp_path
        / f"{version:03d}_{name}.sql"
    )

    path.write_text(
        f"""-- migration: {version:03d}
-- name: {name}

-- +up

{up_sql}

-- +down

{down_sql}
""",
        encoding="utf-8",
    )

    return parse_migration(path)


def test_apply_migration(
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
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL
            );
            """,
        )

        runner = MigrationRunner(database)

        result = runner.apply(migration)

        assert result.migration == migration
        assert result.action == "applied"
        assert result.checksum
        assert len(result.checksum) == 64

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


def test_apply_migration_checksum_is_deterministic(
    tmp_path: Path,
) -> None:
    database = create_database(tmp_path)

    try:
        migration = make_migration(
            tmp_path,
            1,
            "create_users",
            "CREATE TABLE users (id INTEGER);",
            "DROP TABLE users;",
        )

        runner = MigrationRunner(database)

        first_checksum = runner.apply(
            migration
        ).checksum

        runner.rollback(migration)

        second_checksum = runner.apply(
            migration
        ).checksum

        assert first_checksum is not None
        assert second_checksum is not None
        assert first_checksum == second_checksum
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

        assert [
            result.migration.version
            for result in results
        ] == [1, 2]

        records = MigrationHistory(
            database
        ).list_applied()

        assert [
            record.version
            for record in records
        ] == [1, 2]
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

        first_run = runner.apply_all(
            migrations
        )
        second_run = runner.apply_all(
            migrations
        )

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

        pending = runner.pending(
            migrations
        )

        assert [
            migration.version
            for migration in pending
        ] == [2]
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

        with pytest.raises(
            MigrationRunnerError,
            match="already applied",
        ):
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

        with pytest.raises(
            MigrationRunnerError
        ):
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

        record = MigrationHistory(
            database
        ).get(1)

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

        with pytest.raises(
            MigrationRunnerError
        ):
            runner.apply(migration)

        history = MigrationHistory(
            database
        )

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

        results = runner.apply_all(
            migrations
        )

        assert [
            result.migration.version
            for result in results
        ] == [1, 2]
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

        pending = runner.pending(
            migrations
        )

        assert [
            migration.version
            for migration in pending
        ] == [1, 2, 3]
    finally:
        database.close()


def test_applied_preserves_version_order(
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

        runner.apply_all(migrations)

        applied = runner.applied(
            migrations
        )

        assert [
            migration.version
            for migration in applied
        ] == [1, 2, 3]
    finally:
        database.close()


def test_rollback_removes_latest_migration(
    tmp_path: Path,
) -> None:
    database = create_database(tmp_path)

    try:
        migrations = [
            make_migration(
                tmp_path,
                1,
                "first",
                "CREATE TABLE users (id INTEGER);",
                "DROP TABLE users;",
            ),
        ]

        runner = MigrationRunner(database)

        applied = runner.apply_all(
            migrations
        )

        assert len(applied) == 1
        assert runner.applied(
            migrations
        ) == migrations

        result = runner.rollback_latest(
            migrations
        )

        assert result is not None
        assert result.migration.version == 1
        assert result.action == "rolled back"
        assert result.checksum == applied[0].checksum

        assert runner.applied(
            migrations
        ) == []

        table = database.fetch_one(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name = 'users'
            """
        )

        assert table is None
    finally:
        database.close()


def test_rollback_steps_rolls_back_latest_first(
    tmp_path: Path,
) -> None:
    database = create_database(tmp_path)

    try:
        migrations = [
            make_migration(
                tmp_path,
                1,
                "first",
                "SELECT 1;",
                "SELECT 1;",
            ),
            make_migration(
                tmp_path,
                2,
                "second",
                "SELECT 2;",
                "SELECT 2;",
            ),
            make_migration(
                tmp_path,
                3,
                "third",
                "SELECT 3;",
                "SELECT 3;",
            ),
        ]

        runner = MigrationRunner(database)

        runner.apply_all(migrations)

        results = runner.rollback_steps(
            migrations,
            2,
        )

        assert [
            result.migration.version
            for result in results
        ] == [3, 2]

        assert [
            migration.version
            for migration in runner.applied(
                migrations
            )
        ] == [1]
    finally:
        database.close()


def test_rollback_without_applied_migrations_returns_none(
    tmp_path: Path,
) -> None:
    database = create_database(tmp_path)

    try:
        migrations = [
            make_migration(
                tmp_path,
                1,
                "first",
                "SELECT 1;",
                "SELECT 1;",
            ),
        ]

        runner = MigrationRunner(database)

        result = runner.rollback_latest(
            migrations
        )

        assert result is None
    finally:
        database.close()


def test_rollback_steps_returns_empty_for_no_applied_migrations(
    tmp_path: Path,
) -> None:
    database = create_database(tmp_path)

    try:
        runner = MigrationRunner(database)

        results = runner.rollback_steps(
            [],
            1,
        )

        assert results == []
    finally:
        database.close()


def test_rollback_steps_rejects_zero(
    tmp_path: Path,
) -> None:
    database = create_database(tmp_path)

    try:
        runner = MigrationRunner(database)

        with pytest.raises(
            MigrationRunnerError,
            match="greater than zero",
        ):
            runner.rollback_steps([], 0)
    finally:
        database.close()


def test_rollback_steps_rejects_more_than_applied(
    tmp_path: Path,
) -> None:
    database = create_database(tmp_path)

    try:
        migration = make_migration(
            tmp_path,
            1,
            "first",
            "SELECT 1;",
            "SELECT 1;",
        )

        runner = MigrationRunner(database)

        runner.apply(migration)

        with pytest.raises(
            MigrationRunnerError,
            match="only 1",
        ):
            runner.rollback_steps(
                [migration],
                2,
            )
    finally:
        database.close()

def test_pending_uses_applied_versions(
    tmp_path,
) -> None:
    from dbmigrate.database import SQLiteDatabase
    from dbmigrate.history import MigrationHistory
    from dbmigrate.migration import Migration
    from dbmigrate.runner import MigrationRunner

    database = SQLiteDatabase(
        tmp_path / "database.db"
    )
    database.connect()

    history = MigrationHistory(database)
    history.initialize()

    history.record(
        version=1,
        name="create_users",
        checksum="abc",
    )

    migrations = (
        Migration(
            version=1,
            name="create_users",
            up_sql="CREATE TABLE users (id INTEGER);",
            down_sql="DROP TABLE users;",
            path=tmp_path / "001_create_users.sql",
        ),
        Migration(
            version=2,
            name="create_posts",
            up_sql="CREATE TABLE posts (id INTEGER);",
            down_sql="DROP TABLE posts;",
            path=tmp_path / "002_create_posts.sql",
        ),
    )

    runner = MigrationRunner(database)

    pending = runner.pending(
        migrations
    )

    assert [
        migration.version
        for migration in pending
    ] == [2]

    database.close()