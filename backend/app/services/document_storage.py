import hashlib
import os
from pathlib import Path
from uuid import uuid4

UPLOAD_DIR = Path("data/uploads")
MAX_FILE_SIZE = 10 * 1024 * 1024

ALLOWED_EXTENSIONS = {".pdf", ".txt"}


def save_document(claim_id: str, filename: str, content: bytes):
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