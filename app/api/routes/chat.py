# app/api/routes/conversations.py
#--------------------------------------------

from datetime import datetime, timezone
import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_conversation_repo
from app.api.schemas import ChatRequest, ChatResponse, MessageResponse
from app.db.repositories import ConversationRepository

router = APIRouter(prefix="/chat", tags=["chat"])


# === Вспомогательная функция-заглушка для агента ===

async def mock_agent_respond(user_message: str) -> str:
    """
    Заглушка агента. В будущем здесь будет вызов LangGraph.
    
    Сейчас просто возвращает эхо-ответ с подсказкой.
    """
    return (
        f"Я получил твоё сообщение: «{user_message}».\n\n"
        "🚧 Это заглушка — настоящий LangGraph-агент с RAG и Human-in-the-Loop "
        "будет подключён на следующем этапе."
    )


@router.post(
    "/",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Отправить сообщение агенту",
    description="Отправляет сообщение пользователю-агенту. "
                "Если thread_id не указан — создаётся новый тред. "
                "Возвращает как сообщение пользователя, так и ответ агента.",
)
async def chat(
    request: ChatRequest,
    repo: ConversationRepository = Depends(get_conversation_repo),
):
    """
    Основной endpoint для общения с агентом.
    
    Логика:
    1. Если thread_id не указан — создаём новый тред
    2. Если thread_id указан — проверяем, что тред существует
    3. Сохраняем сообщение пользователя
    4. Получаем ответ агента
    5. Сохраняем ответ агента
    6. Возвращаем оба сообщения клиенту
    """
    # === 1. Получаем или создаём тред ===
    thread_id = request.thread_id
    
    if thread_id:

        thread = await repo.get_thread(thread_id)
        if not thread:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Thread '{thread_id}' not found",
            )

        if thread.user_id != request.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this thread",
            )
    else:
        # Создаём новый тред
        thread_id = str(uuid.uuid4())
        await repo.create_thread(
            thread_id=thread_id,
            user_id=request.user_id,
            title=request.message[:50],  # Первые 50 символов как заголовок
        )
    
    # === 2. Сохраняем сообщение пользователя ===
    user_message = await repo.add_message(
        thread_id=thread_id,
        role="user",
        content=request.message,
    )
    
    # === 3. Получаем ответ агента ===
    # TODO: заменить на реальный вызов LangGraph
    assistant_content = await mock_agent_respond(request.message)
    
    # === 4. Сохраняем ответ агента ===
    assistant_message = await repo.add_message(
        thread_id=thread_id,
        role="assistant",
        content=assistant_content,
    )
    
    # === 5. Возвращаем результат ===
    return ChatResponse(
        thread_id=thread_id,
        user_message=MessageResponse.model_validate(user_message),
        assistant_message=MessageResponse.model_validate(assistant_message),
        status="completed",
    )
