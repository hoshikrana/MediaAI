import logging
from fastapi import APIRouter, Request, Depends, BackgroundTasks
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from authlib.integrations.starlette_client import OAuth, OAuthError

from backend.db.session import get_db
from backend.db.models import User
from backend.db.utils import exists, get_or_404
from backend.core.middleware import limiter
from backend.core.security import (
    validate_password_strength, hash_password, verify_password,
    create_access_token, create_refresh_token, set_refresh_cookie, clear_auth_cookies,
    verify_token, get_refresh_token_from_cookie, blacklist_token, generate_verification_token
)
from backend.core.brute_force import brute_force_protector
from backend.core.dependencies import get_client_ip, get_current_user
from backend.core.exceptions import (
    ValidationError, EmailAlreadyExistsError, AuthenticationError, AccountInactiveError
)
from backend.api.v1.schemas.auth import (
    RegisterRequest, TokenResponse, UserResponse, AuthResponse, MessageResponse
)
from backend.core.config import settings

logger = logging.getLogger(__name__)

oauth = OAuth()
oauth.register(
    name="google",
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    client_kwargs={"scope": "openid email profile"},
)

router = APIRouter()

# --- Google OAuth Segment ---
@router.get("/google/login")
async def google_login(request: Request):
    """Redirects to Google consent screen."""
    redirect_uri = settings.GOOGLE_REDIRECT_URI
    return await oauth.google.authorize_redirect(request, redirect_uri)

@router.get("/google/callback")
async def google_callback(request: Request, db: AsyncSession = Depends(get_db)):
    """Handles Google OAuth callback."""
    # Step 1: Exchange code for token
    try:
        google_token = await oauth.google.authorize_access_token(request)
    except OAuthError as e:
        raise AuthenticationError(f"Google OAuth failed: {e.description}")
    
    # Step 2: Get user info
    user_info = google_token.get("userinfo")
    if not user_info or not user_info.get("email_verified"):
        raise AuthenticationError("Google email not verified")
    
    google_id = user_info.get("sub")
    email = user_info.get("email")
    full_name = user_info.get("name", "Google User")
    picture = user_info.get("picture")
    
    # Step 3: Find or create user
    user = await User.get_by_google_id(db, google_id)
    if not user:
        user = await User.get_by_email(db, email)
        if user:
            # Link existing account to Google
            user.google_id = google_id
            user.profile_picture_url = picture
            user.is_active = True
        else:
            # Create new user
            user = User(
                email=email, full_name=full_name,
                google_id=google_id, profile_picture_url=picture,
                is_active=True, is_verified=True
            )
            db.add(user)
    
    await db.commit()
    await db.refresh(user)
    
    # Step 4: Issue tokens
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)
    
    # Step 5: Redirect to frontend
    response = RedirectResponse(
        url=f"{settings.FRONTEND_URL}/auth/callback?token={access_token}"
    )
    set_refresh_cookie(response, refresh_token)
    return response

# --- Email/Password Segment ---
async def send_verification_email(email: str, token: str):
    # TODO: Implement actual email sending logic
    logger.info(f"MOCK EMAIL to {email}: Your verification token is {token}")

async def update_login_stats(user_id: str, ip: str):
    # TODO: Update last_login_at in DB
    pass

@router.post("/register", response_model=MessageResponse)
@limiter.limit("3/hour")
async def register(
    request: Request,
    body: RegisterRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    failures = validate_password_strength(body.password)
    if failures:
        raise ValidationError(f"Password too weak: {'; '.join(failures)}")
        
    if await exists(db, User, email=body.email):
        raise EmailAlreadyExistsError()
        
    user = User(
        email=body.email,
        full_name=body.full_name,
        hashed_password=hash_password(body.password),
        is_active=False # Requires email verification
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    plain_token, token_hash = generate_verification_token()
    background_tasks.add_task(send_verification_email, user.email, plain_token)
    
    logger.info("User registered", extra={"user_id": str(user.id), "email": user.email})
    return MessageResponse(message="Account created. Check your email to verify.")

@router.post("/login", response_model=AuthResponse)
@limiter.limit("5/minute")
async def login(
    request: Request,
    background_tasks: BackgroundTasks,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
    client_ip: str = Depends(get_client_ip)
):
    await brute_force_protector.check_and_record_failure(client_ip)
    
    user = await User.get_by_email(db, form_data.username)
    if not user or not user.hashed_password or not verify_password(form_data.password, user.hashed_password):
        await brute_force_protector.check_and_record_failure(client_ip)
        raise AuthenticationError("Invalid email or password")
        
    if not user.is_active:
        raise AccountInactiveError("Please verify your email before logging in")
        
    brute_force_protector.record_success(client_ip)
    
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)
    
    response = JSONResponse(content=AuthResponse(
        token=TokenResponse(access_token=access_token, token_type="bearer", 
                           expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60),
        user=UserResponse.model_validate(user)
    ).model_dump())
    
    set_refresh_cookie(response, refresh_token)
    background_tasks.add_task(update_login_stats, user.id, client_ip)
    
    logger.info("User logged in", extra={"user_id": str(user.id)})
    return response

@router.post("/logout")
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.replace("Bearer ", "")
    if token:
        try:
            payload = verify_token(token, "access")
            await blacklist_token(payload.jti, payload.exp)
        except Exception:
            pass # Ignore errors on logout
            
    response = JSONResponse(content={"message": "Logged out successfully"})
    clear_auth_cookies(response)
    logger.info("User logged out", extra={"user_id": str(current_user.id)})
    return response

@router.post("/refresh", response_model=TokenResponse)
async def refresh(request: Request, db: AsyncSession = Depends(get_db)):
    raw_refresh = get_refresh_token_from_cookie(request)
    payload = verify_token(raw_refresh, "refresh")
    
    user = await get_or_404(db, User, payload.sub)
    if not user.is_active:
        raise AccountInactiveError()
        
    new_access_token = create_access_token(user.id)
    new_refresh_token = create_refresh_token(user.id)
    
    await blacklist_token(payload.jti, payload.exp)
    
    response = JSONResponse(content=TokenResponse(
        access_token=new_access_token, token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    ).model_dump())
    set_refresh_cookie(response, new_refresh_token)
    return response

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)
