# app/api/schemas.py
#--------------------------------------------

from datetime import datetime
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, ConfigDict, Field


# === Document Schemas ===

class DocumentResponse(BaseModel):
    """Схема ответа для документа"""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    filename: str
    file_type: str
    file_size: Optional[int] = None
    user_id: str
    total_tokens: int = 0
    created_at: datetime
    updated_at: Optional[datetime] = None


class DocumentListResponse(BaseModel):
    """Схема ответа для списка документов"""
    
    documents: List[DocumentResponse]
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
    title: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None


class MessageResponse(BaseModel):
    """Схема ответа для сообщения"""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    thread_id: str
    role: str
    content: str
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = None
    created_at: datetime


class ConversationThreadListResponse(BaseModel):
    """Схема ответа для списка тредов"""
    
    threads: List[ConversationThreadResponse]
    total: int


# === Pending Action Schemas ===

class PendingActionResponse(BaseModel):
    """Схема ответа для pending action"""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    thread_id: str
    action_type: str
    payload: Dict[str, Any]
    status: str
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    created_at: datetime


# === Request Schemas (для входных данных) ===

class CreateThreadRequest(BaseModel):
    """Запрос на создание нового треда"""
    
    user_id: str = Field(..., min_length=1, max_length=255)
    title: Optional[str] = Field(default=None, max_length=255)


class ApprovalRequest(BaseModel):
    """Запрос на одобрение/отклонение действия"""
    
    user_id: str = Field(..., min_length=1, max_length=255)
    approved: bool
    feedback: Optional[str] = Field(default=None, max_length=1000)


class ChatRequest(BaseModel):
    """Запрос на отправку сообщения агенту"""
    
    user_id: str = Field(..., min_length=1, max_length=255)
    message: str = Field(..., min_length=1, max_length=10000)
    thread_id: Optional[str] = None


# === Common Schemas ===

class ErrorResponse(BaseModel):
    """Стандартная схема ошибки"""
    
    detail: str
    error_code: Optional[str] = None


class HealthResponse(BaseModel):
    """Ответ health check"""
    
    status: str
    version: Optional[str] = None
