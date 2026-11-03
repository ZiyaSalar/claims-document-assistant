
import os
from io import BytesIO

from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient


load_dotenv()


def extract_document_with_azure(file_content: bytes) -> dict:
    """
    Extract text and page information from a PDF or image
    using Azure Document Intelligence's prebuilt-read model.
    """

    endpoint = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
    key = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_KEY")

    if not endpoint or not key:
        raise RuntimeError(
            "Azure Document Intelligence endpoint or key is missing"
        )

    client = DocumentIntelligenceClient(
        endpoint=endpoint,
        credential=AzureKeyCredential(key)
    )

    try:
        poller = client.begin_analyze_document(
            "prebuilt-read",
            body=BytesIO(file_content)
        )

        result = poller.result()

        extracted_text = result.content or ""

        pages = []

        for page in result.pages or []:
            page_text = "\n".join(
                line.content for line in (page.lines or [])
            )

            pages.append({
                "page_number": page.page_number,
                "text": page_text
            })

        return {
            "extracted_text": extracted_text,
            "page_count": len(pages),
            "pages": pages,
            "text_length": len(extracted_text)
        }

    finally:
        client.close()
