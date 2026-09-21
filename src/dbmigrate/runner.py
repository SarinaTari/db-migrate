"""Migration execution and rollback."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .checksum import calculate_checksum
from .database import Database, DatabaseError
from .history import HistoryError, MigrationHistory
from .migration import Migration


class MigrationRunnerError(Exception):
    """Raised when migration execution fails."""


@dataclass(frozen=True)
class MigrationResult:
    """Describe a migration execution result."""

    migration: Migration
    action: str
    checksum: str | None = None


class MigrationRunner:
    """Execute and roll back migrations."""

    def __init__(self, database: Database) -> None:
        """Initialize the migration runner."""
        self.database = database
        self.history = MigrationHistory(database)

    def initialize(self) -> None:
        """Initialize migration history."""
        try:
            self.history.initialize()
        except HistoryError as exc:
            raise MigrationRunnerError(str(exc)) from exc

    def pending(
        self,
        migrations: Sequence[Migration],
    ) -> list[Migration]:
        """Return migrations that have not been applied."""
        self.initialize()

        try:
            applied_versions = self.history.applied_versions()
        except HistoryError as exc:
            raise MigrationRunnerError(str(exc)) from exc

        return [
            migration
            for migration in sorted(
                migrations,
                key=lambda item: item.version,
            )
            if migration.version not in applied_versions
        ]

    def applied(
        self,
        migrations: Sequence[Migration],
    ) -> list[Migration]:
        """Return migrations that have been applied."""
        self.initialize()

        try:
            applied_versions = self.history.applied_versions()
        except HistoryError as exc:
            raise MigrationRunnerError(str(exc)) from exc

        return [
            migration
            for migration in sorted(
                migrations,
                key=lambda item: item.version,
            )
            if migration.version in applied_versions
        ]

    def apply(
        self,
        migration: Migration,
    ) -> MigrationResult:
        """Apply one migration."""
        self.initialize()

        try:
            if self.history.is_applied(migration.version):
                raise MigrationRunnerError(
                    f"Migration {migration.identifier} already applied."
                )

            checksum = calculate_checksum(migration)

            with self.database.transaction():
                self.database.execute(migration.up_sql)
                self.history.record(
                    version=migration.version,
                    name=migration.name,
                    checksum=checksum,
                )

        except MigrationRunnerError:
            raise

        except (DatabaseError, HistoryError) as exc:
            raise MigrationRunnerError(
                f"Could not apply migration "
                f"{migration.identifier}: {exc}"
            ) from exc

        return MigrationResult(
            migration=migration,
            action="applied",
            checksum=checksum,
        )

    def apply_all(
        self,
        migrations: Sequence[Migration],
    ) -> list[MigrationResult]:
        """Apply all pending migrations in version order."""
        self.initialize()

        ordered_migrations = sorted(
            migrations,
            key=lambda item: item.version,
        )

        try:
            applied_versions = self.history.applied_versions()
        except HistoryError as exc:
            raise MigrationRunnerError(str(exc)) from exc

        pending = [
            migration
            for migration in ordered_migrations
            if migration.version not in applied_versions
        ]

        results: list[MigrationResult] = []

        for migration in pending:
            results.append(
                self.apply(migration)
            )

        return results

    def rollback(
        self,
        migration: Migration,
    ) -> MigrationResult:
        """Roll back one applied migration."""
        self.initialize()

        try:
            record = self.history.get(migration.version)

            if record is None:
                raise MigrationRunnerError(
                    f"Migration {migration.identifier} "
                    "has not been applied."
                )

            with self.database.transaction():
                self.database.execute(migration.down_sql)
                self.history.remove(migration.version)

        except MigrationRunnerError:
            raise

        except (DatabaseError, HistoryError) as exc:
            raise MigrationRunnerError(
                f"Could not roll back migration "
                f"{migration.identifier}: {exc}"
            ) from exc

        return MigrationResult(
            migration=migration,
            action="rolled back",
            checksum=record.checksum,
        )

    def rollback_latest(
        self,
        migrations: Sequence[Migration],
    ) -> MigrationResult | None:
        """Roll back the latest applied migration."""
        applied = self.applied(migrations)

        if not applied:
            return None

        return self.rollback(applied[-1])

    def rollback_steps(
        self,
        migrations: Sequence[Migration],
        steps: int,
    ) -> list[MigrationResult]:
        """Roll back a number of latest migrations."""
        if steps <= 0:
            raise MigrationRunnerError(
                "Rollback steps must be greater than zero."
            )

        applied = self.applied(migrations)

        if not applied:
            return []

        if steps > len(applied):
            raise MigrationRunnerError(
                f"Cannot roll back {steps} migrations; "
                f"only {len(applied)} are applied."
            )

        results: list[MigrationResult] = []

        for migration in reversed(applied[-steps:]):
            results.append(
                self.rollback(migration)
            )

        return results