from fastapi import FastAPI

from backend.app.api.claims import router as claims_router
from backend.app.api.documents import router as documents_router
from backend.app.api.rag import router as rag_router
from backend.app.api.chat import router as chat_router

from backend.app.api.review_ui import router as review_ui_router

from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles



app = FastAPI(title="Claims Document Assistant")

app.include_router(claims_router)
app.include_router(documents_router)
app.include_router(rag_router)
app.include_router(chat_router)
app.include_router(review_ui_router)


@app.get("/health")
def health_check():
    return {"status": "healthy"}


# -----------------------------------------
# Serve React production build with FastAPI
# -----------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

FRONTEND_DIST = (
    PROJECT_ROOT / "frontend" / "react" / "dist"
)

if FRONTEND_DIST.is_dir():

    app.mount(
        "/assets",
        StaticFiles(
            directory=FRONTEND_DIST / "assets"
        ),
        name="react-assets",
    )

    @app.get("/{full_path:path}", include_in_schema=False)
    def serve_react(full_path: str):

        # Do not return HTML for invalid API paths.
        if (
            full_path == "api"
            or full_path.startswith("api/")
        ):
            raise HTTPException(
                status_code=404,
                detail="API endpoint not found"
            )

        # Let missing file paths return a 404.
        if "." in Path(full_path).name:
            requested_file = (
                FRONTEND_DIST / full_path
            ).resolve()

            if (
                requested_file.is_file()
                and requested_file.is_relative_to(
                    FRONTEND_DIST.resolve()
                )
            ):
                return FileResponse(requested_file)

            raise HTTPException(
                status_code=404,
                detail="File not found"
            )

        # React client-side routes:
        # /, /claims, /agent, /claims/{id}
        return FileResponse(
            FRONTEND_DIST / "index.html"
        )
