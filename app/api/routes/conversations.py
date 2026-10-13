# app/api/routes/conversations.py
#--------------------------------------------

import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import get_conversation_repo
from app.api.schemas import (
    ConversationThreadListResponse,
    ConversationThreadResponse,
    CreateThreadRequest,
    MessageResponse,
)
from app.db.repositories import ConversationRepository

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.post(
    "/",
    response_model=ConversationThreadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создать новый тред диалога",
    description="Создаёт новый тред для диалога пользователя с агентом. "
                "В будущем thread_id будет использоваться LangGraph для хранения состояния.",
)
async def create_conversation(
    request: CreateThreadRequest,
    repo: ConversationRepository = Depends(get_conversation_repo),
):
    """
    Создаёт новый тред диалога.
    """

    # Thread ID генерируется на стороне сервера (UUID4), чтобы гарантировать
    # уникальность и совместимость с LangGraph Checkpointer
    thread_id = str(uuid.uuid4())
    
    thread = await repo.create_thread(
        thread_id=thread_id,
        user_id=request.user_id,
        title=request.title,
    )
    
    return thread


@router.get(
    "/user/{user_id}",
    response_model=ConversationThreadListResponse,
    summary="Получить треды пользователя",
    description="Возвращает список тредов диалогов пользователя, отсортированных по дате обновления.",
)
async def get_user_conversations(
    user_id: str,
    limit: int = Query(default=20, ge=1, le=100, description="Максимум тредов на странице"),
    offset: int = Query(default=0, ge=0, description="Смещение от начала"),
    repo: ConversationRepository = Depends(get_conversation_repo),
):
    """
    Получает список тредов пользователя с пагинацией.
    
    Треды отсортированы по `updated_at` DESC — самые свежие сверху.
    """

    threads, total = await repo.get_user_threads_paginated(
        user_id=user_id,
        limit=limit,
        offset=offset,
    )
    
    return ConversationThreadListResponse(
        threads=threads,
        total=total,
    )


@router.get(
    "/{thread_id}/messages",
    response_model=List[MessageResponse],
    summary="Получить историю сообщений треда",
    description="Возвращает все сообщения в треде, отсортированные по времени создания.",
)
async def get_thread_messages(
    thread_id: str,
    limit: int = Query(default=100, ge=1, le=1000, description="Максимум сообщений"),
    repo: ConversationRepository = Depends(get_conversation_repo),
):
    """
    Получает историю сообщений конкретного треда.
    
    Сообщения отсортированы по `created_at` ASC — от старых к новым,
    как в обычном чате.
    """

    # Проверяем, что тред существует
    thread = await repo.get_thread(thread_id)
    if not thread:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Thread '{thread_id}' not found",
        )
    
    messages = await repo.get_thread_messages(thread_id=thread_id, limit=limit)

    return messages


@router.get(
    "/{thread_id}",
    response_model=ConversationThreadResponse,
    summary="Получить тред по ID",
    description="Возвращает информацию о треде диалога.",
)
async def get_conversation(
    thread_id: str,
    repo: ConversationRepository = Depends(get_conversation_repo),
):
    """Получает тред по ID."""
    thread = await repo.get_thread(thread_id)
    
    if not thread:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Thread '{thread_id}' not found",
        )
    
    return thread
