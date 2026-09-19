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
    report = validate_migrations(tmp_path)

    assert report.is_valid
    assert report.migrations == []
    assert report.errors == []


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

    report = validate_migrations(tmp_path)

    assert report.is_valid
    assert len(report.migrations) == 2
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

    report = validate_migrations(tmp_path)

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

    report = validate_migrations(tmp_path)

    assert not report.is_valid
    assert any(
        "duplicate" in error.lower()
        for error in report.errors
    )