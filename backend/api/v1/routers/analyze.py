import asyncio
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, Form, File, UploadFile, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from pathlib import Path

from backend.db.session import get_db
from backend.db.models import AnalysisSession, AnalysisTask
from backend.core.dependencies import get_current_user, get_pagination, get_model_registry
from backend.core.config import settings
from backend.core.exceptions import InvalidFileTypeError, FileTooLargeError, ModelNotLoadedError
from backend.utils.validators import ImageValidator, sanitize_symptoms_text, validate_patient_id, safe_temp_path
from backend.utils.file_storage import FileStorage
from backend.api.v1.schemas.analysis import TaskSubmitResponse, TaskStatusResponse, AnalysisResult
from backend.orchestration.queue import task_queue
from backend.ml.nlp.whisper import WhisperTranscriber

router = APIRouter()

@router.post("", response_model=TaskSubmitResponse)
@router.post("/", response_model=TaskSubmitResponse, include_in_schema=False)
async def analyze_submission(
    request: Request,
    image: UploadFile = File(...),
    symptoms_text: str = Form(""),
    patient_id: str = Form(""),
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not image:
        raise HTTPException(status_code=422, detail="image field is required")
        
    img_meta = await ImageValidator.validate(image)
    clean_symptoms = sanitize_symptoms_text(symptoms_text)
    clean_patient_id = validate_patient_id(patient_id)
    
    temp_path = safe_temp_path(img_meta.filename)
    with open(temp_path, "wb") as f:
        f.write(img_meta.content)
    stored_file = FileStorage.save_upload(img_meta.content, img_meta.filename, current_user.id)
        
    session = AnalysisSession(
        user_id=current_user.id,
        patient_id=clean_patient_id,
        status="PENDING",
        image_filename=img_meta.filename,
        image_hash=stored_file.sha256,
        symptoms_text=clean_symptoms,
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.ANALYSIS_RETENTION_DAYS),
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    
    task_id = await task_queue.submit(
        session_id=session.id, user_id=current_user.id,
        image_path=str(temp_path), symptoms_text=clean_symptoms, priority=1
    )
    
    status_data = await task_queue.get_status(task_id)
    return TaskSubmitResponse(
        task_id=task_id, session_id=session.id, 
        estimated_wait_seconds=status_data.get("estimated_wait_seconds", 45), 
        position_in_queue=status_data.get("position_in_queue", 1)
    )

@router.get("/status/{task_id}", response_model=TaskStatusResponse)
async def get_status(task_id: str, current_user = Depends(get_current_user)):
    return await task_queue.get_status(task_id)

@router.get("/result/{result_id}")
async def get_result(result_id: str, db: AsyncSession = Depends(get_db), current_user = Depends(get_current_user)):
    task = await db.get(AnalysisTask, result_id)
    if task:
        if task.status != "COMPLETED":
            return {"status": task.status, "message": "Analysis still in progress"}
        session = await db.get(AnalysisSession, task.session_id)
    else:
        session = await db.get(AnalysisSession, result_id)

    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    if session.status != "READY":
        return {"status": session.status, "message": "Analysis still in progress"}

    return session.result_json

@router.delete("/{task_id}")
async def cancel_task(task_id: str, current_user = Depends(get_current_user)):
    success = await task_queue.cancel(task_id, current_user.id)
    return {"cancelled": success, "message": "Task cancelled" if success else "Cannot cancel task"}

@router.post("/transcribe")
async def transcribe_audio(
    audio: UploadFile = File(...),
    registry = Depends(get_model_registry),
    current_user = Depends(get_current_user)
):
    if audio.content_type not in ["audio/wav", "audio/mpeg", "audio/webm", "audio/ogg"]:
        raise InvalidFileTypeError("Audio must be WAV, MP3, WebM, or OGG")
        
    content = await audio.read()
    if len(content) > 25 * 1024 * 1024:
        raise FileTooLargeError("Audio file too large (max 25MB)")
        
    temp_path = safe_temp_path(audio.filename or "audio.webm")
    temp_path.write_bytes(content)
    
    try:
        whisper_state = await registry.get("whisper_tiny")
        if not whisper_state.is_available:
            raise ModelNotLoadedError("Voice transcription unavailable")
            
        result = await asyncio.to_thread(WhisperTranscriber.transcribe, temp_path, whisper_state.model)
        return result
    finally:
        temp_path.unlink(missing_ok=True)
