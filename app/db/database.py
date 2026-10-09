# app/db/database.py
#--------------------------------------------

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.core.config import get_settings


settings = get_settings()

# Создаем асинхронный движок SQLAlchemy
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,  # Выводим SQL-запросы в консоль только в режиме отладки
    pool_size=20,         # Размер пула соединений
    max_overflow=10,      # Максимальное количество дополнительных соединений при пиковой нагрузке
    pool_pre_ping=True,   # Проверяет соединение перед использованием
)

# Фабрика асинхронных сессий
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Базовый класс для всех SQLAlchemy моделей
class Base(DeclarativeBase):
    pass

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency для FastAPI.
    Создает сессию, делает commit при успехе, rollback при ошибке, и всегда закрывает сессию.
    """

    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
