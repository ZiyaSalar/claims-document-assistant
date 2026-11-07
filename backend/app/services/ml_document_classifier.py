
import os
from functools import lru_cache
from pathlib import Path

import torch
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
)

PROJECT_ROOT = Path(__file__).resolve().parents[3]

MODEL_DIR = Path(
    os.getenv(
        "CLASSIFIER_MODEL_DIR",
        str(PROJECT_ROOT / "models" / "claims-document-classifier-v4"),
    )
)

CONFIDENCE_THRESHOLD = 0.7


@lru_cache(maxsize=1)
def load_classifier():
    tokenizer = AutoTokenizer.from_pretrained(
        str(MODEL_DIR),
        local_files_only=True,
    )

    model = AutoModelForSequenceClassification.from_pretrained(
        str(MODEL_DIR),
        local_files_only=True,
    )

    model.eval()
    return tokenizer, model


def classify_document_ml(text: str) -> dict:
    if not text or not text.strip():
        return {
            "predicted_type": "unknown",
            "confidence": 0.0,
            "needs_review": True,
            "class_scores": {},
        }

    tokenizer, model = load_classifier()

    inputs = tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        max_length=512,
    )

    with torch.inference_mode():
        logits = model(**inputs).logits
        probabilities = torch.softmax(logits, dim=-1)[0]

    predicted_id = int(torch.argmax(probabilities).item())
    confidence = float(probabilities[predicted_id].item())

    needs_review = confidence < CONFIDENCE_THRESHOLD

    scores = {
        model.config.id2label[i]: round(float(prob), 4)
        for i, prob in enumerate(probabilities)
    }

    return {
        "predicted_type": (
            "unknown"
            if needs_review
            else model.config.id2label[predicted_id]
        ),
        "confidence": round(confidence, 4),
        "needs_review": needs_review,
        "class_scores": scores,
    }
