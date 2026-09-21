"""MySQL database implementation for dbmigrate."""

from __future__ import annotations

from types import TracebackType
from typing import Any, Iterable

from .database import Database, DatabaseError, Transaction
from .database_capabilities import DatabaseCapabilities
from .database_dialect import (
    DatabaseDialect,
    MySQLDialect,
)


class MySQLTransaction(Transaction):
    """Context manager for MySQL transactions."""

    def __init__(
        self,
        database: "MySQLDatabase",
    ) -> None:
        self.database = database

    def __enter__(self) -> "MySQLDatabase":
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


class MySQLDatabase(Database):
    """MySQL implementation of the database interface."""

    _CAPABILITIES = DatabaseCapabilities(
        transactional_ddl=False,
        drop_column=True,
        schemas=True,
        advisory_locks=True,
    )

    _DIALECT = MySQLDialect()

    def __init__(
        self,
        host: str,
        port: int,
        database: str,
        user: str,
        password: str,
    ) -> None:
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self._connection: Any = None

    @property
    def engine(self) -> str:
        """Return the database engine name."""
        return "mysql"

    @property
    def dialect(self) -> DatabaseDialect:
        """Return the MySQL SQL dialect."""
        return self._DIALECT

    @property
    def capabilities(self) -> DatabaseCapabilities:
        """Return MySQL capabilities."""
        return self._CAPABILITIES

    @property
    def connection(self) -> Any:
        """Return the active MySQL connection."""
        if self._connection is None:
            raise DatabaseError(
                "Database is not connected."
            )

        return self._connection

    @property
    def is_connected(self) -> bool:
        """Return whether a connection is open."""
        return self._connection is not None

    def connect(self) -> None:
        """Open the MySQL connection."""
        if self._connection is not None:
            return

        try:
            import mysql.connector

            self._connection = (
                mysql.connector.connect(
                    host=self.host,
                    port=self.port,
                    database=self.database,
                    user=self.user,
                    password=self.password,
                )
            )

        except ImportError as exc:
            raise DatabaseError(
                "MySQL support requires the "
                "'mysql-connector-python' package. "
                "Install it with "
                "'pip install dbmigrate[mysql]'."
            ) from exc

        except Exception as exc:
            self._connection = None

            raise DatabaseError(
                "Could not connect to MySQL database: "
                f"{exc}"
            ) from exc

    def close(self) -> None:
        """Close the MySQL connection."""
        if self._connection is None:
            return

        connection = self._connection
        self._connection = None

        try:
            connection.close()
        except Exception as exc:
            raise DatabaseError(
                f"Could not close MySQL database: {exc}"
            ) from exc

    def execute(
        self,
        sql: str,
        parameters: Iterable[Any] = (),
    ) -> None:
        """Execute SQL without returning rows."""
        cursor = None

        try:
            cursor = self.connection.cursor()
            cursor.execute(
                sql,
                tuple(parameters),
            )
        except Exception as exc:
            raise DatabaseError(
                f"MySQL execution failed: {exc}"
            ) from exc
        finally:
            if cursor is not None:
                cursor.close()

    def fetch_one(
        self,
        sql: str,
        parameters: Iterable[Any] = (),
    ) -> tuple[Any, ...] | None:
        """Execute SQL and return one row."""
        cursor = None

        try:
            cursor = self.connection.cursor()
            cursor.execute(
                sql,
                tuple(parameters),
            )

            row = cursor.fetchone()

            if row is None:
                return None

            return tuple(row)

        except Exception as exc:
            raise DatabaseError(
                f"MySQL query failed: {exc}"
            ) from exc
        finally:
            if cursor is not None:
                cursor.close()

    def fetch_all(
        self,
        sql: str,
        parameters: Iterable[Any] = (),
    ) -> list[tuple[Any, ...]]:
        """Execute SQL and return all rows."""
        cursor = None

        try:
            cursor = self.connection.cursor()
            cursor.execute(
                sql,
                tuple(parameters),
            )

            return [
                tuple(row)
                for row in cursor.fetchall()
            ]

        except Exception as exc:
            raise DatabaseError(
                f"MySQL query failed: {exc}"
            ) from exc
        finally:
            if cursor is not None:
                cursor.close()

    def commit(self) -> None:
        """Commit the current transaction."""
        try:
            self.connection.commit()
        except Exception as exc:
            raise DatabaseError(
                f"MySQL commit failed: {exc}"
            ) from exc

    def rollback(self) -> None:
        """Roll back the current transaction."""
        try:
            self.connection.rollback()
        except Exception as exc:
            raise DatabaseError(
                f"MySQL rollback failed: {exc}"
            ) from exc

    def begin(self) -> None:
        """Begin an explicit transaction."""
        try:
            self.connection.start_transaction()
        except Exception as exc:
            raise DatabaseError(
                f"Could not begin MySQL transaction: {exc}"
            ) from exc

    def version(self) -> str:
        """Return the MySQL version."""
        row = self.fetch_one(
            self.dialect.version_query()
        )

        if row is None:
            raise DatabaseError(
                "MySQL did not return a version."
            )

        return str(row[0])

    def transaction(self) -> MySQLTransaction:
        """Return a MySQL transaction context manager."""
        return MySQLTransaction(self)