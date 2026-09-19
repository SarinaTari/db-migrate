"""Tests for migration parsing and discovery."""

from pathlib import Path

import pytest

from dbmigrate.migration import (
    MigrationDiscoveryError,
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


def valid_migration(
    version: int = 1,
    name: str = "create_users",
) -> str:
    """Return a valid migration document."""
    return f"""-- migration: {version}
-- name: {name}

-- +up

CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);

-- +down

DROP TABLE users;
"""


def test_parse_valid_migration(
    tmp_path: Path,
):
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
    assert migration.identifier == "001_create_users"
    assert migration.filename == "001_create_users.sql"


def test_parse_migration_requires_metadata(
    tmp_path: Path,
):
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


def test_parse_migration_rejects_empty_up_section(
    tmp_path: Path,
):
    path = tmp_path / "001_create_users.sql"

    write_migration(
        path,
        """
-- migration: 001
-- name: create_users

-- +up

-- +down

DROP TABLE users;
""",
    )

    with pytest.raises(
        MigrationParseError,
        match="empty up section",
    ):
        parse_migration(path)


def test_parse_migration_rejects_empty_down_section(
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

-- +down
""",
    )

    with pytest.raises(
        MigrationParseError,
        match="empty down section",
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


@pytest.mark.parametrize(
    "filename",
    [
        "create_users.sql",
        "001.sql",
        "001_Create_users.sql",
        "001_create users.sql",
        "001_create_users.txt",
    ],
)
def test_invalid_migration_filename_is_rejected(
    tmp_path: Path,
    filename: str,
):
    path = tmp_path / filename

    write_migration(
        path,
        valid_migration(),
    )

    with pytest.raises(
        MigrationParseError,
        match="Invalid migration filename|\\.sql extension",
    ):
        parse_migration(path)


def test_migration_version_must_be_greater_than_zero(
    tmp_path: Path,
):
    path = tmp_path / "000_create_users.sql"

    write_migration(
        path,
        """
-- migration: 000
-- name: create_users

-- +up

CREATE TABLE users (id INTEGER);

-- +down

DROP TABLE users;
""",
    )

    with pytest.raises(
        MigrationParseError,
        match="greater than zero",
    ):
        parse_migration(path)


def test_migration_requires_exactly_one_up_marker(
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

-- +up

CREATE TABLE accounts (id INTEGER);

-- +down

DROP TABLE accounts;
""",
    )

    with pytest.raises(
        MigrationParseError,
        match="exactly one.*-- \\+up",
    ):
        parse_migration(path)


def test_migration_requires_exactly_one_down_marker(
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

-- +down

DROP TABLE users;

-- +down

DROP TABLE accounts;
""",
    )

    with pytest.raises(
        MigrationParseError,
        match="exactly one.*-- \\+down",
    ):
        parse_migration(path)


def test_down_marker_must_follow_up_marker(
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

-- +up

CREATE TABLE users (id INTEGER);
""",
    )

    with pytest.raises(
        MigrationParseError,
        match="before",
    ):
        parse_migration(path)


def test_nonexistent_migration_file_is_rejected(
    tmp_path: Path,
):
    path = tmp_path / "001_create_users.sql"

    with pytest.raises(
        MigrationParseError,
        match="does not exist",
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

    assert [
        migration.version
        for migration in migrations
    ] == [1, 2]


def test_discover_migrations_rejects_duplicate_versions(
    tmp_path: Path,
):
    write_migration(
        tmp_path / "001_create_users.sql",
        valid_migration(
            version=1,
            name="create_users",
        ),
    )

    write_migration(
        tmp_path / "001_create_accounts.sql",
        valid_migration(
            version=1,
            name="create_accounts",
        ),
    )

    with pytest.raises(
        MigrationDiscoveryError,
        match="Duplicate migration version",
    ):
        discover_migrations(tmp_path)


def test_discover_migrations_requires_directory(
    tmp_path: Path,
):
    missing = tmp_path / "migrations"

    with pytest.raises(
        MigrationDiscoveryError,
        match="does not exist",
    ):
        discover_migrations(missing)


def test_discover_migrations_rejects_file_path(
    tmp_path: Path,
):
    path = tmp_path / "migrations.sql"

    path.write_text(
        "not a directory",
        encoding="utf-8",
    )

    with pytest.raises(
        MigrationDiscoveryError,
        match="not a directory",
    ):
        discover_migrations(path)