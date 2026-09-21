"""Tests for migration planning."""

from pathlib import Path

from dbmigrate.database import SQLiteDatabase
from dbmigrate.history import MigrationHistory
from dbmigrate.migration import Migration
from dbmigrate.planner import (
    MigrationPlanner,
    MigrationPlanningError,
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
) -> Migration:
    """Create a migration object for testing."""
    path = (
        tmp_path
        / f"{version:03d}_{name}.sql"
    )

    up_sql = (
        f"CREATE TABLE {name} "
        "(id INTEGER);"
    )

    down_sql = (
        f"DROP TABLE IF EXISTS {name};"
    )

    path.write_text(
        f"""-- migration: {version}
-- name: {name}

-- +up

{up_sql}

-- +down

{down_sql}
""",
        encoding="utf-8",
    )

    return Migration(
        version=version,
        name=name,
        up_sql=up_sql,
        down_sql=down_sql,
        path=path,
    )


def test_plan_reports_all_pending(
    tmp_path: Path,
) -> None:
    database = create_database(tmp_path)

    try:
        migrations = [
            make_migration(
                tmp_path,
                1,
                "users",
            ),
            make_migration(
                tmp_path,
                2,
                "posts",
            ),
        ]

        history = MigrationHistory(
            database
        )

        planner = MigrationPlanner(
            history
        )

        plan = planner.plan(
            migrations
        )

        assert plan.pending == tuple(
            migrations
        )
        assert plan.count == 2
        assert plan.is_empty is False
        assert plan.versions == (1, 2)

    finally:
        database.close()


def test_plan_excludes_applied_migrations(
    tmp_path: Path,
) -> None:
    database = create_database(tmp_path)

    try:
        migrations = [
            make_migration(
                tmp_path,
                1,
                "users",
            ),
            make_migration(
                tmp_path,
                2,
                "posts",
            ),
            make_migration(
                tmp_path,
                3,
                "comments",
            ),
        ]

        history = MigrationHistory(
            database
        )

        history.record(
            version=1,
            name="users",
            checksum="checksum-1",
        )

        planner = MigrationPlanner(
            history
        )

        plan = planner.plan(
            migrations
        )

        assert plan.versions == (2, 3)
        assert plan.count == 2

    finally:
        database.close()


def test_plan_returns_empty_when_everything_is_applied(
    tmp_path: Path,
) -> None:
    database = create_database(tmp_path)

    try:
        migrations = [
            make_migration(
                tmp_path,
                1,
                "users",
            ),
            make_migration(
                tmp_path,
                2,
                "posts",
            ),
        ]

        history = MigrationHistory(
            database
        )

        history.record(
            version=1,
            name="users",
            checksum="checksum-1",
        )

        history.record(
            version=2,
            name="posts",
            checksum="checksum-2",
        )

        planner = MigrationPlanner(
            history
        )

        plan = planner.plan(
            migrations
        )

        assert plan.pending == ()
        assert plan.count == 0
        assert plan.is_empty is True
        assert plan.versions == ()

    finally:
        database.close()


def test_plan_preserves_version_order(
    tmp_path: Path,
) -> None:
    database = create_database(tmp_path)

    try:
        migrations = [
            make_migration(
                tmp_path,
                3,
                "comments",
            ),
            make_migration(
                tmp_path,
                1,
                "users",
            ),
            make_migration(
                tmp_path,
                2,
                "posts",
            ),
        ]

        history = MigrationHistory(
            database
        )

        planner = MigrationPlanner(
            history
        )

        plan = planner.plan(
            migrations
        )

        assert plan.versions == (
            1,
            2,
            3,
        )

    finally:
        database.close()


def test_plan_does_not_execute_migration_sql(
    tmp_path: Path,
) -> None:
    database = create_database(tmp_path)

    try:
        migration = make_migration(
            tmp_path,
            1,
            "users",
        )

        history = MigrationHistory(
            database
        )

        planner = MigrationPlanner(
            history
        )

        plan = planner.plan(
            [migration]
        )

        assert plan.count == 1

        row = database.fetch_one(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name = 'users'
            """
        )

        assert row is None

    finally:
        database.close()


def test_plan_does_not_record_migrations(
    tmp_path: Path,
) -> None:
    database = create_database(tmp_path)

    try:
        migrations = [
            make_migration(
                tmp_path,
                1,
                "users",
            ),
        ]

        history = MigrationHistory(
            database
        )

        planner = MigrationPlanner(
            history
        )

        planner.plan(
            migrations
        )

        assert history.list_applied() == []

    finally:
        database.close()


def test_plan_initializes_history_table(
    tmp_path: Path,
) -> None:
    database = create_database(tmp_path)

    try:
        migration = make_migration(
            tmp_path,
            1,
            "users",
        )

        history = MigrationHistory(
            database
        )

        planner = MigrationPlanner(
            history
        )

        planner.plan(
            [migration]
        )

        row = database.fetch_one(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name = 'schema_migrations'
            """
        )

        assert row is not None
        assert row[0] == "schema_migrations"

    finally:
        database.close()


def test_plan_history_failure_is_wrapped(
    tmp_path: Path,
) -> None:
    class BrokenHistory:
        def initialize(self) -> None:
            raise RuntimeError(
                "history unavailable"
            )

        def list_applied(self):
            return []

    planner = MigrationPlanner(
        BrokenHistory()
    )

    migration = make_migration(
        tmp_path,
        1,
        "users",
    )

    try:
        planner.plan(
            [migration]
        )
    except MigrationPlanningError as exc:
        assert "Could not inspect migration history" in str(
            exc
        )
        assert "history unavailable" in str(
            exc
        )
    else:
        raise AssertionError(
            "Expected MigrationPlanningError."
        )