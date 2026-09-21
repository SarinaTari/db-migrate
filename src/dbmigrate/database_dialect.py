"""SQL dialect definitions for dbmigrate."""

from __future__ import annotations

from abc import ABC, abstractmethod


class DialectError(Exception):
    """Raised when a SQL dialect operation fails."""


class DatabaseDialect(ABC):
    """Abstract SQL dialect used by database adapters."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the dialect name."""

    @property
    @abstractmethod
    def parameter_placeholder(self) -> str:
        """Return the parameter placeholder."""

    @abstractmethod
    def quote_identifier(self, identifier: str) -> str:
        """Quote a SQL identifier."""

    @abstractmethod
    def version_query(self) -> str:
        """Return the query used to obtain database version."""


class SQLiteDialect(DatabaseDialect):
    """SQLite SQL dialect."""

    @property
    def name(self) -> str:
        return "sqlite"

    @property
    def parameter_placeholder(self) -> str:
        return "?"

    def quote_identifier(self, identifier: str) -> str:
        if not identifier:
            raise DialectError(
                "Identifier cannot be empty."
            )

        escaped = identifier.replace(
            '"',
            '""',
        )

        return f'"{escaped}"'

    def version_query(self) -> str:
        return "SELECT sqlite_version()"


class PostgreSQLDialect(DatabaseDialect):
    """PostgreSQL SQL dialect."""

    @property
    def name(self) -> str:
        return "postgresql"

    @property
    def parameter_placeholder(self) -> str:
        return "%s"

    def quote_identifier(self, identifier: str) -> str:
        if not identifier:
            raise DialectError(
                "Identifier cannot be empty."
            )

        escaped = identifier.replace(
            '"',
            '""',
        )

        return f'"{escaped}"'

    def version_query(self) -> str:
        return "SELECT version()"


class MySQLDialect(DatabaseDialect):
    """MySQL SQL dialect."""

    @property
    def name(self) -> str:
        return "mysql"

    @property
    def parameter_placeholder(self) -> str:
        return "%s"

    def quote_identifier(self, identifier: str) -> str:
        if not identifier:
            raise DialectError(
                "Identifier cannot be empty."
            )

        escaped = identifier.replace(
            "`",
            "``",
        )

        return f"`{escaped}`"

    def version_query(self) -> str:
        return "SELECT VERSION()"