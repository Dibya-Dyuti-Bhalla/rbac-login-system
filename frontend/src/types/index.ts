// ─── Auth ─────────────────────────────────────────────────────────────────────
export type RoleName = 'ADMIN' | 'USER' | 'APPROVER' | 'PUBLISHER';

export interface User {
  id: string;
  email: string;
  username: string;
  full_name: string;
  is_active: boolean;
  is_superuser: boolean;
  department?: string;
  avatar_url?: string;
  created_at: string;
  roles: RoleName[];
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface LoginRequest {
  email: string;
  password: string;
}

// ─── Articles ─────────────────────────────────────────────────────────────────
export type ArticleStatus =
  | 'DRAFT'
  | 'PENDING_APPROVAL'
  | 'APPROVED'
  | 'REJECTED'
  | 'DISPUTED'
  | 'PUBLISHED';

export interface Article {
  id: string;
  title: string;
  slug?: string;
  summary?: string;
  content?: string;
  status: ArticleStatus;
  category?: string;
  tags?: string[];
  version: number;
  author_id: string;
  approver_id?: string;
  publisher_id?: string;
  rejection_reason?: string;
  dispute_reason?: string;
  approver_notes?: string;
  submitted_at?: string;
  approved_at?: string;
  published_at?: string;
  created_at: string;
  updated_at: string;
}

export interface ArticleStatusHistory {
  id: string;
  from_status?: ArticleStatus;
  to_status: ArticleStatus;
  comment?: string;
  created_at: string;
}

export interface ArticleCreate {
  title: string;
  content: string;
  summary?: string;
  tags?: string[];
  category?: string;
}

// ─── Pagination ───────────────────────────────────────────────────────────────
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

// ─── Notifications ────────────────────────────────────────────────────────────
export type NotificationType =
  | 'ARTICLE_SUBMITTED' | 'ARTICLE_APPROVED' | 'ARTICLE_REJECTED'
  | 'ARTICLE_DISPUTED' | 'ARTICLE_PUBLISHED'
  | 'ROLE_ASSIGNED' | 'ACCOUNT_ACTIVATED' | 'ACCOUNT_DEACTIVATED' | 'SYSTEM';

export interface Notification {
  id: string;
  type: NotificationType;
  title: string;
  message: string;
  is_read: boolean;
  related_article_id?: string;
  created_at: string;
}

export interface NotificationsResponse {
  items: Notification[];
  total: number;
  unread_count: number;
}

// ─── Admin ────────────────────────────────────────────────────────────────────
export interface PlatformStats {
  users: { total: number; active: number; inactive: number };
  articles: { total: number; by_status: Record<ArticleStatus, number> };
}

export interface AuditLogEntry {
  id: string;
  actor_id?: string;
  action: string;
  resource_type: string;
  resource_id?: string;
  old_values?: Record<string, unknown>;
  new_values?: Record<string, unknown>;
  ip_address?: string;
  created_at: string;
}

export interface Role {
  id: string;
  name: RoleName;
  description?: string;
  permissions: Permission[];
}

export interface Permission {
  id: string;
  name: string;
  description?: string;
  resource?: string;
  action?: string;
}

// ─── API Error ────────────────────────────────────────────────────────────────
export interface ApiError {
  detail: string;
  errors?: { field: string; message: string }[];
}
