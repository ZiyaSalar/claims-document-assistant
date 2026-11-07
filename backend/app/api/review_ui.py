"""Local development UI support: claim-scoped original-file viewer and guarded demo approval.

NOT FOR PRODUCTION: these routes require authentication/authorization before being
served to real employees. Never expose the Codespaces demo to public internet.
"""
import os
from datetime import datetime, timezone
from pathlib import Path

from azure.storage.blob import BlobServiceClient
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field

from backend.app.services.claim_document_status import (
    REQUIRED_DOCUMENTS,
    reconcile_document_status,
    verify_claim_documents,
)
from backend.app.services.claim_repository import (
    get_claim_by_id,
    get_document_by_id,
    get_documents_for_claim,
    update_document,
    update_claim,
)

router = APIRouter(prefix="/api/claims", tags=["Review UI"])

_MIME = {
    "pdf": "application/pdf",
    "txt": "text/plain; charset=utf-8",
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
}


def _claim_document(claim_id: str, document_id: str):
    claim = get_claim_by_id(claim_id)
    if claim is None:
        raise HTTPException(status_code=404, detail="Claim not found")
    document = get_document_by_id(document_id)
    if document is None or str(document.get("claim_id")) != claim_id:
        raise HTTPException(status_code=404, detail="Document not found in this claim")
    return claim, document


class DocumentAcceptance(BaseModel):
    reviewer_name: str = Field(min_length=2, max_length=100)
    reason: str = Field(min_length=1, max_length=1000)


@router.post("/{claim_id}/documents/{document_id}/accept")
def accept_document(
    claim_id: str,
    document_id: str,
    review: DocumentAcceptance,
):
    claim, document = _claim_document(claim_id, document_id)
    expected_type = document.get("document_type")

    if expected_type not in REQUIRED_DOCUMENTS:
        raise HTTPException(
            status_code=400,
            detail="Unsupported or missing document type",
        )
    if document.get("processing_status") != "completed":
        raise HTTPException(
            status_code=409,
            detail="Document processing is not complete",
        )

    classification = dict(document.get("classification") or {})
    previous_review = classification.get("human_review") or {}
    if previous_review.get("accepted") is True:
        raise HTTPException(
            status_code=409,
            detail="Document has already been accepted",
        )

    classification["human_review"] = {
        "accepted": True,
        "reviewer_name": review.reviewer_name.strip(),
        "reason": review.reason.strip(),
        "reviewed_at": datetime.now(timezone.utc).isoformat(),
    }

    # Preserve the ML prediction and confidence.
    document["classification"] = classification
    document["document_status"] = "received"
    update_document(document)

    documents = get_documents_for_claim(claim_id)
    reconcile_document_status(claim, documents)
    verification = verify_claim_documents(claim)
    claim["verification_status"] = verification["verification_status"]
    update_claim(claim)

    return {
        "message": "Document accepted by human reviewer",
        "claim_id": claim_id,
        "document_id": document_id,
        "document_type": expected_type,
        "document_status": "received",
        "human_review": classification["human_review"],
        "verification": verification,
    }


@router.get("/{claim_id}/documents/{document_id}/file")
def view_original_document(claim_id: str, document_id: str):
    """Serve private document bytes to a local demo, never a public blob URL."""
    _, doc = _claim_document(claim_id, document_id)
    extension = str(doc.get("file_type") or Path(doc.get("filename", "")).suffix.lstrip(".")).lower()
    if extension not in _MIME:
        raise HTTPException(status_code=415, detail="Unsupported preview format")
    if doc.get("storage_backend") == "azure":
        connection = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        if not connection or not doc.get("blob_name"):
            raise HTTPException(status_code=503, detail="Blob storage is not configured")
        try:
            blob = BlobServiceClient.from_connection_string(connection).get_blob_client(
                container=os.getenv("AZURE_STORAGE_CONTAINER", "claim-documents"),
                blob=doc["blob_name"],
            )
            # Upload has a 10 MB limit; do not stream an unbounded arbitrary blob.
            if blob.get_blob_properties().size > 10 * 1024 * 1024:
                raise HTTPException(status_code=413, detail="File too large for preview")
            data = blob.download_blob(max_concurrency=1).readall()
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=503, detail="Original file is unavailable") from exc
    elif doc.get("storage_backend") == "local":
        # Reconstruct safe location from validated IDs and known extension.
        from uuid import UUID
        try:
            UUID(claim_id)
            UUID(document_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid identifier")
        path = Path("data/uploads") / claim_id / f"{document_id}.{extension}"
        if not path.is_file() or path.stat().st_size > 10 * 1024 * 1024:
            raise HTTPException(status_code=404, detail="Local source file unavailable")
        data = path.read_bytes()
    else:
        raise HTTPException(status_code=404, detail="Unknown storage backend")
    return Response(
        content=data,
        media_type=_MIME[extension],
        headers={
            "Content-Disposition": "inline",
            "Cache-Control": "private, no-store",
            "X-Content-Type-Options": "nosniff",
            "Content-Security-Policy": "sandbox",
        },
    )


class DemoApproval(BaseModel):
    reviewer_name: str = Field(min_length=2, max_length=100)
    confirmation: str
    evidence_reviewed: bool


def check_demo_approval_eligibility(
    claim: dict,
    documents: list[dict],
) -> dict:
    """
    Validate required-document coverage.

    Extra uploaded files do not invalidate a claim
    when all required categories have accepted evidence.
    """
    reconcile_document_status(claim, documents)
    verification = verify_claim_documents(claim)
    eligible = (
        verification["can_proceed"] is True
        and verification["received_count"]
        == verification["required_count"]
    )
    return {
        "eligible": eligible,
        "verification": verification,
    }


@router.post("/{claim_id}/review/approve")
def approve_demo_claim(claim_id: str, approval: DemoApproval):
    """DEMO ONLY. This is NOT actual insurer authorization or payout eligibility."""
    if os.getenv("ENABLE_DEMO_APPROVAL", "false").lower() != "true":
        raise HTTPException(status_code=403, detail="Demo approval is disabled")
    if approval.confirmation != "APPROVE" or approval.evidence_reviewed is not True:
        raise HTTPException(status_code=400, detail="Explicit reviewer confirmation required")
    claim = get_claim_by_id(claim_id)
    if claim is None:
        raise HTTPException(status_code=404, detail="Claim not found")
    if claim.get("status") == "approved":
        raise HTTPException(status_code=409, detail="Claim already marked approved")
    docs = get_documents_for_claim(claim_id)
    check = check_demo_approval_eligibility(claim, docs)
    if not check["eligible"]:
        raise HTTPException(status_code=409, detail={"message":"Requirements are not satisfied", **check["verification"]})
    claim["verification_status"] = check["verification"]["verification_status"]
    claim["status"] = "approved"
    update_claim(claim)
    return {
        "claim_id": claim_id,
        "status": "approved",
        "mode": "demo_only",
        "reviewer_name": approval.reviewer_name,
        "verification": check["verification"],
        "message": "Demo approval saved. Not an insurer authorization.",
    }
