"""Migration execution and forward migration management."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib

from .database import Database, DatabaseError
from .history import HistoryError, MigrationHistory
from .migration import Migration


class MigrationRunnerError(Exception):
    """Raised when migration execution fails."""


@dataclass(frozen=True)
class AppliedMigration:
    """Describe a migration successfully applied by the runner."""

    migration: Migration
    checksum: str


class MigrationRunner:
    """Execute pending migrations against a database."""

    def __init__(
        self,
        database: Database,
        history: MigrationHistory | None = None,
    ) -> None:
        self.database = database
        self.history = history or MigrationHistory(database)

    def initialize(self) -> None:
        """Initialize the migration history storage."""
        try:
            self.history.initialize()
        except HistoryError as exc:
            raise MigrationRunnerError(
                f"Could not initialize migration runner: {exc}"
            ) from exc

    def pending(
        self,
        migrations: list[Migration] | tuple[Migration, ...],
    ) -> list[Migration]:
        """Return migrations that have not yet been applied in version order."""
        self.initialize()

        ordered_migrations = sorted(
            migrations,
            key=lambda migration: migration.version,
        )

        pending: list[Migration] = []

        for migration in ordered_migrations:
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

    def apply(
        self,
        migration: Migration,
    ) -> AppliedMigration:
        """Apply one migration atomically with its history record."""
        self.initialize()

        try:
            if self.history.is_applied(migration.version):
                raise MigrationRunnerError(
                    f"Migration {migration.identifier} is already applied."
                )
        except HistoryError as exc:
            raise MigrationRunnerError(
                f"Could not determine whether migration "
                f"{migration.identifier} is applied: {exc}"
            ) from exc

        checksum = _calculate_checksum(migration)

        try:
            with self.database.transaction():
                self.database.execute(migration.up_sql)

                self.database.execute(
                    """
                    INSERT INTO schema_migrations
                        (version, name, checksum, applied_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        migration.version,
                        migration.name,
                        checksum,
                        _utc_timestamp(),
                    ),
                )
        except MigrationRunnerError:
            raise
        except DatabaseError as exc:
            raise MigrationRunnerError(
                f"Failed to apply migration "
                f"{migration.identifier}: {exc}"
            ) from exc

        return AppliedMigration(
            migration=migration,
            checksum=checksum,
        )

    def apply_all(
        self,
        migrations: list[Migration] | tuple[Migration, ...],
    ) -> list[AppliedMigration]:
        """Apply all pending migrations in version order."""
        ordered_migrations = sorted(
            migrations,
            key=lambda migration: migration.version,
        )

        pending = self.pending(ordered_migrations)

        applied: list[AppliedMigration] = []

        for migration in pending:
            applied.append(self.apply(migration))

        return applied


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
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat()