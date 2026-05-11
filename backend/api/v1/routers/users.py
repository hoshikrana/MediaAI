import logging
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.session import get_db
from backend.db.models import User, AnalysisSession, APIKey
from backend.core.dependencies import get_current_user, get_pagination
from backend.core.api_keys import generate_api_key
from backend.api.v1.schemas.user import (
    APIKeyCreatedResponse,
    APIKeyResponse,
    CreateAPIKeyRequest,
    SessionListResponse,
    SessionSummary,
    UpdateProfileRequest,
    UserProfileResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/me", response_model=UserProfileResponse)
async def get_profile(current_user: User = Depends(get_current_user)):
    """Get current user profile."""
    return UserProfileResponse.model_validate(current_user)


@router.patch("/me", response_model=UserProfileResponse)
async def update_profile(
    body: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update current user profile."""
    if body.full_name is not None:
        current_user.full_name = body.full_name
    if body.profile_picture_url is not None:
        current_user.profile_picture_url = str(body.profile_picture_url)
    await db.commit()
    await db.refresh(current_user)
    return UserProfileResponse.model_validate(current_user)


@router.get("/sessions", response_model=SessionListResponse)
async def list_sessions(
    current_user: User = Depends(get_current_user),
    pagination: tuple = Depends(get_pagination),
    db: AsyncSession = Depends(get_db)
):
    """List all analysis sessions for the current user, newest first."""
    page, limit = pagination
    offset = (page - 1) * limit

    # Count total
    count_query = select(func.count()).select_from(AnalysisSession).where(
        AnalysisSession.user_id == current_user.id
    )
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Fetch page
    sessions_query = (
        select(AnalysisSession)
        .where(AnalysisSession.user_id == current_user.id)
        .order_by(desc(AnalysisSession.created_at))
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(sessions_query)
    sessions = result.scalars().all()

    session_summaries = []
    for s in sessions:
        result_json = s.result_json or {} if hasattr(s, "result_json") else {}
        risk_level = result_json.get("vision", {}).get("risk_level", "UNKNOWN") if isinstance(result_json, dict) else "UNKNOWN"
        
        session_summaries.append(SessionSummary(
            id=str(s.id),
            patient_id=getattr(s, "patient_id", None),
            status=s.status,
            risk_level=risk_level,
            created_at=s.created_at
        ))

    return SessionListResponse(sessions=session_summaries, total=total)


@router.get("/sessions/{session_id}")
async def get_session_detail(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get one analysis session and its stored result."""
    session = await db.get(AnalysisSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    return jsonable_encoder({
        "id": session.id,
        "patient_id": session.patient_id,
        "status": session.status,
        "image_filename": session.image_filename,
        "symptoms_text": session.symptoms_text,
        "risk_level": session.risk_level,
        "result": session.result_json,
        "created_at": session.created_at,
        "updated_at": session.updated_at,
        "expires_at": session.expires_at,
    })


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete an analysis session owned by the current user."""
    session = await db.get(AnalysisSession, session_id)  # type: ignore
    if not session:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Session not found")
    if session.user_id != current_user.id:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Not authorized")
    
    await db.delete(session)
    await db.commit()
    logger.info("Session deleted", extra={"session_id": session_id, "user_id": str(current_user.id)})
    return {"message": "Session deleted successfully"}


@router.post("/api-keys", response_model=APIKeyCreatedResponse)
async def create_api_key(
    body: CreateAPIKeyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    plain_key, hashed_key = generate_api_key()
    expires_at = None
    if body.expires_in_days:
        expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=body.expires_in_days)

    api_key = APIKey(
        user_id=current_user.id,
        name=body.name,
        key_hash=hashed_key,
        key_prefix=plain_key[:12],
        permissions=body.permissions,
        rate_limit_per_hour=body.rate_limit_per_hour,
        expires_at=expires_at,
    )
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)
    return APIKeyCreatedResponse(
        id=api_key.id,
        name=api_key.name,
        key_prefix=api_key.key_prefix,
        plain_key=plain_key,
        permissions=api_key.permissions,
        created_at=api_key.created_at,
    )


@router.get("/api-keys", response_model=list[APIKeyResponse])
async def list_api_keys(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(APIKey)
        .where(APIKey.user_id == current_user.id)
        .order_by(desc(APIKey.created_at))
    )
    return result.scalars().all()


@router.delete("/api-keys/{key_id}")
async def revoke_api_key(
    key_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    api_key = await db.get(APIKey, key_id)
    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")
    if api_key.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    api_key.is_active = False
    await db.commit()
    return {"message": "API key revoked"}
