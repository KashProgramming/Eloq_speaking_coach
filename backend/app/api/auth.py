from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.core.rate_limit import limiter
from app.core.security import (
    TokenType,
    create_access_token,
    create_refresh_token,
    hash_password,
    safe_decode_token,
    validate_email,
    validate_password,
    verify_password,
)
from app.models import User
from app.schemas.auth import AccessTokenResponse, LoginRequest, RefreshTokenRequest, SignupRequest, SignupResponse, TokenResponse, DeleteAccountResponse, ChangePasswordRequest, ChangePasswordResponse
from app.services.user_service import delete_user_account

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=SignupResponse)
@limiter.limit("5/hour")
def signup(payload: SignupRequest, request: Request, db: Session = Depends(get_db)):
    if not validate_email(payload.email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid email format")

    if not validate_password(payload.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters with 1 uppercase and 1 number",
        )

    existing_user = db.query(User).filter(User.email == payload.email).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    user = User(email=payload.email, password=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)

    return SignupResponse(message="User created", user_id=user.id)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    from datetime import datetime, timedelta
    
    user = db.query(User).filter(User.email == payload.email).first()
    
    # Check if user exists
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    # Check if account is locked
    if user.locked_until:
        if datetime.now(timezone.utc).replace(tzinfo=None) < user.locked_until:
            remaining_minutes = int((user.locked_until - datetime.now(timezone.utc).replace(tzinfo=None)).total_seconds() / 60)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Account locked due to too many failed login attempts. Try again in {remaining_minutes} minutes."
            )
        else:
            # Lock period expired, reset the counter
            user.locked_until = None
            user.failed_login_attempts = 0
            db.commit()
    
    # Verify password
    if not verify_password(payload.password, user.password):
        # Increment failed attempts
        user.failed_login_attempts += 1
        
        if user.failed_login_attempts >= 3:
            # Lock account for 1 hour
            user.locked_until = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=1)
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account locked due to too many failed login attempts. Try again in 60 minutes."
            )
        
        db.commit()
        remaining_attempts = 3 - user.failed_login_attempts
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid credentials. {remaining_attempts} attempt(s) remaining before account lockout."
        )
    
    # Successful login - reset failed attempts
    user.failed_login_attempts = 0
    user.locked_until = None
    db.commit()

    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


@router.post("/refresh", response_model=AccessTokenResponse)
def refresh_token(payload: RefreshTokenRequest, db: Session = Depends(get_db)):
    token_data = safe_decode_token(payload.refresh_token)
    if not token_data or token_data.get("type") != TokenType.REFRESH:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    user = db.query(User).filter(User.id == token_data.get("sub")).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return AccessTokenResponse(access_token=create_access_token(user.id))


@router.delete("/account", response_model=DeleteAccountResponse)
@limiter.limit("3/hour")
def delete_account(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete the current user's account and all associated data.
    This includes:
    - All practice sessions and audio recordings
    - All roleplay sessions and audio recordings
    - User profile and progress data
    - Cloudinary audio files
    """
    result = delete_user_account(db, current_user.id)
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.get("error", "Account deletion failed")
        )
    
    return DeleteAccountResponse(
        message="Account successfully deleted",
        deleted_audio_count=result["audio_counts"]["total"],
        cloudinary_success=result["audio_deletion"]["success"],
        cloudinary_failed=result["audio_deletion"]["failed"]
    )


@router.put("/password", response_model=ChangePasswordResponse)
@limiter.limit("5/hour")
def change_password(
    payload: ChangePasswordRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Change the current user's password.
    Requires current password for verification.
    """
    # Verify current password
    if not verify_password(payload.current_password, current_user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Validate new password
    if not validate_password(payload.new_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters with 1 uppercase and 1 number"
        )
    
    # Ensure new password is different from current
    if verify_password(payload.new_password, current_user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from current password"
        )
    
    # Update password
    current_user.password = hash_password(payload.new_password)
    db.commit()
    
    return ChangePasswordResponse(message="Password successfully changed")
