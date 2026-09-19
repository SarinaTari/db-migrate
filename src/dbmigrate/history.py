"""Migration history management."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from .database import Database, DatabaseError


HISTORY_TABLE = "schema_migrations"

CREATE_HISTORY_TABLE_SQL = f"""
CREATE TABLE IF NOT EXISTS {HISTORY_TABLE} (
    version INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    checksum TEXT NOT NULL,
    applied_at TEXT NOT NULL
)
"""


class HistoryError(Exception):
    """Raised when migration history cannot be managed."""


@dataclass(frozen=True)
class MigrationRecord:
    """A record of an applied migration."""

    version: int
    name: str
    checksum: str
    applied_at: str


class MigrationHistory:
    """Manage the database migration history."""

    def __init__(self, database: Database) -> None:
        self.database = database

    def initialize(self) -> None:
        """Create the migration history table if necessary."""
        try:
            self.database.execute(CREATE_HISTORY_TABLE_SQL)
        except DatabaseError as exc:
            raise HistoryError(
                f"Could not initialize migration history: {exc}"
            ) from exc

    def record(
        self,
        version: int,
        name: str,
        checksum: str,
        applied_at: str | None = None,
    ) -> MigrationRecord:
        """Record an applied migration."""
        if version < 1:
            raise HistoryError(
                "Migration version must be greater than zero."
            )

        if not name:
            raise HistoryError(
                "Migration name must not be empty."
            )

        if not checksum:
            raise HistoryError(
                "Migration checksum must not be empty."
            )

        self.initialize()

        timestamp = applied_at or _utc_timestamp()

        try:
            self.database.execute(
                f"""
                INSERT INTO {HISTORY_TABLE}
                    (version, name, checksum, applied_at)
                VALUES (?, ?, ?, ?)
                """,
                (version, name, checksum, timestamp),
            )
        except DatabaseError as exc:
            raise HistoryError(
                f"Could not record migration {version:03d}: {exc}"
            ) from exc

        return MigrationRecord(
            version=version,
            name=name,
            checksum=checksum,
            applied_at=timestamp,
        )

    def remove(self, version: int) -> None:
        """Remove a migration from the history."""
        if version < 1:
            raise HistoryError(
                "Migration version must be greater than zero."
            )

        self.initialize()

        try:
            self.database.execute(
                f"""
                DELETE FROM {HISTORY_TABLE}
                WHERE version = ?
                """,
                (version,),
            )
        except DatabaseError as exc:
            raise HistoryError(
                f"Could not remove migration {version:03d}: {exc}"
            ) from exc

    def is_applied(self, version: int) -> bool:
        """Return whether a migration version is recorded as applied."""
        if version < 1:
            raise HistoryError(
                "Migration version must be greater than zero."
            )

        self.initialize()

        try:
            row = self.database.fetch_one(
                f"""
                SELECT 1
                FROM {HISTORY_TABLE}
                WHERE version = ?
                """,
                (version,),
            )
        except DatabaseError as exc:
            raise HistoryError(
                f"Could not check migration {version:03d}: {exc}"
            ) from exc

        return row is not None

    def get(self, version: int) -> MigrationRecord | None:
        """Return a migration record by version."""
        if version < 1:
            raise HistoryError(
                "Migration version must be greater than zero."
            )

        self.initialize()

        try:
            row = self.database.fetch_one(
                f"""
                SELECT version, name, checksum, applied_at
                FROM {HISTORY_TABLE}
                WHERE version = ?
                """,
                (version,),
            )
        except DatabaseError as exc:
            raise HistoryError(
                f"Could not retrieve migration {version:03d}: {exc}"
            ) from exc

        if row is None:
            return None

        return MigrationRecord(
            version=int(row[0]),
            name=str(row[1]),
            checksum=str(row[2]),
            applied_at=str(row[3]),
        )

    def list_applied(self) -> list[MigrationRecord]:
        """Return all applied migrations in version order."""
        self.initialize()

        try:
            rows = self.database.fetch_all(
                f"""
                SELECT version, name, checksum, applied_at
                FROM {HISTORY_TABLE}
                ORDER BY version ASC
                """
            )
        except DatabaseError as exc:
            raise HistoryError(
                f"Could not list migration history: {exc}"
            ) from exc

        return [
            MigrationRecord(
                version=int(row[0]),
                name=str(row[1]),
                checksum=str(row[2]),
                applied_at=str(row[3]),
            )
            for row in rows
        ]

    def latest(self) -> MigrationRecord | None:
        """Return the most recently applied migration by version."""
        self.initialize()

        try:
            row = self.database.fetch_one(
                f"""
                SELECT version, name, checksum, applied_at
                FROM {HISTORY_TABLE}
                ORDER BY version DESC
                LIMIT 1
                """
            )
        except DatabaseError as exc:
            raise HistoryError(
                f"Could not retrieve latest migration: {exc}"
            ) from exc

        if row is None:
            return None

        return MigrationRecord(
            version=int(row[0]),
            name=str(row[1]),
            checksum=str(row[2]),
            applied_at=str(row[3]),
        )


def _utc_timestamp() -> str:
    """Return the current UTC timestamp in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat()