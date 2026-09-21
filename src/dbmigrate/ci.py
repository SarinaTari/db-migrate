"""Continuous-integration checks for dbmigrate projects."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from .database import Database
from .logging_config import get_logger
from .migration import Migration, discover_migrations
from .migration_safety import MigrationSafetyChecker
from .reproducibility import check_reproducibility
from .schema import inspect_schema
from .validation import validate_migrations


class CIError(Exception):
    """Raised when CI checks cannot be completed."""


@dataclass(frozen=True)
class CICheckResult:
    """Describe one CI check."""

    name: str
    passed: bool
    message: str


@dataclass(frozen=True)
class CIReport:
    """Describe the complete CI result."""

    checks: tuple[CICheckResult, ...]

    @property
    def passed(self) -> bool:
        """Return whether every CI check passed."""
        return all(
            check.passed
            for check in self.checks
        )

    @property
    def failed(self) -> tuple[CICheckResult, ...]:
        """Return failed checks."""
        return tuple(
            check
            for check in self.checks
            if not check.passed
        )

    @property
    def passed_count(self) -> int:
        """Return the number of passed checks."""
        return sum(
            check.passed
            for check in self.checks
        )

    @property
    def failed_count(self) -> int:
        """Return the number of failed checks."""
        return len(self.failed)

    def format(self) -> str:
        """Return a human-readable CI report."""
        lines = [
            "dbmigrate CI",
            "",
        ]

        for check in self.checks:
            status = "PASS" if check.passed else "FAIL"

            lines.append(
                f"[{status}] "
                f"{check.name}: "
                f"{check.message}"
            )

        lines.extend(
            [
                "",
                (
                    f"Passed: {self.passed_count}    "
                    f"Failed: {self.failed_count}"
                ),
            ]
        )

        if self.passed:
            lines.append("CI checks passed.")
        else:
            lines.append("CI checks failed.")

        return "\n".join(lines)


class CIChecker:
    """Run deterministic project-level CI checks."""

    def __init__(
        self,
        *,
        project_root: Path,
        migrations_directory: Path,
        database: Database,
    ) -> None:
        self.project_root = project_root
        self.migrations_directory = migrations_directory
        self.database = database
        self.logger = get_logger("ci")

    def run(self) -> CIReport:
        """Run all CI checks."""
        checks: list[CICheckResult] = []

        migrations = self._load_migrations(
            checks
        )

        if migrations is None:
            return CIReport(
                checks=tuple(checks)
            )

        self._check_validation(
            checks
        )

        connected_here = False

        try:
            if not self.database.is_connected:
                self.database.connect()
                connected_here = True

            self._check_database(
                checks
            )

            self._check_safety(
                migrations,
                checks,
            )

            self._check_reproducibility(
                migrations,
                checks,
            )

        finally:
            if connected_here:
                self.database.close()

        return CIReport(
            checks=tuple(checks)
        )

    def _load_migrations(
        self,
        checks: list[CICheckResult],
    ) -> tuple[Migration, ...] | None:
        """Load migrations once for the CI run."""
        try:
            migrations = discover_migrations(
                self.migrations_directory
            )

            checks.append(
                CICheckResult(
                    name="migration-discovery",
                    passed=True,
                    message=(
                        f"Discovered "
                        f"{len(migrations)} migration(s)."
                    ),
                )
            )

            self.logger.debug(
                "Discovered %d migrations.",
                len(migrations),
            )

            return migrations

        except Exception as exc:
            checks.append(
                CICheckResult(
                    name="migration-discovery",
                    passed=False,
                    message=str(exc),
                )
            )

            self.logger.error(
                "Migration discovery failed: %s",
                exc,
            )

            return None

    def _check_validation(
        self,
        checks: list[CICheckResult],
    ) -> None:
        """Validate the migration collection."""
        try:
            validation = validate_migrations(
                self.migrations_directory
            )

            if validation.is_valid:
                checks.append(
                    CICheckResult(
                        name="migration-validation",
                        passed=True,
                        message=(
                            f"{validation.migration_count} "
                            "migration(s) valid."
                        ),
                    )
                )
                return

            checks.append(
                CICheckResult(
                    name="migration-validation",
                    passed=False,
                    message="; ".join(
                        validation.errors
                    ),
                )
            )

        except Exception as exc:
            checks.append(
                CICheckResult(
                    name="migration-validation",
                    passed=False,
                    message=str(exc),
                )
            )

    def _check_database(
        self,
        checks: list[CICheckResult],
    ) -> None:
        """Check database connectivity."""
        try:
            version = self.database.version()

            checks.append(
                CICheckResult(
                    name="database-connectivity",
                    passed=True,
                    message=(
                        f"{self.database.engine} "
                        f"{version}"
                    ),
                )
            )

        except Exception as exc:
            checks.append(
                CICheckResult(
                    name="database-connectivity",
                    passed=False,
                    message=str(exc),
                )
            )

    def _check_safety(
        self,
        migrations: Sequence[Migration],
        checks: list[CICheckResult],
    ) -> None:
        """Run migration safety checks."""
        if not self.database.is_connected:
            checks.append(
                CICheckResult(
                    name="migration-safety",
                    passed=False,
                    message="Database is not connected.",
                )
            )
            return

        try:
            report = MigrationSafetyChecker(
                self.database
            ).check(migrations)

            if report.is_safe:
                checks.append(
                    CICheckResult(
                        name="migration-safety",
                        passed=True,
                        message="No blocking safety issues.",
                    )
                )
            else:
                checks.append(
                    CICheckResult(
                        name="migration-safety",
                        passed=False,
                        message="; ".join(
                            issue.format()
                            for issue in report.errors
                        ),
                    )
                )

        except Exception as exc:
            checks.append(
                CICheckResult(
                    name="migration-safety",
                    passed=False,
                    message=str(exc),
                )
            )

    def _check_reproducibility(
        self,
        migrations: Sequence[Migration],
        checks: list[CICheckResult],
    ) -> None:
        """Verify that migrations reproduce the current schema."""
        if not self.database.is_connected:
            checks.append(
                CICheckResult(
                    name="schema-reproducibility",
                    passed=False,
                    message="Database is not connected.",
                )
            )
            return

        if self.database.engine != "sqlite":
            checks.append(
                CICheckResult(
                    name="schema-reproducibility",
                    passed=False,
                    message=(
                        "Schema reproducibility currently "
                        "supports SQLite only."
                    ),
                )
            )
            return

        try:
            target_schema = inspect_schema(
                self.database
            )

            report = check_reproducibility(
                migrations,
                target_schema,
            )

            if report.is_reproducible:
                checks.append(
                    CICheckResult(
                        name="schema-reproducibility",
                        passed=True,
                        message=(
                            "Migrations reproduce "
                            "the current schema."
                        ),
                    )
                )
            else:
                checks.append(
                    CICheckResult(
                        name="schema-reproducibility",
                        passed=False,
                        message=(
                            "Migrations do not reproduce "
                            "the current schema."
                        ),
                    )
                )

        except Exception as exc:
            checks.append(
                CICheckResult(
                    name="schema-reproducibility",
                    passed=False,
                    message=str(exc),
                )
            )