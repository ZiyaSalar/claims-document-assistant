
from backend.app.services.document_checklist import generate_checklist


def test_all_documents_missing():
    result = generate_checklist([])

    assert len(result["missing_documents"]) == 4
    assert result["review_required"] is True


def test_all_documents_present():
    documents = [
        {
            "classification": {
                "predicted_type": doc_type,
                "needs_review": False,
            }
        }
        for doc_type in [
            "hospital_bill",
            "discharge_summary",
            "admission_advice",
            "signed_claim_form",
        ]
    ]

    result = generate_checklist(documents)

    assert result["missing_documents"] == []
    assert result["review_required"] is False


def test_unclassified_document_does_not_count():
    documents = [
        {
            "classification": {
                "predicted_type": "hospital_bill",
                "needs_review": True,
            }
        }
    ]

    result = generate_checklist(documents)

    assert result["checklist"]["hospital_bill"] == "missing"
    assert result["review_required"] is True
