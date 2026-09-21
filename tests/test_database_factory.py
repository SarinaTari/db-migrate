from pathlib import Path

import pytest

from dbmigrate.database import SQLiteDatabase
from dbmigrate.database_factory import (
    create_database,
    parse_database_url,
)
from dbmigrate.database_mysql import MySQLDatabase
from dbmigrate.database_postgres import (
    PostgreSQLDatabase,
)


def test_parse_sqlite_url():
    parsed = parse_database_url(
        "sqlite:///database.db"
    )

    assert parsed.scheme == "sqlite"
    assert parsed.database == "/database.db"
    assert parsed.host is None


def test_create_sqlite_database():
    database = create_database(
        "sqlite:///database.db"
    )

    assert isinstance(
        database,
        SQLiteDatabase,
    )


def test_parse_postgresql_url():
    parsed = parse_database_url(
        "postgresql://user:password@localhost:5432/mydb"
    )

    assert parsed.scheme == "postgresql"
    assert parsed.host == "localhost"
    assert parsed.port == 5432
    assert parsed.database == "mydb"
    assert parsed.username == "user"
    assert parsed.password == "password"


def test_create_postgresql_database():
    database = create_database(
        "postgresql://user:password@localhost:5432/mydb"
    )

    assert isinstance(
        database,
        PostgreSQLDatabase,
    )


def test_parse_mysql_url():
    parsed = parse_database_url(
        "mysql://user:password@localhost:3306/mydb"
    )

    assert parsed.scheme == "mysql"
    assert parsed.host == "localhost"
    assert parsed.port == 3306
    assert parsed.database == "mydb"


def test_create_mysql_database():
    database = create_database(
        "mysql://user:password@localhost:3306/mydb"
    )

    assert isinstance(
        database,
        MySQLDatabase,
    )


def test_unsupported_database_scheme():
    with pytest.raises(Exception):
        parse_database_url(
            "oracle://user:password@localhost/db"
        )


def test_missing_database_name():
    with pytest.raises(Exception):
        parse_database_url(
            "postgresql://user:password@localhost"
        )


def test_sqlite_relative_path_is_relative_to_current_directory(
    tmp_path,
    monkeypatch,
):
    monkeypatch.chdir(tmp_path)

    database = create_database(
        "sqlite:///database.db"
    )

    assert isinstance(
        database,
        SQLiteDatabase,
    )

    assert database.path == (
        tmp_path / "database.db"
    ).resolve()


def test_sqlite_absolute_path_is_preserved(
    tmp_path,
):
    database_path = (
        tmp_path / "database.db"
    )

    database = create_database(
        f"sqlite:////{database_path.as_posix().lstrip('/')}"
    )

    assert database.path == database_path.resolve()