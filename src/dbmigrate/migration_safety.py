"""Safety checks performed before migration execution."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .checksum import verify_migration_checksums
from .database import Database, DatabaseError
from .migration import Migration


class MigrationSafetyError(Exception):
    """Raised when migration safety checks fail."""


@dataclass(frozen=True)
class SafetyIssue:
    """Describe a migration safety issue."""

    severity: str
    code: str
    message: str

    @property
    def is_error(self) -> bool:
        """Return whether this issue blocks execution."""
        return self.severity == "ERROR"

    def format(self) -> str:
        """Return a human-readable representation."""
        return (
            f"[{self.severity}] "
            f"{self.code}: "
            f"{self.message}"
        )


@dataclass(frozen=True)
class SafetyReport:
    """Result of migration safety checks."""

    issues: tuple[SafetyIssue, ...]

    @property
    def is_safe(self) -> bool:
        """Return whether migration execution is safe."""
        return not any(
            issue.is_error
            for issue in self.issues
        )

    @property
    def errors(self) -> tuple[SafetyIssue, ...]:
        """Return blocking issues."""
        return tuple(
            issue
            for issue in self.issues
            if issue.is_error
        )

    @property
    def warnings(self) -> tuple[SafetyIssue, ...]:
        """Return warning issues."""
        return tuple(
            issue
            for issue in self.issues
            if issue.severity == "WARNING"
        )


class MigrationSafetyChecker:
    """Perform pre-execution migration safety checks."""

    def __init__(
        self,
        database: Database,
    ) -> None:
        self.database = database

    def check(
        self,
        migrations: Sequence[Migration],
    ) -> SafetyReport:
        """Run all migration safety checks."""
        issues: list[SafetyIssue] = []

        self._check_database_connection(
            issues
        )
        self._check_migration_order(
            migrations,
            issues,
        )
        self._check_duplicates(
            migrations,
            issues,
        )
        self._check_capabilities(
            migrations,
            issues,
        )
        self._check_applied_migrations(
            migrations,
            issues,
        )

        return SafetyReport(
            issues=tuple(issues)
        )

    def require_safe(
        self,
        migrations: Sequence[Migration],
    ) -> SafetyReport:
        """Run safety checks and raise if unsafe."""
        report = self.check(
            migrations
        )

        if not report.is_safe:
            messages = "\n".join(
                issue.format()
                for issue in report.errors
            )

            raise MigrationSafetyError(
                "Migration safety checks failed:\n"
                f"{messages}"
            )

        return report

    def _check_database_connection(
        self,
        issues: list[SafetyIssue],
    ) -> None:
        try:
            self.database.fetch_one(
                self.database.dialect.version_query()
            )
        except DatabaseError as exc:
            issues.append(
                SafetyIssue(
                    severity="ERROR",
                    code="DATABASE_UNAVAILABLE",
                    message=(
                        "Database connection check failed: "
                        f"{exc}"
                    ),
                )
            )

    def _check_migration_order(
        self,
        migrations: Sequence[Migration],
        issues: list[SafetyIssue],
    ) -> None:
        versions = [
            migration.version
            for migration in migrations
        ]

        if versions != sorted(versions):
            issues.append(
                SafetyIssue(
                    severity="ERROR",
                    code="MIGRATION_ORDER",
                    message=(
                        "Migration files are not ordered "
                        "by version."
                    ),
                )
            )

    def _check_duplicates(
        self,
        migrations: Sequence[Migration],
        issues: list[SafetyIssue],
    ) -> None:
        versions = [
            migration.version
            for migration in migrations
        ]

        duplicate_versions = {
            version
            for version in versions
            if versions.count(version) > 1
        }

        for version in sorted(duplicate_versions):
            issues.append(
                SafetyIssue(
                    severity="ERROR",
                    code="DUPLICATE_VERSION",
                    message=(
                        f"Migration version {version} "
                        "appears more than once."
                    ),
                )
            )

        identifiers = [
            migration.name
            for migration in migrations
        ]

        duplicate_identifiers = {
            identifier
            for identifier in identifiers
            if identifiers.count(identifier) > 1
        }

        for identifier in sorted(
            duplicate_identifiers
        ):
            issues.append(
                SafetyIssue(
                    severity="ERROR",
                    code="DUPLICATE_IDENTIFIER",
                    message=(
                        f"Migration identifier "
                        f"'{identifier}' appears more "
                        "than once."
                    ),
                )
            )

    def _check_capabilities(
        self,
        migrations: Sequence[Migration],
        issues: list[SafetyIssue],
    ) -> None:
        if not migrations:
            return

        if not self.database.capabilities.supports(
            "transactional_ddl"
        ):
            issues.append(
                SafetyIssue(
                    severity="WARNING",
                    code="NON_TRANSACTIONAL_DDL",
                    message=(
                        f"{self.database.engine} does not "
                        "provide transactional DDL. A "
                        "partially applied migration may "
                        "not be automatically reversible."
                    ),
                )
            )

    def _check_applied_migrations(
        self,
        migrations: Sequence[Migration],
        issues: list[SafetyIssue],
    ) -> None:
        try:
            from .history import MigrationHistory

            history = MigrationHistory(
                self.database
            )
            history.initialize()

            records = history.list_applied()

            recorded_versions = {
                record.version
                for record in records
            }

            migration_versions = {
                migration.version
                for migration in migrations
            }

            missing_versions = sorted(
                recorded_versions - migration_versions
            )

            for version in missing_versions:
                record = next(
                    record
                    for record in records
                    if record.version == version
                )

                issues.append(
                    SafetyIssue(
                        severity="ERROR",
                        code="MISSING_MIGRATION",
                        message=(
                            f"Migration {record.version:03d} "
                            f"'{record.name}' is recorded in "
                            "the database but its migration "
                            "file is missing."
                        ),
                    )
                )

            mismatches = verify_migration_checksums(
                migrations,
                records,
            )

            for mismatch in mismatches:
                issues.append(
                    SafetyIssue(
                        severity="ERROR",
                        code="CHECKSUM_MISMATCH",
                        message=mismatch.format(),
                    )
                )

        except DatabaseError as exc:
            issues.append(
                SafetyIssue(
                    severity="ERROR",
                    code="HISTORY_CHECK_FAILED",
                    message=(
                        "Could not verify migration "
                        f"history: {exc}"
                    ),
                )
            )