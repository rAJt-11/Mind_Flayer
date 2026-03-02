"""
config.py – Application configuration using pydantic-settings.
All settings are loaded from environment variables or a .env file.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache


class Settings(BaseSettings):
    # ─── App metadata ─────────────────────────────────────────────────────────
    APP_NAME: str = "Mind Flayer"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = "AI-Powered Personal Life & Work Optimization Assistant"
    DEBUG: bool = Field(default=True)

    # ─── Database ─────────────────────────────────────────────────────────────
    MSSQL_SERVER: str = Field(default="TestDB")
    MSSQL_DATABASE: str = Field(default="Mind_Flayer")
    MSSQL_USERNAME: str = Field(default="test")
    MSSQL_PASSWORD: str = Field(default="Test@2025")
    MSSQL_DRIVER: str = Field(default="ODBC Driver 17 for SQL Server")
    
    DB_URL: str | None = Field(default=None, alias="DATABASE_URL")
    SYNC_DB_URL: str | None = Field(default=None, alias="SYNC_DATABASE_URL")

    @property
    def DATABASE_URL(self) -> str:
        """Async connection string for SQLAlchemy."""
        if self.DB_URL is not None:
            return str(self.DB_URL)
        return "sqlite+aiosqlite:///:memory:"

    @property
    def SYNC_DATABASE_URL(self) -> str:
        """Sync connection string (for seed scripts / alembic)."""
        if self.SYNC_DB_URL is not None:
            return str(self.SYNC_DB_URL)
        return "sqlite:///:memory:"

    # ─── Scheduler ────────────────────────────────────────────────────────────
    SCHEDULER_TIMEZONE: str = "Asia/Kolkata"

    # ─── AI Engine ────────────────────────────────────────────────────────────
    LOW_SLEEP_THRESHOLD: float = 6.0     # hours
    LOW_MOOD_THRESHOLD: int = 4          # 1-10 scale
    HIGH_STRESS_THRESHOLD: int = 7       # 1-10 scale
    GREAT_SLEEP_THRESHOLD: float = 7.5   # hours

    # ─── Auth / Security ──────────────────────────────────────────────────────
    SECRET_KEY: str = "mind-flayer-super-secret-key-change-in-production-32chars!!"
    SESSION_SECRET_KEY: str = "session-secret-key-change-in-production-must-be-long!!"
    JWT_SECRET_KEY: str = "jwt-secret-key-change-in-production-very-long-secret-key!!"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440  # 24 hours

    model_config = {
        "env_file": ".env",
        "case_sensitive": True,
        "extra": "ignore"
    }


@lru_cache()
def get_settings() -> Settings:
    """Return cached settings singleton."""
    return Settings()


settings = get_settings()
