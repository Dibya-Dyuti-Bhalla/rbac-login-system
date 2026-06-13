from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List
from uuid import UUID
from datetime import datetime
import re


# ─── Role & Permission ────────────────────────────────────────────────────────

class PermissionOut(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    resource: Optional[str]
    action: Optional[str]
    model_config = {"from_attributes": True}


class RoleOut(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    permissions: List[PermissionOut] = []
    model_config = {"from_attributes": True}

    @classmethod
    def from_role(cls, role):
        return cls(
            id=role.id,
            name=role.name,
            description=role.description,
            permissions=[PermissionOut.model_validate(rp.permission) for rp in role.role_permissions if rp.permission],
        )


# ─── User ─────────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    email: str
    username: str
    full_name: str
    password: str
    department: Optional[str] = None
    role_names: List[str] = ["USER"]

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Must contain uppercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Must contain digit")
        return v


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    department: Optional[str] = None
    avatar_url: Optional[str] = None
    is_active: Optional[bool] = None


class UserOut(BaseModel):
    id: UUID
    email: str
    username: str
    full_name: str
    is_active: bool
    is_superuser: bool
    department: Optional[str]
    avatar_url: Optional[str]
    created_at: datetime
    roles: List[str] = []
    model_config = {"from_attributes": True}

    @classmethod
    def from_user(cls, user):
        return cls(
            id=user.id,
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            department=user.department,
            avatar_url=user.avatar_url,
            created_at=user.created_at,
            roles=user.role_names,
        )


class AssignRolesRequest(BaseModel):
    role_names: List[str]


# ─── Article ──────────────────────────────────────────────────────────────────

class ArticleCreate(BaseModel):
    title: str
    content: str
    summary: Optional[str] = None
    tags: Optional[List[str]] = []
    category: Optional[str] = None
    source_type: Optional[str] = None
    source_id: Optional[str] = None


class ArticleUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    summary: Optional[str] = None
    tags: Optional[List[str]] = None
    category: Optional[str] = None


class ArticleStatusTransition(BaseModel):
    comment: Optional[str] = None
    reason: Optional[str] = None  # for rejection/dispute


class ArticleOut(BaseModel):
    id: UUID
    title: str
    slug: Optional[str]
    summary: Optional[str]
    status: str
    category: Optional[str]
    tags: Optional[List[str]]
    version: int
    author_id: UUID
    approver_id: Optional[UUID]
    publisher_id: Optional[UUID]
    rejection_reason: Optional[str]
    dispute_reason: Optional[str]
    approver_notes: Optional[str]
    submitted_at: Optional[str]
    approved_at: Optional[str]
    published_at: Optional[str]
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class ArticleStatusHistoryOut(BaseModel):
    id: UUID
    from_status: Optional[str]
    to_status: str
    comment: Optional[str]
    created_at: datetime
    model_config = {"from_attributes": True}


# ─── Pagination ───────────────────────────────────────────────────────────────

class PaginatedResponse(BaseModel):
    items: list
    total: int
    page: int
    page_size: int
    pages: int