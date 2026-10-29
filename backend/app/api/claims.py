
from uuid import uuid4

from fastapi import APIRouter, HTTPException, status

from backend.app.models.claim import ClaimCreate
from backend.app.services.claim_document_status import (
    initialize_document_status,
    mark_document_missing,
    verify_claim_documents,
)
from backend.app.services.claim_repository import (
    save_claim,
    get_claim_by_id,
    get_all_claims,
    update_claim,
)

router = APIRouter(prefix="/api/claims", tags=["Claims"])


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_claim(claim: ClaimCreate):
    new_claim = {
        "claim_id": str(uuid4()),
        **claim.model_dump(),
        "status": "submitted",
        "document_status": initialize_document_status(),
        "verification_status": "incomplete",
    }

    save_claim(new_claim)
    return new_claim


@router.get("/")
def get_claims():
    return get_all_claims()


@router.get("/{claim_id}")
def get_claim(claim_id: str):
    claim = get_claim_by_id(claim_id)

    if claim is None:
        raise HTTPException(status_code=404, detail="Claim not found")

    if not claim.get("document_status"):
        claim["document_status"] = initialize_document_status()

    return claim


@router.patch("/{claim_id}/documents/{document_type}/missing")
def mark_claim_document_missing(claim_id: str, document_type: str):
    claim = get_claim_by_id(claim_id)

    if claim is None:
        raise HTTPException(status_code=404, detail="Claim not found")

    if not claim.get("document_status"):
        claim["document_status"] = initialize_document_status()

    try:
        mark_document_missing(claim, document_type)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    verification = verify_claim_documents(claim)
    claim["verification_status"] = verification["verification_status"]
    update_claim(claim)

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
    claim = get_claim_by_id(claim_id)

    if claim is None:
        raise HTTPException(status_code=404, detail="Claim not found")

    if not claim.get("document_status"):
        claim["document_status"] = initialize_document_status()

    verification = verify_claim_documents(claim)
    claim["verification_status"] = verification["verification_status"]
    update_claim(claim)

    return verification
