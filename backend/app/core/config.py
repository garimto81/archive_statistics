from pydantic_settings import BaseSettings
from typing import Optional, List
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings"""

    # App
    APP_NAME: str = "Archive Statistics Dashboard"
    APP_VERSION: str = "1.2.0"
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

    # Google Sheets Sync
    GOOGLE_SERVICE_ACCOUNT_FILE: str = "service_account_key.json"
    SHEETS_SYNC_ENABLED: bool = True
    SHEETS_SYNC_INTERVAL_MINUTES: int = 30

    # Work Status Sheet (Sheet 3)
    WORK_STATUS_SHEET_URL: str = "https://docs.google.com/spreadsheets/d/1xuN4_1mQME_SVwnI7445JuLd8K7tRS9HDNYYJi2fm2k"

    # Hand Analysis Sheet (WSOP Circuit LA - 8 worksheets)
    HAND_ANALYSIS_SYNC_ENABLED: bool = True
    HAND_ANALYSIS_SHEET_URL: str = "https://docs.google.com/spreadsheets/d/1_RN_W_ZQclSZA0Iez6XniCXVtjkkd5HNZwiT6l-z6d4"

    # Scanner Settings
    SCAN_ALL_FILES: bool = True  # True: 모든 파일 스캔, False: 미디어만
    EXCLUDED_EXTENSIONS: List[str] = [
        '.tmp', '.bak', '.log', '.DS_Store', '.thumbs', '.db',
        '.ini', '.cfg', '.cache', '.lock'
    ]

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
