"""Migration execution and rollback."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
from typing import Sequence

from .database import Database, DatabaseError
from .history import HistoryError, MigrationHistory
from .migration import Migration


class MigrationRunnerError(Exception):
    """Raised when migration execution fails."""


@dataclass(frozen=True)
class MigrationResult:
    """Result of applying or rolling back a migration."""

    migration: Migration
    action: str
    checksum: str | None = None


class MigrationRunner:
    """Apply and roll back database migrations."""

    def __init__(self, database: Database) -> None:
        self.database = database
        self.history = MigrationHistory(database)

    def initialize(self) -> None:
        """Initialize migration history storage."""
        try:
            self.history.initialize()
        except (DatabaseError, HistoryError) as exc:
            raise MigrationRunnerError(
                f"Could not initialize migration history: {exc}"
            ) from exc

    def pending(
        self,
        migrations: Sequence[Migration],
    ) -> list[Migration]:
        """Return unapplied migrations in version order."""
        self.initialize()

        ordered = sorted(
            migrations,
            key=lambda migration: migration.version,
        )

        pending: list[Migration] = []

        for migration in ordered:
            try:
                applied = self.history.is_applied(
                    migration.version
                )
            except HistoryError as exc:
                raise MigrationRunnerError(
                    f"Could not determine migration state for "
                    f"{migration.identifier}: {exc}"
                ) from exc

            if not applied:
                pending.append(migration)

        return pending

    def applied(
        self,
        migrations: Sequence[Migration],
    ) -> list[Migration]:
        """Return applied migrations in version order."""
        self.initialize()

        ordered = sorted(
            migrations,
            key=lambda migration: migration.version,
        )

        result: list[Migration] = []

        for migration in ordered:
            try:
                if self.history.is_applied(migration.version):
                    result.append(migration)
            except HistoryError as exc:
                raise MigrationRunnerError(
                    f"Could not determine migration state for "
                    f"{migration.identifier}: {exc}"
                ) from exc

        return result

    def apply(
        self,
        migration: Migration,
    ) -> MigrationResult:
        """Apply one migration atomically."""
        self.initialize()

        try:
            if self.history.is_applied(migration.version):
                raise MigrationRunnerError(
                    f"Migration {migration.identifier} is already applied."
                )

            checksum = _calculate_checksum(migration)

            self.database.begin()

            try:
                self.database.execute(migration.up_sql)

                self.history.record(
                    migration.version,
                    migration.name,
                    checksum,
                )

                self.database.commit()

            except Exception:
                self.database.rollback()
                raise

        except MigrationRunnerError:
            raise

        except (
            DatabaseError,
            HistoryError,
        ) as exc:
            raise MigrationRunnerError(
                f"Failed to apply migration "
                f"{migration.identifier}: {exc}"
            ) from exc

        except Exception as exc:
            raise MigrationRunnerError(
                f"Failed to apply migration "
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
        results: list[MigrationResult] = []

        for migration in self.pending(migrations):
            results.append(self.apply(migration))

        return results

    def rollback(
        self,
        migration: Migration,
    ) -> MigrationResult:
        """Roll back one applied migration atomically."""
        self.initialize()

        try:
            record = self.history.get(
                migration.version
            )

            if record is None:
                raise MigrationRunnerError(
                    f"Migration {migration.identifier} is not applied."
                )

            self.database.begin()

            try:
                self.database.execute(migration.down_sql)

                self.history.remove(
                    migration.version,
                )

                self.database.commit()

            except Exception:
                self.database.rollback()
                raise

        except MigrationRunnerError:
            raise

        except (
            DatabaseError,
            HistoryError,
        ) as exc:
            raise MigrationRunnerError(
                f"Failed to roll back migration "
                f"{migration.identifier}: {exc}"
            ) from exc

        except Exception as exc:
            raise MigrationRunnerError(
                f"Failed to roll back migration "
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

        migration = applied[-1]

        return self.rollback(migration)

    def rollback_steps(
        self,
        migrations: Sequence[Migration],
        steps: int,
    ) -> list[MigrationResult]:
        """Roll back the requested number of latest migrations."""
        if steps < 1:
            raise MigrationRunnerError(
                "Rollback steps must be greater than zero."
            )

        applied = self.applied(migrations)

        if not applied:
            return []

        if steps > len(applied):
            raise MigrationRunnerError(
                f"Cannot roll back {steps} migrations; "
                f"only {len(applied)} are currently applied."
            )

        results: list[MigrationResult] = []

        for migration in reversed(applied[-steps:]):
            results.append(self.rollback(migration))

        return results


def _calculate_checksum(migration: Migration) -> str:
    """Calculate a deterministic checksum for a migration."""
    content = (
        f"{migration.version}\n"
        f"{migration.name}\n"
        f"{migration.up_sql}\n"
        f"{migration.down_sql}\n"
    )

    return hashlib.sha256(
        content.encode("utf-8")
    ).hexdigest()


def _utc_timestamp() -> str:
    """Return the current UTC timestamp in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat()