from pathlib import Path

from dbmigrate.database import SQLiteDatabase
from dbmigrate.doctor import DatabaseDoctor
from dbmigrate.migration import Migration


def _migration(
    tmp_path: Path,
) -> Migration:
    path = (
        tmp_path
        / "migrations"
        / "001_create_users.sql"
    )

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    return Migration(
        version=1,
        name="create_users",
        up_sql=(
            "CREATE TABLE users "
            "(id INTEGER);"
        ),
        down_sql=(
            "DROP TABLE users;"
        ),
        path=path,
    )


def test_doctor_reports_healthy_database(
    tmp_path: Path,
):
    database = SQLiteDatabase(
        tmp_path / "database.db"
    )

    database.connect()

    try:
        report = DatabaseDoctor(
            database
        ).inspect(
            [_migration(tmp_path)]
        )

        assert report.healthy

        assert any(
            issue.code == "DATABASE_CONNECTION"
            and issue.severity == "PASS"
            for issue in report.passes
        )

        assert any(
            issue.code == "DATABASE_ENGINE"
            and issue.severity == "PASS"
            for issue in report.passes
        )

    finally:
        database.close()


def test_doctor_reports_transactional_ddl(
    tmp_path: Path,
):
    database = SQLiteDatabase(
        tmp_path / "database.db"
    )

    database.connect()

    try:
        report = DatabaseDoctor(
            database
        ).inspect([])

        assert any(
            issue.code == "TRANSACTIONAL_DDL"
            for issue in report.passes
        )

    finally:
        database.close()