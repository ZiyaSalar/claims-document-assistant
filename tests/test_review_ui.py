from fastapi.testclient import TestClient

from backend.app.api import review_ui
from backend.app.main import app
from backend.app.services.claim_document_status import (
    REQUIRED_DOCUMENTS,
    initialize_document_status,
    is_accepted_document,
)

client = TestClient(app)


def setup_acceptance_case(monkeypatch, document):
    claim = {
        "claim_id": "claim-123",
        "document_status": initialize_document_status(),
        "verification_status": "incomplete",
    }

    monkeypatch.setattr(
        review_ui,
        "_claim_document",
        lambda claim_id, document_id: (claim, document),
    )
    monkeypatch.setattr(
        review_ui,
        "update_document",
        lambda updated_document: updated_document,
    )
    monkeypatch.setattr(
        review_ui,
        "get_documents_for_claim",
        lambda claim_id: [document],
    )
    monkeypatch.setattr(review_ui, "update_claim", lambda updated_claim: updated_claim)

    return claim


def test_accept_document_records_review_and_preserves_classification(monkeypatch):
    original_classification = {
        "predicted_type": "discharge_summary",
        "needs_review": True,
        "confidence": 0.42,
    }
    document = {
        "claim_id": "claim-123",
        "document_id": "document-123",
        "document_type": "hospital_bill",
        "document_status": "needs_review",
        "processing_status": "completed",
        "classification": original_classification.copy(),
    }
    claim = setup_acceptance_case(monkeypatch, document)

    response = client.post(
        "/api/claims/claim-123/documents/document-123/accept",
        json={
            "reviewer_name": "  A Reviewer  ",
            "reason": "  Verified manually  ",
            "reviewed_original": True,
            "document_type": "hospital_bill",
        },
    )

    assert response.status_code == 200
    result = response.json()
    assert result["document_status"] == "received"
    assert result["document_type"] == "hospital_bill"
    assert result["human_review"]["accepted"] is True
    assert result["human_review"]["reviewer_name"] == "A Reviewer"
    assert result["human_review"]["reason"] == "Verified manually"
    assert result["verification"]["received_count"] == 1
    assert document["classification"]["predicted_type"] == "discharge_summary"
    assert document["classification"]["needs_review"] is True
    assert document["classification"]["confidence"] == 0.42
    assert claim["verification_status"] == "incomplete"


def test_accept_document_corrects_category_without_changing_prediction(
    monkeypatch,
):
    document = {
        "claim_id": "claim-123",
        "document_id": "document-123",
        "document_type": "hospital_bill",
        "document_status": "needs_review",
        "processing_status": "completed",
        "classification": {
            "predicted_type": "hospital_bill",
            "needs_review": True,
        },
    }
    setup_acceptance_case(monkeypatch, document)

    response = client.post(
        "/api/claims/claim-123/documents/document-123/accept",
        json={
            "reviewer_name": "A Reviewer",
            "reason": "Confirmed against original file",
            "reviewed_original": True,
            "document_type": "admission_advice",
        },
    )

    assert response.status_code == 200
    assert document["document_type"] == "admission_advice"
    assert response.json()["document_type"] == "admission_advice"
    assert (
        document["classification"]["human_review"]["accepted_document_type"]
        == "admission_advice"
    )
    assert document["classification"]["predicted_type"] == "hospital_bill"


def test_accept_document_rejects_invalid_category(monkeypatch):
    document = {
        "claim_id": "claim-123",
        "document_id": "document-123",
        "document_type": "hospital_bill",
        "document_status": "needs_review",
        "processing_status": "completed",
        "classification": {},
    }
    setup_acceptance_case(monkeypatch, document)

    response = client.post(
        "/api/claims/claim-123/documents/document-123/accept",
        json={
            "reviewer_name": "A Reviewer",
            "reason": "Confirmed against original file",
            "reviewed_original": True,
            "document_type": "passport",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid document category"


def test_correct_document_category_records_history_and_preserves_prediction(
    monkeypatch,
):
    document = {
        "claim_id": "claim-123",
        "document_id": "document-123",
        "document_type": "hospital_bill",
        "document_status": "received",
        "classification": {
            "predicted_type": "discharge_summary",
            "human_review": {
                "accepted": True,
                "accepted_document_type": "hospital_bill",
            },
        },
    }
    claim = setup_acceptance_case(monkeypatch, document)

    response = client.patch(
        "/api/claims/claim-123/documents/document-123/category",
        json={
            "reviewer_name": "A Reviewer",
            "reason": "Confirmed against original file",
            "document_type": "admission_advice",
        },
    )

    assert response.status_code == 200
    assert response.json()["previous_type"] == "hospital_bill"
    assert response.json()["document_type"] == "admission_advice"
    assert document["document_type"] == "admission_advice"
    assert document["classification"]["predicted_type"] == "discharge_summary"
    history = document["classification"]["category_corrections"]
    assert len(history) == 1
    assert history[0]["previous_type"] == "hospital_bill"
    assert history[0]["corrected_type"] == "admission_advice"
    assert history[0]["reviewer_name"] == "A Reviewer"
    assert history[0]["reason"] == "Confirmed against original file"
    assert (
        document["classification"]["human_review"][
            "accepted_document_type"
        ]
        == "admission_advice"
    )
    assert claim["verification_status"] == "incomplete"


def test_correct_document_category_requires_prior_acceptance(monkeypatch):
    document = {
        "claim_id": "claim-123",
        "document_id": "document-123",
        "document_type": "hospital_bill",
        "document_status": "needs_review",
        "classification": {"human_review": {"accepted": False}},
    }
    setup_acceptance_case(monkeypatch, document)

    response = client.patch(
        "/api/claims/claim-123/documents/document-123/category",
        json={
            "reviewer_name": "A Reviewer",
            "reason": "Confirmed against original file",
            "document_type": "admission_advice",
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "Document must be accepted by a reviewer first"
    )


def test_correct_document_category_rejects_invalid_category(monkeypatch):
    document = {
        "claim_id": "claim-123",
        "document_id": "document-123",
        "document_type": "hospital_bill",
        "document_status": "received",
        "classification": {"human_review": {"accepted": True}},
    }
    setup_acceptance_case(monkeypatch, document)

    response = client.patch(
        "/api/claims/claim-123/documents/document-123/category",
        json={
            "reviewer_name": "A Reviewer",
            "reason": "Confirmed against original file",
            "document_type": "passport",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid document category"


def test_accept_document_rejects_incomplete_processing(monkeypatch):
    document = {
        "claim_id": "claim-123",
        "document_id": "document-123",
        "document_type": "hospital_bill",
        "processing_status": "processing",
        "classification": {},
    }
    setup_acceptance_case(monkeypatch, document)

    response = client.post(
        "/api/claims/claim-123/documents/document-123/accept",
        json={
            "reviewer_name": "A Reviewer",
            "reason": "Verified manually",
            "reviewed_original": True,
            "document_type": "hospital_bill",
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Document processing is not complete"


def test_accept_document_rejects_duplicate_acceptance(monkeypatch):
    document = {
        "claim_id": "claim-123",
        "document_id": "document-123",
        "document_type": "hospital_bill",
        "processing_status": "completed",
        "classification": {"human_review": {"accepted": True}},
    }
    setup_acceptance_case(monkeypatch, document)

    response = client.post(
        "/api/claims/claim-123/documents/document-123/accept",
        json={
            "reviewer_name": "A Reviewer",
            "reason": "Verified manually",
            "reviewed_original": True,
            "document_type": "hospital_bill",
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Document has already been accepted"


def test_approval_eligibility_ignores_extra_unaccepted_documents():
    documents = [
        {
            "document_id": f"accepted-{document_type}",
            "document_type": document_type,
            "document_status": "received",
            "classification": {
                "predicted_type": document_type,
                "needs_review": False,
            },
        }
        for document_type in REQUIRED_DOCUMENTS
    ]
    documents.append(
        {
            "document_id": "extra-unaccepted-document",
            "document_type": "hospital_bill",
            "document_status": "needs_review",
            "classification": {
                "predicted_type": "unknown",
                "needs_review": True,
            },
        }
    )
    claim = {
        "claim_id": "claim-123",
        "document_status": initialize_document_status(),
    }

    result = review_ui.check_demo_approval_eligibility(claim, documents)

    assert result["eligible"] is True
    assert result["verification"]["received_count"] == len(REQUIRED_DOCUMENTS)
    assert result["verification"]["required_count"] == len(REQUIRED_DOCUMENTS)


def test_approval_eligibility_rejects_missing_required_category():
    documents = [
        {
            "document_id": f"accepted-{document_type}",
            "document_type": document_type,
            "document_status": "received",
            "classification": {
                "predicted_type": document_type,
                "needs_review": False,
            },
        }
        for document_type in REQUIRED_DOCUMENTS
        if document_type != "admission_advice"
    ]
    claim = {
        "claim_id": "claim-123",
        "document_status": initialize_document_status(),
    }

    result = review_ui.check_demo_approval_eligibility(claim, documents)

    assert result["eligible"] is False
    assert result["verification"]["can_proceed"] is False
    assert "admission_advice" in result["verification"]["missing_documents"]


def test_human_accepted_document_satisfies_checklist():
    document = {
        "document_type": "admission_advice",
        "document_status": "received",
        "classification": {
            "predicted_type": "hospital_bill",
            "needs_review": True,
            "human_review": {
                "accepted": True,
                "reviewer_name": "Demo Reviewer",
            },
        },
    }

    assert is_accepted_document(document) is True
