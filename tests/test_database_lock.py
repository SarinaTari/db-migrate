from pathlib import Path

import pytest

from dbmigrate.database import SQLiteDatabase
from dbmigrate.database_lock import (
    MigrationLockError,
    SQLiteMigrationLock,
    create_migration_lock,
)


def test_sqlite_lock_can_be_acquired(
    tmp_path: Path,
):
    database_path = (
        tmp_path / "database.db"
    )

    lock = SQLiteMigrationLock(
        database_path
    )

    lock.acquire()

    try:
        assert lock.is_locked
    finally:
        lock.release()

    assert not lock.is_locked


def test_sqlite_second_lock_fails(
    tmp_path: Path,
):
    database_path = (
        tmp_path / "database.db"
    )

    first = SQLiteMigrationLock(
        database_path
    )

    second = SQLiteMigrationLock(
        database_path
    )

    first.acquire()

    try:
        with pytest.raises(
            MigrationLockError,
            match="Another dbmigrate process",
        ):
            second.acquire()
    finally:
        first.release()


def test_sqlite_lock_can_be_reacquired(
    tmp_path: Path,
):
    database_path = (
        tmp_path / "database.db"
    )

    first = SQLiteMigrationLock(
        database_path
    )

    first.acquire()
    first.release()

    second = SQLiteMigrationLock(
        database_path
    )

    second.acquire()

    try:
        assert second.is_locked
    finally:
        second.release()


def test_sqlite_lock_context_manager(
    tmp_path: Path,
):
    database_path = (
        tmp_path / "database.db"
    )

    lock = SQLiteMigrationLock(
        database_path
    )

    with lock:
        assert lock.is_locked

    assert not lock.is_locked


def test_create_migration_lock_for_sqlite(
    tmp_path: Path,
):
    database = SQLiteDatabase(
        tmp_path / "database.db"
    )

    lock = create_migration_lock(
        database
    )

    assert isinstance(
        lock,
        SQLiteMigrationLock,
    )