from uuid import uuid4

from fastapi import APIRouter, HTTPException, status

from backend.app.models.claim import ClaimCreate



router = APIRouter(prefix="/api/claims", tags=["Claims"])

claims = {}


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_claim(claim: ClaimCreate):
    claim_id = str(uuid4())

    new_claim = {
        "claim_id": claim_id,
        **claim.model_dump(),
        "status": "submitted",
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