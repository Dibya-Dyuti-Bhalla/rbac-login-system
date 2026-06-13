from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime, timezone

from ....db.session import get_db
from ....models.user import User
from ....core.security import (
    verify_password, create_access_token, create_refresh_token, verify_token
)
from ....schemas.auth import LoginRequest, TokenResponse, RefreshRequest, PasswordChangeRequest
from ....middleware.rbac import get_current_user
from ....services.audit_service import AuditService
from ....core.config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )

    # Update last login
    await db.execute(
        update(User)
        .where(User.id == user.id)
        .values(last_login_at=datetime.now(timezone.utc).isoformat())
    )

    # Audit log
    await AuditService.log(
        db, actor_id=user.id, action="auth.login",
        resource_type="user", resource_id=user.id,
        ip_address=request.client.host if request.client else None,
    )

    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    user_id = verify_token(body.refresh_token, token_type="refresh")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/logout")
async def logout(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await AuditService.log(
        db, actor_id=current_user.id, action="auth.logout",
        resource_type="user", resource_id=current_user.id,
        ip_address=request.client.host if request.client else None,
    )
    # In production: add token to Redis blacklist
    return {"message": "Logged out successfully"}


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    from ....schemas.schemas import UserOut
    return UserOut.from_user(current_user)


@router.post("/change-password")
async def change_password(
    body: PasswordChangeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not verify_password(body.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    from ....core.security import get_password_hash
    await db.execute(
        update(User)
        .where(User.id == current_user.id)
        .values(hashed_password=get_password_hash(body.new_password))
    )
    return {"message": "Password changed successfully"}
