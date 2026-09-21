from dbmigrate.database_mysql import (
    MySQLDatabase,
)


def test_mysql_metadata():
    database = MySQLDatabase(
        host="localhost",
        port=3306,
        database="test",
        user="test",
        password="test",
    )

    assert database.engine == "mysql"
    assert database.dialect.name == "mysql"
    assert database.dialect.parameter_placeholder == "%s"


def test_mysql_capabilities():
    database = MySQLDatabase(
        host="localhost",
        port=3306,
        database="test",
        user="test",
        password="test",
    )

    assert not database.capabilities.transactional_ddl
    assert database.capabilities.drop_column
    assert database.capabilities.schemas
    assert database.capabilities.advisory_locks


def test_mysql_connection_starts_closed():
    database = MySQLDatabase(
        host="localhost",
        port=3306,
        database="test",
        user="test",
        password="test",
    )

    assert not database.is_connected