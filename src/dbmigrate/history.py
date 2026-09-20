"""Migration history management."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

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
    """Raised when migration history operations fail."""


@dataclass(frozen=True)
class MigrationRecord:
    """Represent a migration stored in database history."""

    version: int
    name: str
    checksum: str
    applied_at: str


class MigrationHistory:
    """Manage applied migration records."""

    def __init__(
        self,
        database: Database,
    ) -> None:
        self.database = database

    def initialize(self) -> None:
        """Create the migration history table."""
        try:
            self.database.execute(
                CREATE_HISTORY_TABLE_SQL
            )
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
        self._validate_version(version)
        self._validate_name(name)
        self._validate_checksum(checksum)

        self.initialize()

        timestamp = (
            applied_at
            if applied_at is not None
            else self._utc_timestamp()
        )

        try:
            self.database.execute(
                f"""
                INSERT INTO {HISTORY_TABLE}
                (version, name, checksum, applied_at)
                VALUES (?, ?, ?, ?)
                """,
                (
                    version,
                    name,
                    checksum,
                    timestamp,
                ),
            )
        except DatabaseError as exc:
            raise HistoryError(
                f"Could not record migration "
                f"{version:03d}: {exc}"
            ) from exc

        return MigrationRecord(
            version=version,
            name=name,
            checksum=checksum,
            applied_at=timestamp,
        )

    def remove(
        self,
        version: int,
    ) -> None:
        """Remove a migration history record."""
        self._validate_version(version)

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
                f"Could not remove migration "
                f"{version:03d}: {exc}"
            ) from exc

    def is_applied(
        self,
        version: int,
    ) -> bool:
        """Return whether a migration version is applied."""
        self._validate_version(version)

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
                f"Could not check migration "
                f"{version:03d}: {exc}"
            ) from exc

        return row is not None

    def get(
        self,
        version: int,
    ) -> MigrationRecord | None:
        """Return a migration history record."""
        self._validate_version(version)

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
                f"Could not retrieve migration "
                f"{version:03d}: {exc}"
            ) from exc

        if row is None:
            return None

        return self._record_from_row(
            row
        )

    def list_applied(self) -> list[MigrationRecord]:
        """Return applied migrations in version order."""
        self.initialize()

        try:
            rows = self.database.fetch_all(
                f"""
                SELECT version, name, checksum, applied_at
                FROM {HISTORY_TABLE}
                ORDER BY version
                """
            )
        except DatabaseError as exc:
            raise HistoryError(
                f"Could not list migration history: {exc}"
            ) from exc

        return [
            self._record_from_row(row)
            for row in rows
        ]

    def latest(self) -> MigrationRecord | None:
        """Return the latest applied migration."""
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

        return self._record_from_row(
            row
        )

    @staticmethod
    def _record_from_row(
        row: Any,
    ) -> MigrationRecord:
        """Convert a database row to a migration record."""
        return MigrationRecord(
            version=int(row[0]),
            name=str(row[1]),
            checksum=str(row[2]),
            applied_at=str(row[3]),
        )

    @staticmethod
    def _validate_version(
        version: int,
    ) -> None:
        """Validate a migration version."""
        if not isinstance(version, int):
            raise HistoryError(
                "Migration version must be an integer."
            )

        if version <= 0:
            raise HistoryError(
                "Migration version must be greater than zero."
            )

    @staticmethod
    def _validate_name(
        name: str,
    ) -> None:
        """Validate a migration name."""
        if not isinstance(name, str):
            raise HistoryError(
                "Migration name must be a string."
            )

        if not name.strip():
            raise HistoryError(
                "Migration name must not be empty."
            )

    @staticmethod
    def _validate_checksum(
        checksum: str,
    ) -> None:
        """Validate a migration checksum."""
        if not isinstance(checksum, str):
            raise HistoryError(
                "Migration checksum must be a string."
            )

        if not checksum.strip():
            raise HistoryError(
                "Migration checksum must not be empty."
            )

    @staticmethod
    def _utc_timestamp() -> str:
        """Return the current UTC timestamp."""
        return datetime.now(
            timezone.utc
        ).isoformat()