"""Migration safety checks."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .checksum import verify_migration_checksums
from .database import Database, DatabaseError
from .history import HistoryError, MigrationHistory
from .migration import Migration


class MigrationSafetyError(Exception):
    """Raised when migration safety checks fail."""


@dataclass(frozen=True)
class SafetyIssue:
    """Describe one migration safety issue."""

    severity: str
    code: str
    message: str

    @property
    def is_error(self) -> bool:
        """Return whether the issue is an error."""
        return self.severity == "ERROR"

    @property
    def is_warning(self) -> bool:
        """Return whether the issue is a warning."""
        return self.severity == "WARNING"

    def format(self) -> str:
        """Return a human-readable issue description."""
        return (
            f"{self.severity} "
            f"[{self.code}]: "
            f"{self.message}"
        )


@dataclass(frozen=True)
class SafetyReport:
    """Describe the result of migration safety checks."""

    issues: tuple[SafetyIssue, ...]

    @property
    def is_safe(self) -> bool:
        """Return whether no safety errors were found."""
        return not self.errors

    @property
    def errors(self) -> tuple[SafetyIssue, ...]:
        """Return safety errors."""
        return tuple(
            issue
            for issue in self.issues
            if issue.is_error
        )

    @property
    def warnings(self) -> tuple[SafetyIssue, ...]:
        """Return safety warnings."""
        return tuple(
            issue
            for issue in self.issues
            if issue.is_warning
        )

    def format(self) -> str:
        """Return all safety issues as formatted text."""
        if not self.issues:
            return "Migration safety checks passed."

        return "\n".join(
            issue.format()
            for issue in self.issues
        )


class MigrationSafetyChecker:
    """Check migrations for database and execution safety."""

    def __init__(
        self,
        database: Database,
    ) -> None:
        """Initialize the safety checker."""
        self.database = database
        self.history = MigrationHistory(
            database
        )

    def check(
        self,
        migrations: Sequence[Migration],
    ) -> SafetyReport:
        """Run all migration safety checks."""
        issues: list[SafetyIssue] = []

        issues.extend(
            self._check_database_connection()
        )
        issues.extend(
            self._check_migration_order(
                migrations
            )
        )
        issues.extend(
            self._check_duplicates(
                migrations
            )
        )
        issues.extend(
            self._check_capabilities()
        )
        issues.extend(
            self._check_applied_migrations(
                migrations
            )
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
            raise MigrationSafetyError(
                f"Migration safety checks failed:\n"
                f"{report.format()}"
            )

        return report

    def _check_database_connection(
        self,
    ) -> list[SafetyIssue]:
        """Check database connectivity."""
        try:
            self.database.version()
        except DatabaseError as exc:
            return [
                SafetyIssue(
                    severity="ERROR",
                    code="DATABASE_CONNECTION",
                    message=(
                        "Could not connect to the database: "
                        f"{exc}"
                    ),
                )
            ]

        return []

    def _check_migration_order(
        self,
        migrations: Sequence[Migration],
    ) -> list[SafetyIssue]:
        """Check that migration versions are valid and ordered."""
        issues: list[SafetyIssue] = []

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

        invalid_versions = [
            version
            for version in versions
            if version <= 0
        ]

        if invalid_versions:
            issues.append(
                SafetyIssue(
                    severity="ERROR",
                    code="INVALID_VERSION",
                    message=(
                        "Migration versions must be "
                        "greater than zero."
                    ),
                )
            )

        return issues

    def _check_duplicates(
        self,
        migrations: Sequence[Migration],
    ) -> list[SafetyIssue]:
        """Check for duplicate migration versions and identifiers."""
        issues: list[SafetyIssue] = []

        version_counts: dict[int, int] = {}

        for migration in migrations:
            version_counts[migration.version] = (
                version_counts.get(
                    migration.version,
                    0,
                )
                + 1
            )

        for version, count in sorted(
            version_counts.items()
        ):
            if count > 1:
                issues.append(
                    SafetyIssue(
                        severity="ERROR",
                        code="DUPLICATE_VERSION",
                        message=(
                            f"Migration version "
                            f"{version:03d} appears more than once."
                        ),
                    )
                )

        identifier_counts: dict[str, int] = {}

        for migration in migrations:
            identifier = migration.name
            identifier_counts[identifier] = (
                identifier_counts.get(
                    identifier,
                    0,
                )
                + 1
            )

        for identifier, count in sorted(
            identifier_counts.items()
        ):
            if count > 1:
                issues.append(
                    SafetyIssue(
                        severity="ERROR",
                        code="DUPLICATE_IDENTIFIER",
                        message=(
                            f"Migration identifier "
                            f"'{identifier}' appears more than once."
                        ),
                    )
                )

        return issues

    def _check_capabilities(
        self,
    ) -> list[SafetyIssue]:
        """Check database capabilities relevant to migrations."""
        issues: list[SafetyIssue] = []

        capabilities = self.database.capabilities

        if not capabilities.transactional_ddl:
            issues.append(
                SafetyIssue(
                    severity="WARNING",
                    code="NON_TRANSACTIONAL_DDL",
                    message=(
                        f"Database engine "
                        f"'{self.database.engine}' does not "
                        "provide transactional DDL. A migration "
                        "failure may leave partial schema changes."
                    ),
                )
            )

        if not capabilities.advisory_locks:
            issues.append(
                SafetyIssue(
                    severity="WARNING",
                    code="NO_ADVISORY_LOCKS",
                    message=(
                        f"Database engine "
                        f"'{self.database.engine}' does not "
                        "provide advisory locks."
                    ),
                )
            )

        return issues

    def _check_applied_migrations(
        self,
        migrations: Sequence[Migration],
    ) -> list[SafetyIssue]:
        """Check applied migration history against migration files."""
        issues: list[SafetyIssue] = []

        try:
            self.history.initialize()
            records = self.history.list_applied()
        except HistoryError as exc:
            return [
                SafetyIssue(
                    severity="ERROR",
                    code="HISTORY_ACCESS",
                    message=(
                        "Could not inspect migration history: "
                        f"{exc}"
                    ),
                )
            ]

        migration_versions = {
            migration.version
            for migration in migrations
        }

        missing_migrations = [
            record
            for record in records
            if record.version not in migration_versions
        ]

        for record in missing_migrations:
            issues.append(
                SafetyIssue(
                    severity="ERROR",
                    code="MISSING_MIGRATION_FILE",
                    message=(
                        f"Migration {record.version:03d} "
                        f"({record.name}) is recorded as applied "
                        "but its migration file is missing."
                    ),
                )
            )

        try:
            checksum_mismatches = verify_migration_checksums(
                migrations,
                records,
            )
        except Exception as exc:
            issues.append(
                SafetyIssue(
                    severity="ERROR",
                    code="CHECKSUM_VERIFICATION",
                    message=(
                        "Could not verify migration checksums: "
                        f"{exc}"
                    ),
                )
            )
            return issues

        for mismatch in checksum_mismatches:
            issues.append(
                SafetyIssue(
                    severity="ERROR",
                    code="CHECKSUM_MISMATCH",
                    message=(
                        f"Migration {mismatch.migration.identifier} "
                        "has been modified after it was applied."
                    ),
                )
            )

        return issues