import hashlib
from pathlib import Path

from backend.app.services.document_intelligence import (
    extract_document_with_azure
)


def validate_and_extract(file_path: str, file_type: str) -> dict:
    path = Path(file_path)
    content = path.read_bytes()

    file_type = file_type.lower().strip()

    # Calculate SHA-256 locally for duplicate detection.
    sha256 = hashlib.sha256(content).hexdigest()

    # PDF processing through Azure Document Intelligence.
    if file_type == "pdf":

        if not content.startswith(b"%PDF-"):
            raise ValueError("File content is not a valid PDF")

        result = extract_document_with_azure(content)

        return {
            "sha256": sha256,
            "page_count": result["page_count"],
            "extracted_text": result["extracted_text"],
            "text_length": result["text_length"],
            "pages": result["pages"],
        }

    # Image processing through Azure Document Intelligence.
    if file_type in ("png", "jpg", "jpeg"):

        if file_type == "png" and not content.startswith(
            b"\x89PNG\r\n\x1a\n"
        ):
            raise ValueError("File content is not a valid PNG image")

        if file_type in ("jpg", "jpeg") and not content.startswith(
            b"\xff\xd8\xff"
        ):
            raise ValueError("File content is not a valid JPEG image")

        result = extract_document_with_azure(content)

        return {
            "sha256": sha256,
            "page_count": result["page_count"],
            "extracted_text": result["extracted_text"],
            "text_length": result["text_length"],
            "pages": result["pages"],
        }

    # TXT processing remains local.
    if file_type == "txt":

        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError(
                "TXT file must contain valid UTF-8 text"
            ) from exc

        if "\x00" in text:
            raise ValueError(
                "TXT file contains invalid binary content"
            )

        return {
            "sha256": sha256,
            "page_count": None,
            "extracted_text": text,
            "text_length": len(text),
            "pages": None,
        }

    raise ValueError("Unsupported document type")
