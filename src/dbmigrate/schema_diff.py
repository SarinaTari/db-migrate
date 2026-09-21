"""Structural database schema comparison."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .schema import (
    ColumnInfo,
    DatabaseSchema,
    ForeignKeyInfo,
    IndexInfo,
    TableInfo,
    ViewInfo,
)


class SchemaDiffError(Exception):
    """Raised when schema comparison fails."""


@dataclass(frozen=True)
class SchemaChange:
    """Describe one structural schema difference."""

    object_type: str
    object_name: str
    change_type: str
    detail: str

    def format(self) -> str:
        """Return a human-readable description."""
        return (
            f"{self.change_type} "
            f"{self.object_type} "
            f"'{self.object_name}': "
            f"{self.detail}"
        )


@dataclass(frozen=True)
class SchemaDiff:
    """Describe the structural difference between two schemas."""

    changes: tuple[SchemaChange, ...]

    @property
    def is_empty(self) -> bool:
        """Return whether the schemas are structurally identical."""
        return not self.changes

    @property
    def change_count(self) -> int:
        """Return the number of schema changes."""
        return len(self.changes)

    @property
    def additions(self) -> tuple[SchemaChange, ...]:
        """Return added objects or attributes."""
        return tuple(
            change
            for change in self.changes
            if change.change_type == "ADDED"
        )

    @property
    def removals(self) -> tuple[SchemaChange, ...]:
        """Return removed objects or attributes."""
        return tuple(
            change
            for change in self.changes
            if change.change_type == "REMOVED"
        )

    @property
    def modifications(self) -> tuple[SchemaChange, ...]:
        """Return modified objects or attributes."""
        return tuple(
            change
            for change in self.changes
            if change.change_type == "MODIFIED"
        )


def _column_key(
    column: ColumnInfo,
) -> tuple:
    """Return the comparable representation of a column."""
    return (
        column.name,
        column.data_type,
        column.not_null,
        column.default_value,
        column.primary_key_position,
    )


def _index_key(
    index: IndexInfo,
) -> tuple:
    """Return the comparable representation of an index."""
    return (
        index.name,
        index.unique,
        index.columns,
    )


def _foreign_key_key(
    foreign_key: ForeignKeyInfo,
) -> tuple:
    """Return the comparable representation of a foreign key."""
    return (
        foreign_key.column,
        foreign_key.referenced_table,
        foreign_key.referenced_column,
        foreign_key.on_update,
        foreign_key.on_delete,
    )


def _table_key(
    table: TableInfo,
) -> tuple:
    """Return the comparable representation of a table."""
    return (
        tuple(
            _column_key(column)
            for column in table.columns
        ),
        tuple(
            _index_key(index)
            for index in table.indexes
        ),
        tuple(
            _foreign_key_key(foreign_key)
            for foreign_key in table.foreign_keys
        ),
    )


def _view_key(
    view: ViewInfo,
) -> str:
    """Return the normalized comparable representation of a view."""
    return view.normalized()


def _diff_columns(
    expected: TableInfo,
    actual: TableInfo,
) -> list[SchemaChange]:
    """Compare columns belonging to one table."""
    expected_columns = {
        column.name: column
        for column in expected.columns
    }

    actual_columns = {
        column.name: column
        for column in actual.columns
    }

    changes: list[SchemaChange] = []

    for name in sorted(
        expected_columns.keys()
        - actual_columns.keys()
    ):
        changes.append(
            SchemaChange(
                object_type="column",
                object_name=f"{expected.name}.{name}",
                change_type="ADDED",
                detail="column exists in expected schema only.",
            )
        )

    for name in sorted(
        actual_columns.keys()
        - expected_columns.keys()
    ):
        changes.append(
            SchemaChange(
                object_type="column",
                object_name=f"{expected.name}.{name}",
                change_type="REMOVED",
                detail="column exists in actual schema only.",
            )
        )

    for name in sorted(
        expected_columns.keys()
        & actual_columns.keys()
    ):
        expected_column = expected_columns[name]
        actual_column = actual_columns[name]

        if _column_key(expected_column) == _column_key(
            actual_column
        ):
            continue

        changes.append(
            SchemaChange(
                object_type="column",
                object_name=f"{expected.name}.{name}",
                change_type="MODIFIED",
                detail=(
                    "column definition differs between "
                    "expected and actual schema."
                ),
            )
        )

    return changes


def _diff_indexes(
    expected: TableInfo,
    actual: TableInfo,
) -> list[SchemaChange]:
    """Compare indexes belonging to one table."""
    expected_indexes = {
        index.name: index
        for index in expected.indexes
    }

    actual_indexes = {
        index.name: index
        for index in actual.indexes
    }

    changes: list[SchemaChange] = []

    for name in sorted(
        expected_indexes.keys()
        - actual_indexes.keys()
    ):
        changes.append(
            SchemaChange(
                object_type="index",
                object_name=name,
                change_type="ADDED",
                detail="index exists in expected schema only.",
            )
        )

    for name in sorted(
        actual_indexes.keys()
        - expected_indexes.keys()
    ):
        changes.append(
            SchemaChange(
                object_type="index",
                object_name=name,
                change_type="REMOVED",
                detail="index exists in actual schema only.",
            )
        )

    for name in sorted(
        expected_indexes.keys()
        & actual_indexes.keys()
    ):
        if _index_key(
            expected_indexes[name]
        ) == _index_key(
            actual_indexes[name]
        ):
            continue

        changes.append(
            SchemaChange(
                object_type="index",
                object_name=name,
                change_type="MODIFIED",
                detail=(
                    "index definition differs between "
                    "expected and actual schema."
                ),
            )
        )

    return changes


def _diff_foreign_keys(
    expected: TableInfo,
    actual: TableInfo,
) -> list[SchemaChange]:
    """Compare foreign keys belonging to one table."""
    expected_keys = {
        _foreign_key_key(foreign_key)
        for foreign_key in expected.foreign_keys
    }

    actual_keys = {
        _foreign_key_key(foreign_key)
        for foreign_key in actual.foreign_keys
    }

    changes: list[SchemaChange] = []

    for foreign_key in sorted(
        expected_keys - actual_keys
    ):
        changes.append(
            SchemaChange(
                object_type="foreign_key",
                object_name=(
                    f"{expected.name}.{foreign_key[0]}"
                ),
                change_type="ADDED",
                detail=(
                    "foreign key exists in expected "
                    "schema only."
                ),
            )
        )

    for foreign_key in sorted(
        actual_keys - expected_keys
    ):
        changes.append(
            SchemaChange(
                object_type="foreign_key",
                object_name=(
                    f"{expected.name}.{foreign_key[0]}"
                ),
                change_type="REMOVED",
                detail=(
                    "foreign key exists in actual "
                    "schema only."
                ),
            )
        )

    return changes


def _diff_tables(
    expected: DatabaseSchema,
    actual: DatabaseSchema,
) -> list[SchemaChange]:
    """Compare database tables."""
    expected_tables = {
        table.name: table
        for table in expected.tables
    }

    actual_tables = {
        table.name: table
        for table in actual.tables
    }

    changes: list[SchemaChange] = []

    for name in sorted(
        expected_tables.keys()
        - actual_tables.keys()
    ):
        changes.append(
            SchemaChange(
                object_type="table",
                object_name=name,
                change_type="ADDED",
                detail="table exists in expected schema only.",
            )
        )

    for name in sorted(
        actual_tables.keys()
        - expected_tables.keys()
    ):
        changes.append(
            SchemaChange(
                object_type="table",
                object_name=name,
                change_type="REMOVED",
                detail="table exists in actual schema only.",
            )
        )

    for name in sorted(
        expected_tables.keys()
        & actual_tables.keys()
    ):
        expected_table = expected_tables[name]
        actual_table = actual_tables[name]

        if _table_key(expected_table) == _table_key(
            actual_table
        ):
            continue

        changes.extend(
            _diff_columns(
                expected_table,
                actual_table,
            )
        )

        changes.extend(
            _diff_indexes(
                expected_table,
                actual_table,
            )
        )

        changes.extend(
            _diff_foreign_keys(
                expected_table,
                actual_table,
            )
        )

    return changes


def _diff_views(
    expected: DatabaseSchema,
    actual: DatabaseSchema,
) -> list[SchemaChange]:
    """Compare database views."""
    expected_views = {
        view.name: view
        for view in expected.views
    }

    actual_views = {
        view.name: view
        for view in actual.views
    }

    changes: list[SchemaChange] = []

    for name in sorted(
        expected_views.keys()
        - actual_views.keys()
    ):
        changes.append(
            SchemaChange(
                object_type="view",
                object_name=name,
                change_type="ADDED",
                detail="view exists in expected schema only.",
            )
        )

    for name in sorted(
        actual_views.keys()
        - expected_views.keys()
    ):
        changes.append(
            SchemaChange(
                object_type="view",
                object_name=name,
                change_type="REMOVED",
                detail="view exists in actual schema only.",
            )
        )

    for name in sorted(
        expected_views.keys()
        & actual_views.keys()
    ):
        if _view_key(
            expected_views[name]
        ) == _view_key(
            actual_views[name]
        ):
            continue

        changes.append(
            SchemaChange(
                object_type="view",
                object_name=name,
                change_type="MODIFIED",
                detail=(
                    "view definition differs between "
                    "expected and actual schema."
                ),
            )
        )

    return changes


def diff_schemas(
    expected: DatabaseSchema,
    actual: DatabaseSchema,
) -> SchemaDiff:
    """Compare two database schemas structurally."""
    changes: list[SchemaChange] = []

    changes.extend(
        _diff_tables(
            expected,
            actual,
        )
    )

    changes.extend(
        _diff_views(
            expected,
            actual,
        )
    )

    return SchemaDiff(
        changes=tuple(changes)
    )