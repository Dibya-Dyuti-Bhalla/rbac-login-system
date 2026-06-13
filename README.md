# KBG RBAC Platform — Complete Implementation Guide

## What This Is

A full-stack **Role-Based Access Control (RBAC)** platform for the Knowledge Base Generator. It includes a React + TypeScript frontend, a FastAPI Python backend, and a PostgreSQL database. Four roles are supported — Admin, User, Approver, and Publisher — each with a tailored dashboard and article workflow.

---

## Prerequisites

You need these installed on your machine (check by running each command in a terminal):

```
python --version     → Python 3.12+
node --version       → Node 20+
git --version        → any recent version
```

PostgreSQL runs as a portable zip — no installation required.

---

## One-Time Setup

### Step 1 — Get the code

Download the project zip and extract it to your Desktop (or anywhere you prefer). You should have a folder called `kbg-rbac` containing `backend/` and `frontend/`.

---

### Step 2 — Set up PostgreSQL (database)

Download the PostgreSQL 16/17/18 **zip archive** (not the installer) from:
> https://www.enterprisedb.com/download-postgresql-binaries → Windows x86-64

Extract it to: `C:\Users\YOUR_USERNAME\pgsql`

Open PowerShell and run these **one time only**:

```powershell
# Add postgres to PATH for this session
$env:PATH = "C:\Users\$env:USERNAME\pgsql\pgsql\bin;" + $env:PATH

# Initialise the database storage folder
initdb -D C:\Users\$env:USERNAME\pgdata -U postgres -A trust -E UTF8

# Start the database server
pg_ctl -D C:\Users\$env:USERNAME\pgdata -l C:\Users\$env:USERNAME\postgres.log start

# Create the application database
createdb -U postgres kbg_rbac
```

> **Note:** If the `pgdata` folder already exists, skip `initdb` and go straight to `pg_ctl start`.

---

### Step 3 — Set up the backend

Open PowerShell, navigate to the backend folder:

```powershell
cd C:\Users\$env:USERNAME\Desktop\kbg-rbac\backend
```

Create and activate a Python virtual environment:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

> If you get a script execution policy error, run this first:
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

Install dependencies:

```powershell
pip install -r requirements.txt
pip install bcrypt==4.0.1
```

---

### Step 4 — Seed the database

With the venv still active and Postgres running:

```powershell
python -m app.db.seed
```

Expected output:
```
🌱 Seeding permissions...
🌱 Seeding roles...
🌱 Seeding admin user...
✅ Seed complete. Admin login: admin@kbgplatform.com / Admin@123456
```

---

### Step 5 — Install frontend dependencies

Open a **second PowerShell window**:

```powershell
cd C:\Users\$env:USERNAME\Desktop\kbg-rbac\frontend
npm install
```

This takes 1–3 minutes the first time.

---

## Running the App (Daily Use)

You need **three PowerShell terminals** open. After the first-time setup, this is all you run each day.

### Terminal 1 — Start the database

```powershell
$env:PATH = "C:\Users\$env:USERNAME\pgsql\pgsql\bin;" + $env:PATH
pg_ctl -D C:\Users\$env:USERNAME\pgdata start
```

### Terminal 2 — Start the backend

```powershell
cd C:\Users\$env:USERNAME\Desktop\kbg-rbac\backend
.\venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

You'll see: `✅ KBG RBAC Platform v1.0.0 started`

### Terminal 3 — Start the frontend

```powershell
cd C:\Users\$env:USERNAME\Desktop\kbg-rbac\frontend
npm run dev
```

You'll see: `➜  Local:   http://localhost:3000/`

---

## Access the App

| URL | What it is |
|-----|------------|
| http://localhost:3000 | Main application UI |
| http://localhost:8000/api/v1/docs | API documentation (Swagger) |

---

## Default Login

| Field | Value |
|-------|-------|
| Email | `admin@kbgplatform.com` |
| Password | `Admin@123456` |

---

## Creating Test Users

After logging in as admin, go to **User Management → Create User** to add accounts for each role:

| Role | Suggested email | Password |
|------|----------------|----------|
| USER | user@kbgplatform.com | Test@12345 |
| APPROVER | approver@kbgplatform.com | Test@12345 |
| PUBLISHER | publisher@kbgplatform.com | Test@12345 |

Log out and log in as each role to see their role-specific dashboard.

---

## Article Workflow

```
USER creates article (DRAFT)
  ↓
USER submits → PENDING APPROVAL
  ↓
APPROVER reviews → APPROVED or REJECTED
  ↓
PUBLISHER publishes → PUBLISHED
  (or raises dispute → DISPUTED → back to PENDING APPROVAL)
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, TypeScript, Material UI v6, Redux Toolkit |
| Backend | FastAPI (Python 3.12), Uvicorn ASGI |
| Database | PostgreSQL 16+, SQLAlchemy 2 (async) |
| Auth | JWT (access + refresh tokens), bcrypt password hashing |
| API Docs | Swagger / OpenAPI (auto-generated) |
| Notifications | Microsoft Graph API (email) — configurable |
| Webhooks | HMAC-SHA256 signed event delivery |

---

## Project Structure

```
kbg-rbac/
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/   ← All API routes
│   │   ├── core/               ← Config, JWT security
│   │   ├── db/                 ← Database session, seed script
│   │   ├── middleware/         ← RBAC permission guards
│   │   ├── models/             ← SQLAlchemy database models
│   │   ├── schemas/            ← Pydantic request/response schemas
│   │   ├── services/           ← Email, audit, webhook services
│   │   └── main.py             ← FastAPI application entry point
│   ├── requirements.txt
│   └── .env                    ← Environment configuration
├── frontend/
│   ├── src/
│   │   ├── components/         ← Reusable UI components
│   │   ├── hooks/              ← React hooks (auth, etc.)
│   │   ├── pages/              ← Page components per role
│   │   ├── services/           ← Axios API client
│   │   ├── store/              ← Redux state management
│   │   └── App.tsx             ← Routes and auth guards
│   └── package.json
└── README.md
```

---

## Common Issues

| Problem | Fix |
|---------|-----|
| `initdb` not found | Add Postgres bin to PATH: `$env:PATH = "C:\Users\$env:USERNAME\pgsql\pgsql\bin;" + $env:PATH` |
| `ConnectionRefusedError` on seed | Postgres isn't running — run `pg_ctl start` first |
| Script execution blocked | Run: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` |
| `ModuleNotFoundError` | Venv not activated — run `.\venv\Scripts\Activate.ps1` first |
| Port 8000 in use | Change backend to `--port 8080`, update `frontend/.env` to match |
| `npm install` fails (SSL) | Run: `npm config set strict-ssl false` |
| `pip install` fails (SSL) | Run: `pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt` |

---

## Stopping the App

- Frontend: `Ctrl+C` in Terminal 3
- Backend: `Ctrl+C` in Terminal 2
- Database: `pg_ctl -D C:\Users\$env:USERNAME\pgdata stop` in Terminal 1

---

*Built with FastAPI, React, PostgreSQL · Local development only · No admin privileges required*

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
