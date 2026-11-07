
import os

import pytest
from dotenv import load_dotenv
from openai import OpenAI
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery

load_dotenv(".env")

CLAIM_ID = "65df2cd5-7a0d-494f-9c73-a1671e0631aa"
INDEX_NAME = "claim-document-chunks-v2"


@pytest.mark.integration
def test_hybrid_search_retrieves_hospital_bill():
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

    question = "How much money did the hospital charge?"

    embedding = embedding_client.embeddings.create(
        model=os.environ["AZURE_OPENAI_EMBEDDING_DEPLOYMENT"],
        input=question,
    ).data[0].embedding

    assert len(embedding) == 1536

    results = list(search_client.search(
        search_text=question,
        vector_queries=[
            VectorizedQuery(
                vector=embedding,
                k_nearest_neighbors=5,
                fields="content_vector",
            )
        ],
        vector_filter_mode="preFilter",
        filter=f"claim_id eq '{CLAIM_ID}'",
        select=[
            "claim_id",
            "document_id",
            "filename",
            "page_number",
            "content",
        ],
        top=5,
    ))

    assert results, "No search results returned"

    # Every result must belong to the selected claim.
    assert all(
        result["claim_id"] == CLAIM_ID
        for result in results
    )

    # The hospital bill must be among the retrieved documents.
    assert any(
        "hospital_bill" in result["filename"].lower()
        for result in results
    )

    # Check that the amount is present in retrieved evidence.
    assert any(
        "15000" in result["content"]
        for result in results
    )

    print("\nHybrid search results:")
    for result in results:
        print(
            result["filename"],
            "| Page:", result.get("page_number"),
            "| Score:", result.get("@search.score"),
        )
