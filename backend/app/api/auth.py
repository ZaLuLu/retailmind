from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from ..core.db import get_db
from ..models.db import User, RefreshToken, Store, SaleRecord
import os
from decimal import Decimal
from ..schemas.auth import UserCreate, UserResponse, Token, TokenRefreshRequest
from ..schemas.response import SuccessResponse
from ..core.security import (
    hash_password as get_password_hash, 
    verify_password, 
    create_access_token, 
    create_refresh_token,
    hash_token,
    decode_token
)
from ..core.config import settings
from datetime import datetime, timedelta, timezone, date
from ..core.limiter import limiter

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=SuccessResponse[UserResponse], status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def register(request: Request, user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    # Check if user exists
    result = await db.execute(select(User).where(User.email == user_in.email))
    if result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already registered"
        )
    
    # Create user
    new_user = User(
        email=user_in.email,
        password=get_password_hash(user_in.password)
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return SuccessResponse(data=new_user)

@router.post("/login", response_model=SuccessResponse[Token])
@limiter.limit("5/minute")
async def login(request: Request, user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    # Verify user
    result = await db.execute(select(User).where(User.email == user_in.email))
    user = result.scalars().first()
    
    is_valid = False
    new_hash = None
    if user:
        is_valid, new_hash = verify_password(user_in.password, user.password)
        
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
        
    if new_hash:
        user.password = new_hash
        await db.commit()
    
    # Create tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    # Store refresh token
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    new_refresh = RefreshToken(
        user_id=user.id,
        token_hash=hash_token(refresh_token),
        expires_at=expires_at
    )
    db.add(new_refresh)
    await db.commit()
    
    return SuccessResponse(data=Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    ))

@router.post("/demo-login", response_model=SuccessResponse[Token])
@limiter.limit("10/minute")
async def demo_login(request: Request, db: AsyncSession = Depends(get_db)):
    """Creates a new ephemeral demo session and issues a JWT access and refresh token.
    Uses DemoSessionStore for complete visitor isolation.
    """
    from ..services.demo_store import DemoSessionStore
    
    # 1. Cleanup expired demo sessions to keep DB clean
    try:
        await DemoSessionStore.cleanup_expired_sessions(db)
    except Exception as e:
        logger.error(f"Failed to cleanup expired demo sessions: {e}")
        
    # 2. Create the ephemeral demo session
    demo_session_id, user = await DemoSessionStore.create_session(db)
    
    # 3. Create tokens with is_demo=True and demo_session_id in payload
    access_token = create_access_token(data={
        "sub": str(user.id),
        "demo_session_id": demo_session_id,
        "is_demo": True
    })
    refresh_token = create_refresh_token(data={
        "sub": str(user.id),
        "demo_session_id": demo_session_id,
        "is_demo": True
    })
    
    # 4. Store refresh token in DB
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    new_refresh = RefreshToken(
        user_id=user.id,
        token_hash=hash_token(refresh_token),
        expires_at=expires_at
    )
    db.add(new_refresh)
    await db.commit()
    
    return SuccessResponse(data=Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    ))


@router.post("/refresh", response_model=SuccessResponse[Token])
@limiter.limit("20/minute")
async def refresh(request: Request, refresh_data: TokenRefreshRequest, db: AsyncSession = Depends(get_db)):
    # Decode token
    payload = decode_token(refresh_data.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    user_id = payload.get("sub")
    
    # Check DB
    token_hash = hash_token(refresh_data.refresh_token)
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.expires_at > datetime.now(timezone.utc)
        )
    )
    db_token = result.scalars().first()
    
    if not db_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired or revoked"
        )
    
    # Generate new tokens
    new_access = create_access_token(data={"sub": user_id})
    new_refresh = create_refresh_token(data={"sub": user_id})
    
    # Replace old refresh token with new one (Rotate)
    db_token.token_hash = hash_token(new_refresh)
    db_token.expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    await db.commit()
    
    return SuccessResponse(data=Token(
        access_token=new_access,
        refresh_token=new_refresh,
        token_type="bearer"
    ))

@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(refresh_data: TokenRefreshRequest, db: AsyncSession = Depends(get_db)):
    token_hash = hash_token(refresh_data.refresh_token)
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    db_token = result.scalars().first()
    
    if db_token:
        await db.delete(db_token)
        await db.commit()
    
    return None


