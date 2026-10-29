
import pymupdf

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services import document_storage
from backend.app.services.claim_store import claims
from backend.app.api.documents import documents

client = TestClient(app)


def create_claim():
    response = client.post(
        "/api/claims/",
        json={
            "claimant_name": "Test User",
            "policy_number": "POL-TEST",
            "claim_type": "hospitalization",
        },
    )
    assert response.status_code == 201
    return response.json()["claim_id"]


def make_pdf(text="Synthetic hospital bill"):
    pdf = pymupdf.open()
    page = pdf.new_page()
    page.insert_text((72, 72), text)
    content = pdf.tobytes()
    pdf.close()
    return content


def test_upload_and_extract_pdf(tmp_path, monkeypatch):
    monkeypatch.setattr(document_storage, "UPLOAD_DIR", tmp_path)
    claim_id = create_claim()

    response = client.post(
        f"/api/claims/{claim_id}/documents",
        files={"file": ("bill.pdf", make_pdf(), "application/pdf")},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["processing_status"] == "completed"
    assert data["page_count"] == 1
    assert data["text_length"] > 0
    assert data["duplicate"] is False

    text_response = client.get(
        f"/api/claims/{claim_id}/documents/{data['document_id']}/text"
    )

    assert text_response.status_code == 200
    assert "Synthetic hospital bill" in text_response.json()["extracted_text"]


def test_upload_txt(tmp_path, monkeypatch):
    monkeypatch.setattr(document_storage, "UPLOAD_DIR", tmp_path)
    claim_id = create_claim()

    response = client.post(
        f"/api/claims/{claim_id}/documents",
        files={
            "file": (
                "summary.txt",
                b"Synthetic discharge summary",
                "text/plain",
            )
        },
    )

    assert response.status_code == 201
    assert response.json()["file_type"] == "txt"


def test_reject_invalid_pdf(tmp_path, monkeypatch):
    monkeypatch.setattr(document_storage, "UPLOAD_DIR", tmp_path)
    claim_id = create_claim()

    response = client.post(
        f"/api/claims/{claim_id}/documents",
        files={
            "file": (
                "fake.pdf",
                b"This is not a PDF",
                "application/pdf",
            )
        },
    )

    assert response.status_code == 400


def test_reject_unsupported_extension(tmp_path, monkeypatch):
    monkeypatch.setattr(document_storage, "UPLOAD_DIR", tmp_path)
    claim_id = create_claim()

    response = client.post(
        f"/api/claims/{claim_id}/documents",
        files={"file": ("program.exe", b"test content")},
    )

    assert response.status_code == 400


def test_reject_invalid_utf8_txt(tmp_path, monkeypatch):
    monkeypatch.setattr(document_storage, "UPLOAD_DIR", tmp_path)
    claim_id = create_claim()

    response = client.post(
        f"/api/claims/{claim_id}/documents",
        files={"file": ("bad.txt", b"\xff\xfe", "text/plain")},
    )

    assert response.status_code == 400


def test_detect_duplicate(tmp_path, monkeypatch):
    monkeypatch.setattr(document_storage, "UPLOAD_DIR", tmp_path)
    claim_id = create_claim()
    content = b"Synthetic claim summary"

    first = client.post(
        f"/api/claims/{claim_id}/documents",
        files={"file": ("first.txt", content, "text/plain")},
    )
    second = client.post(
        f"/api/claims/{claim_id}/documents",
        files={"file": ("second.txt", content, "text/plain")},
    )

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["duplicate"] is False
    assert second.json()["duplicate"] is True
    assert second.json()["duplicate_of"] == first.json()["document_id"]


def test_reject_missing_claim():
    response = client.post(
        "/api/claims/nonexistent/documents",
        files={"file": ("bill.txt", b"synthetic text")},
    )

    assert response.status_code == 404


def test_list_documents(tmp_path, monkeypatch):
    monkeypatch.setattr(document_storage, "UPLOAD_DIR", tmp_path)
    claim_id = create_claim()

    client.post(
        f"/api/claims/{claim_id}/documents",
        files={"file": ("bill.txt", b"Synthetic bill")},
    )

    response = client.get(f"/api/claims/{claim_id}/documents")

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_matching_document_type_is_received(tmp_path, monkeypatch):
    monkeypatch.setattr(document_storage, "UPLOAD_DIR", tmp_path)
    claim_id = create_claim()

    response = client.post(
        f"/api/claims/{claim_id}/documents",
        data={"document_type": "hospital_bill"},
        files={
            "file": (
                "bill.txt",
                b"Hospital bill invoice total amount room charges",
                "text/plain",
            )
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["document_status"] == "received"
    assert data["classification"]["predicted_type"] == "hospital_bill"

    claim = claims[claim_id]
    assert claim["document_status"]["hospital_bill"]["status"] == "received"
    assert claim["status"] == "submitted"
    assert claim["verification_status"] == "incomplete"


def test_mismatched_document_type_needs_review(tmp_path, monkeypatch):
    monkeypatch.setattr(document_storage, "UPLOAD_DIR", tmp_path)
    claim_id = create_claim()

    response = client.post(
        f"/api/claims/{claim_id}/documents",
        data={"document_type": "hospital_bill"},
        files={
            "file": (
                "discharge.txt",
                b"Discharge summary date of discharge discharge diagnosis",
                "text/plain",
            )
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["document_status"] == "needs_review"
    assert data["classification"]["predicted_type"] == "discharge_summary"
    assert claims[claim_id]["document_status"]["hospital_bill"]["status"] == "pending"
    assert claims[claim_id]["verification_status"] == "incomplete"


def test_ambiguous_document_needs_review(tmp_path, monkeypatch):
    monkeypatch.setattr(document_storage, "UPLOAD_DIR", tmp_path)
    claim_id = create_claim()

    response = client.post(
        f"/api/claims/{claim_id}/documents",
        data={"document_type": "hospital_bill"},
        files={
            "file": (
                "unclear.txt",
                b"Unrelated synthetic document text",
                "text/plain",
            )
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["document_status"] == "needs_review"
    assert data["classification"]["predicted_type"] == "unknown"
    assert claims[claim_id]["document_status"]["hospital_bill"]["status"] == "pending"


def test_reject_unsupported_document_type(tmp_path, monkeypatch):
    monkeypatch.setattr(document_storage, "UPLOAD_DIR", tmp_path)
    claim_id = create_claim()

    response = client.post(
        f"/api/claims/{claim_id}/documents",
        data={"document_type": "passport"},
        files={
            "file": (
                "passport.txt",
                b"Synthetic document",
                "text/plain",
            )
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Unsupported document type"
