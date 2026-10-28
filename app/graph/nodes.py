# app/graph/nodes.py

from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, SystemMessage, ToolMessage
from langgraph.prebuilt import ToolNode
from langgraph.types import interrupt

from app.graph.state import AgentState
from app.tools.agent_tools import ALL_TOOLS, HUMAN_APPROVAL_REQUIRED_TOOLS, is_human_approval_required
from app.core.config import get_settings

import logging
logger = logging.getLogger(__name__)


settings = get_settings()


# === Инициализация LLM ===

# Создаём модель с привязанными инструментами
llm = ChatOpenAI(
    model=settings.OPENAI_MODEL,
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
- Создавать задачи в Jira
- Отправлять email
- Искать информацию в интернете
- Узнавать текущую дату и время

ВАЖНЫЕ ПРАВИЛА:
1. ПОИСК В ДОКУМЕНТАХ: Если пользователь спрашивает о специфичной информации 
(коды, инструкции, данные из файлов, внутренние правила, имена сотрудников), которую ты не знаешь наверняка, 
ТЫ ОБЯЗАН сначала использовать инструмент `search_documents`. Никогда не отвечай "я не знаю" или "у меня нет доступа", 
пока не попробуешь выполнить поиск.
2. ДЕЙСТВИЯ: Если пользователь просит выполнить действие (создать задачу, отправить email), 
НЕМЕДЛЕННО вызови соответствующий инструмент с нужными аргументами. Система автоматически остановит выполнение 
и запросит подтверждение у пользователя, если это необходимо.
3. НЕ спрашивай текстовое разрешение у пользователя ("Хотите, чтобы я это сделал?"). 
    Система автоматически остановит выполнение инструмента и запросит подтверждение у пользователя через интерфейс.
4. Просто вызови инструмент, и граф сам позаботится о Human-in-the-Loop.
5. Будь дружелюбным, но профессиональным.
6. Если не знаешь ответа или не хватает данных для инструмента — честно скажи об этом или задай уточняющий вопрос.

Текущая дата и время: {current_datetime}
"""


# === Узел 1: Agent Node ===

async def agent_node(state: AgentState) -> Dict[str, Any]:
    """
    Главный узел агента (асинхронный).
    
    Вызывает LLM с текущей историей сообщений и инструментами.
    Использует ainvoke, чтобы не блокировать event loop FastAPI.
    
    Args:
        state: Текущее состояние графа
    
    Returns:
        Обновления State (новые сообщения)
    """
    
    # Получаем историю сообщений
    messages = state["messages"]

    # получаем ID пользователя из контекста и добавляем его в правило
    user_context = state.get("user_context") or {}
    current_user_id = user_context.get("user_id", "unknown")
    user_id_instruction = f"\n\nВАЖНО: Текущий идентификатор пользователя, который задал вопрос: '{current_user_id}'."
    
    # Добавляем системный промпт в начало (если его ещё нет)
    if not messages or not isinstance(messages[0], SystemMessage):
        from datetime import datetime
        current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        system_message = SystemMessage(content=SYSTEM_PROMPT.format(current_datetime=current_datetime) + user_id_instruction)
        messages = [system_message] + messages
    
    # вызов LLM
    response = await llm_with_tools.ainvoke(messages)

    # logger.warning(f"🧠 [LLM OUTPUT] Tool calls: {response.tool_calls} | Content: {response.content}")
    
    # Возвращаем обновление State
    return {"messages": [response]}


# === Узел 2: Tools Node ===

# Используем готовый ToolNode из langgraph
# Он автоматически выполняет вызовы инструментов, которые запросила LLM
tools_node = ToolNode(ALL_TOOLS)


# === Узел 3: Human Approval Node ===

async def human_approval_node(state: AgentState) -> Dict[str, Any]:
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
    if not messages:
        return {}
    
    last_message = messages[-1]
    
    # Если это AI-сообщение с вызовами инструментов
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        for tool_call in last_message.tool_calls:
            if is_human_approval_required(tool_call["name"]):
                action_data = {
                    "action_type": tool_call["name"],
                    "tool_call_id": tool_call["id"],
                    "args": tool_call["args"],
                }
                
                # 1. ОСТАНАВЛИВАЕМ граф. 
                # Когда граф будет возобновлён через Command(resume=...), 
                # переменная `decision` получит это значение.
                decision = interrupt({
                    "type": "human_approval_required",
                    "message": f"Агент хочет выполнить действие '{tool_call['name']}'.",
                    "action_data": action_data,
                })
                
                # 2. ГРАФ ВОЗОБНОВЛЁН после Command(resume=...). Обрабатываем решение.
                if decision.get("approved"):
                    # Пользователь одобрил. 
                    # Возвращаем {}, чтобы условное ребро should_continue 
                    # снова увидело tool_calls и направило граф в tools_node.
                    return {}
                
                else:
                    # Пользователь отклонил.
                    # Имитация ответа инструмента об отказе, 
                    # чтобы LLM знала, что делать дальше (например, извиниться).
                    feedback = decision.get("feedback", "Причина не указана.")
                    rejection_message = ToolMessage(
                        content=f"Действие отклонено пользователем. Причина: {feedback}",
                        tool_call_id=tool_call["id"]
                    )
                    return {"messages": [rejection_message]}

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
