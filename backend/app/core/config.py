from pydantic_settings import BaseSettings
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings"""

    # App
    APP_NAME: str = "Archive Statistics Dashboard"
    APP_VERSION: str = "1.1.0"
    DEBUG: bool = True

    # API
    API_PREFIX: str = "/api"

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./archive_stats.db"

    # NAS Connection
    NAS_HOST: str = "10.10.100.122"
    NAS_SHARE: str = "docker"
    NAS_PATH: str = "GGPNAs/ARCHIVE"
    NAS_USERNAME: str = "GGP"
    NAS_PASSWORD: str = "!@QW12qw"

    # Local mounted path (Windows network drive or Linux mount)
    NAS_LOCAL_PATH: str = "Z:/GGPNAs/ARCHIVE"  # Change to mounted drive letter

    # Redis (for background tasks)
    REDIS_URL: str = "redis://localhost:6379/0"

    # Email
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAIL_FROM: Optional[str] = None

    # CORS - LAN access enabled
    CORS_ORIGINS: list = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://221.149.191.199",
        "http://221.149.191.199:80",
        "http://221.149.191.199:3000",
    ]
    CORS_ALLOW_ALL: bool = True  # For LAN deployment

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
