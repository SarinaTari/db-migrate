# Database Migrations

## What Is a Migration?

A database migration is a versioned change to a database schema.

Examples include:

- creating a table
- adding a column
- creating an index
- changing constraints
- removing a table

A migration records the intended transition from one schema state to another.

---

## Up and Down

A migration normally contains two directions.

### Up

Moves the database forward:

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY
);
Down

Reverses the change:

DROP TABLE users;

The migration system will eventually use these sections for applying and rolling back changes.

Versioning

Each migration receives a unique numeric version.

Example:

001_create_users.sql
002_add_email.sql
003_create_posts.sql

The versions establish ordering.

Why Versioning Matters

Without versioning, a migration tool cannot reliably determine:

what has already been applied
what remains pending
what should execute next
what should be rolled back

Versioning provides an explicit schema history.

Migration History

Later phases will maintain database-side migration history.

Conceptually:

CREATE TABLE schema_migrations (
    version INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    checksum TEXT NOT NULL,
    applied_at TIMESTAMP NOT NULL
);

This table is not implemented yet.

Migration Integrity

Later versions of the project will use checksums to detect when an already-applied migration has been modified.

The intended model is:

Migration file
      ↓
Checksum
      ↓
Stored history
      ↓
Compare

This prevents silent modification of migration history.

Database Backends

The project will eventually support:

SQLite
PostgreSQL
MySQL

The migration engine should remain independent from the concrete database backend.

SQL

SQL remains the language of the migration itself.

The tool manages:

migration ordering
validation
execution
history
integrity
analysis

It does not attempt to replace SQL.

Current Phase

Phase 4 establishes the migration format and parser.

No SQL is executed yet.