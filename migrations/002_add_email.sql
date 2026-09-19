-- migration: 002
-- name: add_email

-- +up

ALTER TABLE users ADD COLUMN email TEXT;

-- +down

ALTER TABLE users DROP COLUMN email;