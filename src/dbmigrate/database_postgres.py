"""PostgreSQL database implementation for dbmigrate."""

from __future__ import annotations

from types import TracebackType
from typing import Any, Iterable

from .database import Database, DatabaseError, Transaction
from .database_capabilities import DatabaseCapabilities
from .database_dialect import (
    DatabaseDialect,
    PostgreSQLDialect,
)


class PostgreSQLTransaction(Transaction):
    """Context manager for PostgreSQL transactions."""

    def __init__(
        self,
        database: "PostgreSQLDatabase",
    ) -> None:
        self.database = database

    def __enter__(self) -> "PostgreSQLDatabase":
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


class PostgreSQLDatabase(Database):
    """PostgreSQL implementation of the database interface."""

    _CAPABILITIES = DatabaseCapabilities(
        transactional_ddl=True,
        drop_column=True,
        schemas=True,
        advisory_locks=True,
    )

    _DIALECT = PostgreSQLDialect()

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
        return "postgresql"

    @property
    def dialect(self) -> DatabaseDialect:
        """Return the PostgreSQL SQL dialect."""
        return self._DIALECT

    @property
    def capabilities(self) -> DatabaseCapabilities:
        """Return PostgreSQL capabilities."""
        return self._CAPABILITIES

    @property
    def connection(self) -> Any:
        """Return the active PostgreSQL connection."""
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
        """Open the PostgreSQL connection."""
        if self._connection is not None:
            return

        try:
            import psycopg

            self._connection = psycopg.connect(
                host=self.host,
                port=self.port,
                dbname=self.database,
                user=self.user,
                password=self.password,
                autocommit=True,
            )

        except ImportError as exc:
            raise DatabaseError(
                "PostgreSQL support requires the "
                "'psycopg' package. Install it with "
                "'pip install dbmigrate[postgresql]'."
            ) from exc

        except Exception as exc:
            self._connection = None

            raise DatabaseError(
                "Could not connect to PostgreSQL database: "
                f"{exc}"
            ) from exc

    def close(self) -> None:
        """Close the PostgreSQL connection."""
        if self._connection is None:
            return

        connection = self._connection
        self._connection = None

        try:
            connection.close()
        except Exception as exc:
            raise DatabaseError(
                f"Could not close PostgreSQL database: {exc}"
            ) from exc

    def execute(
        self,
        sql: str,
        parameters: Iterable[Any] = (),
    ) -> None:
        """Execute SQL without returning rows."""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(
                    sql,
                    tuple(parameters),
                )
        except Exception as exc:
            raise DatabaseError(
                f"PostgreSQL execution failed: {exc}"
            ) from exc

    def fetch_one(
        self,
        sql: str,
        parameters: Iterable[Any] = (),
    ) -> tuple[Any, ...] | None:
        """Execute SQL and return one row."""
        try:
            with self.connection.cursor() as cursor:
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
                f"PostgreSQL query failed: {exc}"
            ) from exc

    def fetch_all(
        self,
        sql: str,
        parameters: Iterable[Any] = (),
    ) -> list[tuple[Any, ...]]:
        """Execute SQL and return all rows."""
        try:
            with self.connection.cursor() as cursor:
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
                f"PostgreSQL query failed: {exc}"
            ) from exc

    def commit(self) -> None:
        """Commit the current transaction."""
        try:
            self.connection.commit()
        except Exception as exc:
            raise DatabaseError(
                f"PostgreSQL commit failed: {exc}"
            ) from exc

    def rollback(self) -> None:
        """Roll back the current transaction."""
        try:
            self.connection.rollback()
        except Exception as exc:
            raise DatabaseError(
                f"PostgreSQL rollback failed: {exc}"
            ) from exc

    def begin(self) -> None:
        """Begin an explicit transaction."""
        try:
            self.connection.execute(
                "BEGIN"
            )
        except Exception as exc:
            raise DatabaseError(
                f"Could not begin PostgreSQL "
                f"transaction: {exc}"
            ) from exc

    def version(self) -> str:
        """Return the PostgreSQL version."""
        row = self.fetch_one(
            self.dialect.version_query()
        )

        if row is None:
            raise DatabaseError(
                "PostgreSQL did not return a version."
            )

        return str(row[0])

    def transaction(self) -> PostgreSQLTransaction:
        """Return a PostgreSQL transaction context manager."""
        return PostgreSQLTransaction(self)