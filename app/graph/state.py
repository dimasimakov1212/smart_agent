# app/graph/state.py

from typing import Annotated, Any

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

# === Определение State ===


class AgentState(TypedDict):
    """
    Состояние LangGraph агента.

    Этот State передаётся между узлами графа и персистится через Checkpointer.

    Поля:
    - messages: история диалога (автоматически накапливается через add_messages)
    - thread_id: идентификатор треда (используется Checkpointer)
    - current_pending_action: действие, ожидающее подтверждения (если есть)
    - user_context: дополнительная информация о пользователе
    """

    # История сообщений (использует аннотацию add_messages для автоматического накопления)
    messages: Annotated[list[BaseMessage], add_messages]

    # Идентификатор треда (для LangGraph Checkpointer)
    thread_id: str

    # Текущее действие, ожидающее подтверждения (опционально)
    current_pending_action: dict[str, Any] | None

    # Контекст пользователя (опционально, для персонализации)
    user_context: dict[str, Any] | None


# === Вспомогательные типы ===


class PendingActionData(TypedDict):
    """
    Структура данных для pending action.
    Используется для типизации current_pending_action.
    """

    action_id: int
    action_type: str
    payload: dict[str, Any]
    thread_id: str


class UserContext(TypedDict):
    """
    Контекст пользователя для персонализации ответов.
    Может содержать информацию из RAG, предпочтения, и т.д.
    """

    user_id: str
    relevant_documents: list[dict[str, Any]] | None  # Результаты RAG-поиска
    preferences: dict[str, Any] | None  # Пользовательские настройки
