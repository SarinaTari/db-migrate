"""Tests for migration parsing and discovery."""

from __future__ import annotations

from pathlib import Path

import pytest

from dbmigrate.migration import (
    MigrationDiscoveryError,
    MigrationParseError,
    discover_migrations,
    parse_migration,
)


VALID_MIGRATION = """\
-- migration: 001
-- name: create_users

-- +up

CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);

-- +down

DROP TABLE users;
"""


def write_migration(
    directory: Path,
    filename: str,
    content: str,
) -> Path:
    path = directory / filename
    path.write_text(content, encoding="utf-8")
    return path


def test_parse_valid_migration(tmp_path):
    path = write_migration(
        tmp_path,
        "001_create_users.sql",
        VALID_MIGRATION,
    )

    migration = parse_migration(path)

    assert migration.version == 1
    assert migration.name == "create_users"
    assert migration.path == path.resolve()
    assert migration.filename == "001_create_users.sql"
    assert migration.identifier == "001_create_users"

    assert "CREATE TABLE users" in migration.up_sql
    assert "DROP TABLE users" in migration.down_sql


def test_parse_migration_strips_section_whitespace(tmp_path):
    content = """\
-- migration: 001
-- name: create_users

-- +up


CREATE TABLE users (
    id INTEGER PRIMARY KEY
);


-- +down


DROP TABLE users;


"""

    path = write_migration(
        tmp_path,
        "001_create_users.sql",
        content,
    )

    migration = parse_migration(path)

    assert migration.up_sql.startswith("CREATE TABLE")
    assert migration.up_sql.endswith(");")
    assert migration.down_sql == "DROP TABLE users;"


def test_parse_rejects_invalid_filename(tmp_path):
    path = write_migration(
        tmp_path,
        "create_users.sql",
        VALID_MIGRATION,
    )

    with pytest.raises(
        MigrationParseError,
        match="Invalid migration filename",
    ):
        parse_migration(path)


def test_parse_rejects_zero_version(tmp_path):
    path = write_migration(
        tmp_path,
        "000_create_users.sql",
        VALID_MIGRATION.replace(
            "-- migration: 001",
            "-- migration: 000",
        ),
    )

    with pytest.raises(
        MigrationParseError,
        match="greater than zero",
    ):
        parse_migration(path)


def test_parse_rejects_missing_version_metadata(tmp_path):
    content = """\
-- name: create_users

-- +up

CREATE TABLE users (
    id INTEGER PRIMARY KEY
);

-- +down

DROP TABLE users;
"""

    path = write_migration(
        tmp_path,
        "001_create_users.sql",
        content,
    )

    with pytest.raises(
        MigrationParseError,
        match="migration: <version>",
    ):
        parse_migration(path)


def test_parse_rejects_missing_name_metadata(tmp_path):
    content = """\
-- migration: 001

-- +up

CREATE TABLE users (
    id INTEGER PRIMARY KEY
);

-- +down

DROP TABLE users;
"""

    path = write_migration(
        tmp_path,
        "001_create_users.sql",
        content,
    )

    with pytest.raises(
        MigrationParseError,
        match="name: <name>",
    ):
        parse_migration(path)


def test_parse_rejects_version_mismatch(tmp_path):
    content = VALID_MIGRATION.replace(
        "-- migration: 001",
        "-- migration: 002",
    )

    path = write_migration(
        tmp_path,
        "001_create_users.sql",
        content,
    )

    with pytest.raises(
        MigrationParseError,
        match="version mismatch",
    ):
        parse_migration(path)


def test_parse_rejects_name_mismatch(tmp_path):
    content = VALID_MIGRATION.replace(
        "-- name: create_users",
        "-- name: add_users",
    )

    path = write_migration(
        tmp_path,
        "001_create_users.sql",
        content,
    )

    with pytest.raises(
        MigrationParseError,
        match="name mismatch",
    ):
        parse_migration(path)


def test_parse_rejects_missing_up_marker(tmp_path):
    content = VALID_MIGRATION.replace(
        "-- +up",
        "-- up",
    )

    path = write_migration(
        tmp_path,
        "001_create_users.sql",
        content,
    )

    with pytest.raises(
        MigrationParseError,
        match=r"-- \+up",
    ):
        parse_migration(path)


def test_parse_rejects_missing_down_marker(tmp_path):
    content = VALID_MIGRATION.replace(
        "-- +down",
        "-- down",
    )

    path = write_migration(
        tmp_path,
        "001_create_users.sql",
        content,
    )

    with pytest.raises(
        MigrationParseError,
        match=r"-- \+down",
    ):
        parse_migration(path)


def test_parse_rejects_duplicate_up_marker(tmp_path):
    content = VALID_MIGRATION.replace(
        "-- +down",
        "-- +up\n\nDROP TABLE users;\n\n-- +down",
    )

    path = write_migration(
        tmp_path,
        "001_create_users.sql",
        content,
    )

    with pytest.raises(
        MigrationParseError,
        match="exactly one '-- \\+up'",
    ):
        parse_migration(path)


def test_parse_rejects_up_after_down(tmp_path):
    content = """\
-- migration: 001
-- name: create_users

-- +down

DROP TABLE users;

-- +up

CREATE TABLE users (
    id INTEGER PRIMARY KEY
);
"""

    path = write_migration(
        tmp_path,
        "001_create_users.sql",
        content,
    )

    with pytest.raises(
        MigrationParseError,
        match="before '-- \\+down'",
    ):
        parse_migration(path)


def test_parse_rejects_empty_up_section(tmp_path):
    content = """\
-- migration: 001
-- name: create_users

-- +up

-- +down

DROP TABLE users;
"""

    path = write_migration(
        tmp_path,
        "001_create_users.sql",
        content,
    )

    with pytest.raises(
        MigrationParseError,
        match="empty up section",
    ):
        parse_migration(path)


def test_parse_rejects_empty_down_section(tmp_path):
    content = """\
-- migration: 001
-- name: create_users

-- +up

CREATE TABLE users (
    id INTEGER PRIMARY KEY
);

-- +down
"""

    path = write_migration(
        tmp_path,
        "001_create_users.sql",
        content,
    )

    with pytest.raises(
        MigrationParseError,
        match="empty down section",
    ):
        parse_migration(path)


def test_parse_rejects_missing_file(tmp_path):
    path = tmp_path / "001_create_users.sql"

    with pytest.raises(
        MigrationParseError,
        match="does not exist",
    ):
        parse_migration(path)


def test_parse_rejects_non_sql_file(tmp_path):
    path = write_migration(
        tmp_path,
        "001_create_users.txt",
        VALID_MIGRATION,
    )

    with pytest.raises(
        MigrationParseError,
        match="\\.sql extension",
    ):
        parse_migration(path)


def test_discover_migrations_returns_sorted_versions(tmp_path):
    write_migration(
        tmp_path,
        "003_create_posts.sql",
        VALID_MIGRATION
        .replace("001", "003")
        .replace("create_users", "create_posts"),
    )

    write_migration(
        tmp_path,
        "001_create_users.sql",
        VALID_MIGRATION,
    )

    write_migration(
        tmp_path,
        "002_add_email.sql",
        VALID_MIGRATION
        .replace("001", "002")
        .replace("create_users", "add_email"),
    )

    migrations = discover_migrations(tmp_path)

    assert [migration.version for migration in migrations] == [1, 2, 3]

    assert [migration.name for migration in migrations] == [
        "create_users",
        "add_email",
        "create_posts",
    ]


def test_discover_migrations_rejects_duplicate_versions(tmp_path):
    write_migration(
        tmp_path,
        "001_create_users.sql",
        VALID_MIGRATION,
    )

    write_migration(
        tmp_path,
        "001_add_email.sql",
        VALID_MIGRATION
        .replace("create_users", "add_email"),
    )

    with pytest.raises(
        MigrationDiscoveryError,
        match="Duplicate migration version",
    ):
        discover_migrations(tmp_path)


def test_discover_migrations_rejects_missing_directory(tmp_path):
    missing = tmp_path / "migrations"

    with pytest.raises(
        MigrationDiscoveryError,
        match="does not exist",
    ):
        discover_migrations(missing)


def test_discover_migrations_rejects_file_as_directory(tmp_path):
    path = tmp_path / "not_a_directory"
    path.write_text("", encoding="utf-8")

    with pytest.raises(
        MigrationDiscoveryError,
        match="not a directory",
    ):
        discover_migrations(path)


def test_discover_migrations_ignores_non_sql_files(tmp_path):
    write_migration(
        tmp_path,
        "001_create_users.sql",
        VALID_MIGRATION,
    )

    (tmp_path / "README.md").write_text(
        "not a migration",
        encoding="utf-8",
    )

    migrations = discover_migrations(tmp_path)

    assert len(migrations) == 1
    assert migrations[0].version == 1