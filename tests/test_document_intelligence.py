from pathlib import Path

from backend.app.services.document_intelligence import (
    extract_document_with_azure
)


def test_azure_document_extraction():
    file_path = Path("data/sample_data/sample.pdf")

    assert file_path.exists(), "sample.pdf not found"

    file_content = file_path.read_bytes()

    result = extract_document_with_azure(file_content)

    # Verify response structure
    assert isinstance(result, dict)

    assert "extracted_text" in result
    assert "page_count" in result
    assert "pages" in result
    assert "text_length" in result

    # Verify extracted content
    assert result["page_count"] > 0
    assert result["text_length"] > 0
    assert len(result["pages"]) == result["page_count"]

    print("\nPage count:", result["page_count"])
    print("Text length:", result["text_length"])
    print("\nExtracted text:")
    print(result["extracted_text"])