"""Local-only browser testing API; no authentication yet."""
from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

from backend.app.api.documents import upload_document
from backend.app.services.agent_service import (
    chat, confirm_claim, get_session, cancel_upload,
)

router = APIRouter(prefix='/api/chat', tags=['Chat MVP'])


class MessageRequest(BaseModel):
    session_id: str | None = None
    message: str = Field(min_length=1, max_length=2000)


class Confirmation(BaseModel):
    session_id: str
    approved: bool


class SessionAction(BaseModel):
    session_id: str


@router.post('/message')
async def message(body: MessageRequest):
    try:
        return await chat(body.session_id, body.message)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post('/confirm')
async def confirm(body: Confirmation):
    try:
        return await confirm_claim(body.session_id, body.approved)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post('/upload')
async def upload(session_id: str, file: UploadFile = File(...)):
    try:
        _, state = get_session(session_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    async with state.lock:
        request = state.pending_upload
        if request is None:
            raise HTTPException(status_code=400, detail='No pending upload request')
        if (file.filename or '').rsplit('.', 1)[-1].lower() not in {
            'txt', 'pdf', 'png', 'jpg', 'jpeg',
        }:
            raise HTTPException(status_code=400, detail='Unsupported file extension')
        result = await upload_document(
            claim_id=request['claim_id'],
            file=file,
            document_type=request['document_type'],
        )
        state.pending_upload = None
        state.claim_id = request['claim_id']
        return {'session_id': session_id, 'type': 'upload_complete', 'result': result,
                'message': f"Uploaded {result.get('filename', 'document')}."}


@router.post('/cancel-upload')
async def cancel(body: SessionAction):
    try:
        return cancel_upload(body.session_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
