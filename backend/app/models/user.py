from sqlalchemy import Column, String, Boolean, Text
from sqlalchemy.orm import relationship
from .base import Base, UUIDMixin, TimestampMixin


class User(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "users"

    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    avatar_url = Column(String(500), nullable=True)
    department = Column(String(100), nullable=True)
    last_login_at = Column(String(50), nullable=True)

    # Relationships
    user_roles = relationship("UserRole", back_populates="user", cascade="all, delete-orphan", foreign_keys="UserRole.user_id")
    articles = relationship("Article", back_populates="author", foreign_keys="Article.author_id")
    approved_articles = relationship("Article", back_populates="approver", foreign_keys="Article.approver_id")
    published_articles = relationship("Article", back_populates="publisher", foreign_keys="Article.publisher_id")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    activity_logs = relationship("ActivityLog", back_populates="user", foreign_keys="ActivityLog.user_id")
    audit_logs = relationship("AuditLog", back_populates="actor", foreign_keys="AuditLog.actor_id")

    @property
    def roles(self):
        return [ur.role for ur in self.user_roles if ur.role]

    @property
    def role_names(self):
        return [r.name for r in self.roles]

    def has_role(self, role_name: str) -> bool:
        return role_name.upper() in [r.name.upper() for r in self.roles]

    def has_permission(self, permission_name: str) -> bool:
        for role in self.roles:
            for rp in role.role_permissions:
                if rp.permission.name == permission_name:
                    return True
        return False

    def __repr__(self):
        return f"<User {self.email}>"
