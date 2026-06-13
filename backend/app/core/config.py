from pydantic_settings import BaseSettings
from typing import List, Optional
from functools import lru_cache


class Settings(BaseSettings):
    # App
    APP_NAME: str = "KBG RBAC Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    API_V1_STR: str = "/api/v1"

    # Security
    SECRET_KEY: str = "CHANGE_ME_IN_PRODUCTION_USE_SECRETS_MANAGER"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Database
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "kbg_user"
    POSTGRES_PASSWORD: str = "kbg_password"
    POSTGRES_DB: str = "kbg_rbac"

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def SYNC_DATABASE_URL(self) -> str:
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "https://*.ngrok-free.app",
        "https://*.ngrok.io",
    ]

    # Microsoft Graph API
    AZURE_TENANT_ID: str = ""
    AZURE_CLIENT_ID: str = ""
    AZURE_CLIENT_SECRET: str = ""
    AZURE_SENDER_EMAIL: str = ""
    MS_GRAPH_BASE_URL: str = "https://graph.microsoft.com/v1.0"

    # Webhooks
    WEBHOOK_SECRET: str = "CHANGE_ME_WEBHOOK_SECRET"
    WEBHOOK_RETRY_ATTEMPTS: int = 3
    WEBHOOK_RETRY_DELAY_SECONDS: int = 5

    # ngrok (local dev)
    NGROK_AUTH_TOKEN: Optional[str] = None
    NGROK_PUBLIC_URL: Optional[str] = None

    # Redis (for token blacklisting / session management)
    REDIS_URL: str = "redis://localhost:6379/0"

    # Frontend
    FRONTEND_URL: str = "http://localhost:3000"

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
