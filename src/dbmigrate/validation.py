"""Project-level migration validation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from .checksum import verify_migration_checksums
from .history import MigrationRecord
from .migration import (
    Migration,
    MigrationDiscoveryError,
    MigrationParseError,
    discover_migrations,
)


@dataclass(frozen=True)
class ValidationIssue:
    """Describe a migration validation problem."""

    code: str
    message: str
    path: Path | None = None
    version: int | None = None

    def format(self) -> str:
        """Return a formatted validation message."""
        location = ""

        if self.path is not None:
            location = f" [{self.path}]"

        return (
            f"{self.code}: "
            f"{self.message}"
            f"{location}"
        )


@dataclass(frozen=True)
class ValidationReport:
    """Result of validating a migration directory."""

    migrations: list[Migration]
    errors: list[str]

    @property
    def is_valid(self) -> bool:
        """Return whether validation succeeded."""
        return not self.errors

    @property
    def migration_count(self) -> int:
        """Return the number of discovered migrations."""
        return len(self.migrations)


def _validate_version_sequence(
    migrations: Sequence[Migration],
) -> list[ValidationIssue]:
    """Validate that migration versions are sequential."""
    issues: list[ValidationIssue] = []

    expected = 1

    for migration in migrations:
        if migration.version == expected:
            expected += 1
            continue

        if migration.version > expected:
            issues.append(
                ValidationIssue(
                    code="MIGRATION_GAP",
                    message=(
                        f"Expected migration version "
                        f"{expected:03d}, found "
                        f"{migration.version:03d}."
                    ),
                    path=migration.path,
                    version=migration.version,
                )
            )
            expected = migration.version + 1
            continue

        issues.append(
            ValidationIssue(
                code="MIGRATION_ORDER",
                message=(
                    f"Migration version "
                    f"{migration.version:03d} is out of order."
                ),
                path=migration.path,
                version=migration.version,
            )
        )

    return issues


def _validate_names(
    migrations: Sequence[Migration],
) -> list[ValidationIssue]:
    """Validate migration name uniqueness."""
    issues: list[ValidationIssue] = []
    seen: dict[str, Migration] = {}

    for migration in migrations:
        previous = seen.get(
            migration.name
        )

        if previous is not None:
            issues.append(
                ValidationIssue(
                    code="DUPLICATE_NAME",
                    message=(
                        f"Migration name '{migration.name}' "
                        f"is already used by version "
                        f"{previous.version:03d}."
                    ),
                    path=migration.path,
                    version=migration.version,
                )
            )
        else:
            seen[migration.name] = migration

    return issues


def _validate_collection(
    migrations: Sequence[Migration],
) -> list[ValidationIssue]:
    """Validate the discovered migration collection."""
    issues: list[ValidationIssue] = []

    versions: set[int] = set()

    for migration in migrations:
        if migration.version in versions:
            issues.append(
                ValidationIssue(
                    code="DUPLICATE_VERSION",
                    message=(
                        f"Migration version "
                        f"{migration.version:03d} "
                        "appears more than once."
                    ),
                    path=migration.path,
                    version=migration.version,
                )
            )

        versions.add(
            migration.version
        )

    issues.extend(
        _validate_version_sequence(
            migrations
        )
    )

    issues.extend(
        _validate_names(
            migrations
        )
    )

    return issues


def _validate_checksums(
    migrations: Sequence[Migration],
    records: Sequence[MigrationRecord],
) -> list[ValidationIssue]:
    """Validate checksums for applied migrations."""
    issues: list[ValidationIssue] = []

    mismatches = verify_migration_checksums(
        migrations,
        records,
    )

    for mismatch in mismatches:
        issues.append(
            ValidationIssue(
                code="CHECKSUM_MISMATCH",
                message=mismatch.format(),
                path=mismatch.migration.path,
                version=mismatch.version,
            )
        )

    return issues


def validate_migrations(
    directory: Path,
    records: Sequence[MigrationRecord] | None = None,
) -> ValidationReport:
    """Validate migration files and optional history checksums."""
    try:
        migrations = discover_migrations(
            directory
        )
    except (
        MigrationDiscoveryError,
        MigrationParseError,
    ) as exc:
        return ValidationReport(
            migrations=[],
            errors=[
                str(exc)
            ],
        )

    issues = _validate_collection(
        migrations
    )

    if records is not None:
        issues.extend(
            _validate_checksums(
                migrations,
                records,
            )
        )

    return ValidationReport(
        migrations=list(migrations),
        errors=[
            issue.format()
            for issue in issues
        ],
    )