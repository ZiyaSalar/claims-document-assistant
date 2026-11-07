
import os
import sys
from pathlib import Path

import pytest
from dotenv import load_dotenv


# --------------------------------------------------
# 1. PROJECT PATHS
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

FIXTURE_DIR = (
    PROJECT_ROOT
    / "tests"
    / "fixtures"
    / "claim_documents"
)

MODEL_DIR = (
    PROJECT_ROOT
    / "models"
    / "claims-document-classifier"
)

# Make backend and project modules importable
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

# Load environment variables from project root
load_dotenv(PROJECT_ROOT / ".env")


# --------------------------------------------------
# 2. TEST DOCUMENTS AND EXPECTED LABELS
# --------------------------------------------------

TEST_DOCUMENTS = [
    ("admission_advice.txt", "admission_advice"),
    ("discharge_summary.pdf", "discharge_summary"),
    ("hospital_bill.pdf", "hospital_bill"),
    ("signed_claim_form.pdf", "signed_claim_form"),
]


# --------------------------------------------------
# 3. END-TO-END OCR + CLASSIFIER TEST
# --------------------------------------------------

@pytest.mark.integration
@pytest.mark.parametrize(
    "filename, expected_type",
    TEST_DOCUMENTS
)
def test_pdf_ocr_and_document_classification(
    filename,
    expected_type
):

    # Check Azure credentials
    endpoint = os.getenv(
        "AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT"
    )

    key = os.getenv(
        "AZURE_DOCUMENT_INTELLIGENCE_KEY"
    )

    if not endpoint or not key:
        pytest.skip(
            "Azure Document Intelligence credentials are missing."
        )

    # Check model exists
    assert MODEL_DIR.exists(), (
        f"Trained model not found: {MODEL_DIR}"
    )

    # Check PDF exists
    image_path = FIXTURE_DIR / filename

    assert image_path.exists(), (
        f"Test PDF not found: {image_path}"
    )

    # Import services only when this integration test runs
    from app.services.document_intelligence import (
        extract_document_with_azure
    )

    from scripts.predict_document import (
        predict_document,
        tokenizer,
        MAX_LENGTH,
    )

    # ----------------------------------------------
    # STEP 1: Read PDF
    # ----------------------------------------------

    with open(image_path, "rb") as file:
        image_bytes = file.read()

    assert len(image_bytes) > 0, (
        f"PDF is empty: {filename}"
    )

    # ----------------------------------------------
    # STEP 2: Extract text using Azure OCR
    # ----------------------------------------------

    ocr_result = extract_document_with_azure(
        image_bytes
    )

    extracted_text = ocr_result["extracted_text"]
    # Inspect tokenization and truncation
    all_tokens = tokenizer(
        extracted_text,
        truncation=False
    )

    truncated_tokens = tokenizer(
        extracted_text,
        truncation=True,
        max_length=MAX_LENGTH
    )

    print("\n========== TOKEN INSPECTION ==========")

    print("Original token count:", len(all_tokens["input_ids"]))
    print("Maximum allowed tokens:", MAX_LENGTH)
    print("Tokens actually sent to model:", len(truncated_tokens["input_ids"]))

    print("\nText actually seen by DistilBERT:")
    print(
        tokenizer.decode(
            truncated_tokens["input_ids"],
            skip_special_tokens=True
        )
    )

    print("========== END TOKEN INSPECTION ==========")    

    print("\n========== EXTRACTED OCR TEXT ==========")
    print(extracted_text)
    print("========== END OCR TEXT ==========")

    assert extracted_text.strip(), (
        f"OCR did not extract any text from {filename}"
    )

    assert ocr_result["page_count"] > 0

    # ----------------------------------------------
    # STEP 3: Classify extracted text
    # ----------------------------------------------

    prediction = predict_document(extracted_text)

    # ----------------------------------------------
    # STEP 4: Validate prediction
    # ----------------------------------------------

    print("\n----------------------------------------")
    print("Document:", filename)
    print("Expected:", expected_type)
    print("Predicted:", prediction["predicted_type"])
    print("Confidence:", prediction["confidence"])
    print("Needs Review:", prediction["needs_review"])
    print("OCR Text Length:", len(extracted_text))
    print("Page Count:", ocr_result["page_count"])
    print("Class Scores:", prediction["class_scores"])
    print("----------------------------------------")

    # Check classifier returned all expected fields
    assert "predicted_type" in prediction
    assert "confidence" in prediction
    assert "needs_review" in prediction
    assert "class_scores" in prediction

    # Check probabilities are valid
    assert set(prediction["class_scores"].keys()) == {
        "admission_advice",
        "discharge_summary",
        "hospital_bill",
        "signed_claim_form",
    }

    assert sum(
        prediction["class_scores"].values()
    ) == pytest.approx(1.0, abs=0.001)

    # Check the final classification
    assert prediction["predicted_type"] == expected_type, (
        f"Classification mismatch for {filename}. "
        f"Expected {expected_type}, "
        f"got {prediction['predicted_type']}. "
        f"Confidence: {prediction['confidence']}"
    )

    # A correctly classified document should not need review
    assert prediction["needs_review"] is False
