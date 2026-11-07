
import sys
from pathlib import Path
from transformers import AutoTokenizer

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from app.services.document_intelligence import extract_document_with_azure
from scripts.predict_document import predict_document


PDF_PATH = (
    PROJECT_ROOT
    / "tests"
    / "fixtures"
    / "claim_documents"
    / "hospital_bill.pdf"
)


# 1. Read pdf as bytes
print("\nReading PDF document...")

image_bytes = PDF_PATH.read_bytes()


# 2. Extract text using Azure OCR
print("\nExtracting text using Azure Document Intelligence...")

ocr_result = extract_document_with_azure(image_bytes)

extracted_text = ocr_result["extracted_text"]

# Inspect tokenization
tokenizer = AutoTokenizer.from_pretrained(
    "models/claims-document-classifier-v3"
)

tokens = tokenizer(
    extracted_text,
    truncation=False
)["input_ids"]

tokens_sent = tokenizer(
    extracted_text,
    truncation=True,
    max_length=512
)["input_ids"]

print("\n========== TOKEN INSPECTION ==========")
print("Total tokens:", len(tokens))
print("Tokens sent to model:", len(tokens_sent))
print("Tokens truncated:", max(0, len(tokens) - len(tokens_sent)))

print("\nLast 500 characters of OCR text:")
print(extracted_text[-500:])


# 3. Display OCR results
print("\n========== OCR RESULTS ==========")

print("Page Count:", ocr_result["page_count"])
print("Text Length:", ocr_result["text_length"])

print("\nExtracted Text:")
print(extracted_text)


# 4. Pass extracted text to fine-tuned classifier
print("\nClassifying extracted document...")

prediction = predict_document(extracted_text)


# 5. Display classification results
print("\n========== CLASSIFICATION RESULTS ==========")

print("Predicted Type:", prediction["predicted_type"])
print("Confidence:", prediction["confidence"])
print("Needs Human Review:", prediction["needs_review"])

print("\nClass Probabilities:")

for label, score in prediction["class_scores"].items():
    print(f"{label}: {score}")

print("\nEnd-to-end test completed.")
