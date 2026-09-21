"""Tests for migration linting."""

from pathlib import Path

from dbmigrate.linter import (
    lint_migration,
    lint_migrations,
)
from dbmigrate.migration import Migration


def make_migration(
    version: int,
    name: str,
    up_sql: str,
    down_sql: str = "SELECT 1;",
) -> Migration:
    """Create a migration for testing."""
    return Migration(
        version=version,
        name=name,
        up_sql=up_sql,
        down_sql=down_sql,
        path=Path(
            f"{version:03d}_{name}.sql"
        ),
    )


def test_clean_migration_has_no_issues() -> None:
    migration = make_migration(
        1,
        "create_users",
        """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY
        );
        """,
    )

    issues = lint_migration(
        migration
    )

    assert issues == []


def test_drop_table_is_error() -> None:
    migration = make_migration(
        1,
        "drop_users",
        "DROP TABLE users;",
    )

    issues = lint_migration(
        migration
    )

    assert len(issues) == 1
    assert issues[0].code == "DROP_TABLE"
    assert issues[0].severity == "ERROR"


def test_drop_column_is_error() -> None:
    migration = make_migration(
        1,
        "remove_name",
        "ALTER TABLE users DROP COLUMN name;",
    )

    issues = lint_migration(
        migration
    )

    codes = {
        issue.code
        for issue in issues
    }

    assert "DROP_COLUMN" in codes
    assert "ALTER_TABLE" in codes


def test_delete_without_where_is_error() -> None:
    migration = make_migration(
        1,
        "delete_users",
        "DELETE FROM users;",
    )

    issues = lint_migration(
        migration
    )

    assert len(issues) == 1
    assert issues[0].code == "DELETE_NO_WHERE"
    assert issues[0].severity == "ERROR"


def test_delete_with_where_is_not_flagged() -> None:
    migration = make_migration(
        1,
        "delete_user",
        "DELETE FROM users WHERE id = 1;",
    )

    issues = lint_migration(
        migration
    )

    assert not any(
        issue.code == "DELETE_NO_WHERE"
        for issue in issues
    )


def test_update_without_where_is_warning() -> None:
    migration = make_migration(
        1,
        "update_users",
        "UPDATE users SET active = 1;",
    )

    issues = lint_migration(
        migration
    )

    assert len(issues) == 1
    assert issues[0].code == "UPDATE_NO_WHERE"
    assert issues[0].severity == "WARNING"


def test_update_with_where_is_not_flagged() -> None:
    migration = make_migration(
        1,
        "update_user",
        "UPDATE users SET active = 1 WHERE id = 1;",
    )

    issues = lint_migration(
        migration
    )

    assert not any(
        issue.code == "UPDATE_NO_WHERE"
        for issue in issues
    )


def test_alter_table_is_warning() -> None:
    migration = make_migration(
        1,
        "alter_users",
        "ALTER TABLE users ADD COLUMN email TEXT;",
    )

    issues = lint_migration(
        migration
    )

    assert any(
        issue.code == "ALTER_TABLE"
        and issue.severity == "WARNING"
        for issue in issues
    )


def test_create_index_is_info() -> None:
    migration = make_migration(
        1,
        "index_users",
        "CREATE INDEX idx_users_name ON users(name);",
    )

    issues = lint_migration(
        migration
    )

    assert len(issues) == 1
    assert issues[0].code == "CREATE_INDEX"
    assert issues[0].severity == "INFO"


def test_lint_checks_up_and_down() -> None:
    migration = make_migration(
        1,
        "users",
        "DROP TABLE users;",
        "DROP TABLE archived_users;",
    )

    issues = lint_migration(
        migration
    )

    assert len(issues) == 2

    assert {
        issue.section
        for issue in issues
    } == {"up", "down"}


def test_lint_report_counts_severities() -> None:
    migration = make_migration(
        1,
        "users",
        """
        DROP TABLE users;
        ALTER TABLE accounts ADD COLUMN name TEXT;
        CREATE INDEX idx_name ON accounts(name);
        """,
    )

    report = lint_migrations(
        [migration]
    )

    assert report.error_count == 1
    assert report.warning_count == 1
    assert report.info_count == 1
    assert not report.is_clean
    assert not report.is_valid


def test_lint_report_is_clean() -> None:
    migration = make_migration(
        1,
        "users",
        "CREATE TABLE users (id INTEGER);",
    )

    report = lint_migrations(
        [migration]
    )

    assert report.is_clean
    assert report.is_valid
    assert report.error_count == 0
    assert report.warning_count == 0
    assert report.info_count == 0


def test_lint_migrations_are_sorted() -> None:
    first = make_migration(
        1,
        "first",
        "CREATE TABLE first (id INTEGER);",
    )

    second = make_migration(
        2,
        "second",
        "DROP TABLE second;",
    )

    report = lint_migrations(
        [second, first]
    )

    assert [
        migration.version
        for migration in report.migrations
    ] == [1, 2]


def test_issue_contains_migration_information() -> None:
    migration = make_migration(
        7,
        "remove_users",
        "DROP TABLE users;",
    )

    issues = lint_migration(
        migration
    )

    issue = issues[0]

    assert issue.version == 7
    assert issue.identifier == "007_remove_users"
    assert issue.section == "up"
    assert issue.line == 1


def test_issue_format_contains_useful_information() -> None:
    migration = make_migration(
        1,
        "remove_users",
        "DROP TABLE users;",
    )

    issue = lint_migration(
        migration
    )[0]

    formatted = issue.format()

    assert "ERROR" in formatted
    assert "DROP_TABLE" in formatted
    assert "001_remove_users" in formatted
    assert "up" in formatted
    assert "line 1" in formatted