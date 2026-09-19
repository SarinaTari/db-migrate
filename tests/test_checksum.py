"""Tests for migration checksums."""

from pathlib import Path

from dbmigrate.checksum import (
    calculate_checksum,
    verify_migration_checksum,
    verify_migration_checksums,
)
from dbmigrate.history import MigrationRecord
from dbmigrate.migration import parse_migration


def write_migration(
    path: Path,
    version: int,
    name: str,
    up_sql: str = "SELECT 1;",
    down_sql: str = "SELECT 1;",
) -> None:
    """Write a migration fixture."""
    path.write_text(
        f"""-- migration: {version:03d}
-- name: {name}

-- +up

{up_sql}

-- +down

{down_sql}
""",
        encoding="utf-8",
    )


def test_checksum_is_deterministic(
    tmp_path: Path,
):
    """The same migration should always produce the same checksum."""
    path = tmp_path / "001_users.sql"

    write_migration(
        path,
        1,
        "users",
    )

    migration = parse_migration(
        path
    )

    first = calculate_checksum(
        migration
    )

    second = calculate_checksum(
        migration
    )

    assert first == second
    assert len(first) == 64
    assert all(
        character in "0123456789abcdef"
        for character in first
    )


def test_checksum_changes_when_up_sql_changes(
    tmp_path: Path,
):
    """Changing migration SQL should change its checksum."""
    path = tmp_path / "001_users.sql"

    write_migration(
        path,
        1,
        "users",
        up_sql="CREATE TABLE users (id INTEGER);",
    )

    first_migration = parse_migration(
        path
    )

    first_checksum = calculate_checksum(
        first_migration
    )

    write_migration(
        path,
        1,
        "users",
        up_sql=(
            "CREATE TABLE users "
            "(id INTEGER PRIMARY KEY);"
        ),
    )

    second_migration = parse_migration(
        path
    )

    second_checksum = calculate_checksum(
        second_migration
    )

    assert first_checksum != second_checksum


def test_checksum_changes_when_down_sql_changes(
    tmp_path: Path,
):
    """Changing rollback SQL should change its checksum."""
    path = tmp_path / "001_users.sql"

    write_migration(
        path,
        1,
        "users",
        down_sql="DROP TABLE users;",
    )

    first_migration = parse_migration(
        path
    )

    first_checksum = calculate_checksum(
        first_migration
    )

    write_migration(
        path,
        1,
        "users",
        down_sql="DROP TABLE IF EXISTS users;",
    )

    second_migration = parse_migration(
        path
    )

    second_checksum = calculate_checksum(
        second_migration
    )

    assert first_checksum != second_checksum


def test_checksum_changes_when_name_changes(
    tmp_path: Path,
):
    """Changing the migration name should change its checksum."""
    first_path = tmp_path / "001_users.sql"

    write_migration(
        first_path,
        1,
        "users",
    )

    first_migration = parse_migration(
        first_path
    )

    first_checksum = calculate_checksum(
        first_migration
    )

    second_path = tmp_path / "001_accounts.sql"

    write_migration(
        second_path,
        1,
        "accounts",
    )

    second_migration = parse_migration(
        second_path
    )

    second_checksum = calculate_checksum(
        second_migration
    )

    assert first_checksum != second_checksum


def test_matching_record_has_no_mismatch(
    tmp_path: Path,
):
    """A matching history checksum should verify successfully."""
    path = tmp_path / "001_users.sql"

    write_migration(
        path,
        1,
        "users",
    )

    migration = parse_migration(
        path
    )

    checksum = calculate_checksum(
        migration
    )

    record = MigrationRecord(
        version=1,
        name="users",
        checksum=checksum,
        applied_at="2026-01-01T00:00:00+00:00",
    )

    mismatch = verify_migration_checksum(
        migration,
        record,
    )

    assert mismatch is None


def test_modified_migration_is_detected(
    tmp_path: Path,
):
    """A changed migration should produce a checksum mismatch."""
    path = tmp_path / "001_users.sql"

    write_migration(
        path,
        1,
        "users",
        up_sql="CREATE TABLE users (id INTEGER);",
    )

    original = parse_migration(
        path
    )

    original_checksum = calculate_checksum(
        original
    )

    record = MigrationRecord(
        version=1,
        name="users",
        checksum=original_checksum,
        applied_at="2026-01-01T00:00:00+00:00",
    )

    write_migration(
        path,
        1,
        "users",
        up_sql=(
            "CREATE TABLE users "
            "(id INTEGER PRIMARY KEY);"
        ),
    )

    modified = parse_migration(
        path
    )

    mismatch = verify_migration_checksum(
        modified,
        record,
    )

    assert mismatch is not None
    assert mismatch.expected == original_checksum
    assert mismatch.actual != original_checksum
    assert "checksum mismatch" in mismatch.format().lower()


def test_checksum_verification_ignores_unapplied_migrations(
    tmp_path: Path,
):
    """Only migrations with history records need checksum verification."""
    first_path = tmp_path / "001_users.sql"
    second_path = tmp_path / "002_posts.sql"

    write_migration(
        first_path,
        1,
        "users",
    )

    write_migration(
        second_path,
        2,
        "posts",
    )

    first = parse_migration(
        first_path
    )

    second = parse_migration(
        second_path
    )

    record = MigrationRecord(
        version=1,
        name="users",
        checksum=calculate_checksum(first),
        applied_at="2026-01-01T00:00:00+00:00",
    )

    mismatches = verify_migration_checksums(
        [first, second],
        [record],
    )

    assert mismatches == []


def test_multiple_checksum_mismatches_are_reported(
    tmp_path: Path,
):
    """Multiple modified applied migrations should all be reported."""
    first_path = tmp_path / "001_users.sql"
    second_path = tmp_path / "002_posts.sql"

    write_migration(
        first_path,
        1,
        "users",
        up_sql="CREATE TABLE users (id INTEGER);",
    )

    write_migration(
        second_path,
        2,
        "posts",
        up_sql="CREATE TABLE posts (id INTEGER);",
    )

    first = parse_migration(
        first_path
    )

    second = parse_migration(
        second_path
    )

    first_record = MigrationRecord(
        version=1,
        name="users",
        checksum=calculate_checksum(first),
        applied_at="2026-01-01T00:00:00+00:00",
    )

    second_record = MigrationRecord(
        version=2,
        name="posts",
        checksum=calculate_checksum(second),
        applied_at="2026-01-01T00:00:00+00:00",
    )

    write_migration(
        first_path,
        1,
        "users",
        up_sql="CREATE TABLE users (id INTEGER PRIMARY KEY);",
    )

    write_migration(
        second_path,
        2,
        "posts",
        up_sql=(
            "CREATE TABLE posts "
            "(id INTEGER PRIMARY KEY);"
        ),
    )

    first_modified = parse_migration(
        first_path
    )

    second_modified = parse_migration(
        second_path
    )

    mismatches = verify_migration_checksums(
        [first_modified, second_modified],
        [first_record, second_record],
    )

    assert len(mismatches) == 2
    assert {
        mismatch.version
        for mismatch in mismatches
    } == {1, 2}