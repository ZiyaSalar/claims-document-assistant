import pytest

from backend.app.services.claim_document_status import (
    REQUIRED_DOCUMENTS,
    initialize_document_status,
    mark_document_missing,
    mark_document_received,
    verify_claim_documents,
)


def make_claim():
    return {
        "claim_id": "CLM-TEST-001",
        "document_status": initialize_document_status(),
    }


def test_initial_status_has_four_pending_documents():
    status = initialize_document_status()

    assert set(status) == REQUIRED_DOCUMENTS
    assert len(status) == 4
    assert all(item["status"] == "pending" for item in status.values())


def test_missing_document_blocks_verification():
    claim = make_claim()
    mark_document_missing(claim, "signed_claim_form")

    result = verify_claim_documents(claim)

    assert result["verification_status"] == "incomplete"
    assert "signed_claim_form" in result["missing_documents"]
    assert result["can_proceed"] is False


def test_all_four_received_allows_review():
    claim = make_claim()

    for index, document_type in enumerate(sorted(REQUIRED_DOCUMENTS)):
        mark_document_received(claim, document_type, f"DOC-{index + 1}")

    result = verify_claim_documents(claim)

    assert result["verification_status"] == "ready_for_review"
    assert result["missing_documents"] == []
    assert result["received_count"] == 4
    assert result["can_proceed"] is True


def test_unknown_document_type_is_rejected():
    claim = make_claim()

    with pytest.raises(ValueError, match="Unsupported document type"):
        mark_document_missing(claim, "passport")
