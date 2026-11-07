
import os

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from openai import OpenAI

from backend.app.services.rag_search import (
    build_chunks,
    _claim_filter,
)

HYBRID_INDEX = "claim-document-chunks-v2"
VECTOR_DIMENSIONS = 1536


def get_hybrid_search_client():
    return SearchClient(
        endpoint=os.environ["AZURE_SEARCH_ENDPOINT"].rstrip("/"),
        index_name=HYBRID_INDEX,
        credential=AzureKeyCredential(
            os.environ["AZURE_SEARCH_API_KEY"]
        ),
    )


def get_embedding_client():
    return OpenAI(
        base_url=(
            os.environ["AZURE_OPENAI_ENDPOINT"].rstrip("/")
            + "/"
        ),
        api_key=os.environ["AZURE_OPENAI_API_KEY"],
    )


def sync_hybrid_claim(claim_id: str, documents: list[dict]):
    """
    Rebuild the selected claim's vector index using
    the latest stored OCR text.
    """
    chunks = build_chunks(claim_id, documents)

    # Generate embeddings before modifying the index.
    # This avoids deleting existing chunks if Foundry fails.
    if chunks:
        embedding_client = get_embedding_client()
        deployment = os.environ[
            "AZURE_OPENAI_EMBEDDING_DEPLOYMENT"
        ]

        # Embed several text chunks in one request.
        for start in range(0, len(chunks), 16):
            batch = chunks[start:start + 16]

            response = embedding_client.embeddings.create(
                model=deployment,
                input=[chunk["content"] for chunk in batch],
            )

            if len(response.data) != len(batch):
                raise RuntimeError(
                    "Embedding response count mismatch"
                )

            for item in response.data:
                if not 0 <= item.index < len(batch):
                    raise RuntimeError(
                        "Invalid embedding response index"
                    )

                vector = item.embedding

                if len(vector) != VECTOR_DIMENSIONS:
                    raise RuntimeError(
                        "Unexpected embedding dimensions"
                    )

                batch[item.index]["content_vector"] = vector

        if any("content_vector" not in c for c in chunks):
            raise RuntimeError("Some embeddings are missing")

    client = get_hybrid_search_client()

    # Find old indexed chunks for this claim only.
    existing = [
        {"chunk_id": result["chunk_id"]}
        for result in client.search(
            search_text="*",
            filter=_claim_filter(claim_id),
            select=["chunk_id"],
        )
    ]

    # Delete previous versions, including chunks from
    # documents that are no longer stored in SQL.
    for start in range(0, len(existing), 100):
        results = client.delete_documents(
            documents=existing[start:start + 100]
        )

        if not all(result.succeeded for result in results):
            raise RuntimeError(
                "Hybrid index deletion failed"
            )

    # Upload the current chunks with their embeddings.
    for start in range(0, len(chunks), 100):
        results = client.upload_documents(
            documents=chunks[start:start + 100]
        )

        if not all(result.succeeded for result in results):
            raise RuntimeError(
                "Hybrid index upload failed"
            )

    return {
        "status": "synchronized",
        "index": HYBRID_INDEX,
        "indexed_documents": len(documents),
        "indexed_chunks": len(chunks),
    }
