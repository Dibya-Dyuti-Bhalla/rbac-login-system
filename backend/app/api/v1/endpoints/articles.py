from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from uuid import UUID
from typing import Optional
from datetime import datetime, timezone
import re

from ....db.session import get_db
from ....models.article import Article, ArticleStatus, ArticleStatusHistory
from ....models.user import User
from ....schemas.schemas import (
    ArticleCreate, ArticleUpdate, ArticleOut,
    ArticleStatusTransition, ArticleStatusHistoryOut, PaginatedResponse,
)
from ....middleware.rbac import get_current_user, require_roles, require_permission
from ....services.audit_service import AuditService
from ....services.notification_service import NotificationService
from ....services.webhook_service import WebhookService

router = APIRouter(prefix="/articles", tags=["Articles"])


def _slugify(title: str) -> str:
    slug = re.sub(r"[^\w\s-]", "", title.lower())
    slug = re.sub(r"[\s_-]+", "-", slug).strip("-")
    return slug[:200]


async def _get_article_or_404(db: AsyncSession, article_id: UUID) -> Article:
    result = await db.execute(
        select(Article)
        .where(Article.id == article_id)
        .options(selectinload(Article.status_history))
    )
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article


async def _record_transition(
    db: AsyncSession,
    article: Article,
    from_status: ArticleStatus,
    to_status: ArticleStatus,
    actor: User,
    comment: Optional[str] = None,
):
    history = ArticleStatusHistory(
        article_id=article.id,
        from_status=from_status,
        to_status=to_status,
        changed_by=actor.id,
        comment=comment,
    )
    db.add(history)
    article.status = to_status
    await AuditService.log(
        db, actor_id=actor.id,
        action=f"article.{to_status.lower()}",
        resource_type="article", resource_id=article.id,
        old_values={"status": from_status.value},
        new_values={"status": to_status.value, "comment": comment},
    )


# ─── CRUD ─────────────────────────────────────────────────────────────────────

@router.post("", response_model=ArticleOut, status_code=status.HTTP_201_CREATED)
async def create_article(
    body: ArticleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("articles:create")),
):
    slug = _slugify(body.title)
    # Ensure slug uniqueness
    result = await db.execute(select(Article).where(Article.slug == slug))
    if result.scalar_one_or_none():
        slug = f"{slug}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"

    article = Article(
        title=body.title,
        slug=slug,
        content=body.content,
        summary=body.summary,
        tags=body.tags,
        category=body.category,
        source_type=body.source_type,
        source_id=body.source_id,
        author_id=current_user.id,
        status=ArticleStatus.DRAFT,
    )
    db.add(article)
    await db.flush()

    db.add(ArticleStatusHistory(
        article_id=article.id,
        from_status=None,
        to_status=ArticleStatus.DRAFT,
        changed_by=current_user.id,
        comment="Article created",
    ))
    await AuditService.log(
        db, actor_id=current_user.id, action="article.created",
        resource_type="article", resource_id=article.id,
        new_values={"title": article.title},
    )
    return article


@router.get("", response_model=PaginatedResponse)
async def list_articles(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    category: Optional[str] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Article)

    # Role-based visibility
    if current_user.has_role("ADMIN"):
        pass  # see all
    elif current_user.has_role("APPROVER"):
        query = query.where(Article.status.in_([
            ArticleStatus.PENDING_APPROVAL, ArticleStatus.APPROVED,
            ArticleStatus.REJECTED, ArticleStatus.DISPUTED,
        ]))
    elif current_user.has_role("PUBLISHER"):
        query = query.where(Article.status.in_([
            ArticleStatus.APPROVED, ArticleStatus.DISPUTED, ArticleStatus.PUBLISHED,
        ]))
    else:  # USER - own articles only
        query = query.where(Article.author_id == current_user.id)

    if status:
        query = query.where(Article.status == status.upper())
    if category:
        query = query.where(Article.category == category)
    if search:
        query = query.where(Article.title.ilike(f"%{search}%"))

    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar()

    query = query.offset((page - 1) * page_size).limit(page_size).order_by(Article.updated_at.desc())
    result = await db.execute(query)
    articles = result.scalars().all()

    return PaginatedResponse(
        items=[ArticleOut.model_validate(a) for a in articles],
        total=total, page=page, page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    )


@router.get("/{article_id}", response_model=ArticleOut)
async def get_article(
    article_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    article = await _get_article_or_404(db, article_id)
    # Ownership check for plain users
    if (not current_user.has_role("ADMIN")
            and not current_user.has_role("APPROVER")
            and not current_user.has_role("PUBLISHER")
            and article.author_id != current_user.id):
        raise HTTPException(status_code=403, detail="Access denied")
    return article


@router.patch("/{article_id}", response_model=ArticleOut)
async def update_article(
    article_id: UUID,
    body: ArticleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    article = await _get_article_or_404(db, article_id)

    if article.author_id != current_user.id and not current_user.has_role("ADMIN"):
        raise HTTPException(status_code=403, detail="Only the author can edit this article")
    if article.status not in (ArticleStatus.DRAFT, ArticleStatus.REJECTED):
        raise HTTPException(status_code=400, detail="Article can only be edited in DRAFT or REJECTED state")

    update_data = body.model_dump(exclude_unset=True)
    old_values = {k: getattr(article, k) for k in update_data}
    for key, value in update_data.items():
        setattr(article, key, value)
    article.version += 1

    await AuditService.log(
        db, actor_id=current_user.id, action="article.updated",
        resource_type="article", resource_id=article_id,
        old_values=old_values, new_values=update_data,
    )
    await db.flush()
    return article


@router.delete("/{article_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_article(
    article_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    article = await _get_article_or_404(db, article_id)
    if article.author_id != current_user.id and not current_user.has_role("ADMIN"):
        raise HTTPException(status_code=403, detail="Access denied")
    if article.status == ArticleStatus.PUBLISHED:
        raise HTTPException(status_code=400, detail="Published articles cannot be deleted")
    await db.delete(article)


@router.get("/{article_id}/history", response_model=list[ArticleStatusHistoryOut])
async def get_article_history(
    article_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    article = await _get_article_or_404(db, article_id)
    return article.status_history


# ─── Workflow Transitions ─────────────────────────────────────────────────────

@router.post("/{article_id}/submit", response_model=ArticleOut)
async def submit_for_approval(
    article_id: UUID,
    body: ArticleStatusTransition = ArticleStatusTransition(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("articles:submit")),
):
    article = await _get_article_or_404(db, article_id)
    if article.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the author can submit")
    if article.status not in (ArticleStatus.DRAFT, ArticleStatus.REJECTED):
        raise HTTPException(status_code=400, detail=f"Cannot submit from status: {article.status}")

    old_status = article.status
    article.submitted_at = datetime.now(timezone.utc).isoformat()
    await _record_transition(db, article, old_status, ArticleStatus.PENDING_APPROVAL, current_user, body.comment)
    await NotificationService.notify_article_submitted(db, article, current_user)
    await WebhookService.emit("article.submitted", article)
    await db.flush()
    return article


@router.post("/{article_id}/approve", response_model=ArticleOut)
async def approve_article(
    article_id: UUID,
    body: ArticleStatusTransition = ArticleStatusTransition(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("articles:approve")),
):
    article = await _get_article_or_404(db, article_id)
    if article.status != ArticleStatus.PENDING_APPROVAL:
        raise HTTPException(status_code=400, detail="Article is not pending approval")

    article.approver_id = current_user.id
    article.approved_at = datetime.now(timezone.utc).isoformat()
    article.approver_notes = body.comment
    await _record_transition(db, article, ArticleStatus.PENDING_APPROVAL, ArticleStatus.APPROVED, current_user, body.comment)
    await NotificationService.notify_article_approved(db, article, current_user)
    await WebhookService.emit("article.approved", article)
    await db.flush()
    return article


@router.post("/{article_id}/reject", response_model=ArticleOut)
async def reject_article(
    article_id: UUID,
    body: ArticleStatusTransition,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("articles:reject")),
):
    article = await _get_article_or_404(db, article_id)
    if article.status != ArticleStatus.PENDING_APPROVAL:
        raise HTTPException(status_code=400, detail="Article is not pending approval")
    if not body.reason:
        raise HTTPException(status_code=400, detail="Rejection reason is required")

    article.approver_id = current_user.id
    article.rejection_reason = body.reason
    article.rejected_at = datetime.now(timezone.utc).isoformat()
    await _record_transition(db, article, ArticleStatus.PENDING_APPROVAL, ArticleStatus.REJECTED, current_user, body.reason)
    await NotificationService.notify_article_rejected(db, article, current_user)
    await WebhookService.emit("article.rejected", article)
    await db.flush()
    return article


@router.post("/{article_id}/publish", response_model=ArticleOut)
async def publish_article(
    article_id: UUID,
    body: ArticleStatusTransition = ArticleStatusTransition(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("articles:publish")),
):
    article = await _get_article_or_404(db, article_id)
    if article.status != ArticleStatus.APPROVED:
        raise HTTPException(status_code=400, detail="Only approved articles can be published")

    article.publisher_id = current_user.id
    article.published_at = datetime.now(timezone.utc).isoformat()
    await _record_transition(db, article, ArticleStatus.APPROVED, ArticleStatus.PUBLISHED, current_user, body.comment)
    await NotificationService.notify_article_published(db, article, current_user)
    await WebhookService.emit("article.published", article)
    await db.flush()
    return article


@router.post("/{article_id}/dispute", response_model=ArticleOut)
async def dispute_article(
    article_id: UUID,
    body: ArticleStatusTransition,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("articles:dispute")),
):
    article = await _get_article_or_404(db, article_id)
    if article.status != ArticleStatus.APPROVED:
        raise HTTPException(status_code=400, detail="Only approved articles can be disputed")
    if not body.reason:
        raise HTTPException(status_code=400, detail="Dispute reason is required")

    article.dispute_reason = body.reason
    await _record_transition(db, article, ArticleStatus.APPROVED, ArticleStatus.DISPUTED, current_user, body.reason)
    await WebhookService.emit("article.disputed", article)
    await db.flush()
    return article


@router.post("/{article_id}/return-to-approver", response_model=ArticleOut)
async def return_to_approver(
    article_id: UUID,
    body: ArticleStatusTransition,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("articles:return_to_approver")),
):
    article = await _get_article_or_404(db, article_id)
    if article.status != ArticleStatus.DISPUTED:
        raise HTTPException(status_code=400, detail="Only disputed articles can be returned")

    await _record_transition(db, article, ArticleStatus.DISPUTED, ArticleStatus.PENDING_APPROVAL, current_user, body.comment)
    await db.flush()
    return article
