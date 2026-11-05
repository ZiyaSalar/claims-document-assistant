
REQUIRED_DOCUMENTS = {
    "hospital_bill",
    "admission_advice",
    "discharge_summary",
    "signed_claim_form",
}


def initialize_document_status():
    return {
        document_type: {
            "status": "pending",
            "document_id": None,
        }
        for document_type in sorted(REQUIRED_DOCUMENTS)
    }


def get_document_status(claim):
    if not claim.get("document_status"):
        claim["document_status"] = initialize_document_status()
    return claim["document_status"]


def mark_document_missing(claim, document_type):
    if document_type not in REQUIRED_DOCUMENTS:
        raise ValueError("Unsupported document type")

    status = get_document_status(claim)
    status[document_type] = {
        "status": "missing",
        "document_id": None,
    }
    return status


def mark_document_received(claim, document_type, document_id):
    if document_type not in REQUIRED_DOCUMENTS:
        raise ValueError("Unsupported document type")

    status = get_document_status(claim)
    status[document_type] = {
        "status": "received",
        "document_id": document_id,
    }
    return status


def is_accepted_document(document):
    classification = document.get("classification") or {}
    expected_type = document.get("document_type")

    return (
        expected_type in REQUIRED_DOCUMENTS
        and document.get("document_status") == "received"
        and classification.get("predicted_type") == expected_type
        and classification.get("needs_review") is False
    )


def reconcile_document_status(claim, documents):
    """
    Rebuild the claim's document checklist from saved documents.

    A document counts only when:
    - It has a supported expected type.
    - The model predicts that same type.
    - Human review is not required.
    - The document status is 'received'.
    """
    previous = get_document_status(claim)
    updated = initialize_document_status()

    for document_type in REQUIRED_DOCUMENTS:
        old_entry = previous.get(document_type) or {}
        if old_entry.get("status") == "missing":
            updated[document_type]["status"] = "missing"

    for document in documents:
        if not is_accepted_document(document):
            continue

        document_type = document["document_type"]

        # Use the first qualifying document of each type.
        if updated[document_type]["status"] != "received":
            updated[document_type] = {
                "status": "received",
                "document_id": document["document_id"],
            }

    claim["document_status"] = updated
    return updated


def verify_claim_documents(claim):
    document_status = get_document_status(claim)

    missing_documents = sorted(
        document_type
        for document_type in REQUIRED_DOCUMENTS
        if document_status.get(document_type, {}).get("status")
        != "received"
    )

    received_count = len(REQUIRED_DOCUMENTS) - len(
        missing_documents
    )

    return {
        "claim_id": claim["claim_id"],
        "verification_status": (
            "ready_for_review"
            if not missing_documents
            else "incomplete"
        ),
        "missing_documents": missing_documents,
        "received_count": received_count,
        "required_count": len(REQUIRED_DOCUMENTS),
        "can_proceed": not missing_documents,
    }
