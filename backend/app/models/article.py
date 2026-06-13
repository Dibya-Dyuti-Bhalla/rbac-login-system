import enum
from sqlalchemy import Column, String, Text, ForeignKey, Enum, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from .base import Base, UUIDMixin, TimestampMixin


class ArticleStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    DISPUTED = "DISPUTED"
    PUBLISHED = "PUBLISHED"


class Article(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "articles"

    title = Column(String(500), nullable=False, index=True)
    slug = Column(String(600), unique=True, nullable=True, index=True)
    content = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)
    tags = Column(JSONB, nullable=True, default=list)
    category = Column(String(100), nullable=True, index=True)
    status = Column(
        Enum(ArticleStatus, name="article_status"),
        nullable=False,
        default=ArticleStatus.DRAFT,
        index=True,
    )
    version = Column(Integer, default=1, nullable=False)

    # Source metadata (from KBG ingestion)
    source_type = Column(String(50), nullable=True)  # e.g. "incident_ticket", "meeting_notes"
    source_id = Column(String(255), nullable=True)
    source_metadata = Column(JSONB, nullable=True)

    # Workflow actors
    author_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    approver_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    publisher_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # Feedback
    rejection_reason = Column(Text, nullable=True)
    dispute_reason = Column(Text, nullable=True)
    approver_notes = Column(Text, nullable=True)

    # Timestamps for workflow stages
    submitted_at = Column(String(50), nullable=True)
    approved_at = Column(String(50), nullable=True)
    rejected_at = Column(String(50), nullable=True)
    published_at = Column(String(50), nullable=True)

    # External publish targets
    external_url = Column(String(1000), nullable=True)
    external_system = Column(String(100), nullable=True)

    # Relationships
    author = relationship("User", back_populates="articles", foreign_keys=[author_id])
    approver = relationship("User", back_populates="approved_articles", foreign_keys=[approver_id])
    publisher = relationship("User", back_populates="published_articles", foreign_keys=[publisher_id])
    status_history = relationship("ArticleStatusHistory", back_populates="article", cascade="all, delete-orphan", order_by="ArticleStatusHistory.created_at")

    def __repr__(self):
        return f"<Article {self.title[:40]}... [{self.status}]>"


class ArticleStatusHistory(Base, UUIDMixin, TimestampMixin):
    """Immutable audit trail of every article status transition."""
    __tablename__ = "article_status_history"

    article_id = Column(UUID(as_uuid=True), ForeignKey("articles.id", ondelete="CASCADE"), nullable=False, index=True)
    from_status = Column(Enum(ArticleStatus, name="article_status"), nullable=True)
    to_status = Column(Enum(ArticleStatus, name="article_status"), nullable=False)
    changed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    comment = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSONB, nullable=True)

    article = relationship("Article", back_populates="status_history")
    changed_by_user = relationship("User", foreign_keys=[changed_by])
