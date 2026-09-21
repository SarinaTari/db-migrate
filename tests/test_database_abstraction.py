from pathlib import Path

from dbmigrate.database import (
    Database,
    SQLiteDatabase,
)


def test_sqlite_implements_database_interface(
    tmp_path: Path,
):
    database = SQLiteDatabase(
        tmp_path / "test.db"
    )

    assert isinstance(
        database,
        Database,
    )


def test_database_engine(
    tmp_path: Path,
):
    database = SQLiteDatabase(
        tmp_path / "test.db"
    )

    assert database.engine == "sqlite"


def test_database_capabilities(
    tmp_path: Path,
):
    database = SQLiteDatabase(
        tmp_path / "test.db"
    )

    assert database.capabilities.transactional_ddl
    assert database.capabilities.drop_column
    assert not database.capabilities.schemas
    assert not database.capabilities.advisory_locks


def test_database_version(
    tmp_path: Path,
):
    database = SQLiteDatabase(
        tmp_path / "test.db"
    )

    database.connect()

    try:
        version = database.version()

        assert version
        assert isinstance(version, str)
    finally:
        database.close()


def test_transaction_commits(
    tmp_path: Path,
):
    database = SQLiteDatabase(
        tmp_path / "test.db"
    )

    database.connect()

    try:
        with database.transaction():
            database.execute(
                """
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL
                )
                """
            )

        row = database.fetch_one(
            "SELECT name FROM sqlite_master "
            "WHERE type = 'table' "
            "AND name = 'users'"
        )

        assert row is not None
    finally:
        database.close()


def test_transaction_rolls_back(
    tmp_path: Path,
):
    database = SQLiteDatabase(
        tmp_path / "test.db"
    )

    database.connect()

    try:
        database.execute(
            """
            CREATE TABLE users (
                id INTEGER PRIMARY KEY
            )
            """
        )

        try:
            with database.transaction():
                database.execute(
                    "INSERT INTO users VALUES (1)"
                )

                raise RuntimeError(
                    "test rollback"
                )
        except RuntimeError:
            pass

        row = database.fetch_one(
            "SELECT COUNT(*) FROM users"
        )

        assert row == (0,)
    finally:
        database.close()