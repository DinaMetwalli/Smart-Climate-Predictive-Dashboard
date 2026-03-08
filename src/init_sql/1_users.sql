CREATE TABLE IF NOT EXISTS users(
    id uuid NOT NULL DEFAULT gen_random_uuid() UNIQUE,
    username text NOT NULL UNIQUE,
    password_hash text NOT NULL,
    creation_timestamp TIMESTAMP NOT NULL,
    active BOOLEAN NOT NULL,
    PRIMARY KEY (id)
)