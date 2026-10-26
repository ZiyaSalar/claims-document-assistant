import hashlib
from pathlib import Path

import pymupdf


def validate_and_extract(file_path: str, file_type: str) -> dict:
    path = Path(file_path)
    content = path.read_bytes()

    if file_type == "pdf":
        if not content.startswith(b"%PDF-"):
            raise ValueError("File content is not a valid PDF")

        try:
            with pymupdf.open(stream=content, filetype="pdf") as pdf:
                text = "\n".join(page.get_text() for page in pdf)
                page_count = len(pdf)
        except Exception as exc:
            raise ValueError("PDF is unreadable or corrupted") from exc

        return {
            "sha256": hashlib.sha256(content).hexdigest(),
            "page_count": page_count,
            "extracted_text": text,
            "text_length": len(text),
        }

    if file_type == "txt":
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError("TXT file must contain valid UTF-8 text") from exc

        if "\x00" in text:
            raise ValueError("TXT file contains invalid binary content")

        return {
            "sha256": hashlib.sha256(content).hexdigest(),
            "page_count": None,
            "extracted_text": text,
            "text_length": len(text),
        }

    raise ValueError("Unsupported document type")