DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM regions) THEN
        INSERT INTO regions(region)
        VALUES
            ('africa'),
            ('asia'),
            ('europe'),
            ('northAmerica'),
            ('southAmerica'),
            ('oceania');
    END IF;
END
$$;