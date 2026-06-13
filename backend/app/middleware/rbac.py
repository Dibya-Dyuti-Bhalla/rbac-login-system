"""
RBAC Middleware & FastAPI Dependencies
=======================================
Usage in route handlers:

    @router.get("/admin/users")
    async def list_users(
        current_user: User = Depends(require_roles(["ADMIN"])),
        db: AsyncSession = Depends(get_db),
    ):
        ...

    @router.post("/articles/{id}/approve")
    async def approve_article(
        id: UUID,
        current_user: User = Depends(require_permission("articles:approve")),
        db: AsyncSession = Depends(get_db),
    ):
        ...
"""

from typing import List
from uuid import UUID
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from ..core.security import verify_token
from ..db.session import get_db
from ..models.user import User
from ..models.user_role import UserRole
from ..models.role import Role, RolePermission, Permission

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    token = credentials.credentials
    user_id = verify_token(token, token_type="access")

    result = await db.execute(
        select(User)
        .where(User.id == UUID(user_id))
        .options(
            selectinload(User.user_roles)
            .selectinload(UserRole.role)
            .selectinload(Role.role_permissions)
            .selectinload(RolePermission.permission)
        )
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated. Please contact an administrator.",
        )
    return user


def require_roles(roles: List[str]):
    """Dependency factory: user must have at least one of the given roles."""
    async def _dep(current_user: User = Depends(get_current_user)) -> User:
        user_roles = {r.name.upper() for r in current_user.roles}
        required = {r.upper() for r in roles}
        if not user_roles.intersection(required) and not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role(s): {', '.join(roles)}",
            )
        return current_user
    return _dep


def require_permission(permission: str):
    """Dependency factory: user must have the specified permission."""
    async def _dep(current_user: User = Depends(get_current_user)) -> User:
        if current_user.is_superuser:
            return current_user
        if not current_user.has_permission(permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Missing permission: {permission}",
            )
        return current_user
    return _dep


def require_any_permission(permissions: List[str]):
    """Dependency factory: user must have at least one of the given permissions."""
    async def _dep(current_user: User = Depends(get_current_user)) -> User:
        if current_user.is_superuser:
            return current_user
        for perm in permissions:
            if current_user.has_permission(perm):
                return current_user
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied. Required one of: {', '.join(permissions)}",
        )
    return _dep


# Convenience aliases
get_admin_user = require_roles(["ADMIN"])
get_approver_user = require_roles(["ADMIN", "APPROVER"])
get_publisher_user = require_roles(["ADMIN", "PUBLISHER"])
get_authenticated_user = get_current_user
