"""Tests for migration history."""

from pathlib import Path

import pytest

from dbmigrate.database import SQLiteDatabase
from dbmigrate.history import (
    HISTORY_TABLE,
    HistoryError,
    MigrationHistory,
)


def create_database(
    tmp_path: Path,
) -> SQLiteDatabase:
    database = SQLiteDatabase(
        tmp_path / "test.db"
    )
    database.connect()
    return database


def test_initialize_creates_history_table(
    tmp_path: Path,
):
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


def test_initialize_is_idempotent(
    tmp_path: Path,
):
    database = create_database(tmp_path)

    try:
        history = MigrationHistory(database)

        history.initialize()
        history.initialize()

        row = database.fetch_one(
            f"""
            SELECT COUNT(*)
            FROM {HISTORY_TABLE}
            """
        )

        assert row == (0,)
    finally:
        database.close()


def test_record_and_get_migration(
    tmp_path: Path,
):
    database = create_database(tmp_path)

    try:
        history = MigrationHistory(database)

        record = history.record(
            version=1,
            name="create_users",
            checksum="abc123",
            applied_at="2026-01-01T00:00:00+00:00",
        )

        assert record.version == 1
        assert record.name == "create_users"
        assert record.checksum == "abc123"
        assert (
            record.applied_at
            == "2026-01-01T00:00:00+00:00"
        )

        loaded = history.get(1)

        assert loaded == record
    finally:
        database.close()


def test_record_generates_timestamp_when_not_provided(
    tmp_path: Path,
):
    database = create_database(tmp_path)

    try:
        history = MigrationHistory(database)

        record = history.record(
            version=1,
            name="create_users",
            checksum="abc123",
        )

        assert record.applied_at
        assert "T" in record.applied_at
    finally:
        database.close()


def test_is_applied_returns_true_for_recorded_migration(
    tmp_path: Path,
):
    database = create_database(tmp_path)

    try:
        history = MigrationHistory(database)

        history.record(
            version=1,
            name="create_users",
            checksum="abc123",
        )

        assert history.is_applied(1)
    finally:
        database.close()


def test_is_applied_returns_false_for_unrecorded_migration(
    tmp_path: Path,
):
    database = create_database(tmp_path)

    try:
        history = MigrationHistory(database)

        assert not history.is_applied(1)
    finally:
        database.close()


def test_list_applied_returns_migrations_in_version_order(
    tmp_path: Path,
):
    database = create_database(tmp_path)

    try:
        history = MigrationHistory(database)

        history.record(
            version=2,
            name="add_email",
            checksum="bbb",
            applied_at="2026-01-02T00:00:00+00:00",
        )

        history.record(
            version=1,
            name="create_users",
            checksum="aaa",
            applied_at="2026-01-01T00:00:00+00:00",
        )

        records = history.list_applied()

        assert [
            record.version
            for record in records
        ] == [1, 2]
    finally:
        database.close()


def test_latest_returns_highest_version(
    tmp_path: Path,
):
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
        assert latest.checksum == "bbb"
    finally:
        database.close()


def test_latest_returns_none_when_empty(
    tmp_path: Path,
):
    database = create_database(tmp_path)

    try:
        history = MigrationHistory(database)

        assert history.latest() is None
    finally:
        database.close()


def test_remove_migration(
    tmp_path: Path,
):
    database = create_database(tmp_path)

    try:
        history = MigrationHistory(database)

        history.record(
            version=1,
            name="create_users",
            checksum="abc123",
        )

        assert history.is_applied(1)

        history.remove(1)

        assert not history.is_applied(1)
        assert history.get(1) is None
    finally:
        database.close()


def test_remove_nonexistent_migration_is_safe(
    tmp_path: Path,
):
    database = create_database(tmp_path)

    try:
        history = MigrationHistory(database)

        history.remove(1)

        assert history.get(1) is None
    finally:
        database.close()


def test_duplicate_version_is_rejected(
    tmp_path: Path,
):
    database = create_database(tmp_path)

    try:
        history = MigrationHistory(database)

        history.record(
            version=1,
            name="create_users",
            checksum="abc123",
        )

        with pytest.raises(
            HistoryError,
            match="Could not record migration",
        ):
            history.record(
                version=1,
                name="other_migration",
                checksum="def456",
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
):
    database = create_database(tmp_path)

    try:
        history = MigrationHistory(database)

        with pytest.raises(
            HistoryError,
            match="greater than zero",
        ):
            history.record(
                version=version,
                name="create_users",
                checksum="abc123",
            )
    finally:
        database.close()


@pytest.mark.parametrize(
    "version",
    [0, -1],
)
def test_invalid_version_lookup_is_rejected(
    tmp_path: Path,
    version: int,
):
    database = create_database(tmp_path)

    try:
        history = MigrationHistory(database)

        with pytest.raises(
            HistoryError,
            match="greater than zero",
        ):
            history.get(version)
    finally:
        database.close()


@pytest.mark.parametrize(
    "version",
    [0, -1],
)
def test_invalid_version_is_applied_is_rejected(
    tmp_path: Path,
    version: int,
):
    database = create_database(tmp_path)

    try:
        history = MigrationHistory(database)

        with pytest.raises(
            HistoryError,
            match="greater than zero",
        ):
            history.is_applied(version)
    finally:
        database.close()


@pytest.mark.parametrize(
    "version",
    [0, -1],
)
def test_invalid_version_remove_is_rejected(
    tmp_path: Path,
    version: int,
):
    database = create_database(tmp_path)

    try:
        history = MigrationHistory(database)

        with pytest.raises(
            HistoryError,
            match="greater than zero",
        ):
            history.remove(version)
    finally:
        database.close()


def test_empty_name_is_rejected(
    tmp_path: Path,
):
    database = create_database(tmp_path)

    try:
        history = MigrationHistory(database)

        with pytest.raises(
            HistoryError,
            match="name must not be empty",
        ):
            history.record(
                version=1,
                name="",
                checksum="abc123",
            )
    finally:
        database.close()


def test_empty_checksum_is_rejected(
    tmp_path: Path,
):
    database = create_database(tmp_path)

    try:
        history = MigrationHistory(database)

        with pytest.raises(
            HistoryError,
            match="checksum must not be empty",
        ):
            history.record(
                version=1,
                name="create_users",
                checksum="",
            )
    finally:
        database.close()