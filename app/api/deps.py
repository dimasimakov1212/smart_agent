# app/api/deps.py
#--------------------------------------------

from typing import AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.repositories import (
    DocumentRepository,
    ConversationRepository,
    PendingActionRepository,
)


# === Database Session ===
async def get_session(
    db: AsyncSession = Depends(get_db),
) -> AsyncGenerator[AsyncSession, None]:
    """
    Зависимость для получения сессии БД.
    Используется другими зависимостями для создания репозиториев.
    """
    yield db


# === Repository Dependencies ===
async def get_document_repo(
    session: AsyncSession = Depends(get_db),
) -> DocumentRepository:
    """
    Зависимость для получения DocumentRepository.
    Использование в роуте:
        @router.get("/documents")
        async def get_documents(repo: DocumentRepository = Depends(get_document_repo)):
            ...
    """
    return DocumentRepository(session)


async def get_conversation_repo(
    session: AsyncSession = Depends(get_db),
) -> ConversationRepository:
    """
    Зависимость для получения ConversationRepository.
    """
    return ConversationRepository(session)


async def get_pending_action_repo(
    session: AsyncSession = Depends(get_db),
) -> PendingActionRepository:
    """
    Зависимость для получения PendingActionRepository.
    """
    return PendingActionRepository(session)