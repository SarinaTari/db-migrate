from dbmigrate.database_capabilities import (
    DatabaseCapabilities,
)


def test_capabilities_are_immutable():
    capabilities = DatabaseCapabilities(
        transactional_ddl=True,
        drop_column=True,
        schemas=False,
        advisory_locks=False,
    )

    assert capabilities.transactional_ddl is True
    assert capabilities.drop_column is True
    assert capabilities.schemas is False
    assert capabilities.advisory_locks is False


def test_supports_known_capability():
    capabilities = DatabaseCapabilities(
        transactional_ddl=True,
        drop_column=False,
        schemas=True,
        advisory_locks=False,
    )

    assert capabilities.supports(
        "transactional_ddl"
    )
    assert not capabilities.supports(
        "drop_column"
    )


def test_supports_unknown_capability_raises():
    capabilities = DatabaseCapabilities(
        transactional_ddl=True,
        drop_column=True,
        schemas=True,
        advisory_locks=True,
    )

    try:
        capabilities.supports("unknown")
    except ValueError as exc:
        assert "Unknown database capability" in str(exc)
    else:
        raise AssertionError(
            "Expected ValueError"
        )