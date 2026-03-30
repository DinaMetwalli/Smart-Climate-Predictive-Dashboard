CREATE TABLE IF NOT EXISTS analysis_stats(
    id uuid NOT NULL DEFAULT gen_random_uuid() UNIQUE,
    rmse_val numeric(8,3) NOT NULL,
    mean_bias_val numeric(8,3) NOT NULL,
    pearson_corr_val numeric(8,3) NOT NULL,
    analysis_id uuid NOT NULL,
    region_id uuid NOT NULL,
    PRIMARY KEY (id),
    CONSTRAINT analysis_FK FOREIGN KEY (analysis_id)
    REFERENCES analysis_history(id),
    CONSTRAINT region_FK FOREIGN KEY (region_id)
    REFERENCES regions(id)
)