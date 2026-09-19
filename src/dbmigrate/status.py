"""Migration status inspection."""

from __future__ import annotations

from dataclasses import dataclass

from .history import MigrationRecord
from .migration import Migration


@dataclass(frozen=True)
class MigrationStatus:
    """Describe the relationship between migration files and history."""

    applied: list[Migration]
    pending: list[Migration]
    missing: list[MigrationRecord]

    @property
    def current(self) -> Migration | None:
        """Return the latest applied migration file."""
        if not self.applied:
            return None

        return self.applied[-1]

    @property
    def is_up_to_date(self) -> bool:
        """Return whether there are no pending or missing migrations."""
        return not self.pending and not self.missing

    @property
    def applied_count(self) -> int:
        """Return the number of applied migrations with files."""
        return len(self.applied)

    @property
    def pending_count(self) -> int:
        """Return the number of pending migrations."""
        return len(self.pending)

    @property
    def missing_count(self) -> int:
        """Return the number of history records without files."""
        return len(self.missing)


class MigrationStatusError(Exception):
    """Raised when migration status cannot be determined."""


class MigrationStatusInspector:
    """Inspect migration files against database history."""

    def __init__(self, runner) -> None:
        self.runner = runner

    def inspect(
        self,
        migrations: list[Migration] | tuple[Migration, ...],
    ) -> MigrationStatus:
        """Return the current migration status."""
        try:
            applied = self.runner.applied(migrations)
            pending = self.runner.pending(migrations)
        except Exception as exc:
            raise MigrationStatusError(
                f"Could not determine migration status: {exc}"
            ) from exc

        known_versions = {
            migration.version
            for migration in migrations
        }

        try:
            records = self.runner.history.list_applied()
        except Exception as exc:
            raise MigrationStatusError(
                f"Could not read migration history: {exc}"
            ) from exc

        missing = [
            record
            for record in records
            if record.version not in known_versions
        ]

        return MigrationStatus(
            applied=applied,
            pending=pending,
            missing=missing,
        )