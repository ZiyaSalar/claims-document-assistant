import re

DOCUMENT_PATTERNS = {
    "hospital_bill": [
        r"\bhospital bill\b",
        r"\bitemi[sz]ed bill\b",
        r"\btotal amount\b",
        r"\broom charges\b",
        r"\binvoice\b",
    ],
    "discharge_summary": [
        r"\bdischarge summary\b",
        r"\bdate of discharge\b",
        r"\bdischarged\b",
        r"\bdischarge diagnosis\b",
    ],
    "admission_advice": [
        r"\badmission advice\b",
        r"\badvised admission\b",
        r"\binpatient admission\b",
        r"\badmission date\b",
    ],
    "signed_claim_form": [
        r"\bclaim form\b",
        r"\bmember signature\b",
        r"\bsignature\b",
        r"\bclaimant declaration\b",
    ],
}


def classify_document(text: str) -> dict:
    if not text or not text.strip():
        return {
            "predicted_type": "unknown",
            "confidence": 0.0,
            "needs_review": True,
        }

    normalized_text = re.sub(r"\s+", " ", text.lower())

    scores = {
        category: sum(
            bool(re.search(pattern, normalized_text))
            for pattern in patterns
        )
        for category, patterns in DOCUMENT_PATTERNS.items()
    }

    best_category = max(scores, key=scores.get)
    best_score = scores[best_category]
    total_matches = sum(scores.values())

    if best_score == 0:
        return {
            "predicted_type": "unknown",
            "confidence": 0.0,
            "needs_review": True,
        }

    tied = sum(score == best_score for score in scores.values()) > 1
    confidence = best_score / total_matches

    if tied or confidence < 0.6:
        return {
            "predicted_type": "unknown",
            "confidence": round(confidence, 2),
            "needs_review": True,
        }

    return {
        "predicted_type": best_category,
        "confidence": round(confidence, 2),
        "needs_review": False,
    }