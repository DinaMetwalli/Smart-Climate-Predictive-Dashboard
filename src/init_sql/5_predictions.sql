CREATE TABLE IF NOT EXISTS predictions(
    id uuid NOT NULL DEFAULT gen_random_uuid() UNIQUE,
    month_index integer NOT NULL,
    prediction_val numeric(8,3) NOT NULL,
    analysis_id uuid NOT NULL,
    region_id uuid NOT NULL,
    PRIMARY KEY (id),
    CONSTRAINT analysis_FK FOREIGN KEY (analysis_id)
    REFERENCES analysis_history(id),
    CONSTRAINT region_FK FOREIGN KEY (region_id)
    REFERENCES regions(id)
)