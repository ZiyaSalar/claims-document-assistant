

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
    if "document_status" not in claim:
        claim["document_status"] = initialize_document_status()

    return claim["document_status"]


def mark_document_missing(claim, document_type):
    if document_type not in REQUIRED_DOCUMENTS:
        raise ValueError("Unsupported document type")

    document_status = get_document_status(claim)
    document_status[document_type] = {
        "status": "missing",
        "document_id": None,
    }

    return document_status


def mark_document_received(claim, document_type, document_id):
    if document_type not in REQUIRED_DOCUMENTS:
        raise ValueError("Unsupported document type")

    document_status = get_document_status(claim)
    document_status[document_type] = {
        "status": "received",
        "document_id": document_id,
    }

    return document_status


def verify_claim_documents(claim):
    document_status = get_document_status(claim)

    missing_documents = [
        document_type
        for document_type, details in document_status.items()
        if details["status"] != "received"
    ]

    return {
        "claim_id": claim["claim_id"],
        "verification_status": (
            "ready_for_review" if not missing_documents else "incomplete"
        ),
        "missing_documents": missing_documents,
        "received_count": sum(
            details["status"] == "received"
            for details in document_status.values()
        ),
        "required_count": len(REQUIRED_DOCUMENTS),
        "can_proceed": not missing_documents,
    }
