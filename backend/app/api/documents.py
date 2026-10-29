
from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from backend.app.services.claim_store import claims
from backend.app.services.document_processing import validate_and_extract
from backend.app.services.document_storage import save_document
from backend.app.services.document_classifier import classify_document
from backend.app.services.document_checklist import generate_checklist
from backend.app.services.claim_summary import generate_claim_summary
from backend.app.services.claim_document_status import (
    REQUIRED_DOCUMENTS,
    mark_document_received,
    verify_claim_documents,
)

router = APIRouter(prefix="/api/claims", tags=["Documents"])

documents = {}


@router.post(
    "/{claim_id}/documents",
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    claim_id: str,
    file: UploadFile = File(...),
    document_type: str | None = Form(default=None),
):
    if claim_id not in claims:
        raise HTTPException(status_code=404, detail="Claim not found")

    if document_type is not None and document_type not in REQUIRED_DOCUMENTS:
        raise HTTPException(
            status_code=400,
            detail="Unsupported document type",
        )

    content = await file.read(10 * 1024 * 1024 + 1)

    try:
        metadata = save_document(
            claim_id,
            file.filename or "",
            content,
        )

        processing = validate_and_extract(
            metadata["storage_path"],
            metadata["file_type"],
        )

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    except OSError as exc:
        raise HTTPException(
            status_code=500,
            detail="Could not store or read the file",
        ) from exc

    duplicate_of = next(
        (
            doc["document_id"]
            for doc in documents.values()
            if doc["sha256"] == processing["sha256"]
        ),
        None,
    )

    metadata.update({
        "sha256": processing["sha256"],
        "page_count": processing["page_count"],
        "text_length": processing["text_length"],
        "processing_status": "completed",
        "duplicate": duplicate_of is not None,
        "duplicate_of": duplicate_of,
        "extracted_text": processing["extracted_text"],
    })

    if document_type is not None:
        classification = classify_document(
            processing["extracted_text"]
        )

        metadata["document_type"] = document_type
        metadata["classification"] = classification

        if (
            classification["predicted_type"] == document_type
            and not classification["needs_review"]
        ):
            metadata["document_status"] = "received"
        else:
            metadata["document_status"] = "needs_review"

    documents[metadata["document_id"]] = metadata

    if (
        document_type is not None
        and metadata["document_status"] == "received"
    ):
        mark_document_received(
            claims[claim_id],
            document_type,
            metadata["document_id"],
        )

    verification = verify_claim_documents(claims[claim_id])
    claims[claim_id]["verification_status"] = (
        verification["verification_status"]
    )

    response = {
        key: value
        for key, value in metadata.items()
        if key != "extracted_text"
    }

    if document_type is not None:
        response["verification"] = verification

    return response


@router.get("/{claim_id}/documents")
def list_documents(claim_id: str):
    if claim_id not in claims:
        raise HTTPException(status_code=404, detail="Claim not found")

    return [
        {
            key: value
            for key, value in document.items()
            if key != "extracted_text"
        }
        for document in documents.values()
        if document["claim_id"] == claim_id
    ]


@router.get("/{claim_id}/documents/{document_id}/text")
def get_document_text(claim_id: str, document_id: str):
    if claim_id not in claims:
        raise HTTPException(status_code=404, detail="Claim not found")

    document = documents.get(document_id)

    if document is None or document["claim_id"] != claim_id:
        raise HTTPException(status_code=404, detail="Document not found")

    return {
        "document_id": document_id,
        "extracted_text": document["extracted_text"],
        "text_length": document["text_length"],
        "page_count": document["page_count"],
    }


@router.post("/{claim_id}/documents/{document_id}/classify")
def classify_uploaded_document(claim_id: str, document_id: str):
    if claim_id not in claims:
        raise HTTPException(status_code=404, detail="Claim not found")

    document = documents.get(document_id)

    if document is None or document["claim_id"] != claim_id:
        raise HTTPException(status_code=404, detail="Document not found")

    result = classify_document(document["extracted_text"])
    document["classification"] = result

    return {
        "document_id": document_id,
        **result,
    }


@router.get("/{claim_id}/checklist")
def get_claim_checklist(claim_id: str):
    if claim_id not in claims:
        raise HTTPException(status_code=404, detail="Claim not found")

    claim_documents = [
        document
        for document in documents.values()
        if document["claim_id"] == claim_id
    ]

    result = generate_checklist(claim_documents)

    return {
        "claim_id": claim_id,
        **result,
    }


@router.get("/{claim_id}/summary")
def get_claim_summary(claim_id: str):
    if claim_id not in claims:
        raise HTTPException(status_code=404, detail="Claim not found")

    claim_documents = [
        document
        for document in documents.values()
        if document["claim_id"] == claim_id
    ]

    checklist_result = generate_checklist(claim_documents)

    return generate_claim_summary(
        claim=claims[claim_id],
        checklist_result=checklist_result,
        documents=claim_documents,
    )
