from fastapi import APIRouter, Depends, HTTPException, status, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
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
async def demo_login(db: AsyncSession = Depends(get_db)):
    """Self-bootstrapping demo endpoint. Creates the demo account + seeds dummy
    data on first call, then just issues tokens on every subsequent call.
    No rate limiter here so it never fails on Vercel cold starts.
    """
    demo_email = "demo@retailmind.com"
    demo_pass = "RetailDemo2024!"

    # ── 1. Fetch or create demo user ──────────────────────────────────────────
    result = await db.execute(select(User).where(User.email == demo_email))
    user = result.scalars().first()

    needs_seed = False
    store = None

    if not user:
        from ..core.security import hash_password
        user = User(
            email=demo_email,
            password=hash_password(demo_pass),
            full_name="Alex Demo",
            store_name="RetailMind Demo Store",
            currency="USD",
            is_onboarded=True,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        needs_seed = True
    else:
        # Heal existing demo accounts that have no sales data (e.g. previous seed failed)
        count_result = await db.execute(
            select(SaleRecord).where(SaleRecord.user_id == user.id).limit(1)
        )
        if count_result.scalars().first() is None:
            needs_seed = True
        # Also ensure is_onboarded is True in case it wasn't set
        if not user.is_onboarded:
            user.is_onboarded = True
            await db.commit()

    if needs_seed:

        # ── 2. Get or create demo store ───────────────────────────────────────
        store_result = await db.execute(
            select(Store).where(Store.user_id == user.id).limit(1)
        )
        store = store_result.scalars().first()
        if not store:
            store = Store(
                user_id=user.id,
                name="RetailMind Demo Store",
                location="New York, NY",
            )
            db.add(store)
            await db.commit()
            await db.refresh(store)

        # ── 3. Seed hardcoded demo sales data ─────────────────────────────────
        # 90 days of realistic multi-product retail data — works on any env.
        import random
        random.seed(42)

        products = [
            {"name": "Artisan Leather Journal",   "sku": "ALJ-001", "category": "Stationery",    "price": 34.99, "cost": 12.00},
            {"name": "Premium Fountain Pen",       "sku": "PFP-002", "category": "Stationery",    "price": 89.99, "cost": 28.00},
            {"name": "Wireless Desk Lamp",         "sku": "WDL-003", "category": "Electronics",   "price": 59.99, "cost": 22.00},
            {"name": "Bamboo Desk Organizer",      "sku": "BDO-004", "category": "Office",        "price": 44.99, "cost": 16.00},
            {"name": "Ergonomic Mouse Pad",        "sku": "EMP-005", "category": "Electronics",   "price": 29.99, "cost": 8.50},
            {"name": "Cold Brew Coffee Kit",       "sku": "CBK-006", "category": "Kitchen",       "price": 49.99, "cost": 18.00},
            {"name": "Scented Soy Candle Set",     "sku": "SSC-007", "category": "Home Decor",    "price": 39.99, "cost": 11.00},
            {"name": "Reusable Water Bottle",      "sku": "RWB-008", "category": "Kitchen",       "price": 24.99, "cost": 7.00},
            {"name": "Linen Tote Bag",             "sku": "LTB-009", "category": "Accessories",   "price": 19.99, "cost": 5.50},
            {"name": "Desk Plant Terrarium",       "sku": "DPT-010", "category": "Home Decor",    "price": 54.99, "cost": 20.00},
        ]
        segments = ["Walk-in", "Online", "B2B", "Walk-in", "Online"]

        today = datetime.now(timezone.utc).date()
        records = []
        for day_offset in range(89, -1, -1):
            sale_date = today - timedelta(days=day_offset)
            # 3-8 sales per day across random products
            n_sales = random.randint(3, 8)
            for _ in range(n_sales):
                p = random.choice(products)
                qty = float(random.randint(1, 6))
                # Weekend boost
                if sale_date.weekday() >= 5:
                    qty = float(random.randint(3, 10))
                total_rev = round(qty * p["price"], 2)
                total_cogs = round(qty * p["cost"], 2)
                margin = round(((total_rev - total_cogs) / total_rev) * 100, 2) if total_rev > 0 else None
                records.append(SaleRecord(
                    user_id=user.id,
                    store_id=store.id,
                    product_name=p["name"],
                    product_sku=p["sku"],
                    product_category=p["category"],
                    quantity_sold=qty,
                    unit_price=Decimal(str(p["price"])),
                    total_revenue=Decimal(str(total_rev)),
                    cogs=Decimal(str(total_cogs)),
                    gross_margin=Decimal(str(margin)) if margin is not None else None,
                    sale_date=sale_date,
                    customer_segment=random.choice(segments),
                    currency="USD",
                    source="demo_seed",
                ))

        # Batch insert
        db.add_all(records)
        await db.commit()

    # ── 4. Issue tokens ────────────────────────────────────────────────────────
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    new_refresh = RefreshToken(
        user_id=user.id,
        token_hash=hash_token(refresh_token),
        expires_at=expires_at,
    )
    db.add(new_refresh)
    await db.commit()

    return SuccessResponse(data=Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
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


