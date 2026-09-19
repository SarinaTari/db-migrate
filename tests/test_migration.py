"""Tests for migration parsing and discovery."""

from pathlib import Path

import pytest

from dbmigrate.migration import (
    MigrationParseError,
    discover_migrations,
    parse_migration,
)


def write_migration(
    path: Path,
    content: str,
) -> None:
    path.write_text(
        content.strip() + "\n",
        encoding="utf-8",
    )


def test_parse_valid_migration(tmp_path: Path):
    path = tmp_path / "001_create_users.sql"

    write_migration(
        path,
        """
-- migration: 001
-- name: create_users

-- +up

CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);

-- +down

DROP TABLE users;
""",
    )

    migration = parse_migration(path)

    assert migration.version == 1
    assert migration.name == "create_users"
    assert "CREATE TABLE users" in migration.up_sql
    assert "DROP TABLE users" in migration.down_sql


def test_parse_migration_requires_metadata(tmp_path: Path):
    path = tmp_path / "001_create_users.sql"

    write_migration(
        path,
        """
-- +up

CREATE TABLE users (id INTEGER);

-- +down

DROP TABLE users;
""",
    )

    with pytest.raises(
        MigrationParseError,
        match="migration metadata",
    ):
        parse_migration(path)


def test_parse_migration_requires_up_section(
    tmp_path: Path,
):
    path = tmp_path / "001_create_users.sql"

    write_migration(
        path,
        """
-- migration: 001
-- name: create_users

-- +down

DROP TABLE users;
""",
    )

    with pytest.raises(
        MigrationParseError,
        match="up",
    ):
        parse_migration(path)


def test_parse_migration_requires_down_section(
    tmp_path: Path,
):
    path = tmp_path / "001_create_users.sql"

    write_migration(
        path,
        """
-- migration: 001
-- name: create_users

-- +up

CREATE TABLE users (id INTEGER);
""",
    )

    with pytest.raises(
        MigrationParseError,
        match="down",
    ):
        parse_migration(path)


def test_filename_version_must_match_metadata(
    tmp_path: Path,
):
    path = tmp_path / "002_create_users.sql"

    write_migration(
        path,
        """
-- migration: 001
-- name: create_users

-- +up

CREATE TABLE users (id INTEGER);

-- +down

DROP TABLE users;
""",
    )

    with pytest.raises(
        MigrationParseError,
        match="version",
    ):
        parse_migration(path)


def test_filename_name_must_match_metadata(
    tmp_path: Path,
):
    path = tmp_path / "001_create_users.sql"

    write_migration(
        path,
        """
-- migration: 001
-- name: create_accounts

-- +up

CREATE TABLE accounts (id INTEGER);

-- +down

DROP TABLE accounts;
""",
    )

    with pytest.raises(
        MigrationParseError,
        match="name",
    ):
        parse_migration(path)


def test_discover_migrations_in_version_order(
    tmp_path: Path,
):
    write_migration(
        tmp_path / "002_add_email.sql",
        """
-- migration: 002
-- name: add_email

-- +up

ALTER TABLE users ADD COLUMN email TEXT;

-- +down

ALTER TABLE users DROP COLUMN email;
""",
    )

    write_migration(
        tmp_path / "001_create_users.sql",
        """
-- migration: 001
-- name: create_users

-- +up

CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);

-- +down

DROP TABLE users;
""",
    )

    migrations = discover_migrations(tmp_path)

    assert [migration.version for migration in migrations] == [
        1,
        2,
    ]