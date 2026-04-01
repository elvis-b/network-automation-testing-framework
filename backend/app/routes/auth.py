"""
Authentication Routes

Handles user authentication including login, logout, and token management.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

import bcrypt
import jwt
from app.config import settings
from app.database.mongodb import get_database
from app.models.user import LoginRequest, LoginResponse, Token, UserResponse
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

logger = logging.getLogger(__name__)
router = APIRouter()

# JWT Bearer scheme
security = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"), hashed_password.encode("utf-8")
        )
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False


def get_password_hash(password: str) -> str:
    """Generate password hash."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT access token.

    Args:
        data: Token payload data
        expires_delta: Token expiration time

    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=settings.jwt_expiry_hours)

    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(
        to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm
    )

    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    """
    Decode and verify JWT token.

    Args:
        token: JWT token string

    Returns:
        Decoded token payload or None if invalid
    """
    try:
        payload = jwt.decode(
            token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
        )
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """
    Get current authenticated user from token.

    Args:
        credentials: HTTP Bearer credentials

    Returns:
        User data from token

    Raises:
        HTTPException: If token is invalid or expired
    """
    token = credentials.credentials
    payload = decode_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    Authenticate user and return JWT token.

    Args:
        request: Login credentials (username, password)

    Returns:
        JWT token and user information

    Raises:
        HTTPException: If credentials are invalid
    """
    logger.info(f"Login attempt for user: {request.username}")

    db = get_database()
    users_collection = db["users"]

    # Find user
    user = await users_collection.find_one({"username": request.username})

    if not user:
        logger.warning(f"Login failed: User not found - {request.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )

    # Verify password
    if not verify_password(request.password, user["password_hash"]):
        logger.warning(f"Login failed: Invalid password - {request.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )

    # Check if user is active
    if not user.get("is_active", True):
        logger.warning(f"Login failed: User inactive - {request.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User account is disabled"
        )

    # Create access token
    token_data = {"sub": user["username"], "role": user["role"]}
    access_token = create_access_token(token_data)

    # Update last login
    await users_collection.update_one(
        {"_id": user["_id"]}, {"$set": {"last_login": datetime.utcnow()}}
    )

    logger.info(f"Login successful: {request.username}")

    # Build response
    user_response = UserResponse(
        id=str(user["_id"]),
        username=user["username"],
        email=user.get("email"),
        role=user["role"],
        is_active=user.get("is_active", True),
        created_at=user["created_at"],
        last_login=datetime.utcnow(),
    )

    return LoginResponse(
        token=access_token,
        token_type="bearer",
        expires_in=settings.jwt_expiry_hours * 3600,
        user=user_response,
    )


@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    """
    Logout current user.

    Note: With JWT, logout is typically handled client-side by
    discarding the token. This endpoint provides a standard
    logout flow for API consistency.

    Returns:
        Success message
    """
    logger.info(f"Logout: {current_user.get('sub')}")

    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """
    Get current user information.

    Returns:
        Current user data
    """
    db = get_database()
    users_collection = db["users"]

    user = await users_collection.find_one({"username": current_user.get("sub")})

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    return UserResponse(
        id=str(user["_id"]),
        username=user["username"],
        email=user.get("email"),
        role=user["role"],
        is_active=user.get("is_active", True),
        created_at=user["created_at"],
        last_login=user.get("last_login"),
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(current_user: dict = Depends(get_current_user)):
    """
    Refresh access token.

    Returns:
        New JWT token
    """
    token_data = {"sub": current_user.get("sub"), "role": current_user.get("role")}
    access_token = create_access_token(token_data)

    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.jwt_expiry_hours * 3600,
    )
