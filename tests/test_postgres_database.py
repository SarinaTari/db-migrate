from dbmigrate.database_postgres import (
    PostgreSQLDatabase,
)


def test_postgresql_metadata():
    database = PostgreSQLDatabase(
        host="localhost",
        port=5432,
        database="test",
        user="test",
        password="test",
    )

    assert database.engine == "postgresql"
    assert database.dialect.name == "postgresql"
    assert database.dialect.parameter_placeholder == "%s"


def test_postgresql_capabilities():
    database = PostgreSQLDatabase(
        host="localhost",
        port=5432,
        database="test",
        user="test",
        password="test",
    )

    assert database.capabilities.transactional_ddl
    assert database.capabilities.drop_column
    assert database.capabilities.schemas
    assert database.capabilities.advisory_locks


def test_postgresql_connection_starts_closed():
    database = PostgreSQLDatabase(
        host="localhost",
        port=5432,
        database="test",
        user="test",
        password="test",
    )

    assert not database.is_connected