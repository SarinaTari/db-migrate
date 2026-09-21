"""Tests for migration explanation."""

from pathlib import Path

from dbmigrate.explainer import (
    explain_migration,
    explain_migrations,
)
from dbmigrate.migration import Migration


def make_migration(
    version: int,
    name: str,
    up_sql: str,
    down_sql: str,
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


def test_explain_create_table() -> None:
    migration = make_migration(
        1,
        "create_users",
        "CREATE TABLE users (id INTEGER);",
        "DROP TABLE users;",
    )

    explanation = explain_migration(
        migration
    )

    assert len(
        explanation.explanations
    ) == 2

    assert (
        explanation.explanations[0].operation
        == "CREATE_TABLE"
    )

    assert (
        "users"
        in explanation.explanations[0].description
    )


def test_explain_drop_table() -> None:
    migration = make_migration(
        1,
        "remove_users",
        "DROP TABLE users;",
        "CREATE TABLE users (id INTEGER);",
    )

    explanation = explain_migration(
        migration
    )

    operations = {
        item.operation
        for item in explanation.explanations
    }

    assert "DROP_TABLE" in operations
    assert "CREATE_TABLE" in operations


def test_explain_alter_table() -> None:
    migration = make_migration(
        1,
        "alter_users",
        "ALTER TABLE users ADD COLUMN email TEXT;",
        "ALTER TABLE users DROP COLUMN email;",
    )

    explanation = explain_migration(
        migration
    )

    operations = {
        item.operation
        for item in explanation.explanations
    }

    assert "ALTER_TABLE" in operations


def test_explain_insert_update_delete() -> None:
    migration = make_migration(
        1,
        "change_users",
        """
        INSERT INTO users (name) VALUES ('Alice');
        UPDATE users SET name = 'Bob' WHERE id = 1;
        DELETE FROM users WHERE id = 2;
        """,
        "SELECT 1;",
    )

    explanation = explain_migration(
        migration
    )

    operations = {
        item.operation
        for item in explanation.explanations
    }

    assert operations == {
        "INSERT",
        "UPDATE",
        "DELETE",
    }


def test_explain_index() -> None:
    migration = make_migration(
        1,
        "index_users",
        "CREATE INDEX idx_users_name ON users(name);",
        "DROP INDEX idx_users_name;",
    )

    explanation = explain_migration(
        migration
    )

    operations = {
        item.operation
        for item in explanation.explanations
    }

    assert operations == {
        "CREATE_INDEX",
        "DROP_INDEX",
    }


def test_explanation_contains_section_and_line() -> None:
    migration = make_migration(
        1,
        "users",
        """
        CREATE TABLE users (
            id INTEGER
        );
        """,
        "DROP TABLE users;",
    )

    explanation = explain_migration(
        migration
    )

    first = explanation.explanations[0]

    assert first.section == "up"
    assert first.line == 2


def test_explain_clean_sql_has_no_recognized_operations() -> None:
    migration = make_migration(
        1,
        "noop",
        "SELECT 1;",
        "SELECT 1;",
    )

    explanation = explain_migration(
        migration
    )

    assert explanation.is_empty


def test_explain_migrations_are_sorted() -> None:
    first = make_migration(
        1,
        "first",
        "CREATE TABLE first (id INTEGER);",
        "DROP TABLE first;",
    )

    second = make_migration(
        2,
        "second",
        "CREATE TABLE second (id INTEGER);",
        "DROP TABLE second;",
    )

    result = explain_migrations(
        [second, first]
    )

    assert [
        item.migration.version
        for item in result
    ] == [1, 2]