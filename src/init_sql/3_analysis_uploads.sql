CREATE TABLE IF NOT EXISTS analysis_uploads(
    id uuid NOT NULL UNIQUE,
    analysis_id uuid NOT NULL,
    dataset_file_name text NOT NULL,
    PRIMARY KEY (id),
    CONSTRAINT analysis_FK FOREIGN KEY (analysis_id)
    REFERENCES analysis_history(id)
)