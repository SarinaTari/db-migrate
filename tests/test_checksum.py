"""Tests for migration checksums."""

from pathlib import Path

from dbmigrate.checksum import (
    calculate_checksum,
    verify_migration_checksum,
    verify_migration_checksums,
)
from dbmigrate.history import MigrationRecord
from dbmigrate.migration import Migration


def make_migration(
    tmp_path: Path,
    version: int = 1,
    name: str = "users",
    up_sql: str = "CREATE TABLE users (id INTEGER);",
    down_sql: str = "DROP TABLE users;",
) -> Migration:
    """Create a migration fixture."""
    path = (
        tmp_path
        / f"{version:03d}_{name}.sql"
    )

    path.write_text(
        f"""-- migration: {version}
-- name: {name}

-- +up

{up_sql}

-- +down

{down_sql}
""",
        encoding="utf-8",
    )

    return Migration(
        version=version,
        name=name,
        up_sql=up_sql,
        down_sql=down_sql,
        path=path,
    )


def make_record(
    migration: Migration,
    checksum: str,
) -> MigrationRecord:
    """Create a history record fixture."""
    return MigrationRecord(
        version=migration.version,
        name=migration.name,
        checksum=checksum,
        applied_at="2026-01-01T00:00:00+00:00",
    )


def test_checksum_is_deterministic(
    tmp_path: Path,
) -> None:
    migration = make_migration(
        tmp_path
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
) -> None:
    first = make_migration(
        tmp_path,
        up_sql="CREATE TABLE users (id INTEGER);",
    )

    second = make_migration(
        tmp_path,
        up_sql="CREATE TABLE users (id INTEGER, name TEXT);",
    )

    assert calculate_checksum(
        first
    ) != calculate_checksum(
        second
    )


def test_checksum_changes_when_down_sql_changes(
    tmp_path: Path,
) -> None:
    first = make_migration(
        tmp_path,
        down_sql="DROP TABLE users;",
    )

    second = make_migration(
        tmp_path,
        down_sql="DROP TABLE IF EXISTS users;",
    )

    assert calculate_checksum(
        first
    ) != calculate_checksum(
        second
    )


def test_checksum_changes_when_name_changes(
    tmp_path: Path,
) -> None:
    first = make_migration(
        tmp_path,
        name="users",
    )

    second = make_migration(
        tmp_path,
        name="accounts",
    )

    assert calculate_checksum(
        first
    ) != calculate_checksum(
        second
    )


def test_matching_checksum_has_no_mismatch(
    tmp_path: Path,
) -> None:
    migration = make_migration(
        tmp_path
    )

    checksum = calculate_checksum(
        migration
    )

    record = make_record(
        migration,
        checksum,
    )

    assert verify_migration_checksum(
        migration,
        record,
    ) is None


def test_modified_applied_migration_is_detected(
    tmp_path: Path,
) -> None:
    migration = make_migration(
        tmp_path
    )

    original_checksum = calculate_checksum(
        migration
    )

    modified = make_migration(
        tmp_path,
        up_sql="CREATE TABLE users (id INTEGER, name TEXT);",
    )

    record = make_record(
        migration,
        original_checksum,
    )

    mismatch = verify_migration_checksum(
        modified,
        record,
    )

    assert mismatch is not None
    assert mismatch.expected == original_checksum
    assert mismatch.actual == calculate_checksum(
        modified
    )

    assert (
        "checksum mismatch"
        in mismatch.format().lower()
    )


def test_unapplied_migration_is_ignored(
    tmp_path: Path,
) -> None:
    migration = make_migration(
        tmp_path
    )

    assert verify_migration_checksums(
        [migration],
        [],
    ) == []


def test_multiple_mismatches_are_reported(
    tmp_path: Path,
) -> None:
    first = make_migration(
        tmp_path,
        version=1,
        name="users",
    )

    second = make_migration(
        tmp_path,
        version=2,
        name="posts",
    )

    records = [
        make_record(
            first,
            "0" * 64,
        ),
        make_record(
            second,
            "1" * 64,
        ),
    ]

    mismatches = verify_migration_checksums(
        [first, second],
        records,
    )

    assert {
        mismatch.version
        for mismatch in mismatches
    } == {1, 2}