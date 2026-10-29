
from backend.app.services.claim_summary import generate_claim_summary


def test_summary_reports_missing_documents():
    claim = {"claim_id": "CLM-TEST"}
    checklist = {
        "checklist": {
            "hospital_bill": "present",
            "discharge_summary": "missing",
        },
        "missing_documents": ["discharge_summary"],
        "review_required": True,
    }
    documents = [
        {
            "document_id": "DOC-1",
            "filename": "bill.txt",
            "classification": {
                "predicted_type": "hospital_bill",
                "confidence": 1.0,
                "needs_review": False,
            },
        }
    ]

    result = generate_claim_summary(claim, checklist, documents)

    assert result["claim_id"] == "CLM-TEST"
    assert result["missing_documents"] == ["discharge_summary"]
    assert result["human_review_required"] is True
    assert result["decision"] == "human_review_required"


def test_summary_flags_unclassified_document():
    claim = {"claim_id": "CLM-TEST"}
    checklist = {
        "checklist": {"hospital_bill": "missing"},
        "missing_documents": ["hospital_bill"],
        "review_required": True,
    }
    documents = [
        {
            "document_id": "DOC-2",
            "filename": "unknown.txt",
        }
    ]

    result = generate_claim_summary(claim, checklist, documents)

    assert len(result["review_flags"]) == 1
    assert result["human_review_required"] is True
