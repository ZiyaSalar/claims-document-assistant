from fastapi import FastAPI

from backend.app.api.claims import router as claims_router
from backend.app.api.documents import router as documents_router

app = FastAPI(title="Claims Document Assistant")

app.include_router(claims_router)
app.include_router(documents_router)


@app.get("/health")
def health_check():
    return {"status": "healthy"}