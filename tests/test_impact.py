"""Tests for migration impact analysis."""

from pathlib import Path

from dbmigrate.impact import (
    analyze_migration_impact,
    analyze_migrations,
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


def test_create_table_impact() -> None:
    migration = make_migration(
        1,
        "create_users",
        "CREATE TABLE users (id INTEGER);",
        "DROP TABLE users;",
    )

    impact = analyze_migration_impact(
        migration
    )

    assert impact.tables == ("users",)
    assert impact.operations == (
        "CREATE_TABLE",
        "DROP_TABLE",
    )
    assert impact.risk == "HIGH"
    assert impact.is_destructive


def test_alter_table_is_medium_risk() -> None:
    migration = make_migration(
        1,
        "alter_users",
        "ALTER TABLE users ADD COLUMN email TEXT;",
        "SELECT 1;",
    )

    impact = analyze_migration_impact(
        migration
    )

    assert impact.tables == ("users",)
    assert impact.operations == (
        "ALTER_TABLE",
    )
    assert impact.risk == "MEDIUM"
    assert not impact.is_destructive


def test_update_is_medium_risk() -> None:
    migration = make_migration(
        1,
        "update_users",
        "UPDATE users SET active = 1 WHERE id = 1;",
        "SELECT 1;",
    )

    impact = analyze_migration_impact(
        migration
    )

    assert impact.tables == ("users",)
    assert impact.operations == (
        "UPDATE",
    )
    assert impact.risk == "MEDIUM"


def test_delete_is_medium_risk() -> None:
    migration = make_migration(
        1,
        "delete_users",
        "DELETE FROM users WHERE id = 1;",
        "SELECT 1;",
    )

    impact = analyze_migration_impact(
        migration
    )

    assert impact.operations == (
        "DELETE",
    )
    assert impact.risk == "MEDIUM"


def test_index_is_info_risk() -> None:
    migration = make_migration(
        1,
        "index_users",
        "CREATE INDEX idx_users_name ON users(name);",
        "DROP INDEX idx_users_name;",
    )

    impact = analyze_migration_impact(
        migration
    )

    assert impact.indexes == (
        "idx_users_name",
    )
    assert impact.risk == "HIGH"


def test_multiple_tables_are_sorted() -> None:
    migration = make_migration(
        1,
        "users_orders",
        """
        CREATE TABLE orders (id INTEGER);
        CREATE TABLE users (id INTEGER);
        """,
        "SELECT 1;",
    )

    impact = analyze_migration_impact(
        migration
    )

    assert impact.tables == (
        "orders",
        "users",
    )


def test_analyze_migrations_are_sorted() -> None:
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

    result = analyze_migrations(
        [second, first]
    )

    assert [
        item.migration.version
        for item in result
    ] == [1, 2]