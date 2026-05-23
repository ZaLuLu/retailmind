from fastapi import APIRouter, Depends, HTTPException, status, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from ..core.db import get_db
from ..models.db import User, RefreshToken, Store, SaleRecord
import os
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
from datetime import datetime, timedelta, timezone

router = APIRouter(prefix="/auth", tags=["Authentication"])
limiter = Limiter(key_func=get_remote_address)

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
    demo_email = "demo@retailmind.com"
    demo_pass = "demo123"
    
    # 1. Check if demo user exists
    result = await db.execute(select(User).where(User.email == demo_email))
    user = result.scalars().first()
    
    if not user:
        # Create demo user on-the-fly
        from ..core.security import hash_password
        user = User(
            email=demo_email,
            password=hash_password(demo_pass),
            full_name="Demo Admin",
            store_name="RetailMind Demo Store",
            currency="USD",
            is_onboarded=True
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        # Create demo store
        store = Store(
            user_id=user.id,
            name="RetailMind Demo Store",
            location="Virtual"
        )
        db.add(store)
        await db.commit()
        await db.refresh(store)
        
        # Seed sales data from the Excel file if present
        try:
            import pandas as pd
            # Find the path of demo_retail_data.xlsx
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            excel_path = os.path.join(base_dir, "Demo_data", "demo_retail_data.xlsx")
            if os.path.exists(excel_path):
                df = pd.read_excel(excel_path)
                records = []
                for _, row in df.iterrows():
                    qty = float(row['qty_sold'])
                    unit_price = float(row['unit_price'])
                    unit_cost = float(row.get('unit_cost', 0))
                    total_revenue = qty * unit_price
                    cogs = unit_cost * qty if unit_cost else 0
                    margin = None
                    if total_revenue > 0 and cogs > 0:
                        margin = round(((total_revenue - cogs) / total_revenue) * 100, 2)
                    
                    sale_date = datetime.strptime(str(row['date'])[:10], "%Y-%m-%d").date()
                    record = SaleRecord(
                        user_id=user.id,
                        store_id=store.id,
                        product_name=str(row['product_name']),
                        product_sku=str(row.get('product_id', '')),
                        product_category=str(row.get('category', 'Other')),
                        quantity_sold=qty,
                        unit_price=unit_price,
                        total_revenue=total_revenue,
                        cogs=cogs,
                        gross_margin=margin,
                        sale_date=sale_date,
                        customer_segment=str(row.get('customer_segment', '')),
                        currency="USD",
                        source="demo_seed"
                    )
                    records.append(record)
                
                # Batch insert
                db.add_all(records)
                await db.commit()
        except Exception as e:
            # Fallback — log the error but don't fail registration
            import logging
            logging.getLogger(__name__).error(f"Seeding demo sales data failed: {e}")
            
    # Issue tokens immediately
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
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


