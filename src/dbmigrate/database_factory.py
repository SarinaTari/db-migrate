"""Database URL parsing and database adapter creation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from .database import Database, DatabaseError, SQLiteDatabase
from .database_mysql import MySQLDatabase
from .database_postgres import PostgreSQLDatabase


@dataclass(frozen=True)
class DatabaseURL:
    """Parsed database connection URL."""

    scheme: str
    host: str | None
    port: int | None
    database: str
    username: str | None
    password: str | None


def parse_database_url(
    database_url: str,
) -> DatabaseURL:
    """Parse a database connection URL."""

    if not database_url:
        raise DatabaseError(
            "Database URL cannot be empty."
        )

    parsed = urlparse(database_url)

    scheme = parsed.scheme.lower()

    if scheme == "postgres":
        scheme = "postgresql"

    if scheme not in {
        "sqlite",
        "postgresql",
        "mysql",
    }:
        raise DatabaseError(
            f"Unsupported database scheme: {parsed.scheme}"
        )

    if scheme == "sqlite":
        if parsed.netloc:
            raise DatabaseError(
                "SQLite database URLs must use the "
                "sqlite:///path format."
            )

        raw_path = parsed.path

        if not raw_path:
            raise DatabaseError(
                "SQLite database path is empty."
            )

        return DatabaseURL(
            scheme="sqlite",
            host=None,
            port=None,
            database=raw_path,
            username=None,
            password=None,
        )

    if not parsed.hostname:
        raise DatabaseError(
            f"{scheme} database URL requires a host."
        )

    if not parsed.path or parsed.path == "/":
        raise DatabaseError(
            f"{scheme} database URL requires a database name."
        )

    if not parsed.username:
        raise DatabaseError(
            f"{scheme} database URL requires a username."
        )

    if parsed.password is None:
        raise DatabaseError(
            f"{scheme} database URL requires a password."
        )

    return DatabaseURL(
        scheme=scheme,
        host=parsed.hostname,
        port=parsed.port,
        database=parsed.path.lstrip("/"),
        username=parsed.username,
        password=parsed.password,
    )


def create_database(
    database_url: str,
) -> Database:
    """Create a database adapter from a database URL."""

    parsed = parse_database_url(
        database_url
    )

    if parsed.scheme == "sqlite":
        path = Path(parsed.database)

        # sqlite:///database.db means a path relative
        # to the current working directory.
        #
        # sqlite:////tmp/database.db means an absolute
        # filesystem path.
        if (
            parsed.database.startswith("/")
            and not database_url.startswith("sqlite:////")
        ):
            path = Path(
                parsed.database.lstrip("/")
            )

        if not path.is_absolute():
            path = Path.cwd() / path

        return SQLiteDatabase(path)

    if parsed.scheme == "postgresql":
        return PostgreSQLDatabase(
            host=parsed.host,
            port=parsed.port or 5432,
            database=parsed.database,
            user=parsed.username,
            password=parsed.password,
        )

    if parsed.scheme == "mysql":
        return MySQLDatabase(
            host=parsed.host,
            port=parsed.port or 3306,
            database=parsed.database,
            user=parsed.username,
            password=parsed.password,
        )

    raise DatabaseError(
        f"Unsupported database scheme: {parsed.scheme}"
    )