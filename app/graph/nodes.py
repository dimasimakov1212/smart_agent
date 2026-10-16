# app/graph/nodes.py
#--------------------------------------------

from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.prebuilt import ToolNode
from langgraph.types import interrupt, Command

from app.graph.state import AgentState
from app.tools.agent_tools import ALL_TOOLS, HUMAN_APPROVAL_REQUIRED_TOOLS, is_human_approval_required
from app.core.config import get_settings


settings = get_settings()


# === Инициализация LLM ===

# Создаём модель с привязанными инструментами
llm = ChatOpenAI(
    model="gpt-4o-mini",  # Можно заменить на gpt-4o или другую модель
    api_key=settings.OPENAI_API_KEY,
    base_url=settings.OPENAI_BASE_URL,
    temperature=0.7,
    streaming=True,
)

# Привязываем инструменты к LLM
llm_with_tools = llm.bind_tools(ALL_TOOLS)


# === Системный промпт ===

SYSTEM_PROMPT = """Ты — умный AI-ассистент с доступом к инструментам.

Твои возможности:
- Отвечать на вопросы пользователя
- Искать информацию в документах пользователя
- Создавать задачи в Jira (требует подтверждения)
- Отправлять email (требует подтверждения)
- Искать информацию в интернете
- Узнавать текущую дату и время

ВАЖНО:
- Если пользователь просит выполнить действие, которое требует подтверждения (создание задачи, отправка email), 
  ты ДОЛЖЕН сначала объяснить пользователю, что собираешься сделать, и дождаться явного одобрения.
- НЕ выполняй действия, требующие подтверждения, без явного разрешения пользователя.
- Будь дружелюбным, но профессиональным.
- Если не знаешь ответа — честно скажи об этом.

Текущая дата и время: {current_datetime}
"""


# === Узел 1: Agent Node ===

def agent_node(state: AgentState) -> Dict[str, Any]:
    """
    Главный узел агента.
    
    Вызывает LLM с текущей историей сообщений и инструментами.
    LLM решает, что делать: ответить напрямую или вызвать инструмент.
    
    Args:
        state: Текущее состояние графа
    
    Returns:
        Обновления State (новые сообщения)
    """
    # Получаем историю сообщений
    messages = state["messages"]
    
    # Добавляем системный промпт в начало (если его ещё нет)
    if not messages or not isinstance(messages[0], SystemMessage):
        from datetime import datetime
        current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        system_message = SystemMessage(content=SYSTEM_PROMPT.format(current_datetime=current_datetime))
        messages = [system_message] + messages
    
    # Вызываем LLM
    response = llm_with_tools.invoke(messages)
    
    # Возвращаем обновление State
    return {"messages": [response]}


# === Узел 2: Tools Node ===

# Используем готовый ToolNode из langgraph
# Он автоматически выполняет вызовы инструментов, которые запросила LLM
tools_node = ToolNode(ALL_TOOLS)


# === Узел 3: Human Approval Node ===

def human_approval_node(state: AgentState) -> Dict[str, Any]:
    """
    Узел для проверки, нужно ли подтверждение пользователя.
    
    Если последнее сообщение от LLM содержит вызов инструмента,
    который требует подтверждения, останавливаем граф и ждём одобрения.
    
    Args:
        state: Текущее состояние графа
    
    Returns:
        Обновления State или interrupt для ожидания подтверждения
    """
    messages = state["messages"]
    
    # Проверяем последнее сообщение
    if not messages:
        return {}
    
    last_message = messages[-1]
    
    # Если это AI-сообщение с вызовами инструментов
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        # Проверяем, есть ли среди вызовов инструменты, требующие подтверждения
        for tool_call in last_message.tool_calls:
            tool_name = tool_call["name"]
            
            if is_human_approval_required(tool_name):
                # Останавливаем граф и ждём подтверждения
                # interrupt() возвращает управление пользователю
                # Когда пользователь одобрит, граф продолжится с Command(resume=...)
                
                action_data = {
                    "action_type": tool_name,
                    "tool_call_id": tool_call["id"],
                    "args": tool_call["args"],
                }
                
                # Сохраняем pending action в State
                # (в будущем это будет синхронизировано с БД через API)
                
                # Останавливаем выполнение
                interrupt({
                    "type": "human_approval_required",
                    "message": f"Агент хочет выполнить действие '{tool_name}', которое требует вашего подтверждения.",
                    "action_data": action_data,
                })
    
    # Если подтверждение не нужно — просто возвращаем пустое обновление
    return {}


# === Функция маршрутизации ===

def should_continue(state: AgentState) -> str:
    """
    Определяет, куда идти дальше после agent_node.
    
    Args:
        state: Текущее состояние графа
    
    Returns:
        Имя следующего узла: "tools", "human_approval", или "end"
    """
    messages = state["messages"]
    
    if not messages:
        return "end"
    
    last_message = messages[-1]
    
    # Если LLM запросила вызов инструментов
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        # Проверяем, есть ли инструменты, требующие подтверждения
        for tool_call in last_message.tool_calls:
            if is_human_approval_required(tool_call["name"]):
                return "human_approval"
        
        # Если все инструменты не требуют подтверждения — идём в tools_node
        return "tools"
    
    # Если LLM просто ответила текстом — заканчиваем
    return "end"
