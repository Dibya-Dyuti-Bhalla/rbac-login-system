"""
Webhook Service
===============
Emits signed HTTP POST events to registered webhook endpoints.

Signature: X-KBG-Signature = HMAC-SHA256(secret, payload_json)

Retry strategy:
  - Attempt 1: immediate
  - Attempt 2: +5s
  - Attempt 3: +25s  (exponential back-off: delay * 5)
"""
import hmac
import hashlib
import json
import asyncio
import httpx
from datetime import datetime, timezone
from uuid import UUID
from typing import Any

from ..core.config import settings


class WebhookService:
    # In production this would use a task queue (Celery/ARQ)

    @staticmethod
    def _sign_payload(secret: str, payload: dict) -> str:
        body = json.dumps(payload, default=str).encode()
        return hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()

    @staticmethod
    def _build_payload(event_name: str, resource: Any) -> dict:
        return {
            "event": event_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "id": str(resource.id),
                "title": getattr(resource, "title", None),
                "status": getattr(resource, "status", None),
                "author_id": str(getattr(resource, "author_id", "") or ""),
                "updated_at": str(getattr(resource, "updated_at", "")),
            },
        }

    @classmethod
    async def emit(cls, event_name: str, resource: Any):
        """Fire-and-forget webhook emission. In production: push to task queue."""
        payload = cls._build_payload(event_name, resource)
        asyncio.create_task(cls._deliver_all(event_name, payload))

    @classmethod
    async def _deliver_all(cls, event_name: str, payload: dict):
        """
        In production: load active endpoints from DB that subscribe to event_name.
        Here we show the delivery logic structure.
        """
        # endpoints = await db.execute(select(WebhookEndpoint).where(...))
        # for endpoint in endpoints:
        #     await cls._deliver_with_retry(endpoint.url, endpoint.secret, payload)
        pass

    @classmethod
    async def _deliver_with_retry(
        cls, url: str, secret: str, payload: dict, max_attempts: int = 3
    ) -> bool:
        signature = cls._sign_payload(secret, payload)
        headers = {
            "Content-Type": "application/json",
            "X-KBG-Signature": signature,
            "X-KBG-Event": payload.get("event", ""),
            "User-Agent": "KBG-Webhook/1.0",
        }
        body = json.dumps(payload, default=str)
        delay = settings.WEBHOOK_RETRY_DELAY_SECONDS

        for attempt in range(1, max_attempts + 1):
            try:
                async with httpx.AsyncClient(timeout=10) as client:
                    resp = await client.post(url, content=body, headers=headers)
                    if 200 <= resp.status_code < 300:
                        print(f"[Webhook] ✅ Delivered to {url} (attempt {attempt})")
                        return True
                    else:
                        print(f"[Webhook] ⚠️  {url} returned {resp.status_code} (attempt {attempt})")
            except Exception as e:
                print(f"[Webhook] ❌ Error delivering to {url}: {e} (attempt {attempt})")

            if attempt < max_attempts:
                await asyncio.sleep(delay)
                delay *= 5  # exponential back-off

        return False
