
import logging
import os

from backend.app.database import get_database_backend
from backend.app.services.claim_repository import (
    get_documents_for_claim,
)
from backend.app.services.rag_search import (
    index_claim_documents,
)
from backend.app.services.rag_hybrid_sync import (
    sync_hybrid_claim,
)

logger = logging.getLogger(__name__)


def sync_claim_search(claim_id: str) -> dict:
    if (
        os.getenv("RAG_AUTO_INDEX_ENABLED", "false").lower()
        != "true"
    ):
        return {"status": "disabled"}

    if get_database_backend() != "azure":
        return {"status": "skipped"}

    try:
        documents = get_documents_for_claim(claim_id)
    except Exception:
        logger.exception("Cannot load claim documents for indexing")
        return {
            "status": "failed",
            "message": "Could not load documents for indexing",
        }

    results = {}
    all_succeeded = True

    # Preserve the original keyword index.
    try:
        results["keyword"] = {
            "status": "synchronized",
            **index_claim_documents(claim_id, documents),
        }
    except Exception:
        logger.exception("Keyword index sync failed")
        results["keyword"] = {"status": "failed"}
        all_succeeded = False

    # Automatically maintain the new vector index.
    if (
        os.getenv(
            "RAG_HYBRID_INDEX_ENABLED", "false"
        ).lower() == "true"
    ):
        try:
            results["hybrid"] = sync_hybrid_claim(
                claim_id, documents
            )
        except Exception:
            logger.exception("Hybrid index sync failed")
            results["hybrid"] = {"status": "failed"}
            all_succeeded = False

    return {
        "status": (
            "synchronized" if all_succeeded else "failed"
        ),
        "claim_id": claim_id,
        "indexes": results,
    }
