
import json

from sqlalchemy import text

from backend.app.database import get_database_backend, get_engine
from backend.app.services.claim_store import claims


def _use_azure():
    return get_database_backend() == "azure"


# -------------------- CLAIMS --------------------

def save_claim(claim: dict) -> dict:
    if not _use_azure():
        claims[claim["claim_id"]] = claim
        return claim

    query = text("""
        INSERT INTO dbo.Claims (
            claim_id, claimant_name, policy_number, claim_type,
            status, verification_status, document_status_json
        )
        VALUES (
            :claim_id, :claimant_name, :policy_number, :claim_type,
            :status, :verification_status, :document_status_json
        )
    """)

    params = {
        **{k: claim[k] for k in (
            "claim_id", "claimant_name", "policy_number",
            "claim_type", "status", "verification_status"
        )},
        "document_status_json": json.dumps(
            claim.get("document_status", {})
        ),
    }

    with get_engine().begin() as conn:
        conn.execute(query, params)

    return claim


def _claim_from_row(row):
    claim = dict(row)
    claim["document_status"] = json.loads(
        claim.pop("document_status_json", None) or "{}"
    )
    return claim


def get_claim_by_id(claim_id: str):
    if not _use_azure():
        return claims.get(claim_id)

    query = text("""
        SELECT claim_id, claimant_name, policy_number, claim_type,
               status, verification_status, document_status_json
        FROM dbo.Claims
        WHERE claim_id = :claim_id
    """)

    with get_engine().connect() as conn:
        row = conn.execute(
            query, {"claim_id": claim_id}
        ).mappings().first()

    return _claim_from_row(row) if row else None


def get_all_claims() -> list[dict]:
    if not _use_azure():
        return list(claims.values())

    query = text("""
        SELECT claim_id, claimant_name, policy_number, claim_type,
               status, verification_status, document_status_json
        FROM dbo.Claims
        ORDER BY created_at DESC
    """)

    with get_engine().connect() as conn:
        rows = conn.execute(query).mappings().all()

    return [_claim_from_row(row) for row in rows]


def update_claim(claim: dict) -> dict:
    if not _use_azure():
        claims[claim["claim_id"]] = claim
        return claim

    query = text("""
        UPDATE dbo.Claims
        SET status = :status,
            verification_status = :verification_status,
            document_status_json = :document_status_json
        WHERE claim_id = :claim_id
    """)

    params = {
        "claim_id": claim["claim_id"],
        "status": claim["status"],
        "verification_status": claim["verification_status"],
        "document_status_json": json.dumps(
            claim.get("document_status", {})
        ),
    }

    with get_engine().begin() as conn:
        result = conn.execute(query, params)

    if result.rowcount == 0:
        raise ValueError("Claim not found")

    return claim


# -------------------- DOCUMENTS --------------------

def _document_from_row(row):
    data = dict(row)
    classification = json.loads(
        data.get("classification_json") or "{}"
    )

    return {
        "document_id": data["document_id"],
        "claim_id": data["claim_id"],
        "filename": data["file_name"],
        "file_type": data.get("file_type") or (
            data["file_name"].rsplit(".", 1)[-1].lower()
            if "." in data["file_name"] else ""
        ),
        "content_type": data.get("content_type"),
        "file_size_bytes": data.get("file_size_bytes"),
        "storage_backend": data.get("storage_backend"),
        "blob_name": data.get("blob_name"),
        "sha256": data.get("sha256"),
        "page_count": data.get("page_count"),
        "text_length": data.get("text_length"),
        "processing_status": data.get("processing_status"),
        "duplicate": bool(data.get("is_duplicate", False)),
        "duplicate_of": data.get("duplicate_of"),
        "extracted_text": data.get("extracted_text") or "",
        "document_type": data.get("document_type"),
        "document_status": data.get("document_status"),
        "classification": classification or None,
        "storage_path": None,
    }


def save_document(document: dict) -> dict:
    if not _use_azure():
        from backend.app.api.documents import documents
        documents[document["document_id"]] = document
        return document

    classification = document.get("classification") or {}

    query = text("""
        INSERT INTO dbo.Documents (
            document_id, claim_id, file_name, content_type,
            file_size_bytes, file_type, storage_backend, blob_name,
            sha256, page_count, text_length, processing_status,
            is_duplicate, duplicate_of, document_type,
            predicted_type, needs_review, classification_json,
            extracted_text, document_status
        )
        VALUES (
            :document_id, :claim_id, :file_name, :content_type,
            :file_size_bytes, :file_type, :storage_backend, :blob_name,
            :sha256, :page_count, :text_length, :processing_status,
            :is_duplicate, :duplicate_of, :document_type,
            :predicted_type, :needs_review, :classification_json,
            :extracted_text, :document_status
        )
    """)

    params = {
        "document_id": document["document_id"],
        "claim_id": document["claim_id"],
        "file_name": document.get("filename", "unknown"),
        "content_type": document.get("content_type"),
        "file_size_bytes": document.get("file_size_bytes"),
        "file_type": document.get("file_type"),
        "storage_backend": document.get("storage_backend"),
        "blob_name": document.get("blob_name"),
        "sha256": document.get("sha256"),
        "page_count": document.get("page_count"),
        "text_length": document.get("text_length"),
        "processing_status": document.get("processing_status"),
        "is_duplicate": bool(document.get("duplicate", False)),
        "duplicate_of": document.get("duplicate_of"),
        "document_type": document.get("document_type"),
        "predicted_type": classification.get("predicted_type"),
        "needs_review": bool(classification.get("needs_review", True)),
        "classification_json": json.dumps(classification),
        "extracted_text": document.get("extracted_text"),
        "document_status": document.get("document_status"),
    }

    with get_engine().begin() as conn:
        conn.execute(query, params)

    return document


def get_document_by_id(document_id: str):
    if not _use_azure():
        from backend.app.api.documents import documents
        return documents.get(document_id)

    query = text("""
        SELECT * FROM dbo.Documents
        WHERE document_id = :document_id
    """)

    with get_engine().connect() as conn:
        row = conn.execute(
            query, {"document_id": document_id}
        ).mappings().first()

    return _document_from_row(row) if row else None


def get_all_documents() -> list[dict]:
    if not _use_azure():
        from backend.app.api.documents import documents
        return list(documents.values())

    query = text("SELECT * FROM dbo.Documents")

    with get_engine().connect() as conn:
        rows = conn.execute(query).mappings().all()

    return [_document_from_row(row) for row in rows]


def get_documents_for_claim(claim_id: str) -> list[dict]:
    if not _use_azure():
        from backend.app.api.documents import documents
        return [
            doc for doc in documents.values()
            if doc.get("claim_id") == claim_id
        ]

    query = text("""
        SELECT * FROM dbo.Documents
        WHERE claim_id = :claim_id
        ORDER BY created_at DESC
    """)

    with get_engine().connect() as conn:
        rows = conn.execute(
            query, {"claim_id": claim_id}
        ).mappings().all()

    return [_document_from_row(row) for row in rows]


def update_document(document: dict) -> dict:
    if not _use_azure():
        from backend.app.api.documents import documents
        documents[document["document_id"]] = document
        return document

    classification = document.get("classification") or {}

    query = text("""
        UPDATE dbo.Documents
        SET processing_status = :processing_status,
            document_type = :document_type,
            predicted_type = :predicted_type,
            needs_review = :needs_review,
            classification_json = :classification_json,
            document_status = :document_status,
            extracted_text = :extracted_text
        WHERE document_id = :document_id
          AND claim_id = :claim_id
    """)

    params = {
        "document_id": document["document_id"],
        "claim_id": document["claim_id"],
        "processing_status": document.get("processing_status"),
        "document_type": document.get("document_type"),
        "predicted_type": classification.get("predicted_type"),
        "needs_review": bool(classification.get("needs_review", True)),
        "classification_json": json.dumps(classification),
        "document_status": document.get("document_status"),
        "extracted_text": document.get("extracted_text"),
    }

    with get_engine().begin() as conn:
        result = conn.execute(query, params)

    if result.rowcount == 0:
        raise ValueError("Document not found")

    return document
