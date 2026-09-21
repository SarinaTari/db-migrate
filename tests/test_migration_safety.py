from pathlib import Path

import pytest

from dbmigrate.database import SQLiteDatabase
from dbmigrate.migration import Migration
from dbmigrate.migration_safety import (
    MigrationSafetyChecker,
    MigrationSafetyError,
)


def _migration(
    tmp_path: Path,
    version: int,
    name: str,
) -> Migration:
    path = (
        tmp_path
        / "migrations"
        / f"{version:03d}_{name}.sql"
    )

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    return Migration(
        version=version,
        name=name,
        up_sql=(
            "CREATE TABLE "
            f"{name} (id INTEGER);"
        ),
        down_sql=(
            "DROP TABLE "
            f"{name};"
        ),
        path=path,
    )

def _database(
    tmp_path: Path,
) -> SQLiteDatabase:
    database = SQLiteDatabase(
        tmp_path / "database.db"
    )

    database.connect()

    return database


def test_safe_migrations_are_reported_as_safe(
    tmp_path: Path,
):
    database = _database(tmp_path)

    try:
        migrations = [
            _migration(
                tmp_path,
                1,
                "create_users",
            ),
            _migration(
                tmp_path,
                2,
                "create_posts",
            ),
        ]

        report = MigrationSafetyChecker(
            database
        ).check(migrations)

        assert report.is_safe
        assert not report.errors

    finally:
        database.close()


def test_duplicate_versions_are_rejected(
    tmp_path: Path,
):
    database = _database(tmp_path)

    try:
        migrations = [
            _migration(
                tmp_path,
                1,
                "create_users",
            ),
            _migration(
                tmp_path,
                1,
                "create_posts",
            ),
        ]

        report = MigrationSafetyChecker(
            database
        ).check(migrations)

        assert not report.is_safe

        assert any(
            issue.code == "DUPLICATE_VERSION"
            for issue in report.errors
        )

    finally:
        database.close()


def test_duplicate_identifiers_are_rejected(
    tmp_path: Path,
):
    database = _database(tmp_path)

    try:
        migrations = [
            _migration(
                tmp_path,
                1,
                "create_users",
            ),
            _migration(
                tmp_path,
                2,
                "create_users",
            ),
        ]

        report = MigrationSafetyChecker(
            database
        ).check(migrations)

        assert not report.is_safe

        assert any(
            issue.code == "DUPLICATE_IDENTIFIER"
            for issue in report.errors
        )

    finally:
        database.close()


def test_out_of_order_migrations_are_rejected(
    tmp_path: Path,
):
    database = _database(tmp_path)

    try:
        migrations = [
            _migration(
                tmp_path,
                2,
                "create_posts",
            ),
            _migration(
                tmp_path,
                1,
                "create_users",
            ),
        ]

        report = MigrationSafetyChecker(
            database
        ).check(migrations)

        assert not report.is_safe

        assert any(
            issue.code == "MIGRATION_ORDER"
            for issue in report.errors
        )

    finally:
        database.close()


def test_require_safe_raises_for_unsafe_migrations(
    tmp_path: Path,
):
    database = _database(tmp_path)

    try:
        migrations = [
            _migration(
                tmp_path,
                1,
                "create_users",
            ),
            _migration(
                tmp_path,
                1,
                "create_posts",
            ),
        ]

        with pytest.raises(
            MigrationSafetyError,
            match="Migration safety checks failed",
        ):
            MigrationSafetyChecker(
                database
            ).require_safe(
                migrations
            )

    finally:
        database.close()


def test_empty_migration_set_is_safe(
    tmp_path: Path,
):
    database = _database(tmp_path)

    try:
        report = MigrationSafetyChecker(
            database
        ).check([])

        assert report.is_safe
        assert not report.errors

    finally:
        database.close()


def test_sqlite_reports_transactional_ddl_support(
    tmp_path: Path,
):
    database = _database(tmp_path)

    try:
        migrations = [
            _migration(
                tmp_path,
                1,
                "create_users",
            )
        ]

        report = MigrationSafetyChecker(
            database
        ).check(migrations)

        assert report.is_safe

        assert not any(
            issue.code == "NON_TRANSACTIONAL_DDL"
            for issue in report.warnings
        )

    finally:
        database.close()