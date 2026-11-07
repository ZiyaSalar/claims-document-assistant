from fastapi import FastAPI

from backend.app.api.claims import router as claims_router
from backend.app.api.documents import router as documents_router
from backend.app.api.rag import router as rag_router
from backend.app.api.chat import router as chat_router

from backend.app.api.review_ui import router as review_ui_router



app = FastAPI(title="Claims Document Assistant")

app.include_router(claims_router)
app.include_router(documents_router)
app.include_router(rag_router)
app.include_router(chat_router)
app.include_router(review_ui_router)


@app.get("/health")
def health_check():
    return {"status": "healthy"}