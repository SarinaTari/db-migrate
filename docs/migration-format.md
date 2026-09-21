# Migration Format

## Overview

A migration is a versioned SQL file that describes a database schema change.

Each migration contains two sections:

- `up` — applies the change
- `down` — reverses the change

Migrations are stored in the project's configured migrations directory.

The default directory is:

```text
migrations/
```

A typical migration looks like this:

```sql
-- migration: 001
-- name: create_users

-- +up

CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);

-- +down

DROP TABLE users;
```

---

# Migration Structure

A migration contains four important pieces of metadata or content:

1. migration version
2. migration name
3. `up` SQL
4. `down` SQL

The general structure is:

```text
-- migration: <version>
-- name: <name>

-- +up

<SQL that applies the migration>

-- +down

<SQL that reverses the migration>
```

---

# Migration Version

The migration version identifies the migration and determines its ordering.

Example:

```sql
-- migration: 001
```

Later migrations can use higher versions:

```text
001
002
003
004
```

The migration system uses the version to determine execution order.

Versions must be valid and unique within the migration set.

---

# Migration Name

Each migration has a human-readable name.

Example:

```sql
-- name: create_users
```

The name describes the purpose of the migration.

Good migration names are:

```text
create_users
add_email_to_users
create_orders
add_order_indexes
```

The migration name becomes part of the migration metadata and is also stored in migration history.

---

# Up Section

The `up` section contains SQL that applies the schema change.

It begins with:

```sql
-- +up
```

Example:

```sql
-- +up

CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);
```

The SQL in this section is executed when the migration is applied.

Conceptually:

```text
Migration
   │
   ▼
up SQL
   │
   ▼
Database Schema Changes
```

---

# Down Section

The `down` section contains SQL that reverses the migration.

It begins with:

```sql
-- +down
```

Example:

```sql
-- +down

DROP TABLE users;
```

The down section is used when the migration is rolled back.

Conceptually:

```text
Applied Migration
       │
       ▼
    down SQL
       │
       ▼
Previous Schema State
```

A migration should generally provide a meaningful reverse operation whenever the change can reasonably be reversed.

---

# Complete Example

A complete migration can look like:

```sql
-- migration: 002
-- name: add_email_to_users

-- +up

ALTER TABLE users
ADD COLUMN email TEXT;

-- +down

ALTER TABLE users
DROP COLUMN email;
```

The migration system parses the file into structured migration information:

```text
Version:
002

Name:
add_email_to_users

Up SQL:
ALTER TABLE users
ADD COLUMN email TEXT;

Down SQL:
ALTER TABLE users
DROP COLUMN email;
```

---

# Migration File Naming

Migration files are versioned SQL files stored in the migrations directory.

A typical naming convention is:

```text
<version>_<name>.sql
```

Examples:

```text
001_create_users.sql
002_add_email_to_users.sql
003_create_orders.sql
```

The filename communicates the migration's order and purpose.

The migration parser validates the migration metadata contained in the file rather than relying only on the filename.

---

# Migration Ordering

Migrations are executed according to their version.

For example:

```text
001_create_users.sql
002_add_email.sql
003_create_orders.sql
```

results in:

```text
001
 ↓
002
 ↓
003
```

The migration system validates ordering and detects invalid or duplicate migration versions.

Migrations should therefore be created in a controlled sequence rather than manually assigning conflicting versions.

---

# Migration Creation

New migrations can be created using the CLI:

```bash
dbmigrate create <name>
```

For example:

```bash
dbmigrate create create_users
```

The migration creator determines the next migration version and creates a new SQL migration file.

The generated migration provides the expected structure for the `up` and `down` sections.

---

# Migration Parsing

Migration parsing is handled by:

```text
src/dbmigrate/migration.py
```

The parser extracts:

- version
- name
- up SQL
- down SQL

Malformed migration files result in migration parsing errors rather than being silently accepted.

This ensures that invalid migration definitions are detected before they reach the execution stage.

---

# Migration Discovery

Migration discovery searches the configured migration directory for migration files.

The discovery process:

1. locates the migrations directory
2. identifies migration files
3. parses the migration metadata
4. validates migration definitions
5. orders migrations by version

The result is a collection of structured migration objects used by the planner, validator, runner, and analysis tools.

---

# Migration Checksums

Each migration has a deterministic SHA-256 checksum.

The checksum is calculated from migration metadata and SQL content.

The checksum includes:

```text
migration version
migration name
up SQL
down SQL
```

This means that changing the migration after it has been recorded can be detected.

For example:

```text
Original migration
       │
       ▼
SHA-256 checksum
       │
       ▼
Stored in schema_migrations
```

Later:

```text
Current migration
       │
       ▼
SHA-256 checksum
       │
       ▼
Compare with stored checksum
```

If the values differ, the migration has changed since it was recorded.

---

# Migration History

Applied migrations are recorded in:

```text
schema_migrations
```

The table contains information including:

```text
version
name
checksum
applied_at
```

A simplified representation is:

```sql
CREATE TABLE schema_migrations (
    version INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    checksum TEXT NOT NULL,
    applied_at TIMESTAMP NOT NULL
);
```

This table allows `dbmigrate` to distinguish between:

```text
Migration file exists
```

and:

```text
Migration has actually been applied
```

---

# Migration Validation

Migration validation checks the migration set before execution.

Validation can identify problems such as:

- invalid migration versions
- invalid migration names
- duplicate versions
- duplicate identifiers
- malformed migration definitions
- checksum mismatches

Validation is separate from execution so problems can be identified before database changes occur.

---

# Migration Safety

The migration system also analyzes potentially dangerous SQL.

Examples include:

```sql
DROP TABLE users;
```

```sql
DROP COLUMN email;
```

```sql
DELETE FROM users;
```

```sql
UPDATE users SET name = 'unknown';
```

The safety and linting systems can identify destructive patterns such as:

- dropping tables
- dropping columns
- `DELETE` without a `WHERE` clause
- `UPDATE` without a `WHERE` clause
- other potentially dangerous schema or data operations

These checks are intended to make potentially destructive migrations visible before execution.

---

# SQL Comments and Migration Metadata

Migration metadata is expressed using SQL comments.

For example:

```sql
-- migration: 001
-- name: create_users
```

The section markers are also comments:

```sql
-- +up
```

and:

```sql
-- +down
```

This keeps migration files valid SQL text while allowing `dbmigrate` to interpret their structure.

---

# SQL Content

The migration system stores the SQL sections as migration content.

For example:

```sql
-- +up

CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);

CREATE INDEX idx_users_name
ON users(name);
```

Multiple SQL statements can be included in a migration section.

The SQL is ultimately executed by the selected database implementation.

Database-specific SQL is allowed according to the capabilities and dialect of the target database.

`dbmigrate` does not attempt to translate arbitrary SQL between database engines.

---

# Database Portability

The migration format itself is database-independent, but the SQL contained within a migration may be database-specific.

For example:

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY
);
```

may work across multiple engines, while other SQL syntax may not.

The project therefore separates:

```text
Migration Format
```

from:

```text
Database SQL Dialect
```

The migration engine provides database abstraction, dialect handling, and capability information, but it does not attempt to automatically rewrite arbitrary migration SQL from one database dialect into another.

---

# Reversibility

The `down` section is intended to reverse the corresponding `up` operation.

For example:

```sql
-- +up

CREATE TABLE users (
    id INTEGER PRIMARY KEY
);

-- +down

DROP TABLE users;
```

The relationship is:

```text
up:
previous schema
      │
      ▼
new schema

down:
new schema
   │
   ▼
previous schema
```

Reversibility depends on the SQL written by the migration author.

Some data-destructive operations cannot be perfectly reversed.

For example:

```sql
DELETE FROM users;
```

cannot generally be reversed without having preserved the deleted data separately.

Therefore, a syntactically valid `down` section does not guarantee that all data effects of an `up` migration are recoverable.

---

# Migration Best Practices

## Keep Migrations Focused

A migration should generally represent one logical schema change.

Prefer:

```text
001_create_users.sql
002_add_email_to_users.sql
003_create_orders.sql
```

over one large migration containing unrelated changes.

---

## Avoid Editing Applied Migrations

Once a migration has been applied and recorded in migration history, its contents should generally be treated as immutable.

Instead of modifying an existing migration, create a new migration that changes the schema.

For example:

```text
001_create_users.sql
002_add_email_to_users.sql
```

rather than modifying:

```text
001_create_users.sql
```

after it has already been applied.

This preserves migration history and checksum integrity.

---

## Write a Meaningful Down Migration

Where practical, the `down` section should reverse the schema change made by `up`.

For example:

```sql
-- +up

CREATE TABLE orders (
    id INTEGER PRIMARY KEY
);

-- +down

DROP TABLE orders;
```

---

## Review Destructive Operations

Before applying migrations, review potentially destructive operations such as:

```sql
DROP TABLE
DROP COLUMN
DELETE
UPDATE
```

Use the project's analysis tools to make potentially dangerous operations visible.

---

## Keep Migration Versions Unique

Every migration should have a unique version.

Avoid manually assigning a version that already exists.

The migration creator can determine the next available version.

---

# Migration Format Summary

A valid migration follows this general structure:

```sql
-- migration: <version>
-- name: <name>

-- +up

<SQL>

-- +down

<SQL>
```

The migration system then transforms the file into structured migration data:

```text
Migration
├── version
├── name
├── up_sql
└── down_sql
```

That migration object can then be passed through:

```text
Validation
    │
    ▼
Checksum
    │
    ▼
Planning
    │
    ▼
Safety Analysis
    │
    ▼
Execution
    │
    ▼
History
```

This format provides a simple, explicit representation of database schema changes while allowing the rest of `dbmigrate` to provide validation, safety, planning, execution, and integrity features around it.