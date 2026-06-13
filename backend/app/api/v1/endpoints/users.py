from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from sqlalchemy.orm import selectinload
from uuid import UUID
from typing import Optional

from ....db.session import get_db
from ....models.user import User
from ....models.role import Role
from ....models.user_role import UserRole
from ....schemas.schemas import UserCreate, UserUpdate, UserOut, AssignRolesRequest, PaginatedResponse
from ....middleware.rbac import get_current_user, require_roles
from ....core.security import get_password_hash
from ....services.audit_service import AuditService
from ....services.notification_service import NotificationService

router = APIRouter(prefix="/users", tags=["Users"])


async def _load_user_with_roles(db: AsyncSession, user_id: UUID) -> Optional[User]:
    result = await db.execute(
        select(User)
        .where(User.id == user_id)
        .options(selectinload(User.user_roles).selectinload(UserRole.role))
    )
    return result.scalar_one_or_none()


@router.get("", response_model=PaginatedResponse)
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    role: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN"])),
):
    query = select(User).options(selectinload(User.user_roles).selectinload(UserRole.role))

    if search:
        query = query.where(
            User.full_name.ilike(f"%{search}%") | User.email.ilike(f"%{search}%")
        )
    if is_active is not None:
        query = query.where(User.is_active == is_active)

    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar()

    query = query.offset((page - 1) * page_size).limit(page_size).order_by(User.created_at.desc())
    result = await db.execute(query)
    users = result.scalars().all()

    items = [UserOut.from_user(u) for u in users]
    if role:
        items = [u for u in items if role.upper() in u.roles]

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    )


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(
    body: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN"])),
):
    # Check uniqueness
    result = await db.execute(select(User).where(User.email == body.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    result = await db.execute(select(User).where(User.username == body.username))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Username already taken")

    user = User(
        email=body.email,
        username=body.username,
        full_name=body.full_name,
        hashed_password=get_password_hash(body.password),
        department=body.department,
        is_active=True,
    )
    db.add(user)
    await db.flush()

    # Assign roles
    for role_name in body.role_names:
        result = await db.execute(select(Role).where(Role.name == role_name.upper()))
        role = result.scalar_one_or_none()
        if role:
            db.add(UserRole(user_id=user.id, role_id=role.id, assigned_by=current_user.id))

    await db.flush()
    await AuditService.log(
        db, actor_id=current_user.id, action="user.created",
        resource_type="user", resource_id=user.id,
        new_values={"email": user.email, "roles": body.role_names},
    )

    user = await _load_user_with_roles(db, user.id)
    return UserOut.from_user(user)


@router.get("/{user_id}", response_model=UserOut)
async def get_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN"])),
):
    user = await _load_user_with_roles(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserOut.from_user(user)


@router.patch("/{user_id}", response_model=UserOut)
async def update_user(
    user_id: UUID,
    body: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN"])),
):
    user = await _load_user_with_roles(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    old_values = {"is_active": user.is_active, "full_name": user.full_name}
    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(user, key, value)

    await AuditService.log(
        db, actor_id=current_user.id, action="user.updated",
        resource_type="user", resource_id=user.id,
        old_values=old_values, new_values=update_data,
    )

    # If deactivated, notify user
    if body.is_active is False:
        await NotificationService.notify_account_status(db, user, activated=False)
    elif body.is_active is True:
        await NotificationService.notify_account_status(db, user, activated=True)

    await db.flush()
    user = await _load_user_with_roles(db, user_id)
    return UserOut.from_user(user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN"])),
):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    user = await _load_user_with_roles(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await AuditService.log(
        db, actor_id=current_user.id, action="user.deleted",
        resource_type="user", resource_id=user_id,
        old_values={"email": user.email},
    )
    await db.delete(user)


@router.put("/{user_id}/roles", response_model=UserOut)
async def assign_roles(
    user_id: UUID,
    body: AssignRolesRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN"])),
):
    user = await _load_user_with_roles(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    old_roles = user.role_names

    # Remove existing roles
    await db.execute(delete(UserRole).where(UserRole.user_id == user_id))

    # Assign new roles
    for role_name in body.role_names:
        result = await db.execute(select(Role).where(Role.name == role_name.upper()))
        role = result.scalar_one_or_none()
        if not role:
            raise HTTPException(status_code=400, detail=f"Role '{role_name}' not found")
        db.add(UserRole(user_id=user.id, role_id=role.id, assigned_by=current_user.id))

    await AuditService.log(
        db, actor_id=current_user.id, action="user.roles_assigned",
        resource_type="user", resource_id=user_id,
        old_values={"roles": old_roles}, new_values={"roles": body.role_names},
    )

    await db.flush()
    user = await _load_user_with_roles(db, user_id)
    return UserOut.from_user(user)


@router.post("/{user_id}/toggle-active", response_model=UserOut)
async def toggle_active(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN"])),
):
    user = await _load_user_with_roles(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = not user.is_active
    await db.flush()

    await NotificationService.notify_account_status(db, user, activated=user.is_active)
    await AuditService.log(
        db, actor_id=current_user.id,
        action="user.activated" if user.is_active else "user.deactivated",
        resource_type="user", resource_id=user_id,
        new_values={"is_active": user.is_active},
    )

    user = await _load_user_with_roles(db, user_id)
    return UserOut.from_user(user)
