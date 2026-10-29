
from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from backend.app.services.document_processing import validate_and_extract
from backend.app.services.document_storage import (
    StorageUploadError,
    delete_local_document,
    save_document as save_local_document,
    upload_document_to_blob,
)
from backend.app.services.document_classifier import classify_document
from backend.app.services.document_checklist import generate_checklist
from backend.app.services.claim_summary import generate_claim_summary
from backend.app.services.claim_document_status import (
    REQUIRED_DOCUMENTS,
    initialize_document_status,
    mark_document_received,
    verify_claim_documents,
)
from backend.app.services.claim_repository import (
    get_claim_by_id,
    update_claim,
    save_document as persist_document,
    get_document_by_id,
    get_documents_for_claim,
    get_all_documents,
    update_document,
)

router = APIRouter(prefix="/api/claims", tags=["Documents"])

# Retained for compatibility with existing tests and memory mode.
documents = {}


def _public_document(document: dict) -> dict:
    return {
        key: value
        for key, value in document.items()
        if key not in {"extracted_text", "storage_path"}
    }


@router.post(
    "/{claim_id}/documents",
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    claim_id: str,
    file: UploadFile = File(...),
    document_type: str | None = Form(default=None),
):
    claim = get_claim_by_id(claim_id)

    if claim is None:
        raise HTTPException(status_code=404, detail="Claim not found")

    if not claim.get("document_status"):
        claim["document_status"] = initialize_document_status()

    if document_type is not None and document_type not in REQUIRED_DOCUMENTS:
        raise HTTPException(status_code=400, detail="Unsupported document type")

    content = await file.read(10 * 1024 * 1024 + 1)
    metadata = None

    try:
        metadata = save_local_document(
            claim_id,
            file.filename or "",
            content,
        )

        processing = validate_and_extract(
            metadata["storage_path"],
            metadata["file_type"],
        )

        storage_info = upload_document_to_blob(
            metadata["storage_path"],
            claim_id,
            metadata["document_id"],
        )

    except ValueError as exc:
        if metadata:
            delete_local_document(metadata["storage_path"])
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    except StorageUploadError as exc:
        if metadata:
            delete_local_document(metadata["storage_path"])
        raise HTTPException(
            status_code=503,
            detail="Document storage is temporarily unavailable",
        ) from exc

    except OSError as exc:
        if metadata:
            delete_local_document(metadata["storage_path"])
        raise HTTPException(
            status_code=500,
            detail="Could not store or read the file",
        ) from exc

    duplicate_of = next(
        (
            doc["document_id"]
            for doc in get_all_documents()
            if doc.get("sha256") == processing["sha256"]
        ),
        None,
    )

    metadata.update({
        "claim_id": claim_id,
        "filename": file.filename or "",
        "content_type": file.content_type,
        "file_size_bytes": len(content),
        "sha256": processing["sha256"],
        "page_count": processing["page_count"],
        "text_length": processing["text_length"],
        "processing_status": "completed",
        "duplicate": duplicate_of is not None,
        "duplicate_of": duplicate_of,
        "extracted_text": processing["extracted_text"],
        "storage_backend": storage_info["storage_backend"],
        "blob_name": storage_info["blob_name"],
    })

    if document_type is not None:
        classification = classify_document(processing["extracted_text"])
        metadata["document_type"] = document_type
        metadata["classification"] = classification

        if (
            classification["predicted_type"] == document_type
            and not classification["needs_review"]
        ):
            metadata["document_status"] = "received"
        else:
            metadata["document_status"] = "needs_review"

    # Save metadata only after the file has passed validation and upload.
    persist_document(metadata)

    if metadata.get("document_status") == "received" and document_type:
        mark_document_received(
            claim,
            document_type,
            metadata["document_id"],
        )

    verification = verify_claim_documents(claim)
    claim["verification_status"] = verification["verification_status"]
    update_claim(claim)

    response = _public_document(metadata)

    if document_type is not None:
        response["verification"] = verification

    return response


@router.get("/{claim_id}/documents")
def list_documents(claim_id: str):
    if get_claim_by_id(claim_id) is None:
        raise HTTPException(status_code=404, detail="Claim not found")

    return [
        _public_document(document)
        for document in get_documents_for_claim(claim_id)
    ]


@router.get("/{claim_id}/documents/{document_id}/text")
def get_document_text(claim_id: str, document_id: str):
    if get_claim_by_id(claim_id) is None:
        raise HTTPException(status_code=404, detail="Claim not found")

    document = get_document_by_id(document_id)

    if document is None or document["claim_id"] != claim_id:
        raise HTTPException(status_code=404, detail="Document not found")

    return {
        "document_id": document_id,
        "extracted_text": document.get("extracted_text", ""),
        "text_length": document["text_length"],
        "page_count": document["page_count"],
    }


@router.post("/{claim_id}/documents/{document_id}/classify")
def classify_uploaded_document(claim_id: str, document_id: str):
    if get_claim_by_id(claim_id) is None:
        raise HTTPException(status_code=404, detail="Claim not found")

    document = get_document_by_id(document_id)

    if document is None or document["claim_id"] != claim_id:
        raise HTTPException(status_code=404, detail="Document not found")

    result = classify_document(document["extracted_text"])
    document["classification"] = result
    update_document(document)

    # Update claim document status only for a supplied expected document type
    # whose classification is confidently accepted.
    expected_type = document.get("document_type")
    claim = get_claim_by_id(claim_id)

    if (
        expected_type in REQUIRED_DOCUMENTS
        and result["predicted_type"] == expected_type
        and not result["needs_review"]
    ):
        mark_document_received(claim, expected_type, document_id)
        document["document_status"] = "received"
        update_document(document)

    verification = verify_claim_documents(claim)
    claim["verification_status"] = verification["verification_status"]
    update_claim(claim)

    return {"document_id": document_id, **result}


@router.get("/{claim_id}/checklist")
def get_claim_checklist(claim_id: str):
    if get_claim_by_id(claim_id) is None:
        raise HTTPException(status_code=404, detail="Claim not found")

    claim_documents = get_documents_for_claim(claim_id)
    result = generate_checklist(claim_documents)

    return {"claim_id": claim_id, **result}


@router.get("/{claim_id}/summary")
def get_claim_summary(claim_id: str):
    claim = get_claim_by_id(claim_id)

    if claim is None:
        raise HTTPException(status_code=404, detail="Claim not found")

    claim_documents = get_documents_for_claim(claim_id)
    checklist_result = generate_checklist(claim_documents)

    return generate_claim_summary(
        claim=claim,
        checklist_result=checklist_result,
        documents=claim_documents,
    )
