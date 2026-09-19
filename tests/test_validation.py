"""Tests for migration validation."""

from pathlib import Path

from dbmigrate.validation import validate_migrations


def write_migration(
    path: Path,
    version: int,
    name: str,
) -> None:
    path.write_text(
        f"""
-- migration: {version:03d}
-- name: {name}

-- +up

SELECT 1;

-- +down

SELECT 1;
""".strip()
        + "\n",
        encoding="utf-8",
    )


def test_empty_migration_directory_is_valid(
    tmp_path: Path,
):
    report = validate_migrations(
        tmp_path
    )

    assert report.is_valid
    assert report.migrations == []
    assert report.errors == []
    assert report.migration_count == 0


def test_valid_migrations_are_reported(
    tmp_path: Path,
):
    write_migration(
        tmp_path / "001_first.sql",
        1,
        "first",
    )

    write_migration(
        tmp_path / "002_second.sql",
        2,
        "second",
    )

    report = validate_migrations(
        tmp_path
    )

    assert report.is_valid
    assert len(report.migrations) == 2
    assert report.migration_count == 2
    assert report.errors == []


def test_missing_version_is_reported(
    tmp_path: Path,
):
    write_migration(
        tmp_path / "001_first.sql",
        1,
        "first",
    )

    write_migration(
        tmp_path / "003_third.sql",
        3,
        "third",
    )

    report = validate_migrations(
        tmp_path
    )

    assert not report.is_valid
    assert any(
        "gap" in error.lower()
        for error in report.errors
    )


def test_duplicate_versions_are_reported(
    tmp_path: Path,
):
    write_migration(
        tmp_path / "001_first.sql",
        1,
        "first",
    )

    write_migration(
        tmp_path / "001_second.sql",
        1,
        "second",
    )

    report = validate_migrations(
        tmp_path
    )

    assert not report.is_valid
    assert any(
        "duplicate" in error.lower()
        for error in report.errors
    )


def test_duplicate_names_are_reported(
    tmp_path: Path,
):
    write_migration(
        tmp_path / "001_users.sql",
        1,
        "users",
    )

    write_migration(
        tmp_path / "002_users.sql",
        2,
        "users",
    )

    report = validate_migrations(
        tmp_path
    )

    assert not report.is_valid
    assert any(
        "DUPLICATE_NAME" in error
        for error in report.errors
    )


def test_malformed_migration_is_reported(
    tmp_path: Path,
):
    path = tmp_path / "001_broken.sql"

    path.write_text(
        """
-- migration: 001
-- name: broken

-- +up

CREATE TABLE users (id INTEGER);
""".strip()
        + "\n",
        encoding="utf-8",
    )

    report = validate_migrations(
        tmp_path
    )

    assert not report.is_valid
    assert len(report.migrations) == 0
    assert report.migration_count == 0
    assert report.errors
    assert any(
        "down" in error.lower()
        for error in report.errors
    )


def test_invalid_migration_directory_is_reported(
    tmp_path: Path,
):
    missing_directory = (
        tmp_path / "missing"
    )

    report = validate_migrations(
        missing_directory
    )

    assert not report.is_valid
    assert report.migrations == []
    assert report.migration_count == 0
    assert len(report.errors) == 1