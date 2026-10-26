
REQUIRED_DOCUMENTS = [
    "hospital_bill",
    "discharge_summary",
    "admission_advice",
    "signed_claim_form",
]


def generate_checklist(documents: list[dict]) -> dict:
    present_types = {
        document.get("classification", {}).get("predicted_type")
        for document in documents
        if document.get("classification", {}).get("needs_review") is False
    }

    checklist = {
        doc_type: (
            "present" if doc_type in present_types else "missing"
        )
        for doc_type in REQUIRED_DOCUMENTS
    }

    missing_documents = [
        doc_type
        for doc_type, status in checklist.items()
        if status == "missing"
    ]

    return {
        "checklist": checklist,
        "missing_documents": missing_documents,
        "review_required": bool(missing_documents),
    }
