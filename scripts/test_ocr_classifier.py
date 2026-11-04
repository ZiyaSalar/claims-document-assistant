
import sys
from pathlib import Path

# Allow importing services from the backend folder
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.services.document_intelligence import extract_document_with_azure
from scripts.predict_document import predict_document


# Path of the PNG document
IMAGE_PATH = (
    "data/uploads/44da5a25-b359-4bf5-a507-e2f85060443d/"
    "ziya.png"
)


# 1. Read PNG as bytes
print("\nReading PNG image...")

with open(IMAGE_PATH, "rb") as file:
    image_bytes = file.read()


# 2. Extract text using Azure OCR
print("\nExtracting text using Azure Document Intelligence...")

ocr_result = extract_document_with_azure(image_bytes)

extracted_text = ocr_result["extracted_text"]


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
