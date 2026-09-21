from __future__ import annotations

import sqlite3

import pytest

from dbmigrate.database import SQLiteDatabase
from dbmigrate.schema import (
    DatabaseSchema,
    SchemaInspectionError,
    inspect_and_fingerprint,
    inspect_schema,
    schema_fingerprint,
)


def _database(tmp_path):
    path = tmp_path / "database.db"

    database = SQLiteDatabase(
        path
    )

    database.connect()

    return database


def test_empty_database_has_empty_schema(
    tmp_path,
):
    database = _database(
        tmp_path
    )

    try:
        schema = inspect_schema(
            database
        )

        assert schema.tables == ()
        assert schema.views == ()
        assert schema.is_empty
        assert schema.table_count == 0
        assert schema.view_count == 0
    finally:
        database.close()


def test_inspects_table_and_columns(
    tmp_path,
):
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

        schema = inspect_schema(
            database
        )

        assert len(schema.tables) == 1

        table = schema.tables[0]

        assert table.name == "users"

        assert [
            column.name
            for column in table.columns
        ] == [
            "id",
            "email",
            "name",
        ]

        id_column = next(
            column
            for column in table.columns
            if column.name == "id"
        )

        assert id_column.primary_key_position == 1

        name_column = next(
            column
            for column in table.columns
            if column.name == "name"
        )

        assert name_column.not_null
    finally:
        database.close()


def test_inspects_indexes(
    tmp_path,
):
    database = _database(
        tmp_path
    )

    try:
        database.execute(
            """
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                email TEXT NOT NULL
            )
            """
        )

        database.execute(
            """
            CREATE UNIQUE INDEX idx_users_email
            ON users(email)
            """
        )

        schema = inspect_schema(
            database
        )

        table = schema.tables[0]

        assert len(table.indexes) == 1

        index = table.indexes[0]

        assert index.name == "idx_users_email"
        assert index.unique
        assert index.columns == (
            "email",
        )
    finally:
        database.close()


def test_inspects_foreign_keys(
    tmp_path,
):
    database = _database(
        tmp_path
    )

    try:
        database.execute(
            """
            CREATE TABLE users (
                id INTEGER PRIMARY KEY
            )
            """
        )

        database.execute(
            """
            CREATE TABLE posts (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                FOREIGN KEY(user_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE
            )
            """
        )

        schema = inspect_schema(
            database
        )

        posts = next(
            table
            for table in schema.tables
            if table.name == "posts"
        )

        assert len(posts.foreign_keys) == 1

        foreign_key = posts.foreign_keys[0]

        assert foreign_key.column == "user_id"
        assert foreign_key.referenced_table == "users"
        assert foreign_key.referenced_column == "id"
        assert foreign_key.on_delete == "CASCADE"
    finally:
        database.close()


def test_inspects_views(
    tmp_path,
):
    database = _database(
        tmp_path
    )

    try:
        database.execute(
            """
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                name TEXT
            )
            """
        )

        database.execute(
            """
            CREATE VIEW active_users AS
            SELECT id, name
            FROM users
            """
        )

        schema = inspect_schema(
            database
        )

        assert len(schema.views) == 1

        view = schema.views[0]

        assert view.name == "active_users"
        assert "SELECT id, name FROM users" in view.sql
    finally:
        database.close()


def test_sqlite_internal_objects_are_excluded(
    tmp_path,
):
    database = _database(
        tmp_path
    )

    try:
        database.execute(
            """
            CREATE TABLE users (
                id INTEGER PRIMARY KEY
            )
            """
        )

        schema = inspect_schema(
            database
        )

        assert all(
            not table.name.startswith("sqlite_")
            for table in schema.tables
        )
    finally:
        database.close()


def test_fingerprint_is_deterministic(
    tmp_path,
):
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

        first = inspect_schema(
            database
        ).fingerprint()

        second = inspect_schema(
            database
        ).fingerprint()

        assert first == second
        assert len(first) == 64
    finally:
        database.close()


def test_identical_schemas_have_identical_fingerprints(
    tmp_path,
):
    first_path = (
        tmp_path / "first.db"
    )

    second_path = (
        tmp_path / "second.db"
    )

    first = SQLiteDatabase(
        first_path
    )

    second = SQLiteDatabase(
        second_path
    )

    first.connect()
    second.connect()

    try:
        sql = """
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL
            )
        """

        first.execute(sql)
        second.execute(sql)

        first_fingerprint = inspect_schema(
            first
        ).fingerprint()

        second_fingerprint = inspect_schema(
            second
        ).fingerprint()

        assert (
            first_fingerprint
            == second_fingerprint
        )
    finally:
        first.close()
        second.close()


def test_different_schemas_have_different_fingerprints(
    tmp_path,
):
    first = SQLiteDatabase(
        tmp_path / "first.db"
    )

    second = SQLiteDatabase(
        tmp_path / "second.db"
    )

    first.connect()
    second.connect()

    try:
        first.execute(
            """
            CREATE TABLE users (
                id INTEGER PRIMARY KEY
            )
            """
        )

        second.execute(
            """
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                name TEXT
            )
            """
        )

        first_fingerprint = inspect_schema(
            first
        ).fingerprint()

        second_fingerprint = inspect_schema(
            second
        ).fingerprint()

        assert (
            first_fingerprint
            != second_fingerprint
        )
    finally:
        first.close()
        second.close()


def test_table_order_does_not_change_fingerprint(
    tmp_path,
):
    first = SQLiteDatabase(
        tmp_path / "first.db"
    )

    second = SQLiteDatabase(
        tmp_path / "second.db"
    )

    first.connect()
    second.connect()

    try:
        first.execute(
            """
            CREATE TABLE users (
                id INTEGER PRIMARY KEY
            )
            """
        )

        first.execute(
            """
            CREATE TABLE posts (
                id INTEGER PRIMARY KEY
            )
            """
        )

        second.execute(
            """
            CREATE TABLE posts (
                id INTEGER PRIMARY KEY
            )
            """
        )

        second.execute(
            """
            CREATE TABLE users (
                id INTEGER PRIMARY KEY
            )
            """
        )

        assert (
            inspect_schema(first).fingerprint()
            == inspect_schema(second).fingerprint()
        )
    finally:
        first.close()
        second.close()


def test_schema_fingerprint_helper(
    tmp_path,
):
    database = _database(
        tmp_path
    )

    try:
        database.execute(
            """
            CREATE TABLE users (
                id INTEGER PRIMARY KEY
            )
            """
        )

        schema = inspect_schema(
            database
        )

        assert (
            schema_fingerprint(schema)
            == schema.fingerprint()
        )
    finally:
        database.close()


def test_inspect_and_fingerprint(
    tmp_path,
):
    database = _database(
        tmp_path
    )

    try:
        database.execute(
            """
            CREATE TABLE users (
                id INTEGER PRIMARY KEY
            )
            """
        )

        schema, fingerprint = (
            inspect_and_fingerprint(
                database
            )
        )

        assert isinstance(
            schema,
            DatabaseSchema,
        )

        assert fingerprint == (
            schema.fingerprint()
        )
    finally:
        database.close()