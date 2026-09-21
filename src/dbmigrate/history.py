"""Migration history storage."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from .database import Database, DatabaseError


HISTORY_TABLE = "schema_migrations"


class HistoryError(Exception):
    """Raised when migration history operations fail."""


@dataclass(frozen=True)
class MigrationRecord:
    """Represent one applied migration."""

    version: int
    name: str
    checksum: str
    applied_at: str


class MigrationHistory:
    """Manage the schema_migrations table."""

    TABLE_NAME = HISTORY_TABLE

    def __init__(self, database: Database) -> None:
        self.database = database
        self._initialized = False

    def initialize(self) -> None:
        """Create the migration history table if necessary."""
        if self._initialized:
            return

        try:
            self.database.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {self.TABLE_NAME} (
                    version INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    checksum TEXT NOT NULL,
                    applied_at TIMESTAMP NOT NULL
                )
                """
            )
        except DatabaseError as exc:
            raise HistoryError(
                f"Could not initialize migration history: {exc}"
            ) from exc

        self._initialized = True

    def record(
        self,
        version: int,
        name: str,
        checksum: str,
        applied_at: str | None = None,
    ) -> MigrationRecord:
        """Record an applied migration."""
        self.initialize()
        _validate_version(version)

        if not name.strip():
            raise HistoryError(
                "Migration name must not be empty."
            )

        if not checksum.strip():
            raise HistoryError(
                "Migration checksum must not be empty."
            )

        if applied_at is None:
            applied_at = _utc_timestamp()

        placeholder = self.database.dialect.parameter_placeholder

        try:
            self.database.execute(
                f"""
                INSERT INTO {self.TABLE_NAME}
                    (version, name, checksum, applied_at)
                VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder})
                """,
                (
                    version,
                    name,
                    checksum,
                    applied_at,
                ),
            )
        except DatabaseError as exc:
            raise HistoryError(
                f"Could not record migration {version}: {exc}"
            ) from exc

        return MigrationRecord(
            version=version,
            name=name,
            checksum=checksum,
            applied_at=applied_at,
        )

    def remove(self, version: int) -> None:
        """Remove a migration from history."""
        self.initialize()
        _validate_version(version)

        placeholder = self.database.dialect.parameter_placeholder

        try:
            self.database.execute(
                f"""
                DELETE FROM {self.TABLE_NAME}
                WHERE version = {placeholder}
                """,
                (version,),
            )
        except DatabaseError as exc:
            raise HistoryError(
                f"Could not remove migration {version}: {exc}"
            ) from exc

    def is_applied(self, version: int) -> bool:
        """Return whether a migration version is applied."""
        self.initialize()
        _validate_version(version)

        placeholder = self.database.dialect.parameter_placeholder

        try:
            row = self.database.fetch_one(
                f"""
                SELECT version
                FROM {self.TABLE_NAME}
                WHERE version = {placeholder}
                """,
                (version,),
            )
        except DatabaseError as exc:
            raise HistoryError(
                f"Could not inspect migration history: {exc}"
            ) from exc

        return row is not None

    def get(self, version: int) -> MigrationRecord | None:
        """Return one history record."""
        self.initialize()
        _validate_version(version)

        placeholder = self.database.dialect.parameter_placeholder

        try:
            row = self.database.fetch_one(
                f"""
                SELECT version, name, checksum, applied_at
                FROM {self.TABLE_NAME}
                WHERE version = {placeholder}
                """,
                (version,),
            )
        except DatabaseError as exc:
            raise HistoryError(
                f"Could not inspect migration history: {exc}"
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
        """Return applied migrations in version order."""
        self.initialize()

        try:
            rows = self.database.fetch_all(
                f"""
                SELECT version, name, checksum, applied_at
                FROM {self.TABLE_NAME}
                ORDER BY version
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

    def applied_versions(self) -> set[int]:
        """Return applied migration versions."""
        return {
            record.version
            for record in self.list_applied()
        }

    def latest(self) -> MigrationRecord | None:
        """Return the most recently applied migration."""
        self.initialize()

        try:
            row = self.database.fetch_one(
                f"""
                SELECT version, name, checksum, applied_at
                FROM {self.TABLE_NAME}
                ORDER BY version DESC
                LIMIT 1
                """
            )
        except DatabaseError as exc:
            raise HistoryError(
                f"Could not inspect migration history: {exc}"
            ) from exc

        if row is None:
            return None

        return MigrationRecord(
            version=int(row[0]),
            name=str(row[1]),
            checksum=str(row[2]),
            applied_at=str(row[3]),
        )


def _validate_version(version: int) -> None:
    """Validate a migration version."""
    if version <= 0:
        raise HistoryError(
            "Migration version must be greater than zero."
        )


def _utc_timestamp() -> str:
    """Return the current UTC timestamp."""
    return datetime.now(timezone.utc).isoformat()