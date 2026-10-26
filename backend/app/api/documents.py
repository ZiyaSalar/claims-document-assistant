from fastapi import APIRouter, File, HTTPException, UploadFile, status

from backend.app.api.claims import claims
from backend.app.services.document_processing import validate_and_extract
from backend.app.services.document_storage import save_document
from backend.app.services.document_classifier import classify_document

from backend.app.services.document_checklist import generate_checklist


router = APIRouter(prefix="/api/claims", tags=["Documents"])

documents = {}


@router.post(
    "/{claim_id}/documents",
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    claim_id: str,
    file: UploadFile = File(...),
):
    if claim_id not in claims:
        raise HTTPException(404, "Claim not found")

    content = await file.read(10 * 1024 * 1024 + 1)

    try:
        metadata = save_document(
            claim_id, file.filename or "", content
        )

        processing = validate_and_extract(
            metadata["storage_path"], metadata["file_type"]
        )

    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc

    except OSError as exc:
        raise HTTPException(500, "Could not store or read the file") from exc

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

    documents[metadata["document_id"]] = metadata

    return {
        key: value
        for key, value in metadata.items()
        if key != "extracted_text"
    }


@router.get("/{claim_id}/documents")
def list_documents(claim_id: str):
    if claim_id not in claims:
        raise HTTPException(404, "Claim not found")

    return [
        {key: value for key, value in doc.items() if key != "extracted_text"}
        for doc in documents.values()
        if doc["claim_id"] == claim_id
    ]


@router.get("/{claim_id}/documents/{document_id}/text")
def get_document_text(claim_id: str, document_id: str):
    if claim_id not in claims:
        raise HTTPException(404, "Claim not found")

    document = documents.get(document_id)

    if document is None or document["claim_id"] != claim_id:
        raise HTTPException(404, "Document not found")

    return {
        "document_id": document_id,
        "extracted_text": document["extracted_text"],
        "text_length": document["text_length"],
        "page_count": document["page_count"],
    }
    
    
@router.post("/{claim_id}/documents/{document_id}/classify")
def classify_uploaded_document(claim_id: str, document_id: str):
    if claim_id not in claims:
        raise HTTPException(404, "Claim not found")

    document = documents.get(document_id)

    if document is None or document["claim_id"] != claim_id:
        raise HTTPException(404, "Document not found")

    result = classify_document(document["extracted_text"])

    document["classification"] = result

    return {
        "document_id": document_id,
        **result,
    }
    

@router.get("/{claim_id}/checklist")
def get_claim_checklist(claim_id: str):
    if claim_id not in claims:
        raise HTTPException(404, "Claim not found")

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
