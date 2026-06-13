# KBG RBAC Platform — Complete Implementation Guide

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                             │
│   React 18 + TypeScript + MUI v6 + Redux Toolkit               │
│   Role-based UI: Admin / User / Approver / Publisher           │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTPS / JWT Bearer
┌────────────────────────────▼────────────────────────────────────┐
│                       API GATEWAY                               │
│   FastAPI (Python 3.12)  ·  Uvicorn ASGI                       │
│   RBAC Middleware  ·  JWT Auth  ·  OpenAPI/Swagger docs         │
└───────┬───────────────────┬────────────────┬────────────────────┘
        │                   │                │
┌───────▼──────┐  ┌─────────▼──────┐ ┌──────▼───────────────────┐
│  PostgreSQL  │  │     Redis      │ │  Microsoft Graph API      │
│  SQLAlchemy  │  │  Token store / │ │  OAuth2 Email (SMTP-free) │
│  Alembic     │  │  cache         │ │  Azure App Registration   │
└──────────────┘  └────────────────┘ └──────────────────────────┘
        │
┌───────▼──────────────────────────────────────────────────────────┐
│                    ASYNC SERVICES                                │
│  NotificationService  ·  WebhookService  ·  AuditService        │
└──────────────────────────────────────────────────────────────────┘
```

---

## Database ER Diagram

```
users
├── id (UUID PK)
├── email (UNIQUE)
├── username (UNIQUE)
├── full_name
├── hashed_password
├── is_active
├── is_superuser
├── department
└── last_login_at

roles
├── id (UUID PK)
├── name (UNIQUE)  ← ADMIN | USER | APPROVER | PUBLISHER
├── description
└── is_system

permissions
├── id (UUID PK)
├── name (UNIQUE)  ← "articles:approve"
├── description
├── resource       ← "articles"
└── action         ← "approve"

role_permissions (junction)
├── role_id → roles.id
└── permission_id → permissions.id

user_roles (junction)
├── user_id → users.id
├── role_id → roles.id
├── assigned_at
└── assigned_by → users.id

articles
├── id (UUID PK)
├── title
├── slug (UNIQUE)
├── content
├── summary
├── tags (JSONB)
├── category
├── status (ENUM: DRAFT|PENDING_APPROVAL|APPROVED|REJECTED|DISPUTED|PUBLISHED)
├── version
├── source_type / source_id / source_metadata (JSONB)
├── author_id → users.id
├── approver_id → users.id
├── publisher_id → users.id
├── rejection_reason
├── dispute_reason
└── submitted_at / approved_at / published_at

article_status_history
├── id (UUID PK)
├── article_id → articles.id
├── from_status (ENUM)
├── to_status (ENUM)
├── changed_by → users.id
└── comment

notifications
├── id (UUID PK)
├── user_id → users.id
├── type (ENUM)
├── title / message
├── is_read
├── related_article_id → articles.id
└── email_sent

activity_logs
├── id (UUID PK)
├── user_id → users.id
├── action
├── resource_type / resource_id
├── description
└── ip_address

audit_logs
├── id (UUID PK)
├── actor_id → users.id
├── action
├── resource_type / resource_id
├── old_values (JSONB)
├── new_values (JSONB)
└── ip_address

webhook_endpoints
├── id (UUID PK)
├── url / secret / description
├── is_active
└── events (JSONB)  ← ["article.approved", "article.published"]

webhook_deliveries
├── id (UUID PK)
├── endpoint_id → webhook_endpoints.id
├── event_name / payload (JSONB)
├── status_code / attempts / is_successful
└── next_retry_at
```

---

## Article Workflow State Machine

```
                    ┌─────────┐
         CREATE     │  DRAFT  │
         ──────────►│         │
                    └────┬────┘
                         │ submit (USER)
                         ▼
               ┌──────────────────┐
               │ PENDING_APPROVAL │◄───── return-to-approver (PUBLISHER)
               └────────┬─────────┘
              ┌──────────┴──────────┐
    approve   │                     │  reject
  (APPROVER)  │                     │ (APPROVER)
              ▼                     ▼
         ┌──────────┐         ┌──────────┐
         │ APPROVED │         │ REJECTED │──► (USER edits & re-submits)
         └────┬─────┘         └──────────┘
    ┌─────────┴──────────┐
    │ publish            │ dispute
    │ (PUBLISHER)        │ (PUBLISHER)
    ▼                    ▼
┌───────────┐       ┌──────────┐
│ PUBLISHED │       │ DISPUTED │──► return-to-approver ──► PENDING_APPROVAL
└───────────┘       └──────────┘
```

---

## Role Permissions Matrix

| Permission                | ADMIN | USER | APPROVER | PUBLISHER |
|---------------------------|:-----:|:----:|:--------:|:---------:|
| users:create              |  ✓   |      |          |           |
| users:edit                |  ✓   |      |          |           |
| users:delete              |  ✓   |      |          |           |
| users:assign_roles        |  ✓   |      |          |           |
| users:toggle_active       |  ✓   |      |          |           |
| articles:create           |  ✓   |  ✓  |          |           |
| articles:view_own         |  ✓   |  ✓  |          |           |
| articles:edit_own         |  ✓   |  ✓  |    ✓    |           |
| articles:submit           |  ✓   |  ✓  |          |           |
| articles:view_pending     |  ✓   |      |    ✓    |           |
| articles:view_approved    |  ✓   |      |    ✓    |    ✓     |
| articles:approve          |  ✓   |      |    ✓    |           |
| articles:reject           |  ✓   |      |    ✓    |           |
| articles:publish          |  ✓   |      |          |    ✓     |
| articles:dispute          |  ✓   |      |          |    ✓     |
| articles:return_approver  |  ✓   |      |          |    ✓     |
| kbg:access                |  ✓   |  ✓  |          |           |
| kbg:chatbot               |  ✓   |  ✓  |          |           |
| system:view_audit_logs    |  ✓   |      |          |           |
| system:view_stats         |  ✓   |      |          |           |

---

## Folder Structure

```
kbg-rbac/
├── backend/
│   ├── app/
│   │   ├── api/v1/
│   │   │   ├── __init__.py          # Router aggregator
│   │   │   └── endpoints/
│   │   │       ├── auth.py          # Login, logout, refresh, /me
│   │   │       ├── users.py         # CRUD + role assignment
│   │   │       ├── articles.py      # Full workflow endpoints
│   │   │       ├── admin.py         # Stats, audit logs, activity
│   │   │       └── notifications.py # In-app notifications + roles
│   │   ├── core/
│   │   │   ├── config.py            # Pydantic settings
│   │   │   └── security.py          # JWT, bcrypt utilities
│   │   ├── db/
│   │   │   ├── session.py           # Async SQLAlchemy engine
│   │   │   └── seed.py              # Initial roles, perms, admin
│   │   ├── middleware/
│   │   │   └── rbac.py              # Dependency injection RBAC guards
│   │   ├── models/
│   │   │   ├── base.py              # DeclarativeBase, mixins
│   │   │   ├── user.py              # User model
│   │   │   ├── role.py              # Role, Permission, RolePermission
│   │   │   ├── user_role.py         # UserRole junction
│   │   │   ├── article.py           # Article + StatusHistory
│   │   │   └── notification.py      # Notif, ActivityLog, AuditLog, Webhook
│   │   ├── schemas/
│   │   │   ├── auth.py              # Login, token schemas
│   │   │   └── schemas.py           # All Pydantic I/O schemas
│   │   ├── services/
│   │   │   ├── audit_service.py     # AuditLog + ActivityLog writers
│   │   │   ├── notification_service.py  # In-app + MS Graph email
│   │   │   └── webhook_service.py   # HMAC-signed webhook delivery
│   │   └── main.py                  # FastAPI app, CORS, lifespan
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   └── layout/
│   │   │       └── AppLayout.tsx    # Sidebar + AppBar + role-nav
│   │   ├── hooks/
│   │   │   └── useAuth.ts           # useAuth, hasRole helpers
│   │   ├── pages/
│   │   │   ├── LoginPage.tsx
│   │   │   ├── DashboardPage.tsx    # Role-aware dashboard
│   │   │   ├── ArticlesPage.tsx     # Full workflow table + actions
│   │   │   └── admin/
│   │   │       ├── UserManagementPage.tsx
│   │   │       └── AuditLogsPage.tsx
│   │   ├── services/
│   │   │   └── api.ts               # Axios + auto-refresh interceptor
│   │   ├── store/
│   │   │   └── index.ts             # Redux slices: auth, articles, notif
│   │   ├── theme/
│   │   │   └── index.ts             # MUI dark theme + status colors
│   │   ├── types/
│   │   │   └── index.ts             # TypeScript interfaces
│   │   ├── App.tsx                  # Router + RequireAuth guard
│   │   └── main.tsx
│   ├── Dockerfile
│   ├── vite.config.ts
│   └── package.json
│
├── docker/
│   └── docker-compose.yml
│
├── scripts/
│   └── ngrok_dev.py                 # Tunnel setup for local dev
│
└── README.md
```

---

## API Endpoints Reference

### Authentication
| Method | Path                    | Auth | Description               |
|--------|-------------------------|------|---------------------------|
| POST   | /auth/login             | —    | Login, returns JWT pair   |
| POST   | /auth/refresh           | —    | Refresh access token      |
| POST   | /auth/logout            | ✓    | Logout + audit            |
| GET    | /auth/me                | ✓    | Current user profile      |
| POST   | /auth/change-password   | ✓    | Change own password       |

### Users (ADMIN)
| Method | Path                        | Description               |
|--------|-----------------------------|---------------------------|
| GET    | /users                      | List with pagination      |
| POST   | /users                      | Create user + assign role |
| GET    | /users/{id}                 | Get user detail           |
| PATCH  | /users/{id}                 | Update user               |
| DELETE | /users/{id}                 | Delete user               |
| PUT    | /users/{id}/roles           | Replace roles             |
| POST   | /users/{id}/toggle-active   | Activate/Deactivate       |

### Articles (Role-filtered)
| Method | Path                              | Description                  |
|--------|-----------------------------------|------------------------------|
| POST   | /articles                         | Create (USER)                |
| GET    | /articles                         | List (role-filtered)         |
| GET    | /articles/{id}                    | Detail                       |
| PATCH  | /articles/{id}                    | Edit (DRAFT/REJECTED only)   |
| DELETE | /articles/{id}                    | Delete (not PUBLISHED)       |
| GET    | /articles/{id}/history            | Status history               |
| POST   | /articles/{id}/submit             | DRAFT → PENDING (USER)       |
| POST   | /articles/{id}/approve            | PENDING → APPROVED (APPROVER)|
| POST   | /articles/{id}/reject             | PENDING → REJECTED (APPROVER)|
| POST   | /articles/{id}/publish            | APPROVED → PUBLISHED (PUB)   |
| POST   | /articles/{id}/dispute            | APPROVED → DISPUTED (PUB)    |
| POST   | /articles/{id}/return-to-approver | DISPUTED → PENDING (PUB)     |

### Admin
| Method | Path                  | Description               |
|--------|-----------------------|---------------------------|
| GET    | /admin/stats          | Platform statistics       |
| GET    | /admin/audit-logs     | Immutable audit trail     |
| GET    | /admin/activity       | Activity feed             |

### Notifications
| Method | Path                              | Description               |
|--------|-----------------------------------|---------------------------|
| GET    | /notifications                    | User's notifications      |
| POST   | /notifications/{id}/read          | Mark one read             |
| POST   | /notifications/read-all           | Mark all read             |

---

## Webhook Event Payloads

```json
{
  "event": "article.approved",
  "timestamp": "2025-01-15T10:30:00Z",
  "data": {
    "id": "uuid",
    "title": "Article Title",
    "status": "APPROVED",
    "author_id": "uuid",
    "updated_at": "2025-01-15T10:30:00Z"
  }
}
```

**Supported events:** `article.submitted`, `article.approved`, `article.rejected`,
`article.published`, `article.disputed`

**Signature verification (receiver):**
```python
import hmac, hashlib, json

def verify_webhook(secret: str, payload: bytes, signature: str) -> bool:
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)
```

---

## Microsoft Graph API — Azure Setup

1. **Azure Portal** → App Registrations → New Registration
2. **API Permissions** → Add `Mail.Send` (Application) → Grant admin consent
3. **Certificates & Secrets** → New client secret → copy value
4. Set env vars:
   ```
   AZURE_TENANT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
   AZURE_CLIENT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
   AZURE_CLIENT_SECRET=your-secret
   AZURE_SENDER_EMAIL=notifications@yourdomain.com
   ```

The `MicrosoftGraphEmailService` acquires a token via `client_credentials` flow
(no user interaction) and sends via `POST /users/{sender}/sendMail`.

---

## Step-by-Step Implementation Roadmap

### Phase 1 — Foundation (Week 1)
- [ ] `docker-compose up` PostgreSQL + Redis
- [ ] `cp backend/.env.example backend/.env` → fill in values
- [ ] `pip install -r requirements.txt`
- [ ] `python -m app.db.seed` (creates tables + admin user)
- [ ] `uvicorn app.main:app --reload`
- [ ] Verify Swagger at `http://localhost:8000/api/v1/docs`

### Phase 2 — Backend Auth & RBAC (Week 1-2)
- [ ] Test login at `/auth/login` → get tokens
- [ ] Verify RBAC guards block wrong roles
- [ ] Test article workflow end-to-end via Swagger
- [ ] Add Alembic for migration management
- [ ] Add Redis token blacklist for logout

### Phase 3 — Frontend (Week 2-3)
- [ ] `cd frontend && npm install && npm run dev`
- [ ] Login as admin, verify dashboard
- [ ] Create test users with each role
- [ ] Test role-filtered navigation
- [ ] Complete article CRUD and workflow actions

### Phase 4 — Integrations (Week 3-4)
- [ ] Register Azure app, set env vars
- [ ] Test email via `NotificationService`
- [ ] Register webhook endpoint in DB
- [ ] Test delivery with ngrok: `python scripts/ngrok_dev.py`
- [ ] Verify HMAC signature on receiver

### Phase 5 — Hardening (Week 4-5)
- [ ] Rate limiting (slowapi)
- [ ] Input sanitization
- [ ] HTTPS / TLS in production
- [ ] Secrets via vault (AWS Secrets Manager / Azure Key Vault)
- [ ] Redis token blacklist on logout
- [ ] Database connection pooling tuning
- [ ] Add Celery + Redis for async webhook delivery queue
- [ ] Write integration tests
- [ ] Add monitoring (Prometheus + Grafana or Datadog)

---

## Security Best Practices

| Category         | Implementation                                          |
|------------------|---------------------------------------------------------|
| Passwords        | bcrypt with cost factor 12                              |
| Tokens           | Short-lived JWT (30m access + 7d refresh)              |
| Token Revocation | Redis blacklist on logout                               |
| Permissions      | Least-privilege per role, checked server-side           |
| Audit Trail      | Immutable append-only AuditLog table                   |
| SQL Injection    | SQLAlchemy parameterized queries (no raw SQL)           |
| CORS             | Strict origin allowlist                                 |
| Webhook Auth     | HMAC-SHA256 signed payloads                             |
| Sensitive Config | Environment variables, never hardcoded                  |
| HTTPS            | TLS termination at load balancer / nginx                |
| Rate Limiting    | Per-IP via slowapi or API gateway                       |
| File Uploads     | Validate type + size, scan for malware                  |

---

## Default Credentials (Development Only)

| Email             | Password       | Role  |
|-------------------|----------------|-------|
| admin@kbgplatform.com   | Admin@123456   | ADMIN |

**Change immediately in production.**
