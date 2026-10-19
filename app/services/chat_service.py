# app/services/chat_service.py
#--------------------------------------------

from dataclasses import dataclass
from typing import List, Optional
from uuid import uuid4

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langgraph.graph.state import CompiledStateGraph
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ThreadAccessDeniedError, ThreadNotFoundError
from app.db.models import Message, PendingAction
from app.db.repositories import ConversationRepository, PendingActionRepository


@dataclass
class ChatResult:
    """
    Результат обработки сообщения
    
    assistant_message может быть None, если граф остановился
    в ожидании подтверждения пользователя.
    """
    thread_id: str
    user_message: Message
    assistant_message: Optional[Message]
    status: str
    pending_action: Optional[PendingAction] = None


class ChatService:
    """
    Оркестрация диалога: БД <-> LangGraph.
    
    Ответственность:
    - управление тредами и правами доступа
    - подготовка состояния для графа
    - обработка завершения / прерывания графа
    - сохранение сообщений и pending actions
    """

    def __init__(self, session: AsyncSession, agent_graph: CompiledStateGraph):
        self.session = session
        self.graph = agent_graph
        self.conversations = ConversationRepository(session)
        self.actions = PendingActionRepository(session)

    # === Публичный API сервиса ===

    async def process_message(
        self,
        *,
        user_id: str,
        text: str,
        thread_id: Optional[str] = None,
    ) -> ChatResult:
        """
        Обрабатывает новое сообщение пользователя.
        
        1. Находит или создаёт тред
        2. Готовит входное состояние графа
        3. Запускает граф
        4. Обрабатывает результат: completed / awaiting_approval
        """
        thread_id = await self._resolve_thread(
            user_id=user_id,
            text=text,
            thread_id=thread_id,
        )

        config = {"configurable": {"thread_id": thread_id}}
        input_state = await self._build_input_state(thread_id=thread_id, text=text)

        result = await self.graph.ainvoke(input_state, config)

        # Сохраняем сообщение пользователя (один раз, после выполнения графа)
        user_message = await self.conversations.add_message(
            thread_id=thread_id,
            role="user",
            content=text,
        )

        # === Сценарий 1: граф ждёт подтверждения ===
        if "__interrupt__" in result:
            interrupt_value = result["__interrupt__"][0].value
            action_data = interrupt_value["action_data"]

            pending_action = await self.actions.create_pending_action(
                thread_id=thread_id,
                action_type=action_data["action_type"],
                payload={
                    "tool_call_id": action_data["tool_call_id"],
                    "args": action_data["args"],
                    "message": interrupt_value["message"],
                },
            )

            return ChatResult(
                thread_id=thread_id,
                user_message=user_message,
                assistant_message=None,
                status="awaiting_approval",
                pending_action=pending_action,
            )

        # === Сценарий 2: граф завершился ===
        answer = self._extract_final_answer(result["messages"])

        assistant_message = await self.conversations.add_message(
            thread_id=thread_id,
            role="assistant",
            content=answer,
        )

        return ChatResult(
            thread_id=thread_id,
            user_message=user_message,
            assistant_message=assistant_message,
            status="completed",
        )

    # === Вспомогательные методы ===

    async def _resolve_thread(
        self,
        *,
        user_id: str,
        text: str,
        thread_id: Optional[str],
    ) -> str:
        """Находит существующий тред или создаёт новый. Проверяет права."""

        if thread_id:
            thread = await self.conversations.get_thread(thread_id)

            if thread is None:
                raise ThreadNotFoundError(f"Thread '{thread_id}' not found")

            if thread.user_id != user_id:
                raise ThreadAccessDeniedError(
                    f"User '{user_id}' has no access to thread '{thread_id}'"
                )

            return thread_id

        new_thread_id = str(uuid4())

        await self.conversations.create_thread(
            thread_id=new_thread_id,
            user_id=user_id,
            title=text[:50],
        )
        return new_thread_id

    async def _build_input_state(
        self,
        *,
        thread_id: str,
        text: str,
    ) -> dict:
        """
        Готовит входное состояние для графа.
        
        ВАЖНО: Checkpointer уже хранит историю сообщений треда.
        Повторная передача всей истории из БД приведёт к её дублированию,
        потому что add_messages merge-ит сообщения по ID, а у новых
        HumanMessage ID генерируется заново при каждом вызове.
        
        Поэтому:
        - если checkpoint существует -> передаём только новое сообщение
        - если checkpoint пуст -> восстанавливаем историю из БД один раз
        """

        new_message = HumanMessage(content=text)
        config = {"configurable": {"thread_id": thread_id}}

        checkpoint_state = await self.graph.aget_state(config)
        has_history = bool(checkpoint_state.values.get("messages"))

        messages: List[BaseMessage] = []

        if not has_history:
            existing = await self.conversations.get_thread_messages(
                thread_id=thread_id,
                limit=100,
            )
            for msg in existing:
                if msg.role == "user":
                    messages.append(HumanMessage(content=msg.content))
                elif msg.role == "assistant":
                    messages.append(AIMessage(content=msg.content))

        messages.append(new_message)

        return {
            "messages": messages,
            "thread_id": thread_id,
            "current_pending_action": None,
            "user_context": None,
        }

    @staticmethod
    def _extract_final_answer(messages: List[BaseMessage]) -> str:
        """Достаёт финальный текстовый ответ агента."""
        
        for message in reversed(messages):
            if isinstance(message, AIMessage) and message.content:
                return (
                    message.content
                    if isinstance(message.content, str)
                    else str(message.content)
                )

        return "Не удалось сформировать ответ."