"""Tests for database abstractions and SQLite support."""

from pathlib import Path

import pytest

from dbmigrate.database import (
    DatabaseError,
    SQLiteDatabase,
)


def test_sqlite_database_connects(tmp_path: Path):
    database = SQLiteDatabase(tmp_path / "test.db")

    database.connect()

    assert database.is_connected
    assert database.path == (tmp_path / "test.db").resolve()

    database.close()

    assert not database.is_connected


def test_sqlite_database_creates_database_file(tmp_path: Path):
    database_path = tmp_path / "nested" / "test.db"

    database = SQLiteDatabase(database_path)
    database.connect()

    assert database_path.exists()

    database.close()


def test_sqlite_database_executes_sql(tmp_path: Path):
    database = SQLiteDatabase(tmp_path / "test.db")
    database.connect()

    database.execute(
        """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL
        )
        """
    )

    database.execute(
        "INSERT INTO users (name) VALUES (?)",
        ("Sarina",),
    )

    row = database.fetch_one(
        "SELECT name FROM users WHERE id = ?",
        (1,),
    )

    assert row == ("Sarina",)

    database.close()


def test_sqlite_database_fetches_all_rows(tmp_path: Path):
    database = SQLiteDatabase(tmp_path / "test.db")
    database.connect()

    database.execute(
        """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL
        )
        """
    )

    database.execute(
        "INSERT INTO users (name) VALUES (?)",
        ("Sarina",),
    )

    database.execute(
        "INSERT INTO users (name) VALUES (?)",
        ("Alex",),
    )

    rows = database.fetch_all(
        "SELECT name FROM users ORDER BY id"
    )

    assert rows == [
        ("Sarina",),
        ("Alex",),
    ]

    database.close()


def test_sqlite_transaction_commits(tmp_path: Path):
    database = SQLiteDatabase(tmp_path / "test.db")
    database.connect()

    database.execute(
        """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL
        )
        """
    )

    with database.transaction():
        database.execute(
            "INSERT INTO users (name) VALUES (?)",
            ("Sarina",),
        )

    row = database.fetch_one(
        "SELECT name FROM users"
    )

    assert row == ("Sarina",)

    database.close()


def test_sqlite_transaction_rolls_back_on_error(
    tmp_path: Path,
):
    database = SQLiteDatabase(tmp_path / "test.db")
    database.connect()

    database.execute(
        """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL
        )
        """
    )

    with pytest.raises(RuntimeError):
        with database.transaction():
            database.execute(
                "INSERT INTO users (name) VALUES (?)",
                ("Sarina",),
            )

            raise RuntimeError("simulated failure")

    rows = database.fetch_all(
        "SELECT name FROM users"
    )

    assert rows == []

    database.close()


def test_sqlite_database_enables_foreign_keys(
    tmp_path: Path,
):
    database = SQLiteDatabase(tmp_path / "test.db")
    database.connect()

    row = database.fetch_one(
        "PRAGMA foreign_keys"
    )

    assert row == (1,)

    database.close()


def test_database_requires_connection(tmp_path: Path):
    database = SQLiteDatabase(tmp_path / "test.db")

    with pytest.raises(DatabaseError, match="not connected"):
        database.execute("SELECT 1")


def test_invalid_sql_raises_database_error(
    tmp_path: Path,
):
    database = SQLiteDatabase(tmp_path / "test.db")
    database.connect()

    with pytest.raises(
        DatabaseError,
        match="SQLite execution failed",
    ):
        database.execute(
            "THIS IS NOT VALID SQL"
        )

    database.close()


def test_close_is_safe_when_not_connected(
    tmp_path: Path,
):
    database = SQLiteDatabase(tmp_path / "test.db")

    database.close()

    assert not database.is_connected