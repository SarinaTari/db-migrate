"""Tests for project-level migration validation."""

from __future__ import annotations

from pathlib import Path

from dbmigrate.validation import validate_migrations


VALID_TEMPLATE = """\
-- migration: {version}
-- name: {name}

-- +up

CREATE TABLE {table_name} (
    id INTEGER PRIMARY KEY
);

-- +down

DROP TABLE {table_name};
"""


def write_migration(
    directory: Path,
    version: int,
    name: str,
    table_name: str | None = None,
) -> Path:
    if table_name is None:
        table_name = name.replace("-", "_")

    path = directory / f"{version:03d}_{name}.sql"

    path.write_text(
        VALID_TEMPLATE.format(
            version=f"{version:03d}",
            name=name,
            table_name=table_name,
        ),
        encoding="utf-8",
    )

    return path


def test_empty_migration_directory_is_valid(tmp_path):
    report = validate_migrations(tmp_path)

    assert report.is_valid
    assert report.migration_count == 0
    assert report.issues == ()


def test_contiguous_migrations_are_valid(tmp_path):
    write_migration(tmp_path, 1, "create_users")
    write_migration(tmp_path, 2, "create_posts")
    write_migration(tmp_path, 3, "create_comments")

    report = validate_migrations(tmp_path)

    assert report.is_valid
    assert report.migration_count == 3
    assert [migration.version for migration in report.migrations] == [
        1,
        2,
        3,
    ]


def test_migration_gap_is_reported(tmp_path):
    write_migration(tmp_path, 1, "create_users")
    write_migration(tmp_path, 3, "create_posts")

    report = validate_migrations(tmp_path)

    assert not report.is_valid
    assert len(report.issues) == 1

    issue = report.issues[0]

    assert issue.code == "MIGRATION_GAP"
    assert issue.version == 3
    assert "002" in issue.message


def test_duplicate_migration_versions_are_reported(tmp_path):
    write_migration(tmp_path, 1, "create_users")

    duplicate = tmp_path / "001_create_posts.sql"

    duplicate.write_text(
        VALID_TEMPLATE.format(
            version="001",
            name="create_posts",
            table_name="posts",
        ),
        encoding="utf-8",
    )

    report = validate_migrations(tmp_path)

    assert not report.is_valid
    assert any(
        issue.code == "MIGRATION_DISCOVERY_ERROR"
        for issue in report.issues
    )


def test_duplicate_names_are_reported(tmp_path):
    write_migration(tmp_path, 1, "create_users")
    write_migration(tmp_path, 2, "create_users")

    report = validate_migrations(tmp_path)

    assert not report.is_valid

    duplicate_name_issues = [
        issue
        for issue in report.issues
        if issue.code == "DUPLICATE_NAME"
    ]

    assert len(duplicate_name_issues) == 1
    assert duplicate_name_issues[0].version == 2
    assert "001" in duplicate_name_issues[0].message


def test_invalid_migration_file_is_reported(tmp_path):
    path = tmp_path / "001_create_users.sql"

    path.write_text(
        """\
-- migration: 001
-- name: create_users

-- +up

CREATE TABLE users (
    id INTEGER PRIMARY KEY
);
""",
        encoding="utf-8",
    )

    report = validate_migrations(tmp_path)

    assert not report.is_valid
    assert len(report.issues) == 1
    assert report.issues[0].code == "MIGRATION_PARSE_ERROR"


def test_missing_migration_directory_is_reported(tmp_path):
    missing = tmp_path / "migrations"

    report = validate_migrations(missing)

    assert not report.is_valid
    assert len(report.issues) == 1
    assert report.issues[0].code == "MIGRATION_DISCOVERY_ERROR"


def test_validation_returns_sorted_migrations(tmp_path):
    write_migration(tmp_path, 3, "create_posts")
    write_migration(tmp_path, 1, "create_users")
    write_migration(tmp_path, 2, "create_comments")

    report = validate_migrations(tmp_path)

    assert report.is_valid

    assert [
        migration.identifier
        for migration in report.migrations
    ] == [
        "001_create_users",
        "002_create_comments",
        "003_create_posts",
    ]


def test_validation_issue_format():
    from dbmigrate.validation import ValidationIssue

    issue = ValidationIssue(
        code="MIGRATION_GAP",
        message="Expected version 002.",
        path=Path("/tmp/003_create_posts.sql"),
        version=3,
    )

    formatted = issue.format()

    assert "MIGRATION_GAP" in formatted
    assert "version 003" in formatted
    assert "003_create_posts.sql" in formatted
    assert "Expected version 002." in formatted