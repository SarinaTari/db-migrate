"""Project-level migration validation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .migration import (
    Migration,
    MigrationDiscoveryError,
    MigrationParseError,
    discover_migrations,
)


@dataclass(frozen=True)
class ValidationIssue:
    """A single migration validation issue."""

    code: str
    message: str
    path: Path | None = None
    version: int | None = None

    def format(self) -> str:
        """Return a human-readable representation."""
        location = ""

        if self.path is not None:
            location = f" [{self.path.name}]"

        if self.version is not None:
            location = f" [version {self.version:03d}]" + location

        return f"{self.code}{location}: {self.message}"


@dataclass(frozen=True)
class ValidationReport:
    """Result of validating a migration collection."""

    migrations: tuple[Migration, ...]
    issues: tuple[ValidationIssue, ...]

    @property
    def is_valid(self) -> bool:
        """Return whether validation succeeded."""
        return not self.issues

    @property
    def migration_count(self) -> int:
        """Return the number of successfully discovered migrations."""
        return len(self.migrations)


def _validate_version_sequence(
    migrations: tuple[Migration, ...],
) -> list[ValidationIssue]:
    """Validate that migration versions form a continuous sequence."""
    if not migrations:
        return []

    issues: list[ValidationIssue] = []

    expected_version = 1

    for migration in migrations:
        if migration.version != expected_version:
            if migration.version > expected_version:
                issues.append(
                    ValidationIssue(
                        code="MIGRATION_GAP",
                        message=(
                            f"Expected migration version "
                            f"{expected_version:03d}, but found "
                            f"{migration.version:03d}."
                        ),
                        path=migration.path,
                        version=migration.version,
                    )
                )

            elif migration.version < expected_version:
                issues.append(
                    ValidationIssue(
                        code="MIGRATION_ORDER",
                        message=(
                            f"Migration version {migration.version:03d} "
                            f"appears where {expected_version:03d} "
                            "was expected."
                        ),
                        path=migration.path,
                        version=migration.version,
                    )
                )

        expected_version = migration.version + 1

    return issues


def _validate_names(
    migrations: tuple[Migration, ...],
) -> list[ValidationIssue]:
    """Validate migration-name uniqueness."""
    issues: list[ValidationIssue] = []
    seen_names: dict[str, Migration] = {}

    for migration in migrations:
        previous = seen_names.get(migration.name)

        if previous is not None:
            issues.append(
                ValidationIssue(
                    code="DUPLICATE_NAME",
                    message=(
                        f"Migration name '{migration.name}' is already "
                        f"used by version {previous.version:03d}."
                    ),
                    path=migration.path,
                    version=migration.version,
                )
            )

        else:
            seen_names[migration.name] = migration

    return issues


def validate_migrations(
    directory: Path,
) -> ValidationReport:
    """Discover and validate the migration collection."""
    try:
        migrations = discover_migrations(directory)

    except MigrationParseError as exc:
        return ValidationReport(
            migrations=(),
            issues=(
                ValidationIssue(
                    code="MIGRATION_PARSE_ERROR",
                    message=str(exc),
                ),
            ),
        )

    except MigrationDiscoveryError as exc:
        return ValidationReport(
            migrations=(),
            issues=(
                ValidationIssue(
                    code="MIGRATION_DISCOVERY_ERROR",
                    message=str(exc),
                ),
            ),
        )

    issues: list[ValidationIssue] = []

    issues.extend(_validate_version_sequence(migrations))
    issues.extend(_validate_names(migrations))

    return ValidationReport(
        migrations=migrations,
        issues=tuple(issues),
    )