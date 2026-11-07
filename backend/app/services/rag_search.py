
import hashlib
import os
import logging

from openai import OpenAI
from azure.search.documents.models import VectorizedQuery
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SimpleField,
    SearchableField,
    SearchFieldDataType,
)

load_dotenv(dotenv_path=Path(__file__).resolve().parents[3] / ".env")


def index_name():
    return os.getenv(
        "AZURE_SEARCH_INDEX_NAME", "claim-document-chunks"
    )


@lru_cache(maxsize=1)
def get_search_clients():
    endpoint = os.environ["AZURE_SEARCH_ENDPOINT"].rstrip("/")
    credential = AzureKeyCredential(
        os.environ["AZURE_SEARCH_API_KEY"]
    )

    return (
        SearchIndexClient(endpoint, credential),
        SearchClient(endpoint, index_name(), credential),
    )


def create_search_index():
    index_client, _ = get_search_clients()

    fields = [
        SimpleField(
            name="chunk_id",
            type=SearchFieldDataType.String,
            key=True,
        ),
        SimpleField(
            name="claim_id",
            type=SearchFieldDataType.String,
            filterable=True,
        ),
        SimpleField(
            name="document_id",
            type=SearchFieldDataType.String,
            filterable=True,
        ),
        SimpleField(
            name="filename",
            type=SearchFieldDataType.String,
        ),
        SimpleField(
            name="page_number",
            type=SearchFieldDataType.Int32,
        ),
        SearchableField(
            name="content",
            type=SearchFieldDataType.String,
        ),
    ]

    index = SearchIndex(
        name=index_name(),
        fields=fields,
    )
    index_client.create_or_update_index(index)
    return index_name()


def split_text(text, size=900, overlap=100):
    """Split extracted text into overlapping chunks."""
    text = str(text or "").strip()

    if not text:
        return []

    chunks = []
    start = 0

    while start < len(text):
        end = min(start + size, len(text))
        chunks.append(text[start:end])

        if end == len(text):
            break

        start = end - overlap

    return chunks


def build_chunks(claim_id, documents):
    chunks = []

    for document in documents:
        document_id = str(document["document_id"])
        filename = document.get("filename") or "Unnamed"
        pages = document.get("pages") or []

        # Unknown page provenance stays unknown.
        if not pages:
            pages = [{
                "page_number": None,
                "text": document.get("extracted_text") or "",
            }]

        for page in pages:
            page_number = page.get("page_number")
            text = page.get("text") or ""

            for position, content in enumerate(split_text(text)):
                key = (
                    f"{claim_id}:{document_id}:"
                    f"{page_number}:{position}"
                )
                chunk_id = hashlib.sha256(
                    key.encode("utf-8")
                ).hexdigest()

                chunks.append({
                    "chunk_id": chunk_id,
                    "claim_id": str(claim_id),
                    "document_id": document_id,
                    "filename": filename,
                    "page_number": page_number,
                    "content": content,
                })

    return chunks


def _claim_filter(claim_id):
    escaped = str(claim_id).replace("'", "''")
    return f"claim_id eq '{escaped}'"


def index_claim_documents(claim_id, documents):
    """
    Replace this claim's indexed chunks with current OCR data.
    Use after uploads, updates and deletions.
    """
    _, client = get_search_clients()

    # Fetch existing keys belonging only to this claim.
    existing = list(client.search(
        search_text="*",
        filter=_claim_filter(claim_id),
        select=["chunk_id"],
        top=1000,
    ))

    if len(existing) == 1000:
        raise ValueError(
            "Claim index is too large for this MVP sync"
        )

    # Clear old claim-specific chunks to avoid stale data.
    for start in range(0, len(existing), 500):
        batch = existing[start:start + 500]
        results = client.delete_documents(
            documents=[
                {"chunk_id": item["chunk_id"]}
                for item in batch
            ]
        )
        if not all(item.succeeded for item in results):
            raise RuntimeError("Search chunk deletion failed")

    chunks = build_chunks(claim_id, documents)

    for start in range(0, len(chunks), 500):
        batch = chunks[start:start + 500]
        results = client.upload_documents(documents=batch)

        if not all(item.succeeded for item in results):
            raise RuntimeError("Search chunk upload failed")

    return {
        "claim_id": str(claim_id),
        "indexed_chunks": len(chunks),
        "indexed_documents": len(documents),
    }


def search_claim(claim_id, question, top=5):
    _, client = get_search_clients()

    results = client.search(
        search_text=question,
        filter=_claim_filter(claim_id),
        select=[
            "chunk_id",
            "claim_id",
            "document_id",
            "filename",
            "page_number",
            "content",
        ],
        top=top,
    )

    return [dict(result) for result in results]


logger = logging.getLogger(__name__)

HYBRID_INDEX_NAME = "claim-document-chunks-v2"


def search_claim_hybrid(claim_id, question, top=5):
    """
    Retrieve relevant claim documents using keyword + vector search.
    Uses the same claim_id filter as the original search.
    """

    embedding_client = OpenAI(
        base_url=(
            os.environ["AZURE_OPENAI_ENDPOINT"].rstrip("/") + "/"
        ),
        api_key=os.environ["AZURE_OPENAI_API_KEY"],
    )

    search_client = SearchClient(
        endpoint=os.environ["AZURE_SEARCH_ENDPOINT"].rstrip("/"),
        index_name=HYBRID_INDEX_NAME,
        credential=AzureKeyCredential(
            os.environ["AZURE_SEARCH_API_KEY"]
        ),
    )

    # Convert the question into a 1536-dimensional vector.
    embedding_response = embedding_client.embeddings.create(
        model=os.environ["AZURE_OPENAI_EMBEDDING_DEPLOYMENT"],
        input=question,
    )

    vector = embedding_response.data[0].embedding

    if len(vector) != 1536:
        raise ValueError("Unexpected embedding dimensions")

    vector_query = VectorizedQuery(
        vector=vector,
        k_nearest_neighbors=max(top, 5),
        fields="content_vector",
    )

    results = search_client.search(
        search_text=question,
        vector_queries=[vector_query],
        vector_filter_mode="preFilter",
        filter=_claim_filter(claim_id),
        select=[
            "chunk_id",
            "claim_id",
            "document_id",
            "filename",
            "page_number",
            "content",
        ],
        top=top,
    )

    return [
        dict(result)
        for result in results
        if result["claim_id"] == str(claim_id)
    ]
