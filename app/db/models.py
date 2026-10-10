# app/db/models.py
#--------------------------------------------

from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Integer, Text, DateTime, JSON, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.db.database import Base


# Mixin для переиспользования временных меток
class TimestampMixin:
    """Добавляет поля created_at и updated_at к моделям"""
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        onupdate=func.now(),
        nullable=True,
    )


class Document(Base, TimestampMixin):
    """
    Документ, загруженный пользователем для RAG.
    Связан с DocumentChunk
    """
    __tablename__ = "documents"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    file_type: Mapped[str] = mapped_column(String(50), nullable=False)  # pdf, txt, md, docx
    file_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Размер в байтах
    user_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSON, default=dict, nullable=True)
    total_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    chunks: Mapped[List["DocumentChunk"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
        lazy="selectin",  # Загружаем чанки сразу при запросе документа
    )
    
    def __repr__(self) -> str:
        return f"<Document(id={self.id}, filename='{self.filename}', user_id='{self.user_id}')>"


class DocumentChunk(Base, TimestampMixin):
    """
    Чанк (фрагмент) документа для векторного поиска.
    Связан с Document
    """
    __tablename__ = "document_chunks"
    __table_args__ = (
        # Составной индекс для быстрого поиска чанков конкретного документа
        Index("ix_chunk_document_index", "document_id", "chunk_index"),
    )
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)  # Порядок чанка в документе
    text_content: Mapped[str] = mapped_column(Text, nullable=False)  # Текст чанка
    qdrant_point_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,  # Быстрый поиск по ID вектора в Qdrant
    )
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSON, default=dict, nullable=True)
    token_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    document: Mapped["Document"] = relationship(back_populates="chunks")
    
    def __repr__(self) -> str:
        return f"<DocumentChunk(id={self.id}, document_id={self.document_id}, index={self.chunk_index})>"


class ConversationThread(Base, TimestampMixin):
    """
    Тред (сессия) диалога пользователя с агентом.
    Связан с Message и PendingAction
    """
    __tablename__ = "conversation_threads"
    
    id: Mapped[str] = mapped_column(String(255), primary_key=True)  # UUID из LangGraph
    user_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # Автогенерируемый заголовок
    status: Mapped[str] = mapped_column(
        String(50),
        default="active",
        nullable=False,
        index=True,
    )
    messages: Mapped[List["Message"]] = relationship(
        back_populates="thread",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="Message.created_at",
    )
    pending_actions: Mapped[List["PendingAction"]] = relationship(
        back_populates="thread",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    
    def __repr__(self) -> str:
        return f"<ConversationThread(id='{self.id}', user_id='{self.user_id}', status='{self.status}')>"


class Message(Base, TimestampMixin):
    """
    Сообщение в диалоге (user, assistant, tool, system).
    Связано с ConversationThread
    """
    __tablename__ = "messages"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    thread_id: Mapped[str] = mapped_column(
        String(255),
        ForeignKey("conversation_threads.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(String(50), nullable=False)  # user, assistant, tool, system
    content: Mapped[str] = mapped_column(Text, nullable=False)
    tool_calls: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)  # Если это вызов инструмента
    tool_call_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSON, default=dict, nullable=True)
    thread: Mapped["ConversationThread"] = relationship(back_populates="messages")
    
    def __repr__(self) -> str:
        return f"<Message(id={self.id}, role='{self.role}', thread_id='{self.thread_id}')>"


class PendingAction(Base, TimestampMixin):
    """
    Действие, ожидающее подтверждения пользователем (Human-in-the-Loop).
    Связано с ConversationThread
    """
    __tablename__ = "pending_actions"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    thread_id: Mapped[str] = mapped_column(
        String(255),
        ForeignKey("conversation_threads.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    action_type: Mapped[str] = mapped_column(String(100), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)  # Данные для действия
    status: Mapped[str] = mapped_column(
        String(50),
        default="pending",
        nullable=False,
        index=True,
    )
    approved_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    result: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # Результат выполнения
    thread: Mapped["ConversationThread"] = relationship(back_populates="pending_actions")
    
    def __repr__(self) -> str:
        return f"<PendingAction(id={self.id}, type='{self.action_type}', status='{self.status}')>"
