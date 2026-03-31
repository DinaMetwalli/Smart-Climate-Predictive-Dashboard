CREATE TABLE IF NOT EXISTS analysis_history(
    id uuid NOT NULL DEFAULT gen_random_uuid() UNIQUE,
    analysis_name text NOT NULL,
    creation_timestamp TIMESTAMP NOT NULL,
    prediction_start_date TIMESTAMP NOT NULL,
    user_id uuid NOT NULL,
    PRIMARY KEY (id),
    CONSTRAINT user_FK FOREIGN KEY (user_id)
    REFERENCES users(id)
)