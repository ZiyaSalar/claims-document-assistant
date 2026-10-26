
from pathlib import Path
from datetime import date
import csv
import json

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from pypdf import PdfReader


# Project directories
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "synthetic_data"
DOCUMENTS_DIR = DATA_DIR / "documents"


# Allowed document categories
DOCUMENT_TYPES = {
    "hospital_bill",
    "discharge_summary",
    "admission_advice",
    "signed_claim_form",
}


# Fictional claims
CLAIMS = [
    {
        "claim_id": "CLM001",
        "plan": "BASIC_PLUS",
        "service_type": "inpatient",
        "submission_date": "2026-10-20",
        "review_status": "pending_review",
    },
    {
        "claim_id": "CLM002",
        "plan": "BASIC_PLUS",
        "service_type": "inpatient",
        "submission_date": "2026-10-21",
        "review_status": "pending_review",
    },
]


# Versioned checklist
CHECKLIST = {
    "checklist_id": "CHK001",
    "version": "1.0",
    "plan": "BASIC_PLUS",
    "service_type": "inpatient",
    "required_document_types": [
        "hospital_bill",
        "discharge_summary",
        "admission_advice",
        "signed_claim_form",
    ],
}

# Synthetic document definitions.
# Each entry describes a file that should actually exist.

DOCUMENTS = [
    {
        "document_id": "DOC001",
        "claim_id": "CLM001",
        "filename": "hospital_bill.pdf",
        "document_type": "hospital_bill",
        "content_type": "application/pdf",
        "text": (
            "FICTIONAL HOSPITAL BILL\n"
            "Claim ID: CLM001\n"
            "Provider: Example City Hospital\n"
            "Patient: Fictional Person A\n"
            "Room charges: INR 12000\n"
            "Medical supplies: INR 3000\n"
            "Total amount: INR 15000\n"
        ),
    },
    {
        "document_id": "DOC002",
        "claim_id": "CLM001",
        "filename": "discharge_summary.txt",
        "document_type": "discharge_summary",
        "content_type": "text/plain",
        "text": (
            "FICTIONAL DISCHARGE SUMMARY\n"
            "Claim ID: CLM001\n"
            "Patient: Fictional Person A\n"
            "Admission: 2026-10-10\n"
            "Discharge: 2026-10-13\n"
            "Status: Discharged for routine follow-up.\n"
        ),
    },
    {
        "document_id": "DOC003",
        "claim_id": "CLM001",
        "filename": "admission_advice.txt",
        "document_type": "admission_advice",
        "content_type": "text/plain",
        "text": (
            "FICTIONAL ADMISSION ADVICE\n"
            "Claim ID: CLM001\n"
            "Patient: Fictional Person A\n"
            "Service: Inpatient admission\n"
            "This document is a synthetic test fixture.\n"
        ),
    },
    {
        "document_id": "DOC004",
        "claim_id": "CLM001",
        "filename": "signed_claim_form.pdf",
        "document_type": "signed_claim_form",
        "content_type": "application/pdf",
        "text": (
            "FICTIONAL CLAIM FORM\n"
            "Claim ID: CLM001\n"
            "Patient: Fictional Person A\n"
            "Signature: SIMULATED - NOT A REAL SIGNATURE\n"
            "This form is for software testing only.\n"
        ),
    },
    {
        "document_id": "DOC005",
        "claim_id": "CLM002",
        "filename": "hospital_bill.txt",
        "document_type": "hospital_bill",
        "content_type": "text/plain",
        "text": (
            "FICTIONAL HOSPITAL BILL\n"
            "Claim ID: CLM002\n"
            "Provider: Sample Medical Centre\n"
            "Patient: Fictional Person B\n"
            "Total amount: INR 8500\n"
        ),
    },
    {
        "document_id": "DOC006",
        "claim_id": "CLM002",
        "filename": "discharge_summary.pdf",
        "document_type": "discharge_summary",
        "content_type": "application/pdf",
        "text": (
            "FICTIONAL DISCHARGE SUMMARY\n"
            "Claim ID: CLM002\n"
            "Patient: Fictional Person B\n"
            "Status: Discharged for routine follow-up.\n"
        ),
    },
    {
        "document_id": "DOC007",
        "claim_id": "CLM002",
        "filename": "admission_advice.txt",
        "document_type": "admission_advice",
        "content_type": "text/plain",
        "text": (
            "FICTIONAL ADMISSION ADVICE\n"
            "Claim ID: CLM002\n"
            "Patient: Fictional Person B\n"
            "Service: Inpatient admission\n"
        ),
    },
]


def write_document(document, output_path):
    """Write a TXT or PDF document based on its declared content type."""

    output_path.parent.mkdir(parents=True, exist_ok=True)

    if output_path.exists():
        raise FileExistsError(
            f"Refusing to overwrite existing file: {output_path}"
        )

    if document["content_type"] == "text/plain":
        output_path.write_text(document["text"], encoding="utf-8")

    elif document["content_type"] == "application/pdf":
        pdf = canvas.Canvas(str(output_path), pagesize=A4)
        page_width, page_height = A4

        text_object = pdf.beginText(50, page_height - 60)
        text_object.setFont("Helvetica", 11)
        text_object.setLeading(18)

        for line in document["text"].splitlines():
            # Keep text within the printable page width.
            for start in range(0, max(len(line), 1), 75):
                text_object.textLine(line[start:start + 75])

        pdf.drawText(text_object)
        pdf.save()

    else:
        raise ValueError(
            f"Unsupported content type: {document['content_type']}"
        )


def generate_documents():
    """Generate all declared synthetic document files."""

    for document in DOCUMENTS:
        output_path = (
            DOCUMENTS_DIR
            / document["claim_id"]
            / document["filename"]
        )

        write_document(document, output_path)
        print(f"Created: {output_path.relative_to(PROJECT_ROOT)}")


# CSV column definitions. These establish a consistent data schema.

CLAIM_FIELDS = [
    "claim_id",
    "plan",
    "service_type",
    "submission_date",
    "review_status",
]

DOCUMENT_FIELDS = [
    "document_id",
    "claim_id",
    "filename",
    "document_type",
    "file_path",
    "content_type",
    "processing_status",
]


# Expected outcomes for later checklist-engine tests.
EVALUATION_CASES = [
    {
        "case_id": "EVAL001",
        "claim_id": "CLM001",
        "scenario": "complete_packet",
        "expected_status": "complete",
        "expected_missing_documents": [],
    },
    {
        "case_id": "EVAL002",
        "claim_id": "CLM002",
        "scenario": "missing_signed_claim_form",
        "expected_status": "incomplete",
        "expected_missing_documents": ["signed_claim_form"],
    },
]


def write_csv(filename, fieldnames, rows):
    """Write structured records to a CSV file."""

    output_path = DATA_DIR / filename

    if output_path.exists():
        raise FileExistsError(
            f"Refusing to overwrite existing file: {output_path}"
        )

    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_jsonl(filename, records):
    """Write one JSON object per line."""

    output_path = DATA_DIR / filename

    if output_path.exists():
        raise FileExistsError(
            f"Refusing to overwrite existing file: {output_path}"
        )

    with output_path.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")


def build_document_metadata():
    """Build metadata with paths relative to the project root."""

    metadata = []

    for document in DOCUMENTS:
        relative_path = (
            DOCUMENTS_DIR
            / document["claim_id"]
            / document["filename"]
        ).relative_to(PROJECT_ROOT)

        metadata.append({
            "document_id": document["document_id"],
            "claim_id": document["claim_id"],
            "filename": document["filename"],
            "document_type": document["document_type"],
            "file_path": relative_path.as_posix(),
            "content_type": document["content_type"],
            "processing_status": "pending",
        })

    return metadata


def build_labeled_document_records():
    """Build labels for future classifier experiments."""

    return [
        {
            "document_id": document["document_id"],
            "claim_id": document["claim_id"],
            "filename": document["filename"],
            "document_type": document["document_type"],
            "file_path": (
                DOCUMENTS_DIR
                / document["claim_id"]
                / document["filename"]
            ).relative_to(PROJECT_ROOT).as_posix(),
            "content_type": document["content_type"],
            "processing_status": "pending",
        }
        for document in DOCUMENTS
    ]


def validate_dataset(claims, metadata):
    """Validate IDs, relationships, labels, files, checklists and PDFs."""

    errors = []

    claim_ids = [claim["claim_id"] for claim in claims]
    document_ids = [doc["document_id"] for doc in metadata]

    # Check uniqueness
    if len(claim_ids) != len(set(claim_ids)):
        errors.append("Claim IDs are not unique.")

    if len(document_ids) != len(set(document_ids)):
        errors.append("Document IDs are not unique.")

    claim_id_set = set(claim_ids)

    # Validate each document
    for document in metadata:
        if document["claim_id"] not in claim_id_set:
            errors.append(
                f'{document["document_id"]}: unknown claim '
                f'{document["claim_id"]}'
            )

        if document["document_type"] not in DOCUMENT_TYPES:
            errors.append(
                f'{document["document_id"]}: invalid label '
                f'{document["document_type"]}'
            )

        if document["content_type"] not in {
            "application/pdf",
            "text/plain",
        }:
            errors.append(
                f'{document["document_id"]}: invalid content type'
            )

        file_path = PROJECT_ROOT / document["file_path"]

        if not file_path.is_file():
            errors.append(
                f'{document["document_id"]}: file does not exist: '
                f'{document["file_path"]}'
            )
            continue

        # Verify that PDFs open and contain extractable text.
        if document["content_type"] == "application/pdf":
            try:
                reader = PdfReader(str(file_path))

                if not reader.pages:
                    errors.append(
                        f'{document["document_id"]}: PDF has no pages'
                    )
                    continue

                extracted_text = "\n".join(
                    page.extract_text() or ""
                    for page in reader.pages
                )

                if not extracted_text.strip():
                    errors.append(
                        f'{document["document_id"]}: PDF text is empty'
                    )

            except Exception as exc:
                errors.append(
                    f'{document["document_id"]}: PDF validation failed: '
                    f'{exc}'
                )

    # Validate checklist fields and document categories.
    checklist_required_fields = {
        "checklist_id",
        "version",
        "plan",
        "service_type",
        "required_document_types",
    }

    if not checklist_required_fields.issubset(CHECKLIST):
        errors.append("Checklist is missing required fields.")

    if not set(CHECKLIST["required_document_types"]).issubset(
        DOCUMENT_TYPES
    ):
        errors.append("Checklist contains an invalid document type.")

    # Ensure evaluation cases reference valid claims.
    for case in EVALUATION_CASES:
        if case["claim_id"] not in claim_id_set:
            errors.append(
                f'{case["case_id"]}: unknown claim {case["claim_id"]}'
            )

    # Check that both expected scenarios are represented.
    expected_scenarios = {
        "complete_packet",
        "missing_signed_claim_form",
    }

    actual_scenarios = {
        case["scenario"] for case in EVALUATION_CASES
    }

    if not expected_scenarios.issubset(actual_scenarios):
        errors.append("Complete and incomplete scenarios are required.")

    # Verify actual packet completeness against the checklist.
    for claim in claims:
        received_types = {
            doc["document_type"]
            for doc in metadata
            if doc["claim_id"] == claim["claim_id"]
        }

        missing_types = sorted(
            set(CHECKLIST["required_document_types"]) - received_types
        )

        matching_cases = [
            case for case in EVALUATION_CASES
            if case["claim_id"] == claim["claim_id"]
        ]

        for case in matching_cases:
            expected_missing = sorted(
                case["expected_missing_documents"]
            )

            if missing_types != expected_missing:
                errors.append(
                    f'{case["case_id"]}: expected missing '
                    f'{expected_missing}, actual {missing_types}'
                )

            expected_status = (
                "complete" if not missing_types else "incomplete"
            )

            if case["expected_status"] != expected_status:
                errors.append(
                    f'{case["case_id"]}: expected status does not '
                    f'match the checklist result'
                )

    if errors:
        raise ValueError(
            "Dataset validation failed:\n- " + "\n- ".join(errors)
        )

    print("Validation passed:")
    print(f"  Unique claims: {len(claim_ids)}")
    print(f"  Unique documents: {len(document_ids)}")
    print("  All document files exist.")
    print("  All PDF files open and contain extractable text.")
    print("  Checklist and evaluation scenarios are consistent.")


def generate_dataset():
    """Generate files and metadata without overwriting existing outputs."""

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Refuse to start if any expected output already exists.
    expected_outputs = [
        DATA_DIR / "claim_cases.csv",
        DATA_DIR / "labeled_docs.csv",
        DATA_DIR / "checklists.jsonl",
        DATA_DIR / "evaluation_cases.jsonl",
    ]

    expected_outputs.extend(
        DOCUMENTS_DIR / doc["claim_id"] / doc["filename"]
        for doc in DOCUMENTS
    )

    existing_outputs = [
        path for path in expected_outputs if path.exists()
    ]

    if existing_outputs:
        raise FileExistsError(
            "Existing outputs were found. Nothing was generated:\n"
            + "\n".join(str(path) for path in existing_outputs)
        )

    # Generate the actual documents first.
    generate_documents()

    # Build metadata with paths to the generated files.
    metadata = build_document_metadata()
    labeled_documents = build_labeled_document_records()

    # Validate the in-memory records and actual generated files.
    validate_dataset(CLAIMS, metadata)

    # Export the CSV and JSONL files.
    write_csv("claim_cases.csv", CLAIM_FIELDS, CLAIMS)
    write_csv("labeled_docs.csv", DOCUMENT_FIELDS, labeled_documents)
    write_jsonl("checklists.jsonl", [CHECKLIST])
    write_jsonl("evaluation_cases.jsonl", EVALUATION_CASES)

    print("\nDataset generation completed successfully.")
    print(f"Output directory: {DATA_DIR}")


if __name__ == "__main__":
    generate_dataset()
