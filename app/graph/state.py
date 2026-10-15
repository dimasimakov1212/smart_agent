# app/graph/state.py
#--------------------------------------------

from typing import Annotated, Optional, Dict, Any, List
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


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
    messages: Annotated[List[BaseMessage], add_messages]
    
    # Идентификатор треда (для LangGraph Checkpointer)
    thread_id: str
    
    # Текущее действие, ожидающее подтверждения (опционально)
    current_pending_action: Optional[Dict[str, Any]]
    
    # Контекст пользователя (опционально, для персонализации)
    user_context: Optional[Dict[str, Any]]


# === Вспомогательные типы ===

class PendingActionData(TypedDict):
    """
    Структура данных для pending action.
    Используется для типизации current_pending_action.
    """
    action_id: int
    action_type: str
    payload: Dict[str, Any]
    thread_id: str


class UserContext(TypedDict):
    """
    Контекст пользователя для персонализации ответов.
    Может содержать информацию из RAG, предпочтения, и т.д.
    """
    user_id: str
    relevant_documents: Optional[List[Dict[str, Any]]]  # Результаты RAG-поиска
    preferences: Optional[Dict[str, Any]]  # Пользовательские настройки
