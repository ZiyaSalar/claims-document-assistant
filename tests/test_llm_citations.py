
import json
from types import SimpleNamespace

import pytest

from backend.app.services import llm_summary


def test_evidence_contains_correct_page():
    documents = [{
        "document_id": "DOC-1",
        "filename": "hospital_bill.pdf",
        "document_type": "hospital_bill",
        "pages": [{
            "page_number": 2,
            "text": "Total bill amount: $2500",
        }],
    }]

    sources, _ = llm_summary.prepare_evidence(documents)

    assert sources["D1:P2"]["document_id"] == "DOC-1"
    assert sources["D1:P2"]["page_number"] == 2


def test_valid_citation_and_quote():
    sources = {
        "D1:P1": {
            "document_id": "DOC-1",
            "filename": "bill.pdf",
            "page_number": 1,
            "text": "Total bill amount: $2500",
        }
    }

    findings, rejected = llm_summary.validate_findings(
        [{
            "finding": "The bill lists $2500.",
            "citation": "D1:P1",
            "evidence_excerpt": "Total bill amount: $2500",
        }],
        sources,
    )

    assert len(findings) == 1
    assert rejected == []


def test_reject_nonexistent_citation():
    findings, rejected = llm_summary.validate_findings(
        [{
            "finding": "The bill lists $2500.",
            "citation": "D99:P1",
            "evidence_excerpt": "Total bill amount: $2500",
        }],
        {},
    )

    assert findings == []
    assert len(rejected) == 1


def test_reject_invented_evidence():
    sources = {
        "D1:P1": {
            "document_id": "DOC-1",
            "filename": "bill.pdf",
            "page_number": 1,
            "text": "Total bill amount: $2500",
        }
    }

    findings, rejected = llm_summary.validate_findings(
        [{
            "finding": "The bill lists $9000.",
            "citation": "D1:P1",
            "evidence_excerpt": "Total bill amount: $9000",
        }],
        sources,
    )

    assert findings == []
    assert len(rejected) == 1


def test_generated_summary_has_source_excerpt(monkeypatch):
    documents = [{
        "document_id": "DOC-1",
        "filename": "bill.pdf",
        "document_type": "hospital_bill",
        "pages": [{
            "page_number": 1,
            "text": "Total bill amount: $2500",
        }],
    }]

    llm_response = {
        "findings": [{
            "finding": "The bill lists $2500.",
            "citation": "D1:P1",
            "evidence_excerpt": "Total bill amount: $2500",
        }]
    }

    fake_client = SimpleNamespace(
        chat=SimpleNamespace(
            completions=SimpleNamespace(
                create=lambda **kwargs: SimpleNamespace(
                    choices=[
                        SimpleNamespace(
                            message=SimpleNamespace(
                                content=json.dumps(llm_response)
                            )
                        )
                    ]
                )
            )
        )
    )

    monkeypatch.setenv("AZURE_OPENAI_DEPLOYMENT", "test-model")
    monkeypatch.setattr(
        llm_summary,
        "get_llm_client",
        lambda: fake_client,
    )

    baseline = {
        "missing_documents": ["signed_claim_form"],
        "decision": "human_review_required",
    }

    result = llm_summary.generate_llm_claim_summary(
        claim={"claim_id": "CLM-1"},
        documents=documents,
        baseline_summary=baseline,
    )

    assert result["citation_validation"] == "passed"
    assert result["findings"][0]["page_number"] == 1
    assert result["findings"][0]["evidence_excerpt"] == (
        "Total bill amount: $2500"
    )
    assert result["decision"] == "human_review_required"
    assert result["llm_generated"] is True


def test_all_invalid_findings_return_safe_fallback(monkeypatch):
    documents = [{
        "document_id": "DOC-1",
        "filename": "hospital_bill.pdf",
        "pages": [{
            "page_number": 1,
            "text": "Total bill amount: $2500",
        }],
    }]

    invalid_response = {
        "findings": [{
            "finding": "The bill totals $9000.",
            "citation": "D1:P1",
            "evidence_excerpt": "Total bill amount: $9000",
        }]
    }

    fake_client = SimpleNamespace(
        chat=SimpleNamespace(
            completions=SimpleNamespace(
                create=lambda **kwargs: SimpleNamespace(
                    choices=[
                        SimpleNamespace(
                            message=SimpleNamespace(
                                content=json.dumps(invalid_response)
                            )
                        )
                    ]
                )
            )
        )
    )

    monkeypatch.setenv("AZURE_OPENAI_DEPLOYMENT", "test-model")
    monkeypatch.setattr(
        llm_summary,
        "get_llm_client",
        lambda: fake_client,
    )

    baseline = {
        "claim_id": "CLM-1",
        "missing_documents": ["signed_claim_form"],
        "decision": "human_review_required",
        "human_review_required": True,
    }

    result = llm_summary.generate_llm_claim_summary(
        claim={"claim_id": "CLM-1"},
        documents=documents,
        baseline_summary=baseline,
    )

    assert result["citation_validation"] == "failed"
    assert result["llm_generated"] is False
    assert result["findings"] == []
    assert result["citations"] == []
    assert result["rejected_finding_count"] == 1
    assert result["decision"] == "human_review_required"
