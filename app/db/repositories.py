# app/db/repositories.py
#--------------------------------------------

from typing import Optional, List
from datetime import datetime
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql import func

from app.db.models import (
    Document,
    DocumentChunk,
    ConversationThread,
    Message,
    PendingAction,
)


class DocumentRepository:
    """Репозиторий для работы с документами и их чанками"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_document(
        self,
        filename: str,
        file_type: str,
        file_size: int,
        user_id: str,
        metadata_json: Optional[dict] = None,
    ) -> Document:
        """Создаёт запись о загруженном документе"""

        doc = Document(
            filename=filename,
            file_type=file_type,
            file_size=file_size,
            user_id=user_id,
            metadata_json=metadata_json or {},
        )
        self.session.add(doc)
        await self.session.flush()  # Получаем doc.id без коммита
        return doc

    async def add_chunk(
        self,
        document_id: int,
        chunk_index: int,
        text_content: str,
        qdrant_point_id: str,
        token_count: int,
        metadata_json: Optional[dict] = None,
    ) -> DocumentChunk:
        """Добавляет чанк документа"""

        chunk = DocumentChunk(
            document_id=document_id,
            chunk_index=chunk_index,
            text_content=text_content,
            qdrant_point_id=qdrant_point_id,
            token_count=token_count,
            metadata_json=metadata_json or {},
        )
        self.session.add(chunk)
        await self.session.flush()
        return chunk

    async def update_document_tokens(self, document_id: int, total_tokens: int) -> None:
        """Обновляет суммарное количество токенов в документе"""

        await self.session.execute(
            update(Document)
            .where(Document.id == document_id)
            .values(total_tokens=total_tokens)
        )

    async def get_document_by_id(self, document_id: int) -> Optional[Document]:
        """Получает документ по ID с загруженными чанками"""

        result = await self.session.execute(
            select(Document)
            .options(selectinload(Document.chunks))
            .where(Document.id == document_id)
        )
        return result.scalar_one_or_none()

    async def get_user_documents(
        self, user_id: str, limit: int = 50, offset: int = 0
    ) -> List[Document]:
        """Получает список документов пользователя (без чанков)"""

        result = await self.session.execute(
            select(Document)
            .where(Document.user_id == user_id)
            .order_by(Document.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())


class ConversationRepository:
    """Репозиторий для работы с диалогами и сообщениями"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_thread(
        self,
        thread_id: str,
        user_id: str,
        title: Optional[str] = None,
    ) -> ConversationThread:
        """Создаёт новый тред диалога"""

        thread = ConversationThread(
            id=thread_id,
            user_id=user_id,
            title=title,
            status="active",
        )
        self.session.add(thread)
        await self.session.flush()
        return thread

    async def get_thread(self, thread_id: str) -> Optional[ConversationThread]:
        """Получает тред по ID с загруженными сообщениями"""

        result = await self.session.execute(
            select(ConversationThread)
            .options(selectinload(ConversationThread.messages))
            .where(ConversationThread.id == thread_id)
        )
        return result.scalar_one_or_none()

    async def add_message(
        self,
        thread_id: str,
        role: str,
        content: str,
        tool_calls: Optional[list] = None,
        tool_call_id: Optional[str] = None,
        metadata_json: Optional[dict] = None,
    ) -> Message:
        """Добавляет сообщение в тред"""

        message = Message(
            thread_id=thread_id,
            role=role,
            content=content,
            tool_calls=tool_calls,
            tool_call_id=tool_call_id,
            metadata_json=metadata_json or {},
        )
        self.session.add(message)
        await self.session.flush()
        return message

    async def get_thread_messages(
        self, thread_id: str, limit: int = 100
    ) -> List[Message]:
        """Получает историю сообщений треда"""

        result = await self.session.execute(
            select(Message)
            .where(Message.thread_id == thread_id)
            .order_by(Message.created_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_user_threads(
        self, user_id: str, limit: int = 20
    ) -> List[ConversationThread]:
        """Получает список тредов пользователя (без сообщений)"""

        result = await self.session.execute(
            select(ConversationThread)
            .where(ConversationThread.user_id == user_id)
            .order_by(ConversationThread.updated_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def update_thread_status(self, thread_id: str, status: str) -> None:
        """Обновляет статус треда (active, completed, interrupted)"""

        await self.session.execute(
            update(ConversationThread)
            .where(ConversationThread.id == thread_id)
            .values(status=status, updated_at=func.now())
        )


class PendingActionRepository:
    """Репозиторий для работы с действиями, ожидающими подтверждения"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_pending_action(
        self,
        thread_id: str,
        action_type: str,
        payload: dict,
    ) -> PendingAction:
        """Создаёт действие, ожидающее подтверждения"""

        action = PendingAction(
            thread_id=thread_id,
            action_type=action_type,
            payload=payload,
            status="pending",
        )
        self.session.add(action)
        await self.session.flush()
        return action

    async def get_pending_action(self, action_id: int) -> Optional[PendingAction]:
        """Получает pending action по ID"""

        result = await self.session.execute(
            select(PendingAction).where(PendingAction.id == action_id)
        )
        return result.scalar_one_or_none()

    async def get_pending_for_thread(self, thread_id: str) -> Optional[PendingAction]:
        """Получает последнее pending action для треда"""

        result = await self.session.execute(
            select(PendingAction)
            .where(PendingAction.thread_id == thread_id, PendingAction.status == "pending")
            .order_by(PendingAction.created_at.desc())
        )
        return result.scalars().first()

    async def approve_action(
        self,
        action_id: int,
        approved_by: str,
        result: Optional[dict] = None,
    ) -> None:
        """Одобрение действия пользователем"""

        await self.session.execute(
            update(PendingAction)
            .where(PendingAction.id == action_id)
            .values(
                status="approved",
                approved_by=approved_by,
                approved_at=func.now(),
                result=result,
            )
        )

    async def reject_action(self, action_id: int, rejected_by: str) -> None:
        """Отклонение действия пользователем"""

        await self.session.execute(
            update(PendingAction)
            .where(PendingAction.id == action_id)
            .values(
                status="rejected",
                approved_by=rejected_by,
                approved_at=func.now(),
            )
        )
