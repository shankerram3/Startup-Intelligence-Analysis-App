"""
Security utilities for API authentication and authorization
Provides JWT token handling, password hashing, and security helpers
"""

import os
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

# Use bcrypt directly to avoid passlib's bug detection issues
# passlib's internal bug detection uses a 200+ byte test password
# which exceeds bcrypt's 72-byte limit, causing errors
try:
    import bcrypt

    _bcrypt_available = True
except ImportError:
    _bcrypt_available = False
    # Fallback to passlib if bcrypt not available
    from passlib.context import CryptContext

load_dotenv()

# Security configuration
# Check if authentication is enabled first
ENABLE_AUTH = os.getenv("ENABLE_AUTH", "false").lower() == "true"

# JWT_SECRET_KEY handling:
# - If auth is enabled, SECRET_KEY is required (fail if missing)
# - If auth is disabled, use a dev key with warning (allows development)
SECRET_KEY = os.getenv("JWT_SECRET_KEY")

if ENABLE_AUTH:
    # Production mode: JWT_SECRET_KEY is required when auth is enabled
    if not SECRET_KEY:
        raise ValueError(
            "JWT_SECRET_KEY environment variable is required when ENABLE_AUTH=true. "
            "Set it to a secure random string (e.g., openssl rand -hex 32). "
            "Never use default or hardcoded secrets in production."
        )
elif not SECRET_KEY:
    # Development mode: Use a temporary dev key with warning
    import warnings

    SECRET_KEY = "dev-secret-key-change-in-production-do-not-use-in-production"
    warnings.warn(
        "JWT_SECRET_KEY not set. Using development key. "
        "Set JWT_SECRET_KEY environment variable for production. "
        "Generate with: openssl rand -hex 32",
        UserWarning,
        stacklevel=2,
    )

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
API_KEY_HEADER = os.getenv("API_KEY_HEADER", "X-API-Key")

# Password hashing - use bcrypt directly to avoid passlib's bug detection
# If bcrypt is not available, fall back to passlib (with error handling)
if not _bcrypt_available:
    _pwd_context = None

    def _get_pwd_context():
        """Get password context (passlib fallback)"""
        global _pwd_context
        if _pwd_context is None:
            _pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        return _pwd_context


# Bcrypt has a 72-byte limit for passwords
MAX_BCRYPT_BYTES = 72


def _normalize_password_for_bcrypt(password: str) -> str:
    """
    Normalize password for bcrypt hashing (truncate to 72 bytes if needed)

    Args:
        password: Plain text password

    Returns:
        Password string truncated to 72 bytes if necessary

    Note:
        Bcrypt has a 72-byte limit. Passwords longer than this are truncated.
        This is a known limitation and should be documented to users.
    """
    password_bytes = password.encode("utf-8")
    if len(password_bytes) > MAX_BCRYPT_BYTES:
        # Truncate to first 72 bytes (UTF-8 aware)
        password = password_bytes[:MAX_BCRYPT_BYTES].decode("utf-8", errors="ignore")
    return password


# HTTP Bearer scheme for JWT
security = HTTPBearer()
# Optional security scheme (doesn't auto-raise errors)
optional_security = HTTPBearer(auto_error=False)


class SecurityConfig:
    """
    Security configuration and settings
    """

    ENABLE_AUTH = ENABLE_AUTH  # Use the value determined above
    ENABLE_RATE_LIMITING = os.getenv("ENABLE_RATE_LIMITING", "true").lower() == "true"
    
    # CORS Configuration
    # For production, set ALLOWED_ORIGINS with your main domain(s)
    # Vercel preview deployments are handled automatically via pattern matching
    # Example: ALLOWED_ORIGINS=https://my-app.vercel.app,https://myapp.com
    # Note: Preview deployments (*.vercel.app) are allowed automatically if main domain is included
    default_origins = (
        "http://localhost:5173,http://localhost:5174,http://localhost:3000,"
        "http://127.0.0.1:5173,http://127.0.0.1:5174"
    )
    env_origins = os.getenv("ALLOWED_ORIGINS", default_origins)
    
    # Parse explicit origins
    explicit_origins = [
        origin.strip()
        for origin in env_origins.split(",")
        if origin.strip()
    ]
    
    # Production: Auto-allow Vercel preview deployments if main Vercel domain is present
    # Since FastAPI's CORSMiddleware doesn't support wildcards, we need to explicitly
    # add common Vercel preview patterns or use a custom middleware
    ALLOWED_ORIGINS = explicit_origins.copy()
    has_vercel_domain = any("vercel.app" in origin for origin in explicit_origins)
    
    # If a Vercel domain is configured, enable pattern matching in custom middleware
    # Note: We can't add all possible vercel.app subdomains to ALLOWED_ORIGINS
    # because Vercel generates unique preview URLs for each deployment
    # So we use a custom middleware to handle this dynamically
    _VERCEL_PREVIEW_PATTERN_ENABLED = has_vercel_domain
    MAX_REQUEST_SIZE = int(os.getenv("MAX_REQUEST_SIZE", "10485760"))  # 10MB default
    API_KEYS = (
        set(os.getenv("API_KEYS", "").split(",")) if os.getenv("API_KEYS") else set()
    )


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password

    Args:
        plain_password: Plain text password
        hashed_password: Hashed password to verify against

    Returns:
        True if password matches, False otherwise

    Note:
        Bcrypt has a 72-byte limit, so passwords are truncated if necessary
    """
    normalized_password = _normalize_password_for_bcrypt(plain_password)
    if _bcrypt_available:
        # Use bcrypt directly to avoid passlib's bug detection
        try:
            return bcrypt.checkpw(
                normalized_password.encode("utf-8"), hashed_password.encode("utf-8")
            )
        except (ValueError, TypeError):
            return False
    else:
        # Fallback to passlib
        try:
            return _get_pwd_context().verify(normalized_password, hashed_password)
        except ValueError as e:
            if "cannot be longer than 72 bytes" in str(e):
                return False
            raise


def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt

    Args:
        password: Plain text password

    Returns:
        Hashed password

    Note:
        Bcrypt has a 72-byte limit, so passwords are truncated if necessary
    """
    normalized_password = _normalize_password_for_bcrypt(password)
    if _bcrypt_available:
        # Use bcrypt directly to avoid passlib's bug detection
        password_bytes = normalized_password.encode("utf-8")
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode("utf-8")
    else:
        # Fallback to passlib
        try:
            return _get_pwd_context().hash(normalized_password)
        except ValueError as e:
            if "cannot be longer than 72 bytes" in str(e):
                # Try with further truncation as a fallback
                password_bytes = normalized_password.encode("utf-8")
                if len(password_bytes) > MAX_BCRYPT_BYTES:
                    normalized_password = password_bytes[:MAX_BCRYPT_BYTES].decode(
                        "utf-8", errors="ignore"
                    )
                    return _get_pwd_context().hash(normalized_password)
            raise


def create_access_token(
    data: Dict[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
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


async def verify_token(
    credentials: HTTPAuthorizationCredentials = Security(security),
) -> Dict[str, Any]:
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
    credentials: Optional[HTTPAuthorizationCredentials] = Security(optional_security),
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
    error_str = str(error).lower()

    if "Neo4j" in error_type or "neo4j" in error_str or "database" in error_str:
        return "A database error occurred"
    elif "OpenAI" in error_type or "openai" in error_str or "api" in error_str:
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
        data={"sub": user_id, "role": role}, expires_delta=timedelta(days=1)
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
