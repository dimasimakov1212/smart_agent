# app/graph/builder.py
#--------------------------------------------

from langgraph.graph import StateGraph, END
from langgraph.graph.state import CompiledStateGraph

from app.graph.state import AgentState
from app.graph.nodes import agent_node, tools_node, human_approval_node, should_continue

# Глобальная переменная. Изначально None. 
# Заполняется при старте приложения в main.py
graph: CompiledStateGraph = None  # type: ignore


def build_graph(checkpointer) -> CompiledStateGraph:
    """
    Строит и компилирует LangGraph с переданным чекпоинтером.
    """
    builder = StateGraph(AgentState)
    
    builder.add_node("agent", agent_node)
    builder.add_node("tools", tools_node)
    builder.add_node("human_approval", human_approval_node)
    
    builder.set_entry_point("agent")
    
    builder.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            "human_approval": "human_approval",
            "end": END,
        }
    )
    
    builder.add_edge("human_approval", "tools")
    builder.add_edge("tools", "agent")
    
    # Компилируем с тем чекпоинтером, который был передан (AsyncPostgresSaver)
    return builder.compile(checkpointer=checkpointer)
