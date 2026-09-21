-- migration: 003
-- name: add_user_email

-- +up

ALTER TABLE users
ADD COLUMN email TEXT;

-- +down

ALTER TABLE users
DROP COLUMN email;