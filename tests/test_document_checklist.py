
from backend.app.services.document_checklist import generate_checklist


def test_all_documents_missing():
    result = generate_checklist([])

    assert len(result["missing_documents"]) == 4
    assert result["review_required"] is True


def test_all_documents_present():
    document_types = [
        "hospital_bill",
        "discharge_summary",
        "admission_advice",
        "signed_claim_form",
    ]

    documents = [
        {
            "document_id": f"test-{doc_type}",
            "document_type": doc_type,
            "document_status": "received",
            "classification": {
                "predicted_type": doc_type,
                "needs_review": False,
                "confidence": 0.98,
            },
        }
        for doc_type in document_types
    ]

    result = generate_checklist(documents)

    assert result["missing_documents"] == []
    assert result["review_required"] is False


def test_unclassified_document_does_not_count():
    documents = [
        {
            "document_id": "test-uncertain",
            "document_type": "hospital_bill",
            "document_status": "needs_review",
            "classification": {
                "predicted_type": "hospital_bill",
                "needs_review": True,
            },
        }
    ]

    result = generate_checklist(documents)

    assert result["checklist"]["hospital_bill"] == "missing"
    assert result["review_required"] is True


def test_mismatched_document_does_not_count():
    documents = [
        {
            "document_id": "test-mismatch",
            "document_type": "hospital_bill",
            "document_status": "received",
            "classification": {
                "predicted_type": "discharge_summary",
                "needs_review": False,
            },
        }
    ]

    result = generate_checklist(documents)

    assert result["checklist"]["hospital_bill"] == "missing"
    assert result["review_required"] is True