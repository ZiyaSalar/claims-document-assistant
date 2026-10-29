
from uuid import uuid4

from fastapi import APIRouter, HTTPException, status

from backend.app.models.claim import ClaimCreate
from backend.app.services.claim_store import claims
from backend.app.services.claim_document_status import initialize_document_status

from backend.app.services.claim_document_status import (
    mark_document_missing,
    verify_claim_documents,
)

router = APIRouter(prefix="/api/claims", tags=["Claims"])


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_claim(claim: ClaimCreate):
    claim_id = str(uuid4())

    new_claim = {
        "claim_id": claim_id,
        **claim.model_dump(),
        "status": "submitted",
        "document_status": initialize_document_status(),
        "verification_status": "incomplete",
    }

    claims[claim_id] = new_claim
    return new_claim


@router.get("/")
def get_claims():
    return list(claims.values())


@router.get("/{claim_id}")
def get_claim(claim_id: str):
    claim = claims.get(claim_id)

    if claim is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Claim not found",
        )

    return claim


@router.patch("/{claim_id}/documents/{document_type}/missing")
def mark_claim_document_missing(claim_id: str, document_type: str):
    claim = claims.get(claim_id)

    if claim is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Claim not found",
        )

    try:
        mark_document_missing(claim, document_type)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    verification = verify_claim_documents(claim)
    claim["verification_status"] = verification["verification_status"]

    return {
        "message": "Document marked as missing",
        "claim_id": claim_id,
        "document_type": document_type,
        "document_status": claim["document_status"],
        "verification": verification,
        "claim_status": claim["status"],
    }


@router.get("/{claim_id}/verification")
def get_claim_verification(claim_id: str):
    claim = claims.get(claim_id)

    if claim is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Claim not found",
        )

    verification = verify_claim_documents(claim)
    claim["verification_status"] = verification["verification_status"]

    return verification
