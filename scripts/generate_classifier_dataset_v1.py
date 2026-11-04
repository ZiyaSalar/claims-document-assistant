
from pathlib import Path
from datetime import date, timedelta
import csv
import random
import re

# ==================================================
# 1. CONFIGURATION
# ==================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "data" / "synthetic_data"
OUTPUT_FILE = OUTPUT_DIR / "classifier_dataset_v2.csv"

RANDOM_SEED = 42
SAMPLES_PER_CLASS = 125

rng = random.Random(RANDOM_SEED)

# ==================================================
# 2. SYNTHETIC INFORMATION
# ==================================================

patients = [
    "Aarav Sharma", "Riya Patel", "Kabir Mehta",
    "Ananya Verma", "Ishaan Gupta", "Meera Nair",
    "Vivaan Rao", "Sara Khan", "Arjun Malhotra",
    "Diya Iyer", "Reyansh Shah", "Aditi Joshi",
]

hospitals = [
    "Green Valley Hospital",
    "City Care Medical Centre",
    "Sunrise Multispeciality Hospital",
    "Hopewell Hospital",
    "Metro Health Centre",
    "National Medical Institute",
    "Silverline Hospital",
]

doctors = [
    "Dr. Amit Shah", "Dr. Neha Kapoor",
    "Dr. Rahul Nair", "Dr. Priya Mehta",
    "Dr. Karan Rao", "Dr. Anjali Verma",
]

diagnoses = [
    "Acute respiratory infection",
    "Gastrointestinal infection",
    "Viral fever",
    "Dehydration",
    "Post-operative recovery",
    "Acute abdominal pain",
    "Urinary tract infection",
    "Community acquired pneumonia",
]

treatments = [
    "Medication and clinical observation",
    "Intravenous fluids and medication",
    "Antibiotic therapy",
    "Surgical treatment and monitoring",
    "Supportive care and observation",
    "Diagnostic tests and medical management",
]

departments = [
    "General Medicine",
    "Cardiology",
    "Orthopaedics",
    "General Surgery",
    "Neurology",
    "Emergency Medicine",
]

follow_ups = [
    "Review after seven days",
    "Continue prescribed medicines",
    "Attend the outpatient department",
    "Return for clinical assessment",
    "Follow up with the treating consultant",
]

payment_statuses = [
    "Paid",
    "Partially Paid",
    "Pending",
]

claim_categories = [
    "Cashless Hospitalization",
    "Medical Reimbursement",
    "Inpatient Treatment",
    "Hospitalization Expenses",
]

claim_ids = [f"CLM{i:04d}" for i in range(1, 1000)]

# ==================================================
# 3. TEMPLATE DEFINITIONS
# Eight template families per document class.
#
# Train:      templates 0-4
# Validation: templates 5-6
# Test:       template 7
# ==================================================

templates = {
    "admission_advice": [
        """
        ADMISSION ADVICE
        Patient Name: {patient}
        Claim Reference: {claim}
        Hospital: {hospital}
        Date of Admission: {admission_date}
        Department: {department}
        Reason for Admission: {diagnosis}
        The patient has been admitted for inpatient treatment.
        Attending Doctor: {doctor}
        """,
        """
        INPATIENT ADMISSION NOTICE
        This is to inform that {patient} was admitted to {hospital}.
        Reference Number: {claim}
        Admission Date: {admission_date}
        Reason for Admission: {diagnosis}
        Consultant: {doctor}
        Department: {department}
        """,
        """
        HOSPITAL ADMISSION RECORD
        Patient: {patient}
        Case ID: {claim}
        Facility: {hospital}
        Admission Details:
        The above patient has been registered for inpatient care
        beginning {admission_date}.
        Initial Assessment: {diagnosis}
        Responsible Physician: {doctor}
        """,
        """
        ADMISSION INTIMATION
        Insured Person: {patient}
        Claim ID: {claim}
        Hospital Name: {hospital}
        Admission Date: {admission_date}
        Treatment Category: Inpatient
        Ward: {department}
        This document confirms the patient's hospital admission.
        """,
        """
        PATIENT ADMISSION CONFIRMATION
        Name of Patient: {patient}
        Hospital: {hospital}
        Reference ID: {claim}
        Date: {admission_date}
        Status: Admitted
        Medical Department: {department}
        The patient is registered for hospital treatment.
        """,
        """
        NOTICE OF INPATIENT REGISTRATION
        Patient Details: {patient}
        Provider: {hospital}
        Authorization Reference: {claim}
        Registered On: {admission_date}
        Admission Reason: {diagnosis}
        The patient has been accepted for inpatient care.
        """,
        """
        HOSPITALIZATION ADMISSION LETTER
        To Whom It May Concern,
        This confirms the admission of {patient} at {hospital}.
        Claim Reference: {claim}
        Date of Entry: {admission_date}
        Unit: {department}
        Attending Consultant: {doctor}
        """,
        """
        INPATIENT REGISTRATION SLIP
        Patient: {patient}
        Facility: {hospital}
        Case Reference: {claim}
        Admission Time: {admission_date}
        Current Status: Patient admitted
        Assigned Department: {department}
        """,
    ],

    "discharge_summary": [
        """
        DISCHARGE SUMMARY
        Patient Name: {patient}
        Claim Reference: {claim}
        Hospital: {hospital}
        Date of Admission: {admission_date}
        Date of Discharge: {discharge_date}
        Final Diagnosis: {diagnosis}
        Treatment Provided: {treatment}
        Discharge Status: Stable
        Consultant: {doctor}
        """,
        """
        PATIENT DISCHARGE REPORT
        Patient: {patient}
        Case Number: {claim}
        Facility: {hospital}
        Final Diagnosis: {diagnosis}
        Hospital Stay: {admission_date} to {discharge_date}
        Treatment Course: {treatment}
        Condition at Discharge: Stable
        Follow-up: {follow_up}
        """,
        """
        SUMMARY OF HOSPITALIZATION
        Name: {patient}
        Reference ID: {claim}
        Hospital Name: {hospital}
        Admission: {admission_date}
        Discharge: {discharge_date}
        Clinical Findings: {diagnosis}
        Advice: {follow_up}
        Treating Doctor: {doctor}
        """,
        """
        DISCHARGE NOTE
        Patient Details: {patient}
        Claim ID: {claim}
        Hospital: {hospital}
        Diagnosis: {diagnosis}
        Treatment Course: {treatment}
        Discharged On: {discharge_date}
        Discharge Condition: Stable
        Follow-up Instructions: {follow_up}
        """,
        """
        FINAL DISCHARGE RECORD
        Patient Name: {patient}
        Hospital: {hospital}
        Claim Number: {claim}
        Admission Date: {admission_date}
        Discharge Date: {discharge_date}
        Diagnosis at Discharge: {diagnosis}
        Outcome: Discharged after completion of treatment.
        Physician: {doctor}
        """,
        """
        CLINICAL DISCHARGE DOCUMENT
        Name of Patient: {patient}
        Medical Facility: {hospital}
        Reference: {claim}
        Diagnosis: {diagnosis}
        Procedures and Treatment: {treatment}
        Date Released: {discharge_date}
        Clinical Condition: Stable
        Next Review: {follow_up}
        """,
        """
        SUMMARY OF PATIENT CARE
        Patient: {patient}
        Provider: {hospital}
        Case Reference: {claim}
        Inpatient Period: {admission_date} - {discharge_date}
        Medical Assessment: {diagnosis}
        Care Administered: {treatment}
        Disposition: Discharged
        """,
        """
        FINAL INPATIENT CARE REPORT
        Patient Name: {patient}
        Hospital: {hospital}
        Claim Reference: {claim}
        Principal Diagnosis: {diagnosis}
        Treatment Administered: {treatment}
        Date of Admission: {admission_date}
        Date of Release: {discharge_date}
        Status on Release: Stable
        """,
    ],

    "hospital_bill": [
        """
        HOSPITAL BILL
        Patient Name: {patient}
        Claim Reference: {claim}
        Hospital: {hospital}
        Room Charges: INR {room}
        Consultation Charges: INR {consultation}
        Medicine Charges: INR {medicine}
        Total Amount: INR {total}
        Payment Status: {payment_status}
        """,
        """
        FINAL INVOICE
        Billed To: {patient}
        Invoice Reference: {claim}
        Provider: {hospital}
        Bed and Nursing Charges: INR {room}
        Doctor Fees: INR {consultation}
        Pharmacy: INR {medicine}
        Amount Payable: INR {total}
        """,
        """
        MEDICAL EXPENSE STATEMENT
        Patient: {patient}
        Claim ID: {claim}
        Healthcare Facility: {hospital}
        Accommodation: INR {room}
        Professional Services: INR {consultation}
        Medical Supplies: INR {medicine}
        Grand Total: INR {total}
        """,
        """
        TAX INVOICE - HOSPITAL SERVICES
        Customer Name: {patient}
        Bill Number: {claim}
        Hospital Name: {hospital}
        Inpatient Room: INR {room}
        Medical Consultation: INR {consultation}
        Pharmacy Expenses: INR {medicine}
        Net Bill Amount: INR {total}
        """,
        """
        PATIENT BILLING RECORD
        Name: {patient}
        Reference Number: {claim}
        Hospital: {hospital}
        Treatment Charges: INR {consultation}
        Room Charges: INR {room}
        Supplies and Medicines: INR {medicine}
        Total Bill: INR {total}
        Balance Due: INR 0
        """,
        """
        ITEMIZED HOSPITAL INVOICE
        Account Holder: {patient}
        Billing Reference: {claim}
        Medical Provider: {hospital}
        Accommodation Charges: INR {room}
        Clinical Services: INR {consultation}
        Pharmacy Expenses: INR {medicine}
        Invoice Total: INR {total}
        Status: {payment_status}
        """,
        """
        STATEMENT OF MEDICAL CHARGES
        Patient: {patient}
        Facility: {hospital}
        Account Number: {claim}
        Ward Charges: INR {room}
        Professional Fees: INR {consultation}
        Medication Cost: INR {medicine}
        Amount Due: INR {total}
        """,
        """
        INPATIENT BILLING SUMMARY
        Patient Name: {patient}
        Hospital Name: {hospital}
        Bill Reference: {claim}
        Room and Nursing: INR {room}
        Medical Services: INR {consultation}
        Drugs and Supplies: INR {medicine}
        Total Invoice Value: INR {total}
        Payment: {payment_status}
        """,
    ],

    "signed_claim_form": [
        """
        HEALTH INSURANCE CLAIM FORM
        Insured Patient Name: {patient}
        Claim Number: {claim}
        Hospital Name: {hospital}
        Type of Claim: {claim_category}
        Bank and Policy Details: Provided separately
        Declaration: I confirm that the information provided is accurate.
        Signature of Claimant: SIMULATED SIGNATURE
        """,
        """
        CLAIM REIMBURSEMENT APPLICATION
        Name of Insured: {patient}
        Reference ID: {claim}
        Name of Hospital: {hospital}
        Claim Category: {claim_category}
        Patient Declaration: I request reimbursement of eligible expenses.
        Claimant Signature: SIMULATED SIGNATURE
        Date of Submission: {submission_date}
        """,
        """
        INSURANCE CLAIM SUBMISSION FORM
        Policy Holder: {patient}
        Claim ID: {claim}
        Healthcare Provider: {hospital}
        Patient Relationship: Self
        Declaration by Insured: Details submitted are true to my knowledge.
        Signature: SIMULATED SIGNATURE
        """,
        """
        MEDICAL CLAIM FORM
        Patient Name: {patient}
        Claim Reference Number: {claim}
        Hospital: {hospital}
        Requested Benefit: {claim_category}
        Authorization: I authorize processing of this claim.
        Signed By: {patient}
        Signature: SIMULATED SIGNATURE
        """,
        """
        COMPLETED CLAIM APPLICATION
        Insured Person: {patient}
        Claim Reference: {claim}
        Hospital Details: {hospital}
        Claim Type: {claim_category}
        Declaration: I certify that the attached details are correct.
        Signature of Insured: SIMULATED SIGNATURE
        """,
        """
        PATIENT INSURANCE DECLARATION
        Name of Policy Holder: {patient}
        Claim Reference: {claim}
        Treatment Provider: {hospital}
        Requested Coverage: {claim_category}
        I declare that the attached claim information is correct.
        Authorized Signature: SIMULATED SIGNATURE
        """,
        """
        REIMBURSEMENT CLAIM APPLICATION
        Insured Member: {patient}
        Reference Number: {claim}
        Hospital Attended: {hospital}
        Benefit Requested: {claim_category}
        Declaration of Claimant: I request payment under my policy.
        Signature of Applicant: SIMULATED SIGNATURE
        """,
        """
        SIGNED MEDICAL INSURANCE FORM
        Applicant Name: {patient}
        Claim Identifier: {claim}
        Healthcare Institution: {hospital}
        Claim Purpose: {claim_category}
        I certify the information in this application is correct.
        Applicant Authorization: SIMULATED SIGNATURE
        """,
    ],
}

# ==================================================
# 4. CREATE RANDOM DOCUMENT VALUES
# ==================================================

def make_example(document_type, template):
    patient = rng.choice(patients)
    hospital = rng.choice(hospitals)

    admission_date = date(
        2026, 1, 1
    ) + timedelta(days=rng.randint(0, 300))

    stay_days = rng.randint(1, 12)
    discharge_date = admission_date + timedelta(days=stay_days)

    room = rng.randrange(5000, 25001, 500)
    consultation = rng.randrange(1000, 6001, 500)
    medicine = rng.randrange(1000, 12001, 500)

    values = {
        "patient": patient,
        "hospital": hospital,
        "doctor": rng.choice(doctors),
        "claim": rng.choice(claim_ids),
        "admission_date": admission_date.strftime("%d/%m/%Y"),
        "discharge_date": discharge_date.strftime("%d/%m/%Y"),
        "submission_date": admission_date.strftime("%d/%m/%Y"),
        "diagnosis": rng.choice(diagnoses),
        "treatment": rng.choice(treatments),
        "department": rng.choice(departments),
        "follow_up": rng.choice(follow_ups),
        "payment_status": rng.choice(payment_statuses),
        "claim_category": rng.choice(claim_categories),
        "room": room,
        "consultation": consultation,
        "medicine": medicine,
        "total": room + consultation + medicine,
    }

    return template.format(**values).strip()


# ==================================================
# 5. CONTROLLED OCR AND LAYOUT VARIATIONS
# ==================================================

def apply_ocr_variation(text):
    # Some documents retain normal line breaks.
    # Others are flattened by text extraction.
    if rng.random() < 0.40:
        text = " ".join(text.split())
    else:
        text = "\n".join(
            line.strip() for line in text.splitlines() if line.strip()
        )

    # Small OCR-like punctuation and spacing variations.
    if rng.random() < 0.15:
        text = text.replace(": ", " ", 1)

    if rng.random() < 0.10:
        text = re.sub(r" {2,}", " ", text)

    # Apply a small number of character recognition errors.
    # The same noise process applies to every class.
    if rng.random() < 0.20:
        substitutions = {
            "0": "O",
            "1": "I",
            "O": "0",
            "I": "1",
        }

        chars = list(text)
        eligible = [
            i for i, char in enumerate(chars)
            if char in substitutions
        ]

        if eligible:
            position = rng.choice(eligible)
            chars[position] = substitutions[chars[position]]
            text = "".join(chars)

    # Occasionally break a word with an OCR-style space.
    if rng.random() < 0.08:
        words = text.split()
        candidates = [
            i for i, word in enumerate(words)
            if len(word) >= 8 and word.isalpha()
        ]

        if candidates:
            index = rng.choice(candidates)
            word = words[index]
            cut = rng.randint(3, len(word) - 2)
            words[index] = word[:cut] + " " + word[cut:]
            text = " ".join(words)

    return text


# ==================================================
# 6. GENERATE TRAIN / VALIDATION / TEST DATA
# ==================================================

def generate_dataset():
    rows = []

    split_templates = {
        "train": list(range(5)),
        "validation": [5, 6],
        "test": [7],
    }

    split_counts = {
        "train": 75,
        "validation": 25,
        "test": 25,
    }

    for document_type, class_templates in templates.items():

        for split, template_indices in split_templates.items():

            count = split_counts[split]

            for _ in range(count):
                template_index = rng.choice(template_indices)
                template = class_templates[template_index]

                text = make_example(document_type, template)
                text = apply_ocr_variation(text)

                rows.append({
                    "text": text,
                    "label": document_type,
                    "split": split,
                })

    rng.shuffle(rows)

    return rows


# ==================================================
# 7. VALIDATE AND SAVE DATASET
# ==================================================

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if OUTPUT_FILE.exists():
        raise FileExistsError(
            f"{OUTPUT_FILE} already exists. "
            "Rename or move it before generating a new version."
        )

    rows = generate_dataset()

    if len(rows) != 500:
        raise ValueError(
            f"Expected 500 examples, generated {len(rows)}"
        )

    for row in rows:
        if not row["text"].strip():
            raise ValueError("Empty document text found.")

        if row["label"] not in templates:
            raise ValueError(f"Invalid label: {row['label']}")

        if row["split"] not in ["train", "validation", "test"]:
            raise ValueError(f"Invalid split: {row['split']}")

    with OUTPUT_FILE.open(
        "w", newline="", encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=["text", "label", "split"]
        )

        writer.writeheader()
        writer.writerows(rows)

    print("\nDataset generated successfully!")
    print("Output:", OUTPUT_FILE)
    print("Total examples:", len(rows))

    for split in ["train", "validation", "test"]:
        split_rows = [
            row for row in rows if row["split"] == split
        ]

        print(f"\n{split.upper()}: {len(split_rows)} examples")

        for label in templates:
            count = sum(
                row["label"] == label for row in split_rows
            )
            print(f"  {label}: {count}")

    print(
        "\nUnique texts:",
        len(set(row["text"] for row in rows))
    )


if __name__ == "__main__":
    main()
