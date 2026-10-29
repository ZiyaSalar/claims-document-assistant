IF COL_LENGTH('dbo.Claims', 'document_status_json') IS NULL
BEGIN
    ALTER TABLE dbo.Claims
    ADD document_status_json NVARCHAR(MAX) NULL;
END;