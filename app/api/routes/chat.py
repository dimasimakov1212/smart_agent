# app/api/routes/chat.py
#--------------------------------------------

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_chat_service
from app.api.schemas import ChatRequest, ChatResponse, MessageResponse, PendingActionResponse
from app.core.exceptions import ThreadAccessDeniedError, ThreadNotFoundError
from app.services.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post(
    "/",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Отправить сообщение агенту",
    description="Отправляет сообщение LangGraph-агенту. "
                "Если thread_id не указан — создаётся новый тред. "
                "Возвращает как сообщение пользователя, так и ответ агента.",
)

async def chat(
    request: ChatRequest,
    service: ChatService = Depends(get_chat_service),
):
    """
    Основной endpoint для общения с LangGraph-агентом.
    """
    
    try:
        result = await service.process_message(
            user_id=request.user_id,
            text=request.message,
            thread_id=request.thread_id,
        )
    except ThreadNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except ThreadAccessDeniedError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )
    
    return ChatResponse(
        thread_id=result.thread_id,
        user_message=MessageResponse.model_validate(result.user_message),
        assistant_message=(
            MessageResponse.model_validate(result.assistant_message)
            if result.assistant_message
            else None
        ),
        status=result.status,
        pending_action=(
            PendingActionResponse.model_validate(result.pending_action)
            if result.pending_action
            else None
        ),
    )
