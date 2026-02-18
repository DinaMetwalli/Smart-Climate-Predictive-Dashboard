CREATE TABLE IF NOT EXISTS users(
    id uuid NOT NULL UNIQUE,
    username text NOT NULL UNIQUE,
    password_hash text NOT NULL,
    creation_timestamp TIMESTAMP NOT NULL,
    PRIMARY KEY (id)
)