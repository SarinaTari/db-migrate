"""Migration locking and concurrency control."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from types import TracebackType

from .database import Database, DatabaseError


class MigrationLockError(DatabaseError):
    """Raised when a migration lock cannot be acquired."""


class MigrationLock(ABC):
    """Abstract migration lock."""

    @abstractmethod
    def acquire(self) -> None:
        """Acquire the migration lock."""

    @abstractmethod
    def release(self) -> None:
        """Release the migration lock."""

    @abstractmethod
    def __enter__(self) -> "MigrationLock":
        """Acquire and return the lock."""

    @abstractmethod
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool:
        """Release the lock."""


class SQLiteMigrationLock(MigrationLock):
    """Filesystem-based migration lock for SQLite."""

    def __init__(
        self,
        database_path: Path,
    ) -> None:
        self.database_path = (
            database_path.expanduser().resolve()
        )
        self.lock_path = Path(
            f"{self.database_path}.dbmigrate.lock"
        )
        self._file = None

    @property
    def is_locked(self) -> bool:
        """Return whether this lock is currently held."""
        return self._file is not None

    def acquire(self) -> None:
        """Acquire an exclusive filesystem lock."""
        if self._file is not None:
            return

        try:
            import fcntl
        except ImportError as exc:
            raise MigrationLockError(
                "SQLite migration locking requires "
                "the platform fcntl module."
            ) from exc

        try:
            self.lock_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            file = self.lock_path.open(
                "a+",
                encoding="utf-8",
            )

            try:
                fcntl.flock(
                    file.fileno(),
                    fcntl.LOCK_EX | fcntl.LOCK_NB,
                )
            except BlockingIOError as exc:
                file.close()

                raise MigrationLockError(
                    "Another dbmigrate process is currently "
                    "running migrations for this database."
                ) from exc
            except OSError:
                file.close()
                raise

            self._file = file

        except MigrationLockError:
            raise
        except OSError as exc:
            raise MigrationLockError(
                f"Could not acquire SQLite migration lock "
                f"'{self.lock_path}': {exc}"
            ) from exc

    def release(self) -> None:
        """Release the filesystem lock."""
        if self._file is None:
            return

        file = self._file

        try:
            import fcntl

            fcntl.flock(
                file.fileno(),
                fcntl.LOCK_UN,
            )
            file.close()

        except OSError as exc:
            raise MigrationLockError(
                f"Could not release SQLite migration lock: "
                f"{exc}"
            ) from exc

        finally:
            self._file = None

    def __enter__(self) -> "SQLiteMigrationLock":
        self.acquire()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool:
        self.release()
        return False


class PostgreSQLMigrationLock(MigrationLock):
    """Advisory migration lock for PostgreSQL."""

    LOCK_KEY = 812739

    def __init__(
        self,
        database: Database,
    ) -> None:
        self.database = database
        self._acquired = False

    @property
    def is_locked(self) -> bool:
        """Return whether this lock is currently held."""
        return self._acquired

    def acquire(self) -> None:
        """Acquire the PostgreSQL advisory lock."""
        if self._acquired:
            return

        row = self.database.fetch_one(
            "SELECT pg_try_advisory_lock(%s)",
            (self.LOCK_KEY,),
        )

        if row is None or not bool(row[0]):
            raise MigrationLockError(
                "Another dbmigrate process is currently "
                "running migrations for this database."
            )

        self._acquired = True

    def release(self) -> None:
        """Release the PostgreSQL advisory lock."""
        if not self._acquired:
            return

        try:
            self.database.fetch_one(
                "SELECT pg_advisory_unlock(%s)",
                (self.LOCK_KEY,),
            )
        finally:
            self._acquired = False

    def __enter__(self) -> "PostgreSQLMigrationLock":
        self.acquire()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool:
        self.release()
        return False


class MySQLMigrationLock(MigrationLock):
    """Named migration lock for MySQL."""

    LOCK_NAME = "dbmigrate:migrations"
    TIMEOUT_SECONDS = 0

    def __init__(
        self,
        database: Database,
    ) -> None:
        self.database = database
        self._acquired = False

    @property
    def is_locked(self) -> bool:
        """Return whether this lock is currently held."""
        return self._acquired

    def acquire(self) -> None:
        """Acquire the MySQL named lock."""
        if self._acquired:
            return

        row = self.database.fetch_one(
            "SELECT GET_LOCK(%s, %s)",
            (
                self.LOCK_NAME,
                self.TIMEOUT_SECONDS,
            ),
        )

        if row is None or row[0] != 1:
            raise MigrationLockError(
                "Another dbmigrate process is currently "
                "running migrations for this database."
            )

        self._acquired = True

    def release(self) -> None:
        """Release the MySQL named lock."""
        if not self._acquired:
            return

        try:
            self.database.fetch_one(
                "SELECT RELEASE_LOCK(%s)",
                (self.LOCK_NAME,),
            )
        finally:
            self._acquired = False

    def __enter__(self) -> "MySQLMigrationLock":
        self.acquire()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool:
        self.release()
        return False


def create_migration_lock(
    database: Database,
) -> MigrationLock:
    """Create the appropriate migration lock."""

    if database.engine == "sqlite":
        path = getattr(
            database,
            "path",
            None,
        )

        if path is None:
            raise MigrationLockError(
                "SQLite database does not expose its "
                "database path."
            )

        return SQLiteMigrationLock(path)

    if database.engine == "postgresql":
        return PostgreSQLMigrationLock(
            database
        )

    if database.engine == "mysql":
        return MySQLMigrationLock(
            database
        )

    raise MigrationLockError(
        "Migration locking is not supported for "
        f"database engine '{database.engine}'."
    )