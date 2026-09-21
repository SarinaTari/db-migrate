"""Tests for migration reproducibility."""

from pathlib import Path

from dbmigrate.database import SQLiteDatabase
from dbmigrate.migration import Migration
from dbmigrate.reproducibility import (
    check_reproducibility,
    reproduce_schema,
)
from dbmigrate.schema import inspect_schema


def _migration(
    version: int,
    name: str,
    up_sql: str,
    down_sql: str = "",
) -> Migration:
    return Migration(
        version=version,
        name=name,
        up_sql=up_sql,
        down_sql=down_sql,
        path=Path(
            f"{version:03d}_{name}.sql"
        ),
    )


def _database(tmp_path):
    database = SQLiteDatabase(
        tmp_path / "database.db"
    )
    database.connect()
    return database


def test_reproduce_schema_from_migrations(tmp_path):
    migrations = [
        _migration(
            1,
            "create_users",
            """
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL
            );
            """,
        ),
    ]

    schema = reproduce_schema(
        migrations
    )

    assert schema.table_count == 1
    assert schema.tables[0].name == "users"


def test_reproducibility_succeeds_for_matching_schema(
    tmp_path,
):
    migrations = [
        _migration(
            1,
            "create_users",
            """
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL
            );
            """,
        ),
    ]

    database = _database(
        tmp_path
    )

    try:
        database.execute(
            """
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL
            )
            """
        )

        target_schema = inspect_schema(
            database
        )

        report = check_reproducibility(
            migrations,
            target_schema,
        )

        assert report.is_reproducible
        assert report.diff.is_empty
        assert (
            report.expected_fingerprint
            == report.actual_fingerprint
        )

    finally:
        database.close()


def test_reproducibility_detects_schema_difference(
    tmp_path,
):
    migrations = [
        _migration(
            1,
            "create_users",
            """
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL
            );
            """,
        ),
    ]

    database = _database(
        tmp_path
    )

    try:
        database.execute(
            """
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT
            )
            """
        )

        target_schema = inspect_schema(
            database
        )

        report = check_reproducibility(
            migrations,
            target_schema,
        )

        assert not report.is_reproducible
        assert not report.diff.is_empty
        assert any(
            change.object_name
            == "users.email"
            for change in report.diff.changes
        )

    finally:
        database.close()


def test_reproduced_schema_has_deterministic_fingerprint():
    migrations = [
        _migration(
            1,
            "create_users",
            """
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL
            );
            """,
        ),
    ]

    first = reproduce_schema(
        migrations
    )

    second = reproduce_schema(
        migrations
    )

    assert (
        first.fingerprint()
        == second.fingerprint()
    )