# app/core/config.py
#--------------------------------------------

from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # Игнорируем лишние переменные в .env
        case_sensitive=False,
    )
    
    # === Database ===
    # Дефолты для локальной разработки (docker-compose)
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5433
    POSTGRES_DB: str = "smart_agent"
    
    # === Qdrant ===
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    
    # === OpenAI ===
    # БЕЗ дефолта — обязательно должно быть в .env или окружении!
    OPENAI_API_KEY: str
    
    # === Опциональные настройки ===
    # LangSmith для observability
    LANGCHAIN_TRACING_V2: bool = False
    LANGCHAIN_API_KEY: str = ""
    LANGCHAIN_PROJECT: str = "smart_agent"
    
    # Приложение
    APP_ENV: str = "development"  # development, staging, production
    DEBUG: bool = True
    
    @property
    def DATABASE_URL(self) -> str:
        """Async URL для SQLAlchemy (основной код)"""
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    @property
    def DATABASE_URL_SYNC(self) -> str:
        """Sync URL для Alembic (миграции)"""
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

@lru_cache()
def get_settings() -> Settings:
    return Settings()
