"""
Enhanced Security Module for RetailMind
Implements Argon2id hashing with legacy bcrypt fallback, and PyJWT token handling.
"""
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, Tuple
import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from passlib.context import CryptContext
from ..core.config import settings

# Initialize Argon2id password hasher (OWASP recommended parameters)
ph = PasswordHasher(
    time_cost=2,          # Number of iterations
    memory_cost=102400,   # 100 MiB memory usage
    parallelism=8,        # Parallel threads
    hash_len=32,          # Output length
    salt_len=16           # Salt length
)

# Legacy bcrypt hasher context for credentials migration support
legacy_crypto = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"

def hash_password(password: str) -> str:
    """Hash password using Argon2id"""
    return ph.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> Tuple[bool, Optional[str]]:
    """
    Verify a plain password against a hash.
    Supports seamless migration from legacy bcrypt ($2b$) hashes to Argon2id.
    
    Returns:
        (is_valid, new_hash_if_rehash_needed)
    """
    # Check if the hash represents a legacy bcrypt hash
    if hashed_password.startswith("$2b$") or hashed_password.startswith("$2a$"):
        try:
            if legacy_crypto.verify(plain_password, hashed_password):
                # Password is valid; generate new Argon2id hash for migration
                return True, hash_password(plain_password)
        except Exception:
            pass
        return False, None

    try:
        ph.verify(hashed_password, plain_password)
        # Check if hash parameters have changed and require a rehash
        if ph.check_needs_rehash(hashed_password):
            return True, hash_password(plain_password)
        return True, None
    except VerifyMismatchError:
        return False, None
    except Exception:
        return False, None

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token with unique JTI"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    
    jti = secrets.token_urlsafe(32)
    to_encode.update({
        "exp": expire,
        "jti": jti,
        "type": "access"
    })
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=ALGORITHM)

def create_refresh_token(data: dict) -> str:
    """Create long-lived JWT refresh token with unique JTI"""
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = data.copy()
    jti = secrets.token_urlsafe(32)
    to_encode.update({
        "exp": expire,
        "jti": jti,
        "type": "refresh"
    })
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=ALGORITHM)

def decode_token(token: str) -> Optional[dict]:
    """Decode a JWT token securely using PyJWT"""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None

def hash_token(token: str) -> str:
    """Hash a token securely (using SHA-256) for DB storage to prevent leak exposures"""
    import hashlib
    return hashlib.sha256(token.encode()).hexdigest()
