from sqlalchemy import Column, String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base, UUIDMixin, TimestampMixin

# Canonical role names
ROLE_ADMIN = "ADMIN"
ROLE_USER = "USER"
ROLE_APPROVER = "APPROVER"
ROLE_PUBLISHER = "PUBLISHER"

# All permissions
PERMISSIONS = {
    # User management (ADMIN)
    "users:create": "Create users",
    "users:edit": "Edit users",
    "users:delete": "Delete users",
    "users:view": "View all users",
    "users:assign_roles": "Assign roles to users",
    "users:toggle_active": "Activate/Deactivate accounts",
    # Article permissions
    "articles:create": "Create/Generate articles",
    "articles:view_own": "View own articles",
    "articles:edit_own": "Edit own articles",
    "articles:submit": "Submit articles for approval",
    "articles:view_pending": "View pending articles",
    "articles:view_approved": "View approved articles",
    "articles:view_all": "View all articles",
    "articles:approve": "Approve articles",
    "articles:reject": "Reject articles",
    "articles:publish": "Publish articles",
    "articles:dispute": "Raise disputes on articles",
    "articles:return_to_approver": "Return articles to approver",
    "articles:comment": "Add comments/feedback to articles",
    # System
    "system:view_audit_logs": "View audit logs",
    "system:view_activity": "View all activity",
    "system:manage_settings": "Manage system settings",
    "system:view_stats": "View system statistics",
    # Knowledge Base Generator
    "kbg:access": "Access KBG features",
    "kbg:source_sync": "Use Source & Sync functionality",
    "kbg:chatbot": "Use chatbot",
    # Notifications
    "notifications:send": "Send status update notifications",
}

ROLE_PERMISSIONS = {
    ROLE_ADMIN: list(PERMISSIONS.keys()),
    ROLE_USER: [
        "articles:create", "articles:view_own", "articles:edit_own",
        "articles:submit", "kbg:access", "kbg:source_sync", "kbg:chatbot",
    ],
    ROLE_APPROVER: [
        "articles:view_pending", "articles:view_approved", "articles:approve",
        "articles:reject", "articles:comment", "notifications:send",
        "articles:edit_own",
    ],
    ROLE_PUBLISHER: [
        "articles:view_approved", "articles:publish", "articles:dispute",
        "articles:return_to_approver",
    ],
}


class Permission(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "permissions"

    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(String(255), nullable=True)
    resource = Column(String(50), nullable=True)  # e.g. "articles", "users"
    action = Column(String(50), nullable=True)     # e.g. "create", "read"

    role_permissions = relationship("RolePermission", back_populates="permission")


class Role(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "roles"

    name = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    is_system = Column(String(5), default="true")  # system roles can't be deleted

    role_permissions = relationship("RolePermission", back_populates="role", cascade="all, delete-orphan")
    user_roles = relationship("UserRole", back_populates="role")

    @property
    def permissions(self):
        return [rp.permission for rp in self.role_permissions if rp.permission]

    def __repr__(self):
        return f"<Role {self.name}>"


class RolePermission(Base, UUIDMixin):
    __tablename__ = "role_permissions"

    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, index=True)
    permission_id = Column(UUID(as_uuid=True), ForeignKey("permissions.id", ondelete="CASCADE"), nullable=False, index=True)

    role = relationship("Role", back_populates="role_permissions")
    permission = relationship("Permission", back_populates="role_permissions")
