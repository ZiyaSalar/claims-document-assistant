import hashlib
import os
from pathlib import Path
from uuid import uuid4

from azure.storage.blob import BlobServiceClient, ContentSettings
from dotenv import load_dotenv

load_dotenv()

UPLOAD_DIR = Path("data/uploads")
MAX_FILE_SIZE = 10 * 1024 * 1024
ALLOWED_EXTENSIONS = {".pdf", ".txt"}


class StorageUploadError(Exception):
    """Raised when a document cannot be stored in the configured backend."""


def save_document(claim_id: str, filename: str, content: bytes) -> dict:
    """Validate basic file properties and save a temporary processing copy."""
    extension = Path(filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise ValueError("Only PDF and TXT files are allowed")

    if not content:
        raise ValueError("Empty files are not allowed")

    if len(content) > MAX_FILE_SIZE:
        raise ValueError("File exceeds the 10 MB limit")

    document_id = str(uuid4())
    file_hash = hashlib.sha256(content).hexdigest()

    destination = UPLOAD_DIR / claim_id
    destination.mkdir(parents=True, exist_ok=True)

    file_path = destination / f"{document_id}{extension}"

    with file_path.open("xb") as file:
        file.write(content)

    return {
        "document_id": document_id,
        "claim_id": claim_id,
        "filename": Path(filename).name,
        "file_type": extension[1:],
        "size_bytes": len(content),
        "sha256": file_hash,
        "storage_path": str(file_path),
    }


def upload_document_to_blob(
    file_path: str,
    claim_id: str,
    document_id: str,
) -> dict:
    """Upload a validated document to Azure or retain local-only behavior."""
    backend = os.getenv("STORAGE_BACKEND", "local").strip().lower()

    if backend == "local":
        return {
            "storage_backend": "local",
            "blob_name": None,
        }

    if backend != "azure":
        raise StorageUploadError("Unsupported storage backend configuration")

    connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    container_name = os.getenv(
        "AZURE_STORAGE_CONTAINER",
        "claim-documents",
    )

    if not connection_string:
        raise StorageUploadError(
            "Azure storage is enabled but its connection string is not configured"
        )

    path = Path(file_path)
    blob_name = f"claims/{claim_id}/{path.name}"

    content_types = {
        ".pdf": "application/pdf",
        ".txt": "text/plain; charset=utf-8",
    }

    try:
        service = BlobServiceClient.from_connection_string(
            connection_string
        )

        blob_client = service.get_blob_client(
            container=container_name,
            blob=blob_name,
        )

        with path.open("rb") as file:
            blob_client.upload_blob(
                file,
                overwrite=False,
                content_settings=ContentSettings(
                    content_type=content_types[path.suffix.lower()]
                ),
            )

        return {
            "storage_backend": "azure",
            "blob_name": blob_name,
        }

    except Exception as exc:
        raise StorageUploadError(
            "Azure document upload failed"
        ) from exc


def delete_local_document(file_path: str) -> None:
    """Remove a temporary local processing copy when appropriate."""
    try:
        Path(file_path).unlink(missing_ok=True)
    except OSError:
        pass