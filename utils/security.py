"""
Security utilities for API authentication and authorization
Provides JWT token handling, password hashing, and security helpers
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os
from dotenv import load_dotenv

load_dotenv()

# Security configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
API_KEY_HEADER = os.getenv("API_KEY_HEADER", "X-API-Key")

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer scheme for JWT
security = HTTPBearer()


class SecurityConfig:
    """
    Security configuration and settings
    """
    ENABLE_AUTH = os.getenv("ENABLE_AUTH", "false").lower() == "true"
    ENABLE_RATE_LIMITING = os.getenv("ENABLE_RATE_LIMITING", "true").lower() == "true"
    ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
    MAX_REQUEST_SIZE = int(os.getenv("MAX_REQUEST_SIZE", "10485760"))  # 10MB default
    API_KEYS = set(os.getenv("API_KEYS", "").split(",")) if os.getenv("API_KEYS") else set()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password

    Args:
        plain_password: Plain text password
        hashed_password: Hashed password to verify against

    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt

    Args:
        password: Plain text password

    Returns:
        Hashed password
    """
    return pwd_context.hash(password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token

    Args:
        data: Data to encode in the token (e.g., {"sub": "user_id"})
        expires_delta: Optional expiration time delta

    Returns:
        Encoded JWT token

    Example:
        token = create_access_token({"sub": "user123", "role": "admin"})
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


def decode_access_token(token: str) -> Dict[str, Any]:
    """
    Decode and validate a JWT access token

    Args:
        token: JWT token to decode

    Returns:
        Decoded token payload

    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=401,
            detail=f"Could not validate credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)) -> Dict[str, Any]:
    """
    Verify JWT token from Authorization header

    Args:
        credentials: HTTP Bearer credentials from request

    Returns:
        Decoded token payload

    Raises:
        HTTPException: If token is invalid

    Usage:
        @app.get("/protected")
        async def protected_route(token_data: dict = Depends(verify_token)):
            user_id = token_data.get("sub")
            return {"user_id": user_id}
    """
    token = credentials.credentials
    return decode_access_token(token)


async def verify_api_key(api_key: str) -> bool:
    """
    Verify API key against configured keys

    Args:
        api_key: API key to verify

    Returns:
        True if valid, False otherwise
    """
    if not SecurityConfig.API_KEYS:
        # If no API keys configured, allow all (development mode)
        return True

    return api_key in SecurityConfig.API_KEYS


async def optional_auth(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security, auto_error=False)
) -> Optional[Dict[str, Any]]:
    """
    Optional authentication - allows both authenticated and anonymous access

    Args:
        credentials: Optional HTTP Bearer credentials

    Returns:
        Token payload if authenticated, None if anonymous

    Usage:
        @app.get("/endpoint")
        async def endpoint(user: Optional[dict] = Depends(optional_auth)):
            if user:
                # Authenticated request
                return {"user_id": user["sub"], "data": "sensitive"}
            else:
                # Anonymous request
                return {"data": "public"}
    """
    if not credentials:
        return None

    if not SecurityConfig.ENABLE_AUTH:
        return None

    try:
        return decode_access_token(credentials.credentials)
    except HTTPException:
        return None


def get_current_user_id(token_data: Dict[str, Any] = Depends(verify_token)) -> str:
    """
    Extract user ID from token

    Args:
        token_data: Decoded token data

    Returns:
        User ID from token

    Raises:
        HTTPException: If user ID not found in token

    Usage:
        @app.get("/profile")
        async def get_profile(user_id: str = Depends(get_current_user_id)):
            return {"user_id": user_id}
    """
    user_id = token_data.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token: missing user ID")
    return user_id


def sanitize_error_message(error: Exception, include_details: bool = False) -> str:
    """
    Sanitize error messages before returning to client

    Args:
        error: Exception to sanitize
        include_details: Whether to include detailed error info (dev mode)

    Returns:
        Sanitized error message

    Example:
        try:
            result = dangerous_operation()
        except Exception as e:
            error_msg = sanitize_error_message(e, include_details=False)
            raise HTTPException(status_code=500, detail=error_msg)
    """
    if include_details:
        return str(error)

    # Generic error messages for production
    error_type = type(error).__name__

    if "Neo4j" in error_type or "database" in str(error).lower():
        return "Database operation failed"
    elif "OpenAI" in error_type or "api" in str(error).lower():
        return "External service unavailable"
    elif "ValueError" in error_type or "ValidationError" in error_type:
        return "Invalid input data"
    else:
        return "An internal error occurred"


# Example token generation for testing
def generate_test_token(user_id: str = "test_user", role: str = "user") -> str:
    """
    Generate a test JWT token for development/testing

    Args:
        user_id: User ID to encode
        role: User role to encode

    Returns:
        JWT token string

    Example:
        token = generate_test_token("user123", "admin")
        # Use in requests: headers={"Authorization": f"Bearer {token}"}
    """
    return create_access_token(
        data={"sub": user_id, "role": role},
        expires_delta=timedelta(days=1)
    )


# Password validation rules
def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Validate password meets security requirements

    Args:
        password: Password to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"

    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"

    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"

    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one digit"

    return True, "Password is strong"
