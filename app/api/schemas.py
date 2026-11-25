# app/api/schemas.py

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

# === Document Schemas ===


class DocumentResponse(BaseModel):
    """Схема ответа для документа"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    file_type: str
    file_size: int | None = None
    user_id: str
    total_tokens: int = 0
    created_at: datetime
    updated_at: datetime | None = None


class DocumentListResponse(BaseModel):
    """Схема ответа для списка документов"""

    documents: list[DocumentResponse]
    total: int


class DocumentUploadResponse(BaseModel):
    """Схема ответа после загрузки документа"""

    id: int
    filename: str
    file_type: str
    file_size: int
    status: str = Field(default="uploaded", description="Статус обработки")
    message: str = Field(
        default="Документ загружен. Чанкинг и векторизация будут выполнены асинхронно."
    )


# === Conversation Schemas ===


class ConversationThreadResponse(BaseModel):
    """Схема ответа для треда диалога"""

    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    title: str | None = None
    status: str
    created_at: datetime
    updated_at: datetime | None = None


class MessageResponse(BaseModel):
    """Схема ответа для сообщения"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    thread_id: str
    role: str
    content: str
    tool_calls: list[dict[str, Any]] | None = None
    tool_call_id: str | None = None
    metadata_json: dict[str, Any] | None = None
    created_at: datetime


class ConversationThreadListResponse(BaseModel):
    """Схема ответа для списка тредов"""

    threads: list[ConversationThreadResponse]
    total: int


# === Pending Action Schemas ===


class PendingActionResponse(BaseModel):
    """Схема ответа для pending action"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    thread_id: str
    action_type: str
    payload: dict[str, Any]
    status: str
    approved_by: str | None = None
    approved_at: datetime | None = None
    result: dict[str, Any] | None = None
    created_at: datetime


# === Request Schemas (для входных данных) ===


class CreateThreadRequest(BaseModel):
    """Запрос на создание нового треда"""

    user_id: str = Field(..., min_length=1, max_length=255)
    title: str | None = Field(default=None, max_length=255)


class ApprovalRequest(BaseModel):
    """Запрос на одобрение/отклонение действия"""

    user_id: str = Field(..., min_length=1, max_length=255)
    approved: bool
    feedback: str | None = Field(default=None, max_length=1000)


class ChatRequest(BaseModel):
    """Запрос на отправку сообщения агенту"""

    user_id: str = Field(..., min_length=1, max_length=255)
    message: str = Field(..., min_length=1, max_length=10000)
    thread_id: str | None = None


class ChatResponse(BaseModel):
    """Ответ на сообщение пользователя"""

    thread_id: str
    user_message: MessageResponse
    assistant_message: MessageResponse | None = Field(
        default=None,
        description="Ответ агента. None, если граф остановился в ожидании подтверждения.",
    )
    status: str = Field(
        default="completed", description="Статус обработки: completed, awaiting_approval, error"
    )
    pending_action: PendingActionResponse | None = Field(
        default=None,
        description="Действие, ожидающее подтверждения (если status='awaiting_approval')",
    )


# === Common Schemas ===


class ErrorResponse(BaseModel):
    """Стандартная схема ошибки"""

    detail: str
    error_code: str | None = None


class HealthResponse(BaseModel):
    """Ответ health check"""

    status: str
    version: str | None = None
