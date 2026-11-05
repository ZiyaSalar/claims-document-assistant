
from backend.app.services.claim_document_status import (
    REQUIRED_DOCUMENTS,
    is_accepted_document,
)


def generate_checklist(documents: list[dict]) -> dict:
    present_types = {
        document["document_type"]
        for document in documents
        if is_accepted_document(document)
    }

    checklist = {
        document_type: (
            "present"
            if document_type in present_types
            else "missing"
        )
        for document_type in sorted(REQUIRED_DOCUMENTS)
    }

    missing_documents = [
        document_type
        for document_type, status in checklist.items()
        if status == "missing"
    ]

    return {
        "checklist": checklist,
        "missing_documents": missing_documents,
        "review_required": bool(missing_documents),
    }
