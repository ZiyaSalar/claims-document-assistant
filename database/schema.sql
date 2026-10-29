
-- 1. Claims table
IF OBJECT_ID('dbo.Claims', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Claims (
        claim_id VARCHAR(36) PRIMARY KEY,
        claimant_name NVARCHAR(200) NOT NULL,
        policy_number NVARCHAR(100) NOT NULL,
        claim_type NVARCHAR(100) NOT NULL,
        status NVARCHAR(50) NOT NULL
            DEFAULT 'submitted',
        verification_status NVARCHAR(50) NOT NULL
            DEFAULT 'incomplete',
        created_at DATETIME2 NOT NULL
            DEFAULT SYSUTCDATETIME()
    );
END;
GO

-- 2. Documents table
IF OBJECT_ID('dbo.Documents', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Documents (
        document_id VARCHAR(36) PRIMARY KEY,
        claim_id VARCHAR(36) NOT NULL,

        file_name NVARCHAR(255) NOT NULL,
        content_type NVARCHAR(100),
        file_size_bytes BIGINT,

        -- Azure Blob Storage reference
        storage_backend NVARCHAR(30),
        blob_name NVARCHAR(1024),

        -- Validation and duplicate detection
        sha256 CHAR(64),
        page_count INT,
        text_length INT,
        processing_status NVARCHAR(50),
        is_duplicate BIT NOT NULL DEFAULT 0,
        duplicate_of VARCHAR(36),

        -- Document type and classification
        document_type NVARCHAR(100),
        predicted_type NVARCHAR(100),
        needs_review BIT NOT NULL DEFAULT 1,
        classification_json NVARCHAR(MAX),

        -- Initial extracted text storage
        extracted_text NVARCHAR(MAX),

        created_at DATETIME2 NOT NULL
            DEFAULT SYSUTCDATETIME(),

        CONSTRAINT FK_Documents_Claims
            FOREIGN KEY (claim_id)
            REFERENCES dbo.Claims(claim_id),

        CONSTRAINT FK_Documents_Duplicate
            FOREIGN KEY (duplicate_of)
            REFERENCES dbo.Documents(document_id)
    );

    CREATE INDEX IX_Documents_ClaimId
        ON dbo.Documents(claim_id);

    CREATE INDEX IX_Documents_SHA256
        ON dbo.Documents(sha256);
END;
GO
