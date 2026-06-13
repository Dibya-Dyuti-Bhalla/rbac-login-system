from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from uuid import UUID

from ....db.session import get_db
from ....models.notification import Notification
from ....models.role import Role, RolePermission
from ....models.user import User
from ....middleware.rbac import get_current_user, require_roles
from ....schemas.schemas import RoleOut

notifications_router = APIRouter(prefix="/notifications", tags=["Notifications"])
roles_router = APIRouter(prefix="/roles", tags=["Roles"])


# ─── Notifications ────────────────────────────────────────────────────────────

@notifications_router.get("")
async def list_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    unread_only: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Notification).where(Notification.user_id == current_user.id)
    if unread_only:
        query = query.where(Notification.is_read == False)

    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar()
    result = await db.execute(
        query.order_by(Notification.created_at.desc())
        .offset((page - 1) * page_size).limit(page_size)
    )
    items = result.scalars().all()

    return {
        "items": [
            {
                "id": str(n.id),
                "type": n.type.value,
                "title": n.title,
                "message": n.message,
                "is_read": n.is_read,
                "related_article_id": str(n.related_article_id) if n.related_article_id else None,
                "created_at": n.created_at.isoformat(),
            }
            for n in items
        ],
        "total": total,
        "unread_count": (await db.execute(
            select(func.count(Notification.id))
            .where(Notification.user_id == current_user.id, Notification.is_read == False)
        )).scalar(),
    }


@notifications_router.post("/{notification_id}/read")
async def mark_read(
    notification_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await db.execute(
        update(Notification)
        .where(Notification.id == notification_id, Notification.user_id == current_user.id)
        .values(is_read=True)
    )
    return {"message": "Marked as read"}


@notifications_router.post("/read-all")
async def mark_all_read(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await db.execute(
        update(Notification)
        .where(Notification.user_id == current_user.id, Notification.is_read == False)
        .values(is_read=True)
    )
    return {"message": "All notifications marked as read"}


# ─── Roles ────────────────────────────────────────────────────────────────────

@roles_router.get("")
async def list_roles(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(["ADMIN"])),
):
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(Role).options(
            selectinload(Role.role_permissions).selectinload(RolePermission.permission)
        )
    )
    roles = result.scalars().all()
    return [RoleOut.from_role(r) for r in roles]
