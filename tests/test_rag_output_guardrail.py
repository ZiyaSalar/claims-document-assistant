import json
import os
from types import SimpleNamespace
from unittest.mock import patch

from backend.app.services.rag_service import answer_claim_question


def run_rag_with_fake_answer(finding):
    text = "The patient was admitted for further treatment."
    documents = [{
        "document_id": "demo-doc-1",
        "filename": "test_admission.txt",
        "extracted_text": text,
        "pages": [],
    }]
    search_results = [{
        "document_id": "demo-doc-1",
        "content": text,
        "page_number": None,
    }]
    fake_response = {
        "findings": [{
            "finding": finding,
            "citation": "S1",
            "evidence_excerpt": text,
        }]
    }
    response = SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(
                    content=json.dumps(fake_response)
                )
            )
        ]
    )
    client = SimpleNamespace(
        chat=SimpleNamespace(
            completions=SimpleNamespace(
                create=lambda **kwargs: response
            )
        )
    )
    with (
        patch.dict(os.environ, {
            "RAG_SEARCH_MODE": "keyword",
            "AZURE_OPENAI_DEPLOYMENT": "test-deployment",
        }),
        patch(
            "backend.app.services.rag_service.search_claim",
            return_value=search_results,
        ),
        patch(
            "backend.app.services.rag_service.get_llm_client",
            return_value=client,
        ),
    ):
        return answer_claim_question(
            "demo-claim-1",
            "What does the admission document say?",
            documents,
        )


def test_unauthorized_approval_is_rejected():
    result = run_rag_with_fake_answer(
        "This insurance claim is approved."
    )

    assert result["answer_status"] == "insufficient_evidence"
    assert result["findings"] == []


def test_legitimate_document_finding_is_allowed():
    result = run_rag_with_fake_answer(
        "The patient was admitted for further treatment."
    )

    assert result["answer_status"] == "grounded"
    assert len(result["findings"]) == 1
