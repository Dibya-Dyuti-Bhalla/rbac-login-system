"""
Notification Service
====================
Handles both in-app notifications (DB) and email via Microsoft Graph API.

Azure App Registration required:
  - API permission: Mail.Send (Application)
  - Grant admin consent

Environment variables:
  AZURE_TENANT_ID, AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_SENDER_EMAIL
"""
import httpx
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.article import Article
from ..models.user import User
from ..models.notification import Notification, NotificationType
from ..core.config import settings


class MicrosoftGraphEmailService:
    _access_token: Optional[str] = None

    @classmethod
    async def _get_token(cls) -> str:
        """Obtain OAuth2 client_credentials token from Azure AD."""
        url = f"https://login.microsoftonline.com/{settings.AZURE_TENANT_ID}/oauth2/v2.0/token"
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, data={
                "grant_type": "client_credentials",
                "client_id": settings.AZURE_CLIENT_ID,
                "client_secret": settings.AZURE_CLIENT_SECRET,
                "scope": "https://graph.microsoft.com/.default",
            })
            resp.raise_for_status()
            cls._access_token = resp.json()["access_token"]
            return cls._access_token

    @classmethod
    async def send_email(cls, to_email: str, subject: str, html_body: str):
        """Send email via Microsoft Graph API Send Mail endpoint."""
        if not all([settings.AZURE_TENANT_ID, settings.AZURE_CLIENT_ID, settings.AZURE_CLIENT_SECRET]):
            print(f"[Email - MOCK] To: {to_email} | Subject: {subject}")
            return

        token = await cls._get_token()
        url = f"{settings.MS_GRAPH_BASE_URL}/users/{settings.AZURE_SENDER_EMAIL}/sendMail"

        payload = {
            "message": {
                "subject": subject,
                "body": {"contentType": "HTML", "content": html_body},
                "toRecipients": [{"emailAddress": {"address": to_email}}],
                "from": {"emailAddress": {"address": settings.AZURE_SENDER_EMAIL}},
            },
            "saveToSentItems": False,
        }

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                url, json=payload,
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            )
            if resp.status_code != 202:
                print(f"[Email Error] {resp.status_code}: {resp.text}")


def _article_email_html(title: str, status: str, message: str, article_url: str) -> str:
    return f"""
    <html><body style="font-family:Arial,sans-serif;max-width:600px;margin:auto">
      <div style="background:#1a1a2e;padding:20px;border-radius:8px 8px 0 0">
        <h2 style="color:#e2b96f;margin:0">KBG Platform</h2>
      </div>
      <div style="padding:24px;border:1px solid #e2e8f0;border-top:none;border-radius:0 0 8px 8px">
        <h3>Article {status}</h3>
        <p><strong>{title}</strong></p>
        <p>{message}</p>
        <a href="{article_url}" style="background:#4f46e5;color:white;padding:10px 20px;
           border-radius:6px;text-decoration:none;display:inline-block;margin-top:16px">
          View Article
        </a>
      </div>
      <p style="color:#999;font-size:12px;text-align:center;margin-top:16px">
        KBG Platform · Do not reply to this email
      </p>
    </body></html>
    """


class NotificationService:
    @staticmethod
    async def _create_notification(
        db: AsyncSession,
        user: User,
        notification_type: NotificationType,
        title: str,
        message: str,
        article: Optional[Article] = None,
        send_email: bool = True,
    ):
        notif = Notification(
            user_id=user.id,
            type=notification_type,
            title=title,
            message=message,
            related_article_id=article.id if article else None,
        )
        db.add(notif)

        if send_email:
            try:
                article_url = f"{settings.FRONTEND_URL}/articles/{article.id}" if article else settings.FRONTEND_URL
                html = _article_email_html(
                    title=article.title if article else "N/A",
                    status=notification_type.value.replace("_", " ").title(),
                    message=message,
                    article_url=article_url,
                )
                await MicrosoftGraphEmailService.send_email(user.email, title, html)
                notif.email_sent = True
            except Exception as e:
                print(f"[Email send failed] {e}")

    @classmethod
    async def notify_article_submitted(cls, db: AsyncSession, article: Article, author: User):
        # Notify approvers (in production, query for all approver-role users)
        message = f"Article '{article.title}' has been submitted for approval by {author.full_name}."
        await cls._create_notification(
            db, author, NotificationType.ARTICLE_SUBMITTED,
            "Article Submitted for Approval", message, article, send_email=False,
        )

    @classmethod
    async def notify_article_approved(cls, db: AsyncSession, article: Article, approver: User):
        # Fetch author and notify
        message = f"Your article '{article.title}' has been approved and is ready for publishing."
        # In production: load article.author relationship and notify them
        await cls._create_notification(
            db, approver, NotificationType.ARTICLE_APPROVED,
            "Article Approved", message, article,
        )

    @classmethod
    async def notify_article_rejected(cls, db: AsyncSession, article: Article, approver: User):
        message = f"Article '{article.title}' was rejected. Reason: {article.rejection_reason}"
        await cls._create_notification(
            db, approver, NotificationType.ARTICLE_REJECTED,
            "Article Rejected", message, article,
        )

    @classmethod
    async def notify_article_published(cls, db: AsyncSession, article: Article, publisher: User):
        message = f"Article '{article.title}' has been published successfully."
        await cls._create_notification(
            db, publisher, NotificationType.ARTICLE_PUBLISHED,
            "Article Published", message, article,
        )

    @classmethod
    async def notify_account_status(cls, db: AsyncSession, user: User, activated: bool):
        status_str = "activated" if activated else "deactivated"
        notif_type = NotificationType.ACCOUNT_ACTIVATED if activated else NotificationType.ACCOUNT_DEACTIVATED
        await cls._create_notification(
            db, user, notif_type,
            f"Account {status_str.title()}",
            f"Your KBG Platform account has been {status_str}.",
            send_email=True,
        )
