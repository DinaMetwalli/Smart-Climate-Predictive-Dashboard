CREATE TABLE IF NOT EXISTS analysis_history(
    id uuid NOT NULL UNIQUE,
    analysis_name text NOT NULL,
    creation_timestamp TIMESTAMP NOT NULL,
    user_id uuid NOT NULL,
    PRIMARY KEY (id),
    CONSTRAINT user_FK FOREIGN KEY (user_id)
    REFERENCES users(id)
)