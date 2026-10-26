from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
import uuid
from datetime import datetime, timezone

from app.Auth.schemas import Credentials, TokenResponse, UserResponse
from app.Auth.security import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.Auth.models import User
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


@router.post("/login", response_model=TokenResponse)
def login(
    credentials: Credentials,
    db: Session = Depends(get_db),
) -> TokenResponse:
    user = db.scalar(select(User).where(User.username == credentials.username))
    if user is None or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
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
