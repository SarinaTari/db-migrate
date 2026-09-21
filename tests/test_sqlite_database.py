from pathlib import Path

import pytest

from dbmigrate.database import (
    DatabaseError,
    SQLiteDatabase,
)


def test_sqlite_creates_database(
    tmp_path: Path,
):
    path = (
        tmp_path
        / "nested"
        / "database.db"
    )

    database = SQLiteDatabase(path)

    database.connect()

    try:
        assert path.exists()
        assert database.is_connected
    finally:
        database.close()


def test_sqlite_reuses_connection(
    tmp_path: Path,
):
    database = SQLiteDatabase(
        tmp_path / "database.db"
    )

    database.connect()
    first = database.connection

    database.connect()

    try:
        assert database.connection is first
    finally:
        database.close()


def test_sqlite_execute_and_fetch(
    tmp_path: Path,
):
    database = SQLiteDatabase(
        tmp_path / "database.db"
    )

    database.connect()

    try:
        database.execute(
            """
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL
            )
            """
        )

        database.execute(
            "INSERT INTO users (name) "
            "VALUES (?)",
            ("Sarina",),
        )

        row = database.fetch_one(
            "SELECT id, name FROM users"
        )

        assert row == (1, "Sarina")

        rows = database.fetch_all(
            "SELECT name FROM users"
        )

        assert rows == [("Sarina",)]
    finally:
        database.close()


def test_sqlite_foreign_keys_are_enabled(
    tmp_path: Path,
):
    database = SQLiteDatabase(
        tmp_path / "database.db"
    )

    database.connect()

    try:
        row = database.fetch_one(
            "PRAGMA foreign_keys"
        )

        assert row == (1,)
    finally:
        database.close()


def test_operations_require_connection(
    tmp_path: Path,
):
    database = SQLiteDatabase(
        tmp_path / "database.db"
    )

    with pytest.raises(DatabaseError):
        database.execute(
            "SELECT 1"
        )


def test_close_is_idempotent(
    tmp_path: Path,
):
    database = SQLiteDatabase(
        tmp_path / "database.db"
    )

    database.connect()
    database.close()
    database.close()

    assert not database.is_connected