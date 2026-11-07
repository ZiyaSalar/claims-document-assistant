
import os
from pathlib import Path

from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SearchField,
    SimpleField,
    SearchableField,
    SearchFieldDataType,
    VectorSearch,
    VectorSearchProfile,
    HnswAlgorithmConfiguration,
)

load_dotenv(Path.cwd() / ".env")

INDEX_NAME = "claim-document-chunks-v2"

client = SearchIndexClient(
    endpoint=os.environ["AZURE_SEARCH_ENDPOINT"].rstrip("/"),
    credential=AzureKeyCredential(
        os.environ["AZURE_SEARCH_API_KEY"]
    ),
)

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
    SearchField(
        name="content_vector",
        type=SearchFieldDataType.Collection(
            SearchFieldDataType.Single
        ),
        searchable=True,
        vector_search_dimensions=1536,
        vector_search_profile_name="claims-vector-profile",
        hidden=True,
    ),
]

vector_search = VectorSearch(
    algorithms=[
        HnswAlgorithmConfiguration(
            name="claims-hnsw",
        ),
    ],
    profiles=[
        VectorSearchProfile(
            name="claims-vector-profile",
            algorithm_configuration_name="claims-hnsw",
        ),
    ],
)

index = SearchIndex(
    name=INDEX_NAME,
    fields=fields,
    vector_search=vector_search,
)

if INDEX_NAME in list(client.list_index_names()):
    print("Hybrid index already exists:", INDEX_NAME)
else:
    client.create_index(index)
    print("Hybrid index created:", INDEX_NAME)

print("Existing indexes:", list(client.list_index_names()))
