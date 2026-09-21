# Testing and CI

## Overview

Testing is a central part of `dbmigrate` because a migration tool operates on persistent database state.

The project uses automated tests to verify:

- migration parsing
- migration execution
- migration history
- database abstraction
- database-specific behavior
- schema inspection
- schema differences
- migration safety
- integrity checks
- concurrency protection
- CLI behavior
- reproducibility
- CI functionality

The testing architecture is designed to catch regressions while allowing the project to evolve across multiple database backends.

---

# 1. Testing Philosophy

The project follows several testing principles.

### Test Core Logic Independently

Business logic should be testable without requiring a complete end-to-end database environment whenever possible.

### Test Database Behavior

Database-specific behavior must also be tested because SQLite, PostgreSQL, and MySQL are not identical.

### Test the CLI

The command-line interface is part of the public user experience and therefore requires dedicated tests.

### Test Failure Paths

A migration tool must be tested not only when operations succeed, but also when they fail.

### Test Reproducibility

A migration chain should be capable of recreating the expected schema from a clean starting state.

---

# 2. Test Framework

The project uses:

```text
pytest
```

Tests can be run with:

```bash
python -m pytest
```

This is the primary command for running the project's automated test suite.

---

# 3. Test Organization

Tests are organized by subsystem.

Conceptually:

```text
tests/
├── migration tests
├── database tests
├── schema tests
├── analysis tests
├── safety tests
├── CLI tests
└── integration tests
```

The exact files evolve as new functionality is added.

This organization keeps related behavior grouped together while allowing individual components to be tested independently.

---

# 4. Unit Tests

Unit tests verify individual components in isolation.

Examples include:

```text
Migration parsing
Checksum calculation
Validation
Planning
Status calculation
Schema representation
SQL analysis
Impact analysis
Configuration
Logging
Performance helpers
```

A unit test should ideally have a small scope.

For example:

```text
Input
  │
  ▼
Migration Parser
  │
  ▼
Expected Migration Object
```

This makes failures easier to diagnose.

---

# 5. Database Tests

Database-related tests verify the database abstraction and its implementations.

These tests cover concepts such as:

```text
Connection creation
SQL execution
Transactions
Parameters
Database version
Schema inspection
Locking
Database capabilities
```

The purpose is to verify both the common interface and the behavior specific to each supported database.

---

# 6. SQLite Tests

SQLite is used extensively in the automated test suite because it is:

- available through Python's standard library
- easy to create temporarily
- fast
- suitable for isolated test environments

A test can create a temporary SQLite database, execute the required operation, and remove the database afterward.

Conceptually:

```text
Test
 │
 ▼
Temporary SQLite DB
 │
 ▼
Execute Operation
 │
 ▼
Assert Result
 │
 ▼
Cleanup
```

This keeps tests isolated from the developer's local database.

---

# 7. PostgreSQL Tests

PostgreSQL-specific behavior should be tested against PostgreSQL when an appropriate test database is available.

This is important because a successful SQLite test does not prove that PostgreSQL behavior is identical.

PostgreSQL-specific tests can cover:

```text
Connection handling
Dialect behavior
Parameter placeholders
Transactions
Advisory locking
Schema inspection
Database capabilities
```

The test environment is responsible for providing a usable PostgreSQL instance.

---

# 8. MySQL Tests

MySQL-specific behavior should likewise be tested against MySQL when the test environment provides a usable instance.

Relevant tests include:

```text
Connection handling
Dialect behavior
Parameter placeholders
Transactions
Named locking
Schema inspection
Database capabilities
```

This prevents database-specific differences from being hidden behind SQLite-only tests.

---

# 9. Migration Tests

Migration tests verify the complete lifecycle of migration files.

A typical test creates:

```text
001_create_users.sql
```

with:

```sql
-- +up

CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);

-- +down

DROP TABLE users;
```

The test can then verify:

```text
Migration discovered
        ↓
Migration parsed
        ↓
Migration validated
        ↓
Migration planned
        ↓
Migration executed
        ↓
History recorded
```

---

# 10. Migration History Tests

History tests verify the `schema_migrations` table and its interaction with migration execution.

Important behavior includes:

```text
Record applied migration
Read migration history
Detect applied migrations
Remove rollback records
Store checksums
Store timestamps
```

History tests are especially important because migration planning depends on accurate recorded state.

---

# 11. Checksum Tests

Checksum tests verify that identical migrations produce identical checksums.

Conceptually:

```text
Migration A
   │
   ▼
SHA-256
   │
   ▼
Checksum A

Migration A again
   │
   ▼
SHA-256
   │
   ▼
Checksum A
```

Changing relevant migration content should change the checksum.

For example:

```text
Original SQL
     │
     ▼
Checksum A

Modified SQL
     │
     ▼
Checksum B
```

where:

```text
Checksum A != Checksum B
```

---

# 12. Validation Tests

Validation tests cover malformed or inconsistent migration collections.

Examples include:

```text
Duplicate version
Invalid migration metadata
Malformed sections
Missing required information
Invalid ordering
Checksum mismatch
```

Both successful and failing validation cases should be tested.

---

# 13. Planner Tests

Planner tests verify that the migration planner correctly determines:

```text
Applied migrations
Pending migrations
Migration order
Target migration state
```

For example:

```text
Files:
001
002
003
004

Applied:
001
002

Expected pending:
003
004
```

The planner should not execute SQL itself.

This distinction is important because planning must remain safe and inspectable.

---

# 14. Runner Tests

The migration runner is responsible for applying and rolling back migrations.

Tests should verify:

```text
Apply migration
Rollback migration
Apply multiple migrations
Rollback multiple migrations
Record history
Remove history
Handle execution failures
```

Failure tests are especially important.

For example:

```text
Migration SQL fails
      │
      ▼
Runner reports error
      │
      ▼
Failed migration is not recorded
```

Where transactional behavior supports rollback, the test should also verify the resulting database state.

---

# 15. Schema Tests

Schema tests verify database inspection.

Typical cases include:

```text
Create table
Inspect table
Inspect columns
Inspect column types
Inspect nullability
Inspect indexes
```

Schema tests should also verify that structural information is represented consistently.

---

# 16. Composite Index Ordering

Column ordering is important for composite indexes.

For example:

```sql
CREATE INDEX idx_users_name_email
ON users(name, email);
```

is not equivalent to:

```sql
CREATE INDEX idx_users_name_email
ON users(email, name);
```

The schema test suite therefore verifies that database-defined index column order is preserved.

This prevents schema comparisons from treating structurally different indexes as identical.

---

# 17. Schema Diff Tests

Schema-diff tests compare two schemas and verify that differences are correctly identified.

Examples:

```text
Added table
Removed table
Added column
Removed column
Changed column
Added index
Removed index
```

A useful test structure is:

```text
Schema A
   │
   ▼
Schema Diff
   ▲
   │
Schema B
```

followed by assertions about the expected differences.

---

# 18. Linter Tests

The SQL linter has dedicated tests for potentially dangerous operations.

Examples include:

```sql
DROP TABLE users;
```

and:

```sql
DELETE FROM users;
```

The test suite also verifies that keywords inside comments and string literals are not incorrectly interpreted as SQL operations.

For example:

```sql
-- DROP TABLE users;

SELECT 'DROP TABLE users';
```

should not be treated as two destructive operations.

Multiline statements are also tested to ensure that formatting does not affect analysis incorrectly.

---

# 19. Explainer Tests

The explanation subsystem is tested to ensure that supported SQL operations are converted into the expected human-readable descriptions.

Tests cover:

```text
CREATE TABLE
DROP TABLE
ALTER TABLE
CREATE INDEX
DROP INDEX
```

and other supported operations.

The parser used for explanations must also distinguish SQL keywords from comments and string literals.

---

# 20. Impact Analysis Tests

Impact-analysis tests verify that migration operations are identified and classified consistently.

For example:

```text
CREATE TABLE
```

should produce information describing the creation of a table.

Likewise:

```text
DROP TABLE
```

should be recognized as a destructive schema operation.

Tests also verify combined migrations containing multiple operations.

---

# 21. Locking Tests

Concurrency-related tests verify the database-locking abstraction.

The general scenario is:

```text
Process A
   │
   ▼
Acquire Lock
   │
   ▼
Process B attempts lock
   │
   ▼
Expected contention behavior
```

The tests verify that the lock mechanism prevents conflicting migration operations according to the backend's locking implementation.

---

# 22. Reproducibility Tests

Reproducibility tests create a fresh database and apply the migration chain.

Conceptually:

```text
Empty Database
      │
      ▼
Apply All Migrations
      │
      ▼
Inspect Schema
      │
      ▼
Generate Schema Representation
      │
      ▼
Compare Expected Result
```

These tests help detect migration chains that work only because an existing database contains hidden historical state.

The current reproducibility test implementation uses SQLite.

---

# 23. CLI Tests

The CLI is tested separately from internal components.

CLI tests verify things such as:

```text
Command parsing
Command output
Exit status
Database setup
Migration execution
Error reporting
Version output
```

For example, the CLI's database-version output is treated as an explicit output contract.

The current expected SQLite label is:

```text
SQLite version:
```

Changing user-facing output should therefore be considered carefully because tests and scripts may depend on it.

---

# 24. CI Tests

The project also tests the CI-oriented functionality.

The CI subsystem combines checks into an automated workflow.

Conceptually:

```text
CI Command
    │
    ├── Validation
    ├── Integrity Checks
    ├── Reproducibility
    └── Database Checks
            │
            ▼
        Exit Status
```

A successful CI run should produce a successful process exit status.

Failures should propagate as a non-zero result.

---

# 25. Logging Tests

Logging behavior is tested where appropriate.

The logging subsystem supports configurable logging behavior, including:

```text
quiet
verbose
log level
```

The tests help ensure that:

- handlers are not unnecessarily duplicated
- logging configuration is respected
- invalid levels are handled correctly
- quiet and verbose behavior remains predictable

---

# 26. Performance Tests

The project includes performance-oriented utilities and tests.

Performance tests should be interpreted carefully.

Their purpose is primarily to:

```text
Measure
Compare
Detect obvious regressions
```

rather than to guarantee a specific execution time on every machine.

Performance results depend on:

```text
CPU
Disk
Database engine
Database size
Operating system
Python version
```

Therefore, performance tests should not be treated as universal benchmarks.

---

# 27. Temporary Test Resources

Tests should avoid modifying permanent development databases whenever possible.

Temporary resources are preferred:

```text
Temporary directory
      │
      ├── Temporary database
      └── Temporary migrations
```

After the test:

```text
Cleanup
```

This improves isolation and reduces accidental state leakage between tests.

---

# 28. Test Isolation

Tests should be independent.

A test should not rely on another test having:

```text
Created a table
Applied a migration
Configured a database
Created a file
```

before it runs.

Instead, each test should construct the state it requires.

This makes the test suite:

- reproducible
- parallelization-friendly
- easier to debug
- less sensitive to execution order

---

# 29. Full Test Run

The complete test suite can be run with:

```bash
python -m pytest
```

A successful run should report all tests passing.

The project reached a test baseline of:

```text
300 passed
```

during the final testing and architecture phase.

This number represents the project state at that milestone and may change as new tests are added.

---

# 30. Compilation Checks

In addition to pytest, Python source files can be checked with:

```bash
python -m compileall src
```

This provides a basic syntax/compilation-level verification of the source tree.

It does not replace behavioral testing.

The two checks serve different purposes:

```text
compileall
   │
   └── Syntax / compilation verification

pytest
   │
   └── Behavioral verification
```

---

# 31. CLI Smoke Tests

After running the automated tests, basic CLI smoke tests can verify that the installed or local CLI still starts correctly.

Examples include:

```bash
dbmigrate --help
dbmigrate version
```

Depending on the environment, additional safe read-only commands can be exercised.

Smoke tests are useful for catching packaging or command-entry-point problems that unit tests may not expose.

---

# 32. Continuous Integration

The project includes a GitHub Actions workflow:

```text
.github/workflows/ci.yml
```

The purpose of the workflow is to run automated checks in a clean environment.

A CI pipeline provides an additional verification layer because it does not depend entirely on the developer's local machine.

Conceptually:

```text
Git Push
   │
   ▼
GitHub Actions
   │
   ├── Install dependencies
   ├── Run tests
   ├── Run checks
   └── Report result
```

---

# 33. Why CI Matters

Local tests can pass while a project still fails in a clean environment because of:

- missing dependencies
- undeclared package requirements
- environment-specific assumptions
- untracked files
- incorrect configuration
- packaging problems

CI helps expose these problems.

This is particularly important for a portfolio project because it demonstrates that the project can be verified outside the developer's local environment.

---

# 34. CI and Database Support

Multi-database support introduces additional testing considerations.

SQLite can generally run directly inside a CI environment.

PostgreSQL and MySQL require database services when their integration tests are enabled.

Conceptually:

```text
CI Environment
      │
      ├── Python
      │
      ├── SQLite
      │
      ├── PostgreSQL
      │
      └── MySQL
```

The exact services enabled depend on the CI configuration and the tests being executed.

---

# 35. Testing Failure Paths

A reliable migration tool must test failure behavior, not only successful execution.

Examples include:

```text
Invalid SQL
Invalid migration
Duplicate migration version
Checksum mismatch
Database connection failure
Lock acquisition failure
Rollback failure
Invalid configuration
```

The important question is not simply:

> Did the command fail?

It is also:

> Did the system remain in a safe and understandable state after the failure?

---

# 36. Testing Integrity

Integrity tests verify relationships between multiple pieces of state.

For example:

```text
Migration File
      │
      ▼
Checksum
      │
      ▼
Migration History
```

and:

```text
Migration Chain
      │
      ▼
Fresh Database
      │
      ▼
Final Schema
```

Testing these relationships is important because migration correctness cannot always be established by testing isolated functions.

---

# 37. Testing Architecture

The project's test architecture can be viewed as several layers:

```text
                ┌───────────────────┐
                │    CLI Tests      │
                └─────────┬─────────┘
                          │
                ┌─────────▼─────────┐
                │ Integration Tests │
                └─────────┬─────────┘
                          │
          ┌───────────────┼───────────────┐
          │               │               │
          ▼               ▼               ▼
     Migration Tests  Database Tests  Schema Tests
          │               │               │
          └───────────────┼───────────────┘
                          │
                          ▼
                    Unit Tests
```

The layers complement one another.

---

# 38. Testing Before Release

A practical final verification sequence is:

```bash
python -m pytest
```

then:

```bash
python -m compileall src
```

then basic CLI smoke tests:

```bash
dbmigrate --help
dbmigrate version
```

Then inspect the repository:

```bash
git status
```

and review changes:

```bash
git diff
```

The exact release process may also include documentation checks and CI verification.

---

# 39. Regression Testing

Every bug fixed in the project should ideally receive a regression test when practical.

For example, if a database-specific placeholder bug is discovered:

```text
Bug
 │
 ▼
Fix
 │
 ▼
Regression Test
 │
 ▼
Future test runs
```

This prevents the same issue from silently returning later.

The same principle applies to:

- CLI output
- schema ordering
- migration parsing
- transaction behavior
- checksum handling
- database-specific behavior

---

# 40. Test Suite as Architecture Documentation

The test suite is not only a correctness mechanism.

It also documents expected behavior.

For example, a test asserting:

```text
SQLite version:
```

documents part of the CLI's user-facing contract.

A test asserting composite index ordering documents an important schema invariant.

A test asserting checksum behavior documents migration-integrity expectations.

Therefore:

```text
Implementation
      +
Tests
      =
Executable specification
```

---

# 41. Testing Limitations

Automated tests cannot reproduce every possible production database environment.

Potential differences include:

- database versions
- operating systems
- filesystem behavior
- network conditions
- concurrent workloads
- database configuration
- external schema modifications

Passing tests therefore provides evidence of correctness within the tested scenarios, not an absolute guarantee for every possible environment.

---

# 42. Summary

The testing strategy for `dbmigrate` combines:

```text
Unit Tests
Integration Tests
Database Tests
Schema Tests
CLI Tests
Failure Tests
Integrity Tests
Reproducibility Tests
Performance Tests
CI Tests
```

The core local verification workflow is:

```bash
python -m pytest
python -m compileall src
dbmigrate --help
dbmigrate version
```

The project reached a baseline of **300 passing tests** during final architecture and testing work.

The overall testing philosophy is:

```text
Test Components
      +
Test Database Behavior
      +
Test Integration
      +
Test Failure Paths
      +
Test Reproducibility
      +
Test in CI
      =
Higher Confidence in Migration Safety
```