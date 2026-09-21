"""Database and migration health diagnostics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .database import Database, DatabaseError
from .migration import Migration
from .migration_safety import (
    MigrationSafetyChecker,
    SafetyIssue,
)


@dataclass(frozen=True)
class DoctorReport:
    """Result of database health diagnostics."""

    issues: tuple[SafetyIssue, ...]

    @property
    def healthy(self) -> bool:
        """Return whether the database is healthy."""
        return not any(
            issue.severity == "ERROR"
            for issue in self.issues
        )

    @property
    def errors(self) -> tuple[SafetyIssue, ...]:
        """Return diagnostic errors."""
        return tuple(
            issue
            for issue in self.issues
            if issue.severity == "ERROR"
        )

    @property
    def warnings(self) -> tuple[SafetyIssue, ...]:
        """Return diagnostic warnings."""
        return tuple(
            issue
            for issue in self.issues
            if issue.severity == "WARNING"
        )

    @property
    def passes(self) -> tuple[SafetyIssue, ...]:
        """Return successful checks."""
        return tuple(
            issue
            for issue in self.issues
            if issue.severity == "PASS"
        )


class DatabaseDoctor:
    """Inspect database and migration health."""

    def __init__(
        self,
        database: Database,
    ) -> None:
        self.database = database

    def inspect(
        self,
        migrations: Sequence[Migration],
    ) -> DoctorReport:
        """Run database health checks."""
        issues: list[SafetyIssue] = []

        self._check_connection(
            issues
        )

        if not self.database.is_connected:
            return DoctorReport(
                issues=tuple(issues)
            )

        self._check_engine(
            issues
        )

        self._check_capabilities(
            issues
        )

        safety_report = MigrationSafetyChecker(
            self.database
        ).check(
            migrations
        )

        issues.extend(
            safety_report.issues
        )

        return DoctorReport(
            issues=tuple(issues)
        )

    def _check_connection(
        self,
        issues: list[SafetyIssue],
    ) -> None:
        try:
            self.database.fetch_one(
                self.database.dialect.version_query()
            )

            issues.append(
                SafetyIssue(
                    severity="PASS",
                    code="DATABASE_CONNECTION",
                    message=(
                        "Database connection is healthy."
                    ),
                )
            )

        except DatabaseError as exc:
            issues.append(
                SafetyIssue(
                    severity="ERROR",
                    code="DATABASE_CONNECTION",
                    message=(
                        f"Database connection failed: {exc}"
                    ),
                )
            )

    def _check_engine(
        self,
        issues: list[SafetyIssue],
    ) -> None:
        issues.append(
            SafetyIssue(
                severity="PASS",
                code="DATABASE_ENGINE",
                message=(
                    f"Database engine: "
                    f"{self.database.engine}."
                ),
            )
        )

    def _check_capabilities(
        self,
        issues: list[SafetyIssue],
    ) -> None:
        capabilities = (
            self.database.capabilities
        )

        if capabilities.transactional_ddl:
            issues.append(
                SafetyIssue(
                    severity="PASS",
                    code="TRANSACTIONAL_DDL",
                    message=(
                        "Transactional DDL is supported."
                    ),
                )
            )
        else:
            issues.append(
                SafetyIssue(
                    severity="WARNING",
                    code="TRANSACTIONAL_DDL",
                    message=(
                        "Transactional DDL is not "
                        "supported by this database."
                    ),
                )
            )

        if capabilities.advisory_locks:
            issues.append(
                SafetyIssue(
                    severity="PASS",
                    code="ADVISORY_LOCKS",
                    message=(
                        "Database advisory locking is "
                        "available."
                    ),
                )
            )
        elif self.database.engine == "sqlite":
            issues.append(
                SafetyIssue(
                    severity="PASS",
                    code="MIGRATION_LOCK",
                    message=(
                        "SQLite uses an exclusive "
                        "filesystem migration lock."
                    ),
                )
            )
        else:
            issues.append(
                SafetyIssue(
                    severity="WARNING",
                    code="MIGRATION_LOCK",
                    message=(
                        "Native advisory locking is "
                        "not available."
                    ),
                )
            )