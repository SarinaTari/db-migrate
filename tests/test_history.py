"""Tests for migration history management."""

from pathlib import Path

import pytest

from dbmigrate.database import SQLiteDatabase
from dbmigrate.history import (
    HISTORY_TABLE,
    HistoryError,
    MigrationHistory,
)


def create_database(tmp_path: Path) -> SQLiteDatabase:
    """Create and connect a temporary SQLite database."""
    database = SQLiteDatabase(tmp_path / "test.db")
    database.connect()
    return database


def test_initialize_creates_history_table(tmp_path: Path) -> None:
    database = create_database(tmp_path)

    try:
        history = MigrationHistory(database)

        history.initialize()

        row = database.fetch_one(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name = ?
            """,
            (HISTORY_TABLE,),
        )

        assert row == (HISTORY_TABLE,)
    finally:
        database.close()


def test_initialize_is_idempotent(tmp_path: Path) -> None:
    database = create_database(tmp_path)

    try:
        history = MigrationHistory(database)

        history.initialize()
        history.initialize()

        assert history.list_applied() == []
    finally:
        database.close()


def test_record_and_get_migration(tmp_path: Path) -> None:
    database = create_database(tmp_path)

    try:
        history = MigrationHistory(database)

        record = history.record(
            version=1,
            name="create_users",
            checksum="abc123",
            applied_at="2026-01-01T12:00:00+00:00",
        )

        assert record.version == 1
        assert record.name == "create_users"
        assert record.checksum == "abc123"
        assert record.applied_at == "2026-01-01T12:00:00+00:00"

        stored = history.get(1)

        assert stored == record
    finally:
        database.close()


def test_is_applied(tmp_path: Path) -> None:
    database = create_database(tmp_path)

    try:
        history = MigrationHistory(database)

        assert history.is_applied(1) is False

        history.record(
            version=1,
            name="create_users",
            checksum="abc123",
        )

        assert history.is_applied(1) is True
    finally:
        database.close()


def test_list_applied_orders_by_version(tmp_path: Path) -> None:
    database = create_database(tmp_path)

    try:
        history = MigrationHistory(database)

        history.record(
            version=2,
            name="add_email",
            checksum="bbb",
        )

        history.record(
            version=1,
            name="create_users",
            checksum="aaa",
        )

        records = history.list_applied()

        assert [record.version for record in records] == [1, 2]
        assert [record.name for record in records] == [
            "create_users",
            "add_email",
        ]
    finally:
        database.close()


def test_latest_returns_highest_version(tmp_path: Path) -> None:
    database = create_database(tmp_path)

    try:
        history = MigrationHistory(database)

        history.record(
            version=1,
            name="create_users",
            checksum="aaa",
        )

        history.record(
            version=2,
            name="add_email",
            checksum="bbb",
        )

        latest = history.latest()

        assert latest is not None
        assert latest.version == 2
        assert latest.name == "add_email"
    finally:
        database.close()


def test_latest_returns_none_for_empty_history(
    tmp_path: Path,
) -> None:
    database = create_database(tmp_path)

    try:
        history = MigrationHistory(database)

        assert history.latest() is None
    finally:
        database.close()


def test_remove_migration(tmp_path: Path) -> None:
    database = create_database(tmp_path)

    try:
        history = MigrationHistory(database)

        history.record(
            version=1,
            name="create_users",
            checksum="abc123",
        )

        assert history.is_applied(1) is True

        history.remove(1)

        assert history.is_applied(1) is False
        assert history.get(1) is None
    finally:
        database.close()


def test_duplicate_version_is_rejected(tmp_path: Path) -> None:
    database = create_database(tmp_path)

    try:
        history = MigrationHistory(database)

        history.record(
            version=1,
            name="create_users",
            checksum="abc123",
        )

        with pytest.raises(HistoryError):
            history.record(
                version=1,
                name="different_name",
                checksum="different",
            )
    finally:
        database.close()


@pytest.mark.parametrize(
    "version",
    [0, -1],
)
def test_invalid_version_is_rejected(
    tmp_path: Path,
    version: int,
) -> None:
    database = create_database(tmp_path)

    try:
        history = MigrationHistory(database)

        with pytest.raises(HistoryError):
            history.record(
                version=version,
                name="invalid",
                checksum="abc123",
            )
    finally:
        database.close()


def test_empty_name_is_rejected(tmp_path: Path) -> None:
    database = create_database(tmp_path)

    try:
        history = MigrationHistory(database)

        with pytest.raises(HistoryError):
            history.record(
                version=1,
                name="",
                checksum="abc123",
            )
    finally:
        database.close()


def test_empty_checksum_is_rejected(tmp_path: Path) -> None:
    database = create_database(tmp_path)

    try:
        history = MigrationHistory(database)

        with pytest.raises(HistoryError):
            history.record(
                version=1,
                name="create_users",
                checksum="",
            )
    finally:
        database.close()