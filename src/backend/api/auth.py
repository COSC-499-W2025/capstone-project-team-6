"""Authentication API endpoints."""

import uuid
from datetime import datetime, timedelta
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from backend.database import authenticate_user, create_user

router = APIRouter(prefix="/api/auth", tags=["Authentication"])
security = HTTPBearer()

# In-memory token storage (shared across modules)
active_tokens: Dict[str, Dict[str, Any]] = {}


class UserCredentials(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    username: str


class MessageResponse(BaseModel):
    message: str
    details: Dict[str, Any] | None = None


def create_access_token(username: str) -> str:
    """Create a new access token for a user."""
    token = str(uuid.uuid4())
    active_tokens[token] = {
        "username": username,
        "created_at": datetime.now(),
        "expires_at": datetime.now() + timedelta(hours=24),
    }
    return token


def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)) -> str:
    """Verify token and return username."""
    token = credentials.credentials

    if token not in active_tokens:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    token_data = active_tokens[token]

    if datetime.now() > token_data["expires_at"]:
        del active_tokens[token]
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
        )

    return token_data["username"]


@router.post("/signup", response_model=TokenResponse, status_code=201)
async def signup(credentials: UserCredentials):
    """Register a new user and return access token."""
    try:
        from backend.database import UserAlreadyExistsError

        create_user(credentials.username, credentials.password)
        token = create_access_token(credentials.username)

        return TokenResponse(
            access_token=token,
            username=credentials.username,
        )
    except UserAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists",
        )


@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserCredentials):
    """Login and return access token."""
    if authenticate_user(credentials.username, credentials.password):
        token = create_access_token(credentials.username)
        return TokenResponse(
            access_token=token,
            username=credentials.username,
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )


@router.post("/logout")
async def logout(username: str = Depends(verify_token)):
    """Logout and invalidate token."""
    # Remove all tokens for this user
    tokens_to_remove = [
        token for token, data in active_tokens.items() if data["username"] == username
    ]
    for token in tokens_to_remove:
        del active_tokens[token]

    return MessageResponse(message="Successfully logged out")
