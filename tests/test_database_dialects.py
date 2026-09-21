import pytest

from dbmigrate.database_dialect import (
    DialectError,
    MySQLDialect,
    PostgreSQLDialect,
    SQLiteDialect,
)


def test_sqlite_dialect():
    dialect = SQLiteDialect()

    assert dialect.name == "sqlite"
    assert dialect.parameter_placeholder == "?"
    assert (
        dialect.quote_identifier("users")
        == '"users"'
    )
    assert (
        dialect.version_query()
        == "SELECT sqlite_version()"
    )


def test_postgresql_dialect():
    dialect = PostgreSQLDialect()

    assert dialect.name == "postgresql"
    assert dialect.parameter_placeholder == "%s"
    assert (
        dialect.quote_identifier("users")
        == '"users"'
    )
    assert (
        dialect.version_query()
        == "SELECT version()"
    )


def test_mysql_dialect():
    dialect = MySQLDialect()

    assert dialect.name == "mysql"
    assert dialect.parameter_placeholder == "%s"
    assert (
        dialect.quote_identifier("users")
        == "`users`"
    )
    assert (
        dialect.version_query()
        == "SELECT VERSION()"
    )


@pytest.mark.parametrize(
    "dialect",
    [
        SQLiteDialect(),
        PostgreSQLDialect(),
        MySQLDialect(),
    ],
)
def test_empty_identifier_is_rejected(dialect):
    with pytest.raises(DialectError):
        dialect.quote_identifier("")


def test_identifier_quotes_are_escaped():
    assert (
        SQLiteDialect().quote_identifier(
            'user"name'
        )
        == '"user""name"'
    )

    assert (
        MySQLDialect().quote_identifier(
            "user`name"
        )
        == "`user``name`"
    )