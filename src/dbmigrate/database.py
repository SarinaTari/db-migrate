"""Database abstractions and SQLite implementation for dbmigrate."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
import sqlite3
from types import TracebackType
from typing import Any, Iterable, Self


class DatabaseError(Exception):
    """Raised when a database operation fails."""


class Database(ABC):
    """Abstract database interface used by dbmigrate."""

    @abstractmethod
    def connect(self) -> None:
        """Open a database connection."""

    @abstractmethod
    def close(self) -> None:
        """Close the database connection."""

    @abstractmethod
    def execute(
        self,
        sql: str,
        parameters: Iterable[Any] = (),
    ) -> None:
        """Execute SQL that does not need returned rows."""

    @abstractmethod
    def fetch_one(
        self,
        sql: str,
        parameters: Iterable[Any] = (),
    ) -> tuple[Any, ...] | None:
        """Execute SQL and return one row."""

    @abstractmethod
    def fetch_all(
        self,
        sql: str,
        parameters: Iterable[Any] = (),
    ) -> list[tuple[Any, ...]]:
        """Execute SQL and return all rows."""

    @abstractmethod
    def commit(self) -> None:
        """Commit the current transaction."""

    @abstractmethod
    def rollback(self) -> None:
        """Roll back the current transaction."""

    @abstractmethod
    def transaction(self) -> "Transaction":
        """Return a transaction context manager."""


class Transaction(ABC):
    """Abstract transaction context manager."""

    @abstractmethod
    def __enter__(self) -> Database:
        """Begin the transaction and return the database."""

    @abstractmethod
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool:
        """Commit or roll back the transaction."""


class SQLiteTransaction(Transaction):
    """Context manager for SQLite transactions."""

    def __init__(self, database: "SQLiteDatabase") -> None:
        self.database = database

    def __enter__(self) -> "SQLiteDatabase":
        self.database.begin()
        return self.database

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool:
        if exc_type is None:
            self.database.commit()
        else:
            self.database.rollback()

        return False


class SQLiteDatabase(Database):
    """SQLite implementation of the database interface."""

    def __init__(self, path: Path) -> None:
        self.path = path.expanduser().resolve()
        self._connection: sqlite3.Connection | None = None

    @property
    def connection(self) -> sqlite3.Connection:
        """Return the active SQLite connection."""
        if self._connection is None:
            raise DatabaseError("Database is not connected.")

        return self._connection

    @property
    def is_connected(self) -> bool:
        """Return whether a connection is currently open."""
        return self._connection is not None

    def connect(self) -> None:
        """Open the SQLite database connection."""
        if self._connection is not None:
            return

        try:
            self.path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            self._connection = sqlite3.connect(
                self.path,
                isolation_level=None,
            )

            self._connection.execute(
                "PRAGMA foreign_keys = ON"
            )

        except sqlite3.Error as exc:
            self._connection = None

            raise DatabaseError(
                f"Could not connect to SQLite database "
                f"'{self.path}': {exc}"
            ) from exc

        except OSError as exc:
            self._connection = None

            raise DatabaseError(
                f"Could not prepare SQLite database path "
                f"'{self.path}': {exc}"
            ) from exc

    def close(self) -> None:
        """Close the SQLite database connection."""
        if self._connection is None:
            return

        connection = self._connection
        self._connection = None

        try:
            connection.close()
        except sqlite3.Error as exc:
            raise DatabaseError(
                f"Could not close SQLite database "
                f"'{self.path}': {exc}"
            ) from exc

    def execute(
        self,
        sql: str,
        parameters: Iterable[Any] = (),
    ) -> None:
        """Execute SQL without returning rows."""
        try:
            self.connection.execute(
                sql,
                tuple(parameters),
            )
        except sqlite3.Error as exc:
            raise DatabaseError(
                f"SQLite execution failed: {exc}"
            ) from exc

    def fetch_one(
        self,
        sql: str,
        parameters: Iterable[Any] = (),
    ) -> tuple[Any, ...] | None:
        """Execute SQL and return one row."""
        try:
            cursor = self.connection.execute(
                sql,
                tuple(parameters),
            )

            try:
                return cursor.fetchone()
            finally:
                cursor.close()

        except sqlite3.Error as exc:
            raise DatabaseError(
                f"SQLite query failed: {exc}"
            ) from exc

    def fetch_all(
        self,
        sql: str,
        parameters: Iterable[Any] = (),
    ) -> list[tuple[Any, ...]]:
        """Execute SQL and return all rows."""
        try:
            cursor = self.connection.execute(
                sql,
                tuple(parameters),
            )

            try:
                return cursor.fetchall()
            finally:
                cursor.close()

        except sqlite3.Error as exc:
            raise DatabaseError(
                f"SQLite query failed: {exc}"
            ) from exc

    def commit(self) -> None:
        """Commit the current transaction."""
        try:
            self.connection.commit()
        except sqlite3.Error as exc:
            raise DatabaseError(
                f"SQLite commit failed: {exc}"
            ) from exc

    def rollback(self) -> None:
        """Roll back the current transaction."""
        try:
            self.connection.rollback()
        except sqlite3.Error as exc:
            raise DatabaseError(
                f"SQLite rollback failed: {exc}"
            ) from exc

    def begin(self) -> None:
        """Begin an explicit transaction."""
        try:
            self.connection.execute("BEGIN")
        except sqlite3.Error as exc:
            raise DatabaseError(
                f"Could not begin SQLite transaction: {exc}"
            ) from exc

    def transaction(self) -> SQLiteTransaction:
        """Return a SQLite transaction context manager."""
        return SQLiteTransaction(self)