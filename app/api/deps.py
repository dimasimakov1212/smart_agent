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
from app.services.chat_service import ChatService
import app.graph.builder as builder_module


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


# === Service Dependencies ===
async def get_chat_service(
    session: AsyncSession = Depends(get_db),
) -> ChatService:
    """
    Зависимость для получения ChatService.
    Обращаемся к builder_module.graph во время выполнения, 
    когда lifespan уже инициализировал граф.
    """
    
    # Проверка если сервер запросили до старта
    if builder_module.graph is None:
        raise RuntimeError("LangGraph не инициализирован. Проверьте logs startup.")
        
    return ChatService(session=session, agent_graph=builder_module.graph)
