
from backend.app.services.rag_search import create_search_index

if __name__ == "__main__":
    name = create_search_index()
    print("Azure AI Search index ready:", name)
