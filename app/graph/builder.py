# app/graph/builder.py
#--------------------------------------------

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

from app.graph.state import AgentState
from app.graph.nodes import agent_node, tools_node, human_approval_node, should_continue


def build_graph() -> StateGraph:
    """
    Строит и компилирует LangGraph.
    
    Архитектура графа:
    1. START -> agent_node
    2. agent_node -> should_continue (условное ребро)
      - Если LLM вызвала инструмент, требующий подтверждения -> human_approval_node
      - Если LLM вызвала обычный инструмент -> tools_node
      - Если LLM просто ответила -> END
    3. human_approval_node -> interrupt (пауза)
      - При resume (Command) -> tools_node (для выполнения одобренного действия)
    4. tools_node -> agent_node (LLM формулирует ответ на основе результата инструмента)
    """
    
    # 1. Инициализируем граф с нашим State
    builder = StateGraph(AgentState)
    
    # 2. Добавляем узлы
    builder.add_node("agent", agent_node)
    builder.add_node("tools", tools_node)
    builder.add_node("human_approval", human_approval_node)
    
    # 3. Настраиваем рёбра (маршрутизацию)
    
    # Точка входа всегда в agent_node
    builder.set_entry_point("agent")
    
    # Условное ребро после agent_node
    builder.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            "human_approval": "human_approval",
            "end": END,
        }
    )
    
    # После human_approval (если пользователь одобрил и мы сделали resume), 
    # идём выполнять инструмент
    builder.add_edge("human_approval", "tools")
    
    # После выполнения инструментов, возвращаемся к агенту для формулировки ответа
    builder.add_edge("tools", "agent")
    
    # 4. Добавляем Checkpointer (память)
    # Для локальной разработки используем MemorySaver.
    # В продакшене здесь будет AsyncPostgresSaver или AsyncSqliteSaver.
    checkpointer = MemorySaver()
    
    # 5. Компилируем граф
    graph = builder.compile(checkpointer=checkpointer)
    
    return graph


# Создаём глобальный экземпляр графа для использования в API
graph = build_graph()
