"""Tests for migration creation."""

from pathlib import Path

import pytest

from dbmigrate.migration_creator import (
    MigrationCreationError,
    create_migration,
    validate_migration_name,
)


def write_migration(
    path: Path,
    version: int,
    name: str,
) -> None:
    path.write_text(
        f"""-- migration: {version:03d}
-- name: {name}

-- +up

SELECT 1;

-- +down

SELECT 1;
""",
        encoding="utf-8",
    )


def test_validate_migration_name_accepts_valid_name():
    assert (
        validate_migration_name(
            "create_users"
        )
        == "create_users"
    )


@pytest.mark.parametrize(
    "name",
    [
        "create-users",
        "create_users",
        "users2",
        "2_create_users",
        "a",
        "a1",
        "a-b_c",
    ],
)
def test_validate_migration_name_accepts_supported_names(
    name: str,
):
    assert validate_migration_name(name) == name


@pytest.mark.parametrize(
    "name",
    [
        "",
        " ",
        "CreateUsers",
        "create users",
        "create.users",
        "create/users",
        "_create_users",
        "-create_users",
        "CREATE_USERS",
    ],
)
def test_validate_migration_name_rejects_invalid_names(
    name: str,
):
    with pytest.raises(
        MigrationCreationError,
        match="Invalid migration name|must not be empty",
    ):
        validate_migration_name(name)


def test_create_first_migration(
    tmp_path: Path,
):
    migrations_path = (
        tmp_path / "migrations"
    )

    result = create_migration(
        migrations_path,
        "create_users",
    )

    assert result.version == 1
    assert result.name == "create_users"
    assert result.identifier == (
        "001_create_users"
    )

    assert result.path == (
        migrations_path
        / "001_create_users.sql"
    )

    assert result.path.is_file()

    content = result.path.read_text(
        encoding="utf-8"
    )

    assert (
        "-- migration: 001"
        in content
    )
    assert (
        "-- name: create_users"
        in content
    )
    assert "-- +up" in content
    assert "-- +down" in content
    assert (
        "-- Write your SQL here."
        in content
    )
    assert (
        "-- Write your rollback SQL here."
        in content
    )


def test_create_migration_creates_directory(
    tmp_path: Path,
):
    migrations_path = (
        tmp_path
        / "nested"
        / "migrations"
    )

    result = create_migration(
        migrations_path,
        "create_users",
    )

    assert migrations_path.is_dir()
    assert result.path.is_file()


def test_create_migration_uses_next_version(
    tmp_path: Path,
):
    migrations_path = tmp_path / "migrations"

    migrations_path.mkdir()

    write_migration(
        migrations_path / "001_create_users.sql",
        1,
        "create_users",
    )

    write_migration(
        migrations_path / "002_add_email.sql",
        2,
        "add_email",
    )

    result = create_migration(
        migrations_path,
        "create_accounts",
    )

    assert result.version == 3
    assert result.path.name == (
        "003_create_accounts.sql"
    )


def test_create_migration_uses_max_version(
    tmp_path: Path,
):
    migrations_path = tmp_path / "migrations"

    migrations_path.mkdir()

    write_migration(
        migrations_path / "001_first.sql",
        1,
        "first",
    )

    write_migration(
        migrations_path / "005_fifth.sql",
        5,
        "fifth",
    )

    result = create_migration(
        migrations_path,
        "sixth",
    )

    assert result.version == 6
    assert result.path.name == (
        "006_sixth.sql"
    )


def test_create_migration_rejects_invalid_existing_migration(
    tmp_path: Path,
):
    migrations_path = tmp_path / "migrations"
    migrations_path.mkdir()

    (
        migrations_path
        / "001_broken.sql"
    ).write_text(
        "not a valid migration",
        encoding="utf-8",
    )

    with pytest.raises(
        MigrationCreationError,
        match="Could not inspect existing migrations",
    ):
        create_migration(
            migrations_path,
            "create_users",
        )


def test_create_migration_does_not_overwrite_existing_file(
    tmp_path: Path,
):
    migrations_path = tmp_path / "migrations"
    migrations_path.mkdir()

    existing = (
        migrations_path
        / "001_create_users.sql"
    )

    write_migration(
        existing,
        1,
        "create_users",
    )

    original_content = existing.read_text(
        encoding="utf-8"
    )

    with pytest.raises(
        MigrationCreationError,
        match="already exists",
    ):
        create_migration(
            migrations_path,
            "create_users",
        )

    assert existing.read_text(
        encoding="utf-8"
    ) == original_content


def test_create_migration_with_existing_directory(
    tmp_path: Path,
):
    migrations_path = tmp_path / "migrations"
    migrations_path.mkdir()

    result = create_migration(
        migrations_path,
        "create_users",
    )

    assert result.path.exists()