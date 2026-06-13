from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional

from ....db.session import get_db
from ....models.notification import AuditLog, ActivityLog
from ....models.user import User
from ....models.article import Article, ArticleStatus
from ....middleware.rbac import require_roles

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/stats")
async def get_platform_stats(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(["ADMIN"])),
):
    """Dashboard statistics for admin."""
    total_users = (await db.execute(select(func.count(User.id)))).scalar()
    active_users = (await db.execute(select(func.count(User.id)).where(User.is_active == True))).scalar()
    total_articles = (await db.execute(select(func.count(Article.id)))).scalar()

    status_counts = {}
    for status in ArticleStatus:
        count = (await db.execute(
            select(func.count(Article.id)).where(Article.status == status)
        )).scalar()
        status_counts[status.value] = count

    return {
        "users": {"total": total_users, "active": active_users, "inactive": total_users - active_users},
        "articles": {"total": total_articles, "by_status": status_counts},
    }


@router.get("/audit-logs")
async def get_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(["ADMIN"])),
):
    query = select(AuditLog).order_by(AuditLog.created_at.desc())
    if action:
        query = query.where(AuditLog.action.ilike(f"%{action}%"))
    if resource_type:
        query = query.where(AuditLog.resource_type == resource_type)

    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar()
    result = await db.execute(query.offset((page - 1) * page_size).limit(page_size))
    logs = result.scalars().all()

    return {
        "items": [
            {
                "id": str(log.id),
                "actor_id": str(log.actor_id) if log.actor_id else None,
                "action": log.action,
                "resource_type": log.resource_type,
                "resource_id": str(log.resource_id) if log.resource_id else None,
                "old_values": log.old_values,
                "new_values": log.new_values,
                "ip_address": log.ip_address,
                "created_at": log.created_at.isoformat(),
            }
            for log in logs
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/activity")
async def get_activity_feed(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(["ADMIN"])),
):
    query = select(ActivityLog).order_by(ActivityLog.created_at.desc())
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar()
    result = await db.execute(query.offset((page - 1) * page_size).limit(page_size))
    logs = result.scalars().all()

    return {
        "items": [
            {
                "id": str(log.id),
                "user_id": str(log.user_id) if log.user_id else None,
                "action": log.action,
                "resource_type": log.resource_type,
                "description": log.description,
                "created_at": log.created_at.isoformat(),
            }
            for log in logs
        ],
        "total": total,
        "page": page,
    }
