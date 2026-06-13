from typing import Optional, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.notification import AuditLog, ActivityLog


class AuditService:
    @staticmethod
    async def log(
        db: AsyncSession,
        actor_id: Optional[UUID],
        action: str,
        resource_type: str,
        resource_id: Optional[UUID] = None,
        old_values: Optional[dict] = None,
        new_values: Optional[dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None,
    ):
        entry = AuditLog(
            actor_id=actor_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            old_values=old_values,
            new_values=new_values,
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id,
        )
        db.add(entry)

    @staticmethod
    async def activity(
        db: AsyncSession,
        user_id: Optional[UUID],
        action: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[UUID] = None,
        description: Optional[str] = None,
        ip_address: Optional[str] = None,
        metadata: Optional[dict] = None,
    ):
        entry = ActivityLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            description=description,
            ip_address=ip_address,
            metadata_=metadata,
        )
        db.add(entry)
