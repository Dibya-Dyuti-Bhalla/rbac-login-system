from sqlalchemy import Column, ForeignKey, DateTime, func, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base, UUIDMixin


class UserRole(Base, UUIDMixin):
    __tablename__ = "user_roles"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, index=True)
    assigned_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    assigned_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    user = relationship("User", back_populates="user_roles", foreign_keys="UserRole.user_id")
    role = relationship("Role", back_populates="user_roles")
    assigned_by_user = relationship("User", foreign_keys="UserRole.assigned_by")
