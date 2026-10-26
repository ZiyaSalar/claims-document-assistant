from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.document_classifier import classify_document

client = TestClient(app)


def test_classify_hospital_bill():
    result = classify_document(
        "FICTIONAL HOSPITAL BILL. Room charges. Total amount INR 15000."
    )

    assert result["predicted_type"] == "hospital_bill"
    assert result["needs_review"] is False


def test_classify_discharge_summary():
    result = classify_document(
        "FICTIONAL DISCHARGE SUMMARY. Patient discharged."
    )

    assert result["predicted_type"] == "discharge_summary"


def test_classify_admission_advice():
    result = classify_document(
        "FICTIONAL ADMISSION ADVICE. Inpatient admission."
    )

    assert result["predicted_type"] == "admission_advice"


def test_classify_signed_claim_form():
    result = classify_document(
        "FICTIONAL CLAIM FORM. Signature: SIMULATED."
    )

    assert result["predicted_type"] == "signed_claim_form"


def test_unknown_document():
    result = classify_document("A document with unrelated content.")

    assert result["predicted_type"] == "unknown"
    assert result["needs_review"] is True


def test_empty_document():
    result = classify_document("   ")

    assert result["predicted_type"] == "unknown"
    assert result["needs_review"] is True


def test_classification_api():
    claim_response = client.post(
        "/api/claims/",
        json={
            "claimant_name": "Test User",
            "policy_number": "POL-CLASSIFY",
            "claim_type": "hospitalization",
        },
    )
    claim_id = claim_response.json()["claim_id"]

    upload_response = client.post(
        f"/api/claims/{claim_id}/documents",
        files={
            "file": (
                "bill.txt",
                b"FICTIONAL HOSPITAL BILL. Room charges. Total amount INR 15000.",
                "text/plain",
            )
        },
    )
    document_id = upload_response.json()["document_id"]

    response = client.post(
        f"/api/claims/{claim_id}/documents/{document_id}/classify"
    )

    assert response.status_code == 200
    assert response.json()["predicted_type"] == "hospital_bill"