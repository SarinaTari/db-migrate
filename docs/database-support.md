# Database Support

## Overview

`dbmigrate` is designed around a database abstraction layer so that the migration system can work with multiple database engines without coupling the migration logic to a single database.

The currently supported database engines are:

- SQLite
- PostgreSQL
- MySQL

The project separates database-specific behavior from migration logic through several components:

```text
Migration System
       │
       ▼
Database Interface
       │
       ├── SQLite
       ├── PostgreSQL
       └── MySQL
```

This architecture allows the same migration lifecycle to be used across different database systems while keeping database-specific behavior inside the appropriate implementation.

---

# 1. Supported Databases

## SQLite

SQLite is the simplest supported database backend and is useful for:

- local development
- testing
- examples
- reproducibility checks
- small projects

A SQLite database is represented by a local database file.

Example:

```text
dbmigrate.db
```

SQLite requires no separate database server.

The project uses Python's built-in `sqlite3` module for SQLite access.

---

## PostgreSQL

PostgreSQL is supported as a server-based relational database.

The project uses the PostgreSQL Python driver:

```text
psycopg
```

PostgreSQL requires connection information such as:

```text
host
port
database
username
password
```

The exact connection configuration is handled by the database configuration and factory layers rather than by individual migration commands.

---

## MySQL

MySQL is supported as another server-based relational database.

The project uses:

```text
mysql.connector
```

for MySQL connections.

Like PostgreSQL, MySQL normally requires:

```text
host
port
database
username
password
```

The database configuration layer provides these settings to the database implementation.

---

# 2. Database Abstraction

The migration system does not directly depend on SQLite, PostgreSQL, or MySQL.

Instead, it communicates with a common database interface.

Conceptually:

```text
Migration Runner
       │
       ▼
Database Interface
       │
       ├──────────────┐
       │              │
       ▼              ▼
SQLite Database   PostgreSQL Database
       │
       └──────────────┐
                      ▼
                MySQL Database
```

The migration runner can therefore operate on a database without needing to know the implementation details of the connection.

This separation is one of the central architectural decisions of the project.

---

# 3. Database Factory

The database factory is responsible for selecting the appropriate database implementation.

Conceptually:

```text
Configuration
     │
     ▼
Database Factory
     │
     ├── sqlite
     ├── postgres
     └── mysql
```

The rest of the application receives a database abstraction rather than constructing database connections itself.

This prevents database-selection logic from being duplicated throughout the codebase.

---

# 4. Database Dialects

Although the migration system uses a common interface, SQL databases do not behave identically.

The project therefore includes a database dialect abstraction.

A dialect represents database-specific SQL behavior.

Examples include:

```text
Parameter placeholders
Identifier handling
Database-specific SQL syntax
```

For example, parameterized queries can use different placeholder styles.

SQLite and MySQL commonly use:

```sql
?
```

while PostgreSQL uses:

```sql
%s
```

The history subsystem uses the configured dialect rather than hard-coding a single placeholder format.

This keeps database-specific SQL details out of generic migration logic.

---

# 5. Database Capabilities

SQL dialect alone does not describe every relevant database behavior.

The project therefore also has a database capability abstraction.

Capabilities describe features or behavioral properties of a database.

Examples include:

```text
Transactional DDL
Locking support
Schema inspection
Database version information
```

Conceptually:

```text
Database
   │
   ├── Dialect
   │
   └── Capabilities
```

This allows higher-level code to ask what a database supports instead of making assumptions based only on its name.

---

# 6. Why Dialects and Capabilities Are Separate

A dialect answers:

> "How should database-specific SQL be written?"

Capabilities answer:

> "What database behavior or feature is available?"

These are different concerns.

For example:

```text
PostgreSQL
├── Dialect
│   └── PostgreSQL SQL conventions
│
└── Capabilities
    ├── locking
    ├── transactional behavior
    └── schema inspection
```

Keeping these concepts separate makes the architecture easier to extend.

---

# 7. Transactions

Transactions are important for migration safety.

The migration runner can use transactions to group operations such as:

```text
Migration SQL
      +
Migration History Update
```

into one logical operation where supported.

Conceptually:

```text
BEGIN
  │
  ├── Execute migration
  │
  ├── Record migration
  │
  ▼
COMMIT
```

If execution fails:

```text
BEGIN
  │
  ├── Execute migration
  │
  ├── Failure
  │
  ▼
ROLLBACK
```

The exact transactional behavior depends on the selected database and its capabilities.

The application should therefore use the capability abstraction rather than assuming that all databases behave identically.

---

# 8. Database Locking

Concurrent migration execution is dangerous because two processes may attempt to modify the schema at the same time.

The project provides database-specific locking support.

The locking layer abstracts this behavior:

```text
Migration Runner
       │
       ▼
Database Lock
       │
       ├── SQLite locking
       ├── PostgreSQL advisory locking
       └── MySQL named locking
```

The higher-level migration runner does not need to implement the details of each locking mechanism.

---

# 9. SQLite Locking

SQLite uses a filesystem-based lock through the project's database-locking implementation.

Conceptually:

```text
Migration Process
       │
       ▼
Acquire local lock
       │
       ▼
Execute migration
       │
       ▼
Release lock
```

This prevents multiple `dbmigrate` processes from intentionally entering the migration critical section at the same time.

SQLite's database-level behavior still applies independently of the application lock.

---

# 10. PostgreSQL Locking

PostgreSQL uses an advisory-lock mechanism.

The application can acquire a lock associated with the migration process before performing migration operations.

Conceptually:

```text
Application
     │
     ▼
PostgreSQL Advisory Lock
     │
     ▼
Migration
     │
     ▼
Release Lock
```

The lock is managed by PostgreSQL rather than by a local lock file.

---

# 11. MySQL Locking

MySQL uses a database-level named lock.

The project uses MySQL's locking mechanism through:

```sql
GET_LOCK(...)
```

The conceptual workflow is:

```text
Application
     │
     ▼
GET_LOCK(...)
     │
     ▼
Migration
     │
     ▼
Release Named Lock
```

This allows migration coordination to occur through the database itself.

---

# 12. Schema Inspection

Database support also includes schema inspection.

The schema layer can inspect database structures such as:

```text
Tables
Columns
Types
Nullable properties
Indexes
Constraints
```

The result is represented using common Python structures rather than exposing raw database-driver-specific objects to the rest of the application.

Conceptually:

```text
SQLite ────────┐
               │
PostgreSQL ────┼──► Schema Representation
               │
MySQL ─────────┘
```

This common representation enables higher-level schema analysis.

---

# 13. Schema Comparison

Once a database schema has been represented in a common form, it can be compared with another schema.

For example:

```text
Schema A
   │
   ├── users
   └── orders

Schema B
   │
   ├── users
   ├── orders
   └── products
```

The schema-diff system can identify structural differences.

This is useful for:

- migration analysis
- verification
- reproducibility
- development workflows

---

# 14. Database Version Information

The database abstraction also provides database version information.

The CLI can expose database information through its diagnostics and database-related functionality.

For example:

```text
SQLite version: ...
```

Database-specific version queries remain inside the appropriate database implementation.

The CLI does not need to know how each database reports its version.

---

# 15. Connection Management

Connection creation is separated from migration logic.

The general architecture is:

```text
Configuration
      │
      ▼
Database Factory
      │
      ▼
Database Implementation
      │
      ▼
Connection
```

This prevents individual commands from duplicating connection setup.

It also makes it easier to change database configuration without changing migration algorithms.

---

# 16. Configuration

Database configuration can specify information required to connect to the selected backend.

Depending on the database, this can include:

```text
Database type
Host
Port
Database name
Username
Password
SQLite path
```

SQLite primarily requires a database path, while server-based databases require connection parameters.

The configuration layer keeps these details separate from the migration logic.

---

# 17. Cross-Database Migration Logic

The goal of the abstraction is not to translate arbitrary SQL between database engines.

For example, `dbmigrate` does not attempt to transform:

```sql
PostgreSQL-specific SQL
```

automatically into:

```sql
SQLite SQL
```

or:

```sql
MySQL SQL
```

Instead, migration authors are responsible for writing SQL appropriate for the target database.

The abstraction provides common infrastructure for:

- connections
- transactions
- migration history
- locking
- schema inspection
- database metadata
- parameterized internal queries

---

# 18. SQL Portability

SQL migrations should be written with the intended target database in mind.

For example, a migration using only widely supported SQL may work across several databases:

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);
```

However, database-specific syntax may require a database-specific migration.

For example:

```sql
-- PostgreSQL-specific syntax
```

should not automatically be assumed to work on SQLite or MySQL.

The project's database abstraction does not hide genuine SQL dialect differences.

---

# 19. Migration History Portability

The migration history table is created and accessed through the database abstraction.

The conceptual structure is:

```text
schema_migrations
├── version
├── name
├── checksum
└── applied_at
```

The history implementation uses the database dialect when executing parameterized queries.

This is important because parameter placeholder syntax differs between database engines.

The migration history logic therefore remains database-independent while the dialect supplies database-specific details.

---

# 20. Database Capability Matrix

The project intentionally keeps database-specific behavior explicit.

| Capability | SQLite | PostgreSQL | MySQL |
|---|---|---|---|
| Local database file | Yes | No | No |
| Server-based database | No | Yes | Yes |
| Python driver | `sqlite3` | `psycopg` | `mysql.connector` |
| Database dialect | Yes | Yes | Yes |
| Capability abstraction | Yes | Yes | Yes |
| Schema inspection | Yes | Yes | Yes |
| Database-level locking | SQLite-specific handling | Advisory lock | Named lock |
| Transaction support | Supported according to SQLite behavior | Supported | Supported |
| Reproducibility workflow | Supported | Not currently used by the reproducibility implementation | Not currently used by the reproducibility implementation |

The capability matrix describes the current project implementation rather than claiming that the underlying databases lack features not currently exposed by `dbmigrate`.

---

# 21. Adding Another Database

The architecture is designed so that another database can be added without rewriting the migration system.

A new backend would conceptually require:

```text
New Database Implementation
          │
          ├── Database interface
          ├── Database dialect
          ├── Database capabilities
          ├── Connection handling
          ├── Schema inspection
          └── Locking behavior
```

The database factory would then be extended to construct the new implementation.

Higher-level components such as:

```text
Migration
Planner
Runner
History
Status
Linter
Schema Diff
Impact Analysis
```

should remain largely database-independent.

---

# 22. Database Layer Architecture

The database portion of the architecture can be summarized as:

```text
                    ┌──────────────────┐
                    │   Configuration  │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │ Database Factory │
                    └────────┬─────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
          ┌───────┐      ┌──────────┐   ┌───────┐
          │SQLite │      │PostgreSQL│   │ MySQL │
          └───┬───┘      └────┬─────┘   └───┬───┘
              │               │             │
              └───────────────┼─────────────┘
                              ▼
                     Common Database API
                              │
              ┌───────────────┼───────────────┐
              │               │               │
              ▼               ▼               ▼
          Dialect        Capabilities       Lock
                              │
                              ▼
                       Schema Inspection
```

---

# 23. Design Goals

The multi-database architecture has several goals.

## Keep Migration Logic Independent

Migration planning and execution should not contain database-specific connection code.

## Isolate SQL Differences

Database-specific syntax and parameter behavior belong in the dialect layer.

## Make Capabilities Explicit

The application should not assume that every database provides identical transactional or locking behavior.

## Centralize Connection Creation

Database factories should own database implementation selection.

## Support Extension

Adding another database should primarily require implementing the database abstraction and registering the new backend.

---

# 24. Current Scope

The current database scope intentionally focuses on relational databases:

```text
SQLite
PostgreSQL
MySQL
```

The project does not attempt to support:

- NoSQL databases
- arbitrary external data stores
- automatic SQL translation
- ORM-specific migration systems
- distributed database orchestration

The objective is to provide a clear and extensible relational database migration architecture rather than an abstraction over every possible storage technology.

---

# Summary

`dbmigrate` separates database-independent migration logic from database-specific behavior.

The architecture consists of:

```text
Database Interface
       │
       ├── Database Implementations
       │
       ├── Database Dialects
       │
       ├── Database Capabilities
       │
       ├── Database Locking
       │
       └── Schema Inspection
```

SQLite, PostgreSQL, and MySQL are supported through this architecture.

The result is a migration system that can share the same high-level workflow across databases while keeping genuine database differences explicit and isolated.