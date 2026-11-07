
import os

import httpx

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

from backend.app.models.claim import ClaimCreate
from backend.app.api.claims import create_claim as create_claim_api

from backend.app.services.claim_repository import (
    get_claim_by_id,
    get_documents_for_claim,
)
from backend.app.services.claim_document_status import (
    REQUIRED_DOCUMENTS,
)

API_BASE = os.getenv(
    "MCP_API_BASE_URL",
    "http://127.0.0.1:8000",
).rstrip("/")

mcp = MCPServer(
    "Claims Document Assistant",
    instructions=(
        "Tools expose claim information for human insurance reviewers. "
        "Never infer claim approval from document completeness."
    ),
)


async def call_claim_api(method, path, **kwargs):
    """Call an existing local Claims Assistant endpoint."""
    try:
        async with httpx.AsyncClient(timeout=90.0) as client:
            response = await client.request(
                method,
                f"{API_BASE}{path}",
                **kwargs,
            )
            response.raise_for_status()
            return response.json()

    except httpx.HTTPStatusError as exc:
        raise ToolError(
            f"Claims API returned HTTP "
            f"{exc.response.status_code}"
        ) from exc

    except httpx.RequestError as exc:
        raise ToolError("Claims API is unavailable") from exc


@mcp.tool()
def get_claim_details(claim_id: str) -> dict:
    """Get existing claim details by claim ID."""
    claim = get_claim_by_id(claim_id)

    if claim is None:
        raise ToolError("Claim not found")

    return {
        "claim_id": str(claim["claim_id"]),
        "claimant_name": claim["claimant_name"],
        "policy_number": claim["policy_number"],
        "claim_type": claim["claim_type"],
        "status": claim["status"],
        "verification_status": claim["verification_status"],
    }


@mcp.tool()
def get_claim_manifest(claim_id: str) -> dict:
    """List documents uploaded for a particular claim."""
    if get_claim_by_id(claim_id) is None:
        raise ToolError("Claim not found")

    documents = get_documents_for_claim(claim_id)

    return {
        "claim_id": claim_id,
        "document_count": len(documents),
        "documents": [
            {
                "document_id": str(doc["document_id"]),
                "filename": doc.get("filename"),
                "document_type": doc.get("document_type"),
                "document_status": doc.get("document_status"),
                "processing_status": doc.get("processing_status"),
            }
            for doc in documents
        ],
    }


@mcp.tool()
def get_required_documents(
    service_type: str = "hospitalization",
) -> dict:
    """Get the project's baseline required-document checklist."""
    if service_type != "hospitalization":
        raise ToolError(
            "Only hospitalization is configured in this MCP prototype"
        )

    return {
        "service_type": service_type,
        "required_documents": sorted(REQUIRED_DOCUMENTS),
        "source": "project_baseline",
        "note": (
            "This is the project's generic checklist, "
            "not plan-specific insurance policy rules."
        ),
    }


@mcp.tool()
def create_claim(
    claimant_name: str,
    policy_number: str,
    claim_type: str,
) -> dict:
    """Create a new insurance claim after client-side confirmation."""

    claimant_name = claimant_name.strip()
    policy_number = policy_number.strip()
    claim_type = claim_type.strip()

    if not all([claimant_name, policy_number, claim_type]):
        raise ToolError("All claim fields are required")

    claim = ClaimCreate(
        claimant_name=claimant_name,
        policy_number=policy_number,
        claim_type=claim_type,
    )

    result = create_claim_api(claim)

    return {
        "claim_id": result["claim_id"],
        "claimant_name": result["claimant_name"],
        "policy_number": result["policy_number"],
        "claim_type": result["claim_type"],
        "status": result["status"],
    }


@mcp.tool()
async def get_claim_summary(claim_id: str) -> dict:
    """Get the existing LLM-enabled claim summary."""
    if get_claim_by_id(claim_id) is None:
        raise ToolError("Claim not found")

    return await call_claim_api(
        "GET",
        f"/api/claims/{claim_id}/summary",
        params={"llm": "true"},
    )


@mcp.tool()
async def ask_claim_question(
    claim_id: str,
    question: str,
) -> dict:
    """Ask a document question using the existing RAG API."""
    if get_claim_by_id(claim_id) is None:
        raise ToolError("Claim not found")

    if not question.strip():
        raise ToolError("Question cannot be empty")

    return await call_claim_api(
        "POST",
        f"/api/claims/{claim_id}/ask",
        json={"question": question},
    )


@mcp.tool()
def request_document_upload(
    claim_id: str,
    document_type: str,
) -> dict:
    """
    Request a file upload for an existing claim.
    Supported document types:
    admission_advice, discharge_summary,
    hospital_bill, signed_claim_form.
    Accepts human-readable names such as
    'admission advice' and 'hospital bill'.
    """
    if get_claim_by_id(claim_id) is None:
        raise ToolError("Claim not found")

    normalized_type = (
        document_type.strip()
        .lower()
        .replace("-", "_")
        .replace(" ", "_")
    )
    if normalized_type not in REQUIRED_DOCUMENTS:
        raise ToolError(
            f"Unsupported document type: {document_type}. "
            f"Supported types: {', '.join(sorted(REQUIRED_DOCUMENTS))}"
        )

    return {
        "action": "select_file",
        "claim_id": claim_id,
        "document_type": normalized_type,
        "requires_user_confirmation": True,
    }


@mcp.tool()
async def get_claim_verification(claim_id: str) -> dict:
    """
    Get authoritative claim verification and document
    review statuses.
    Use for questions about missing, uploaded,
    accepted, or review-required documents.
    """
    if get_claim_by_id(claim_id) is None:
        raise ToolError("Claim not found")

    verification = await call_claim_api(
        "GET",
        f"/api/claims/{claim_id}/verification",
    )
    documents = get_documents_for_claim(claim_id)
    uploaded = [
        {
            "document_id": str(doc["document_id"]),
            "filename": doc["filename"],
            "document_type": doc.get("document_type"),
            "document_status": doc.get("document_status"),
            "needs_review": (
                doc.get("document_status") == "needs_review"
                or (doc.get("classification") or {}).get(
                    "needs_review", False
                )
            ),
        }
        for doc in documents
    ]
    return {
        **verification,
        "uploaded_documents": uploaded,
        "explanation": (
            "An uploaded document may still be unsatisfied "
            "in the checklist if it needs review. "
            "Document completeness is not claim approval."
        ),
    }



if __name__ == "__main__":
    mcp.run()
