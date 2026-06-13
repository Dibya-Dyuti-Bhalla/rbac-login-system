import enum
from sqlalchemy import Column, String, Text, Boolean, ForeignKey, Integer, Enum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from .base import Base, UUIDMixin, TimestampMixin


# ─── Notification ────────────────────────────────────────────────────────────

class NotificationType(str, enum.Enum):
    ARTICLE_SUBMITTED = "ARTICLE_SUBMITTED"
    ARTICLE_APPROVED = "ARTICLE_APPROVED"
    ARTICLE_REJECTED = "ARTICLE_REJECTED"
    ARTICLE_DISPUTED = "ARTICLE_DISPUTED"
    ARTICLE_PUBLISHED = "ARTICLE_PUBLISHED"
    ROLE_ASSIGNED = "ROLE_ASSIGNED"
    ACCOUNT_ACTIVATED = "ACCOUNT_ACTIVATED"
    ACCOUNT_DEACTIVATED = "ACCOUNT_DEACTIVATED"
    SYSTEM = "SYSTEM"


class Notification(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "notifications"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    type = Column(Enum(NotificationType, name="notification_type"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False, nullable=False)
    related_article_id = Column(UUID(as_uuid=True), ForeignKey("articles.id", ondelete="SET NULL"), nullable=True)
    email_sent = Column(Boolean, default=False, nullable=False)
    metadata_ = Column("metadata", JSONB, nullable=True)

    user = relationship("User", back_populates="notifications")
    article = relationship("Article", foreign_keys=[related_article_id])


# ─── Activity Log ─────────────────────────────────────────────────────────────

class ActivityLog(Base, UUIDMixin, TimestampMixin):
    """High-level user activity feed (what the user did)."""
    __tablename__ = "activity_logs"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(String(100), nullable=False, index=True)  # e.g. "article.submitted"
    resource_type = Column(String(50), nullable=True)         # e.g. "article"
    resource_id = Column(UUID(as_uuid=True), nullable=True)
    description = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    metadata_ = Column("metadata", JSONB, nullable=True)

    user = relationship("User", back_populates="activity_logs")


# ─── Audit Log ────────────────────────────────────────────────────────────────

class AuditLog(Base, UUIDMixin, TimestampMixin):
    """Immutable audit trail for compliance (who changed what, before/after)."""
    __tablename__ = "audit_logs"

    actor_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(50), nullable=False, index=True)
    resource_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    old_values = Column(JSONB, nullable=True)
    new_values = Column(JSONB, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    session_id = Column(String(100), nullable=True)

    actor = relationship("User", back_populates="audit_logs")


# ─── Webhooks ─────────────────────────────────────────────────────────────────

class WebhookEndpoint(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "webhook_endpoints"

    url = Column(String(2000), nullable=False)
    secret = Column(String(255), nullable=False)
    description = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    events = Column(JSONB, nullable=False, default=list)  # list of event names
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    deliveries = relationship("WebhookDelivery", back_populates="endpoint", cascade="all, delete-orphan")


class WebhookDelivery(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "webhook_deliveries"

    endpoint_id = Column(UUID(as_uuid=True), ForeignKey("webhook_endpoints.id", ondelete="CASCADE"), nullable=False, index=True)
    event_name = Column(String(100), nullable=False, index=True)
    payload = Column(JSONB, nullable=False)
    status_code = Column(Integer, nullable=True)
    response_body = Column(Text, nullable=True)
    attempts = Column(Integer, default=0, nullable=False)
    is_successful = Column(Boolean, default=False, nullable=False)
    error_message = Column(Text, nullable=True)
    next_retry_at = Column(String(50), nullable=True)

    endpoint = relationship("WebhookEndpoint", back_populates="deliveries")
