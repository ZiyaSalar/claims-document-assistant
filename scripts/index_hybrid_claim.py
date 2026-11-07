
import argparse
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient

from backend.app.services.claim_repository import (
    get_claim_by_id,
    get_documents_for_claim,
)
from backend.app.services.rag_search import build_chunks

load_dotenv(Path.cwd() / ".env")

INDEX_NAME = "claim-document-chunks-v2"


def main(claim_id):
    if get_claim_by_id(claim_id) is None:
        raise ValueError("Claim not found")

    documents = get_documents_for_claim(claim_id)
    chunks = build_chunks(claim_id, documents)

    if not chunks:
        print("No OCR text available to index.")
        return

    embedding_client = OpenAI(
        base_url=os.environ["AZURE_OPENAI_ENDPOINT"].rstrip("/") + "/",
        api_key=os.environ["AZURE_OPENAI_API_KEY"],
    )

    search_client = SearchClient(
        endpoint=os.environ["AZURE_SEARCH_ENDPOINT"].rstrip("/"),
        index_name=INDEX_NAME,
        credential=AzureKeyCredential(
            os.environ["AZURE_SEARCH_API_KEY"]
        ),
    )

    print(f"Documents found: {len(documents)}")
    print(f"Text chunks generated: {len(chunks)}")

    for i, chunk in enumerate(chunks, start=1):
        response = embedding_client.embeddings.create(
            model=os.environ["AZURE_OPENAI_EMBEDDING_DEPLOYMENT"],
            input=chunk["content"],
        )

        vector = response.data[0].embedding

        if len(vector) != 1536:
            raise ValueError("Unexpected embedding dimensions")

        chunk["content_vector"] = vector
        print(f"Embedding generated: {i}/{len(chunks)}")

    # Upload in small batches.
    for start in range(0, len(chunks), 50):
        batch = chunks[start:start + 50]
        results = search_client.upload_documents(
            documents=batch
        )

        failures = [
            result.key
            for result in results
            if not result.succeeded
        ]

        if failures:
            raise RuntimeError(
                f"Failed to index chunks: {failures}"
            )

    print("Hybrid indexing successful!")
    print("Indexed chunks:", len(chunks))
    print("Index:", INDEX_NAME)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--claim-id", required=True)
    args = parser.parse_args()

    main(args.claim_id)
