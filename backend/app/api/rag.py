
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from azure.core.exceptions import AzureError
from openai import OpenAIError

from backend.app.services.claim_repository import (
    get_claim_by_id,
    get_documents_for_claim,
)
from backend.app.services.rag_search import (
    index_claim_documents,
)
from backend.app.services.rag_service import (
    answer_claim_question,
)

router = APIRouter(
    prefix="/api/claims",
    tags=["RAG Question Answering"],
)


class ClaimQuestion(BaseModel):
    question: str = Field(min_length=3, max_length=500)


@router.post("/{claim_id}/rag/index")
def index_claim(claim_id: str):
    claim = get_claim_by_id(claim_id)

    if claim is None:
        raise HTTPException(
            status_code=404,
            detail="Claim not found",
        )

    documents = get_documents_for_claim(claim_id)

    try:
        return index_claim_documents(claim_id, documents)

    except (AzureError, RuntimeError) as exc:
        raise HTTPException(
            status_code=503,
            detail="Azure AI Search indexing failed",
        ) from exc


@router.post("/{claim_id}/ask")
def ask_claim(claim_id: str, request: ClaimQuestion):
    claim = get_claim_by_id(claim_id)

    if claim is None:
        raise HTTPException(
            status_code=404,
            detail="Claim not found",
        )

    documents = get_documents_for_claim(claim_id)

    try:
        return answer_claim_question(
            claim_id=claim_id,
            question=request.question.strip(),
            documents=documents,
        )

    except (AzureError, OpenAIError) as exc:
        raise HTTPException(
            status_code=503,
            detail="RAG service temporarily unavailable",
        ) from exc
