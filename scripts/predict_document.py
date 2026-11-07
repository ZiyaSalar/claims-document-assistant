
import torch

from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
)

# ==================================================
# 1. CONFIGURATION
# ==================================================

MODEL_DIR = "models/claims-document-classifier-v3"
MAX_LENGTH = 512
CONFIDENCE_THRESHOLD = 0.70

# ==================================================
# 2. LOAD MODEL AND TOKENIZER
# ==================================================

print("Loading fine-tuned DistilBERT model...")

device = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)

tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)

model = AutoModelForSequenceClassification.from_pretrained(
    MODEL_DIR
)

model.to(device)
model.eval()

print("Model loaded successfully!")
print("Device:", device)


# ==================================================
# 3. DOCUMENT PREDICTION FUNCTION
# ==================================================

def predict_document(text):

    if not text or not text.strip():
        raise ValueError("Document text cannot be empty.")

    # Convert text into tokens
    inputs = tokenizer(
        text,
        truncation=True,
        max_length=MAX_LENGTH,
        return_tensors="pt",
    )

    inputs = {
        key: value.to(device)
        for key, value in inputs.items()
    }

    # Get model predictions
    with torch.no_grad():
        outputs = model(**inputs)

    # Convert logits into probabilities
    probabilities = torch.softmax(
        outputs.logits,
        dim=1,
    )[0]

    # Find the class with the highest probability
    predicted_id = torch.argmax(probabilities).item()

    predicted_type = model.config.id2label[predicted_id]

    confidence = probabilities[predicted_id].item()

    needs_review = confidence < CONFIDENCE_THRESHOLD
    
    if needs_review:
        predicted_type = "unknown"

    # Scores for all four classes
    class_scores = {
        model.config.id2label[i]: round(
            probabilities[i].item(), 4
        )
        for i in range(len(probabilities))
    }

    return {
        "predicted_type": predicted_type,
        "confidence": round(confidence, 4),
        "needs_review": needs_review,
        "class_scores": class_scores,
    }


# ==================================================
# 4. TEST MULTIPLE DOCUMENT TYPES
# ==================================================

if __name__ == "__main__":

    test_documents = {
        "Admission advice": """
        INPATIENT ADMISSION AUTHORIZATION

        Patient: Ananya Verma
        Hospital: Green Valley Hospital
        Claim Reference: CLM1234

        The patient has been approved for inpatient
        admission beginning 04/11/2026.

        Reason for Admission: Acute respiratory infection
        Authorized Department: General Medicine
        """,

        "Discharge summary": """
        FINAL HOSPITAL DISCHARGE REPORT

        Patient: Riya Patel
        Hospital: City Care Medical Centre
        Claim Reference: CLM2345

        Final Diagnosis: Gastrointestinal infection
        Treatment Administered: Medication and observation
        Date of Discharge: 10/11/2026
        Condition at Discharge: Stable
        Follow-up: Continue prescribed medication.
        """,

        "Hospital bill": """
        ITEMIZED MEDICAL INVOICE

        Patient: Kabir Mehta
        Hospital: Sunrise Multispeciality Hospital
        Invoice Number: INV3456

        Room Charges: INR 15000
        Doctor Consultation: INR 3000
        Medicines: INR 4500
        Total Amount Payable: INR 22500
        Payment Status: Pending
        """,

        "Signed claim form": """
        HEALTH INSURANCE REIMBURSEMENT APPLICATION

        Insured Person: Meera Nair
        Claim Number: CLM4567
        Hospital: Hopewell Hospital

        Claim Type: Medical Reimbursement

        Declaration:
        I confirm that the information provided is true
        and request reimbursement under my policy.

        Signature of Claimant: SIMULATED SIGNATURE
        """,

        "Unfamiliar document": """
        EMPLOYEE LEAVE APPLICATION

        Employee Name: Rahul Sharma
        Department: Finance
        Leave Type: Annual Leave
        Start Date: 12/11/2026
        End Date: 15/11/2026

        I request approval for the above leave period.
        """
    }

    for document_name, text in test_documents.items():

        result = predict_document(text)

        print("\n" + "=" * 55)
        print("INPUT DOCUMENT:", document_name)
        print("=" * 55)

        print("Predicted Type:", result["predicted_type"])
        print("Confidence:", result["confidence"])
        print("Needs Review:", result["needs_review"])

        print("\nClass probabilities:")

        for label, score in result["class_scores"].items():
            print(f"{label}: {score}")
