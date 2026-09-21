"""Tests for database schema comparison."""

from dbmigrate.schema import (
    ColumnInfo,
    DatabaseSchema,
    ForeignKeyInfo,
    IndexInfo,
    TableInfo,
    ViewInfo,
)
from dbmigrate.schema_diff import diff_schemas


def _table(
    name: str = "users",
    columns=None,
    indexes=None,
    foreign_keys=None,
):
    return TableInfo(
        name=name,
        columns=tuple(
            columns
            or (
                ColumnInfo(
                    name="id",
                    data_type="INTEGER",
                    not_null=False,
                    default_value=None,
                    primary_key_position=1,
                ),
                ColumnInfo(
                    name="name",
                    data_type="TEXT",
                    not_null=True,
                    default_value=None,
                    primary_key_position=0,
                ),
            )
        ),
        indexes=tuple(
            indexes or ()
        ),
        foreign_keys=tuple(
            foreign_keys or ()
        ),
    )


def _schema(
    tables=(),
    views=(),
):
    return DatabaseSchema(
        tables=tuple(tables),
        views=tuple(views),
    )


def test_identical_schemas_have_no_changes():
    schema = _schema(
        tables=(
            _table(),
        )
    )

    diff = diff_schemas(
        schema,
        schema,
    )

    assert diff.is_empty
    assert diff.change_count == 0


def test_detects_added_table():
    expected = _schema(
        tables=(
            _table(),
        )
    )

    actual = _schema()

    diff = diff_schemas(
        expected,
        actual,
    )

    assert diff.change_count == 1
    assert diff.changes[0].change_type == "ADDED"
    assert diff.changes[0].object_type == "table"
    assert diff.changes[0].object_name == "users"


def test_detects_removed_table():
    expected = _schema()

    actual = _schema(
        tables=(
            _table(),
        )
    )

    diff = diff_schemas(
        expected,
        actual,
    )

    assert diff.change_count == 1
    assert diff.changes[0].change_type == "REMOVED"
    assert diff.changes[0].object_type == "table"
    assert diff.changes[0].object_name == "users"


def test_detects_added_column():
    expected = _schema(
        tables=(
            _table(
                columns=(
                    ColumnInfo(
                        name="id",
                        data_type="INTEGER",
                        not_null=False,
                        default_value=None,
                        primary_key_position=1,
                    ),
                    ColumnInfo(
                        name="name",
                        data_type="TEXT",
                        not_null=True,
                        default_value=None,
                        primary_key_position=0,
                    ),
                    ColumnInfo(
                        name="email",
                        data_type="TEXT",
                        not_null=False,
                        default_value=None,
                        primary_key_position=0,
                    ),
                )
            ),
        )
    )

    actual = _schema(
        tables=(
            _table(),
        )
    )

    diff = diff_schemas(
        expected,
        actual,
    )

    assert diff.change_count == 1
    assert diff.changes[0].change_type == "ADDED"
    assert diff.changes[0].object_type == "column"
    assert diff.changes[0].object_name == "users.email"


def test_detects_removed_column():
    expected = _schema(
        tables=(
            _table(
                columns=(
                    ColumnInfo(
                        name="id",
                        data_type="INTEGER",
                        not_null=False,
                        default_value=None,
                        primary_key_position=1,
                    ),
                )
            ),
        )
    )

    actual = _schema(
        tables=(
            _table(),
        )
    )

    diff = diff_schemas(
        expected,
        actual,
    )

    assert diff.change_count == 1
    assert diff.changes[0].change_type == "REMOVED"
    assert diff.changes[0].object_type == "column"
    assert diff.changes[0].object_name == "users.name"
    

def test_detects_modified_column():
    expected = _schema(
        tables=(
            _table(
                columns=(
                    ColumnInfo(
                        name="id",
                        data_type="INTEGER",
                        not_null=False,
                        default_value=None,
                        primary_key_position=1,
                    ),
                    ColumnInfo(
                        name="name",
                        data_type="VARCHAR",
                        not_null=True,
                        default_value=None,
                        primary_key_position=0,
                    ),
                )
            ),
        )
    )

    actual = _schema(
        tables=(
            _table(),
        )
    )

    diff = diff_schemas(
        expected,
        actual,
    )

    assert diff.change_count == 1
    assert diff.changes[0].change_type == "MODIFIED"
    assert diff.changes[0].object_type == "column"
    assert diff.changes[0].object_name == "users.name"


def test_detects_added_index():
    index = IndexInfo(
        name="idx_users_name",
        unique=False,
        columns=("name",),
    )

    expected = _schema(
        tables=(
            _table(
                indexes=(index,)
            ),
        )
    )

    actual = _schema(
        tables=(
            _table(),
        )
    )

    diff = diff_schemas(
        expected,
        actual,
    )

    assert diff.change_count == 1
    assert diff.changes[0].change_type == "ADDED"
    assert diff.changes[0].object_type == "index"


def test_detects_modified_index():
    expected = _schema(
        tables=(
            _table(
                indexes=(
                    IndexInfo(
                        name="idx_users_name",
                        unique=True,
                        columns=("name",),
                    ),
                )
            ),
        )
    )

    actual = _schema(
        tables=(
            _table(
                indexes=(
                    IndexInfo(
                        name="idx_users_name",
                        unique=False,
                        columns=("name",),
                    ),
                )
            ),
        )
    )

    diff = diff_schemas(
        expected,
        actual,
    )

    assert diff.change_count == 1
    assert diff.changes[0].change_type == "MODIFIED"


def test_detects_added_foreign_key():
    foreign_key = ForeignKeyInfo(
        column="user_id",
        referenced_table="users",
        referenced_column="id",
        on_update="NO ACTION",
        on_delete="CASCADE",
    )

    expected = _schema(
        tables=(
            _table(
                foreign_keys=(foreign_key,)
            ),
        )
    )

    actual = _schema(
        tables=(
            _table(),
        )
    )

    diff = diff_schemas(
        expected,
        actual,
    )

    assert diff.change_count == 1
    assert diff.changes[0].change_type == "ADDED"
    assert diff.changes[0].object_type == "foreign_key"


def test_detects_added_view():
    expected = _schema(
        views=(
            ViewInfo(
                name="active_users",
                sql="CREATE VIEW active_users AS "
                "SELECT id, name FROM users",
            ),
        )
    )

    actual = _schema()

    diff = diff_schemas(
        expected,
        actual,
    )

    assert diff.change_count == 1
    assert diff.changes[0].change_type == "ADDED"
    assert diff.changes[0].object_type == "view"


def test_detects_modified_view():
    expected = _schema(
        views=(
            ViewInfo(
                name="active_users",
                sql="CREATE VIEW active_users AS "
                "SELECT id, name, email FROM users",
            ),
        )
    )

    actual = _schema(
        views=(
            ViewInfo(
                name="active_users",
                sql="CREATE VIEW active_users AS "
                "SELECT id, name FROM users",
            ),
        )
    )

    diff = diff_schemas(
        expected,
        actual,
    )

    assert diff.change_count == 1
    assert diff.changes[0].change_type == "MODIFIED"


def test_additions_and_removals_are_classified():
    expected = _schema(
        tables=(
            _table(),
        )
    )

    actual = _schema(
        views=(
            ViewInfo(
                name="users_view",
                sql="CREATE VIEW users_view AS "
                "SELECT id FROM users",
            ),
        )
    )

    diff = diff_schemas(
        expected,
        actual,
    )

    assert len(diff.additions) == 1
    assert len(diff.removals) == 1