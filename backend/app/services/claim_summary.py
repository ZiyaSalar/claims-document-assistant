
def generate_claim_summary(
    claim: dict,
    checklist_result: dict,
    documents: list[dict],
) -> dict:
    classified_documents = []
    review_flags = []

    for document in documents:
        classification = document.get("classification")

        if not classification:
            review_flags.append({
                "document_id": document["document_id"],
                "reason": "Document has not been classified",
            })
            continue

        doc_type = classification.get("predicted_type", "unknown")

        if classification.get("needs_review", True):
            review_flags.append({
                "document_id": document["document_id"],
                "reason": "Document classification requires review",
            })

        classified_documents.append({
            "document_id": document["document_id"],
            "filename": document["filename"],
            "predicted_type": doc_type,
            "confidence": classification.get("confidence", 0.0),
            "needs_review": classification.get("needs_review", True),
        })

    missing = checklist_result["missing_documents"]

    if missing:
        summary = (
            f"Claim {claim['claim_id']} has "
            f"{len(missing)} missing required document type(s). "
            "Human review is required."
        )
    else:
        summary = (
            f"Claim {claim['claim_id']} has all required document "
            "types recorded in the checklist. This does not establish "
            "claim eligibility or guarantee that the documents are valid."
        )

    return {
        "claim_id": claim["claim_id"],
        "summary": summary,
        "classified_documents": classified_documents,
        "checklist": checklist_result["checklist"],
        "missing_documents": missing,
        "review_flags": review_flags,
        "human_review_required": (
            checklist_result["review_required"] or bool(review_flags)
        ),
        "decision": "human_review_required",
    }
