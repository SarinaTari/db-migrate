# Phase 4 — Migration Format

## Objective

Phase 4 introduces the formal migration file format used by `db-migrate`.

The goal is to establish a reliable representation of database migrations before introducing database connectivity or SQL execution.

---

## Migration Structure

Each migration consists of:

- a numeric version
- a migration name
- an up operation
- a down operation

Example:

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
Filename Convention

Migration files follow:

<version>_<name>.sql

Examples:

001_create_users.sql
002_add_email.sql
003_create_posts.sql

The version must be a positive integer.

The name must begin with a lowercase alphanumeric character and may contain:

lowercase letters
numbers
underscores
hyphens
Metadata Consistency

The filename and metadata must describe the same migration.

For:

001_create_users.sql

the file must contain:

-- migration: 001
-- name: create_users

The parser rejects mismatches.

For example:

001_create_users.sql

with:

-- migration: 002
-- name: create_users

is invalid.

Up and Down Sections

A migration must contain exactly one:

-- +up

marker and exactly one:

-- +down

marker.

The up marker must appear before the down marker.

Both sections must contain SQL.

Domain Model

The parser produces an immutable Migration object:

Migration
├── version
├── name
├── up_sql
├── down_sql
└── path

The model also provides:

identifier
filename

properties.

Parsing Pipeline

Migration processing follows:

Path
 ↓
Filename parsing
 ↓
Metadata parsing
 ↓
Filename/metadata consistency
 ↓
Section extraction
 ↓
Section validation
 ↓
Migration object
Discovery

discover_migrations():

verifies the directory exists
finds .sql files
parses each migration
sorts migrations by version
detects duplicate versions
returns an immutable tuple

Example:

003_create_posts.sql
001_create_users.sql
002_add_email.sql

becomes:

001_create_users
002_add_email
003_create_posts
Why Discovery Is Separate From Parsing

Parsing answers:

"Is this one migration file valid, and what does it contain?"

Discovery answers:

"What migrations exist in this project, and are they collectively valid enough to form an ordered migration set?"

Keeping these responsibilities separate will make later phases easier to test and extend.

Error Handling

Phase 4 introduces:

MigrationError
├── MigrationParseError
└── MigrationDiscoveryError

MigrationParseError is used for problems within an individual migration.

Examples:

invalid filename
missing metadata
metadata mismatch
missing up
missing down
empty SQL section

MigrationDiscoveryError is used for problems involving the migration collection.

Examples:

missing migration directory
migration path is not a directory
duplicate versions
What Phase 4 Does Not Do

The parser does not:

execute SQL
connect to SQLite
connect to PostgreSQL
connect to MySQL
validate SQL syntax against a database
determine whether SQL is semantically correct
modify the filesystem
modify a database

These responsibilities belong to later phases.

Testing

Phase 4 adds tests for:

valid migrations
filename parsing
metadata parsing
filename/metadata mismatches
invalid versions
missing metadata
missing section markers
duplicate markers
incorrect section ordering
empty sections
missing files
invalid extensions
migration discovery
deterministic ordering
duplicate versions
invalid migration directories

The parser is intentionally tested heavily because later migration execution depends on reliable migration objects.

Completion Criteria

Phase 4 is complete when:

migration files have a documented format
migration filenames are validated
metadata is parsed
migration sections are parsed
malformed migrations fail explicitly
migration objects are immutable
migration discovery is deterministic
duplicate versions are rejected
automated tests cover the parser and discovery system
Next Phase

Phase 5 will build on this foundation by strengthening migration discovery and validation.

The next phase will focus on:

project-level migration validation
migration sequence checks
clearer validation reporting
detecting migration-set inconsistencies
preparing the migration collection for database execution

Database connectivity remains outside Phase 5.