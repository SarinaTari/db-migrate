# Blog Database Example

This example demonstrates a small database schema managed with `dbmigrate`.

The example contains three migrations:

```text
001_create_users
        ↓
002_create_posts
        ↓
003_add_user_email
```

## Database Schema

The resulting database contains:

### users

```text
id
name
email
```

### posts

```text
id
user_id
title
body
created_at
```

The `posts.user_id` column references `users.id`.

---

## Migration Files

```text
migrations/
├── 001_create_users.sql
├── 002_create_posts.sql
└── 003_add_user_email.sql
```

### Migration 001

Creates the `users` table.

### Migration 002

Creates the `posts` table and connects posts to users through a foreign key.

### Migration 003

Adds an `email` column to the `users` table.

---

## Running the Example

From the project root:

```bash
dbmigrate up
```

The migration system applies the migrations in version order.

Check the migration state:

```bash
dbmigrate status
```

Inspect migration history:

```bash
dbmigrate history
```

Inspect the current version:

```bash
dbmigrate current
```

---

## Validation and Analysis

Validate the migration chain:

```bash
dbmigrate validate
```

Create a migration plan:

```bash
dbmigrate plan
```

Lint the migrations:

```bash
dbmigrate lint
```

Explain migration operations:

```bash
dbmigrate explain
```

Analyze migration impact:

```bash
dbmigrate impact
```

Inspect the resulting schema:

```bash
dbmigrate schema
```

---

## Rolling Back

The migrations contain explicit `down` sections.

A rollback can therefore reverse the migration sequence when the database and migration operations support it.

For example:

```bash
dbmigrate down
```

Afterward, inspect the state again:

```bash
dbmigrate status
```

---

## Purpose

This example is intentionally small.

Its purpose is to demonstrate the complete migration lifecycle without introducing application-specific complexity:

```text
Migration files
      ↓
Discovery
      ↓
Validation
      ↓
Planning
      ↓
Execution
      ↓
History
      ↓
Schema inspection
      ↓
Analysis
```

For a larger application, the same migration structure can be extended with additional migrations.