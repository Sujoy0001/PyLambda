import hashlib
import secrets
import smtplib
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
import httpx

from app.Auth.schemas import (
    Credentials,
    ForgotPasswordRequest,
    LoginCredentials,
    PasswordChangeRequest,
    PhoneVerificationRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserResponse,
)
from app.Auth.security import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.Auth.email import (
    send_password_reset_email,
    validate_smtp_configuration,
)
from app.Auth.models import PasswordResetToken, PhoneDetail, User
from app.middlewares.config import settings
from app.middlewares.logging import logger
from app.db.session import get_db

router = APIRouter()
bearer_scheme = HTTPBearer(auto_error=False)


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def signup(credentials: Credentials, db: Session = Depends(get_db)) -> UserResponse:
    existing_user = db.scalar(
        select(User).where(User.username == credentials.username)
    )
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username is already registered",
        )
    
    current_time = datetime.now(timezone.utc)

    user = User(
        id=uuid.uuid4(),
        username=credentials.username,
        useremail=credentials.useremail,
        hashed_password=hash_password(credentials.password),
        isAdmin=False,
        active=True,
        verified=False,
        created_at=current_time,
    )
    
    db.add(user)
    
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username is already registered",
        ) from None

    return UserResponse(
        username=user.username,
        useremail=user.useremail
    )


@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
def login(
    LoginCredentials: LoginCredentials,
    db: Session = Depends(get_db),
) -> TokenResponse:
    user = db.scalar(select(User).where(User.useremail == LoginCredentials.useremail))
    if user is None or not verify_password(LoginCredentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return TokenResponse(
        access_token=create_access_token(user.username),
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer token required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    username = decode_access_token(credentials.credentials)
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.scalar(select(User).where(User.username == username))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


@router.get("/me", response_model=UserResponse)
def read_current_user(
    user: User = Depends(get_current_user),
) -> UserResponse:
    return UserResponse(
        username=user.username,
        useremail=user.useremail
    )


@router.post("/me/change-password", status_code=status.HTTP_200_OK)
def change_password(
    payload: PasswordChangeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    if not verify_password(
        payload.current_password, current_user.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    if payload.current_password == payload.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from the current password",
        )

    now = datetime.now(timezone.utc)
    current_user.hashed_password = hash_password(payload.new_password)
    db.execute(
        update(PasswordResetToken)
        .where(
            PasswordResetToken.user_id == current_user.id,
            PasswordResetToken.used_at.is_(None),
        )
        .values(used_at=now)
    )
    db.commit()
    return {"message": "Password changed successfully"}


@router.post(
    "/forgot-password",
    status_code=status.HTTP_202_ACCEPTED,
)
def forgot_password(
    payload: ForgotPasswordRequest,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    try:
        validate_smtp_configuration()
    except RuntimeError:
        logger.exception("Password reset email is not configured")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Password reset service is unavailable",
        ) from None

    user = db.scalar(
        select(User).where(User.useremail == payload.useremail)
    )
    if user is None:
        return {
            "message": (
                "If the account exists, a password reset email has been sent"
            )
        }

    now = datetime.now(timezone.utc)
    db.execute(
        update(PasswordResetToken)
        .where(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.used_at.is_(None),
        )
        .values(used_at=now)
    )

    token = secrets.token_urlsafe(32)
    reset_token = PasswordResetToken(
        id=uuid.uuid4(),
        user_id=user.id,
        token_hash=hashlib.sha256(token.encode("utf-8")).hexdigest(),
        expires_at=now
        + timedelta(minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES),
    )
    db.add(reset_token)
    db.commit()

    try:
        send_password_reset_email(user.useremail, token)
    except (OSError, smtplib.SMTPException):
        logger.exception("Failed to send password reset email")
        db.delete(reset_token)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Password reset email could not be sent",
        ) from None

    return {
        "message": (
            "If the account exists, a password reset email has been sent"
        )
    }


@router.post("/reset-password", status_code=status.HTTP_200_OK)
def reset_password(
    payload: ResetPasswordRequest,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    token_hash = hashlib.sha256(payload.token.encode("utf-8")).hexdigest()
    reset_token = db.scalar(
        select(PasswordResetToken).where(
            PasswordResetToken.token_hash == token_hash
        )
    )
    now = datetime.now(timezone.utc)

    if reset_token is None or reset_token.used_at is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password reset token is invalid or expired",
        )

    expires_at = reset_token.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at <= now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password reset token is invalid or expired",
        )

    user = db.get(User, reset_token.user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password reset token is invalid or expired",
        )

    token_update = db.execute(
        update(PasswordResetToken)
        .where(
            PasswordResetToken.id == reset_token.id,
            PasswordResetToken.used_at.is_(None),
        )
        .values(used_at=now)
        .returning(PasswordResetToken.id)
    )
    if token_update.scalar_one_or_none() is None:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password reset token is invalid or expired",
        )

    user.hashed_password = hash_password(payload.new_password)
    db.execute(
        update(PasswordResetToken)
        .where(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.id != reset_token.id,
            PasswordResetToken.used_at.is_(None),
        )
        .values(used_at=now)
    )
    db.commit()
    return {"message": "Password reset successfully"}


@router.post("/me/verify-phone", status_code=status.HTTP_200_OK)
async def verify_authenticated_user_phone(
    payload: PhoneVerificationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Takes a phone number, queries APILayer live, validates the phone status, 
    and saves the dynamic location/carrier data to the database.
    """
    
    # 1. Define clean query parameters for the outgoing HTTP client call
    # Notice: 'callback' is removed, and country_code is omitted so the API infers it from the leading '+' prefix
    query_params = {
        "access_key": settings.ACCESS_KEY,
        "number": payload.phone_number,
        "format": 1
    }

    # 2. Make an asynchronous live HTTP request to APILayer
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(settings.NUMVERIFY_BASE_URL, params=query_params, timeout=10.0)
            response.raise_for_status()
            api_data = response.json()
        except httpx.HTTPError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
                detail="Phone verification service is temporarily unavailable"
            )

    # 3. Structural API Validation Check
    if not api_data.get("valid"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="The provided phone number is invalid or structurally incorrect"
        )
        
    if api_data.get("line_type") != "mobile":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Only mobile cell lines are allowed for operational verification"
        )

    # 4. Check for conflicts across other accounts
    phone_exists = db.query(PhoneDetail).filter(
        PhoneDetail.phone_number == api_data["international_format"]
    ).first()
    
    if phone_exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="This phone number is already linked to another user account"
        )

    # 5. Check if this specific user already has an active phone profile relation mapping
    user_phone_profile = db.query(PhoneDetail).filter(
        PhoneDetail.user_id == current_user.id
    ).first()

    if user_phone_profile:
        # Update target parameters for shifting/re-verifying user profile assets
        user_phone_profile.phone_number = api_data["international_format"]
        user_phone_profile.local_format = api_data["local_format"]
        user_phone_profile.country_code = api_data["country_code"]
        user_phone_profile.country_name = api_data["country_name"]
        user_phone_profile.location = api_data["location"]
        user_phone_profile.carrier = api_data["carrier"]
        user_phone_profile.line_type = api_data["line_type"]
    else:
        # Generate new phone profile instance bound to the authenticated user ID
        new_phone_detail = PhoneDetail(
            user_id=current_user.id,
            phone_number=api_data["international_format"],
            local_format=api_data["local_format"],
            country_code=api_data["country_code"],
            country_name=api_data["country_name"],
            location=api_data["location"],
            carrier=api_data["carrier"],
            line_type=api_data["line_type"]
        )
        db.add(new_phone_detail)

    # 6. Mark the core model user column flag as verified
    current_user.verified = True
    db.commit()

    return {
        "status": "success",
        "message": "Phone registration verified and recorded natively!",
    }