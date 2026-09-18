"""Auth endpoints — login, refresh, logout, me."""
from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.security import (
    ACCESS_COOKIE,
    clear_auth_cookies,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_token_from_request,
    set_auth_cookies,
    verify_password,
)
from fastapi import Request

router = APIRouter()


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    user_id: str
    email: str
    full_name: str
    role: str
    merchant_id: str
    merchant_name: str
    sandbox: bool = True
    sandbox_label: str = "Sandbox · Synthetic Demo Data"


async def _get_current_user(request: Request, db: AsyncSession = Depends(get_db)):
    token = get_current_token_from_request(request)
    payload = decode_token(token)
    user_id = payload.get("sub")
    merchant_id = payload.get("merchant_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    return {"user_id": user_id, "merchant_id": merchant_id}


@router.post("/login", response_model=LoginResponse)
async def login(
    body: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    from src.models.user import User, MerchantUser
    from src.models.merchant import Merchant

    stmt = select(User).where(
        and_(User.email == body.email, User.is_active == True)  # noqa: E712
    )
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Get primary merchant
    stmt2 = select(MerchantUser).where(
        and_(MerchantUser.user_id == user.id, MerchantUser.is_primary == True)  # noqa: E712
    )
    result2 = await db.execute(stmt2)
    mu = result2.scalar_one_or_none()
    if not mu:
        raise HTTPException(status_code=400, detail="No merchant linked to this account")

    stmt3 = select(Merchant).where(Merchant.id == mu.merchant_id)
    result3 = await db.execute(stmt3)
    merchant = result3.scalar_one_or_none()
    if not merchant:
        raise HTTPException(status_code=400, detail="Merchant not found")

    access_token = create_access_token(
        subject=user.id, merchant_id=mu.merchant_id
    )
    refresh_token = create_refresh_token(subject=user.id)
    set_auth_cookies(response, access_token, refresh_token)

    return LoginResponse(
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        merchant_id=mu.merchant_id,
        merchant_name=merchant.name,
    )


@router.post("/logout")
async def logout(response: Response):
    clear_auth_cookies(response)
    return {"message": "Logged out"}


@router.get("/me")
async def me(request: Request, db: AsyncSession = Depends(get_db)):
    ctx = await _get_current_user(request, db)
    from src.models.user import User
    from src.models.merchant import Merchant
    stmt = select(User).where(User.id == ctx["user_id"])
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    merchant = None
    if ctx["merchant_id"]:
        stmt2 = select(Merchant).where(Merchant.id == ctx["merchant_id"])
        result2 = await db.execute(stmt2)
        merchant = result2.scalar_one_or_none()

    return {
        "user_id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "merchant_id": ctx["merchant_id"],
        "merchant_name": merchant.name if merchant else None,
        "sandbox": True,
        "sandbox_label": "Sandbox · Synthetic Demo Data",
    }
