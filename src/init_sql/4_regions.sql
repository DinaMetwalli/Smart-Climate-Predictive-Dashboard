CREATE TABLE IF NOT EXISTS regions(
    id uuid NOT NULL DEFAULT gen_random_uuid() UNIQUE,
    region text NOT NULL UNIQUE
)