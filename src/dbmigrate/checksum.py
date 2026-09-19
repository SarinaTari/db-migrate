"""Migration checksum calculation and verification."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from typing import Sequence

from .history import MigrationRecord
from .migration import Migration


class ChecksumError(Exception):
    """Raised when migration checksum verification fails."""


@dataclass(frozen=True)
class ChecksumMismatch:
    """Describe a migration checksum mismatch."""

    migration: Migration
    expected: str
    actual: str

    @property
    def version(self) -> int:
        """Return the migration version."""
        return self.migration.version

    @property
    def identifier(self) -> str:
        """Return the migration identifier."""
        return self.migration.identifier

    def format(self) -> str:
        """Return a human-readable mismatch description."""
        return (
            f"Migration {self.identifier} checksum mismatch: "
            f"database has {self.expected}, "
            f"current file has {self.actual}."
        )


def calculate_checksum(
    migration: Migration,
) -> str:
    """Calculate a deterministic SHA-256 checksum."""
    content = (
        f"{migration.version}\n"
        f"{migration.name}\n"
        f"{migration.up_sql}\n"
        f"{migration.down_sql}\n"
    )

    return hashlib.sha256(
        content.encode("utf-8")
    ).hexdigest()


def verify_migration_checksum(
    migration: Migration,
    record: MigrationRecord,
) -> ChecksumMismatch | None:
    """Compare a migration's current checksum with its history record."""
    actual = calculate_checksum(
        migration
    )

    if actual == record.checksum:
        return None

    return ChecksumMismatch(
        migration=migration,
        expected=record.checksum,
        actual=actual,
    )


def verify_migration_checksums(
    migrations: Sequence[Migration],
    records: Sequence[MigrationRecord],
) -> list[ChecksumMismatch]:
    """Return checksum mismatches for applied migrations."""
    records_by_version = {
        record.version: record
        for record in records
    }

    mismatches: list[ChecksumMismatch] = []

    for migration in migrations:
        record = records_by_version.get(
            migration.version
        )

        if record is None:
            continue

        mismatch = verify_migration_checksum(
            migration,
            record,
        )

        if mismatch is not None:
            mismatches.append(
                mismatch
            )

    return mismatches