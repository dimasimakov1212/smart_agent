# app/graph/agent_tools.py
#--------------------------------------------

from typing import Dict, Any, List, Optional
from datetime import datetime
from langchain_core.tools import tool


# === Информационные инструменты ===

@tool
def get_current_datetime() -> str:
    """
    Получает текущую дату и время.
    Используй, когда нужно узнать текущее время, дату или день недели.
    """
    now = datetime.now()
    return f"Текущая дата и время: {now.strftime('%Y-%m-%d %H:%M:%S')} ({now.strftime('%A')})"


@tool
def search_documents(query: str, user_id: str, limit: int = 5) -> str:
    """
    Ищет релевантные документы пользователя по запросу.
    
    Args:
        query: Поисковый запрос
        user_id: ID пользователя, чьи документы ищем
        limit: Максимальное количество результатов
    
    Returns:
        Список найденных фрагментов документов с метаданными
    
    Используй, когда нужно найти информацию в загруженных документах пользователя.
    """
    # TODO: Интеграция с Qdrant для векторного поиска
    # Сейчас возвращаем заглушку
    
    return (
        f"🔍 Поиск документов для пользователя '{user_id}' по запросу: '{query}'\n\n"
        "🚧 Это заглушка — реальный RAG-поиск через Qdrant будет добавлен позже.\n\n"
        "В будущем здесь будут результаты векторного поиска с релевантными фрагментами документов."
    )


# === Инструменты действий (требуют подтверждения) ===

@tool
def create_jira_task(
    title: str,
    description: str,
    priority: str = "medium",
    assignee: Optional[str] = None,
) -> str:
    """
    Создаёт задачу в Jira.
    
    Args:
        title: Заголовок задачи
        description: Описание задачи
        priority: Приоритет (low, medium, high, critical)
        assignee: Исполнитель (опционально)
    
    Returns:
        Информация о созданной задаче
    
    ВАЖНО: Это действие требует подтверждения пользователя (Human-in-the-Loop).
    Перед выполнением агент должен дождаться одобрения.
    """
    # TODO: Интеграция с Jira API
    # Сейчас возвращаем заглушку
    
    task_info = {
        "task_id": "PROJ-123",
        "title": title,
        "description": description,
        "priority": priority,
        "assignee": assignee or "Unassigned",
        "status": "created",
    }
    
    return (
        f"✅ Задача в Jira создана (заглушка):\n"
        f"- ID: {task_info['task_id']}\n"
        f"- Заголовок: {task_info['title']}\n"
        f"- Приоритет: {task_info['priority']}\n"
        f"- Исполнитель: {task_info['assignee']}\n\n"
        "🚧 Это заглушка — реальная интеграция с Jira будет добавлена позже."
    )


@tool
def send_email(
    to: str,
    subject: str,
    body: str,
    cc: Optional[List[str]] = None,
) -> str:
    """
    Отправляет email.
    
    Args:
        to: Email получателя
        subject: Тема письма
        body: Тело письма
        cc: Список email для копии (опционально)
    
    Returns:
        Информация об отправленном письме
    
    ВАЖНО: Это действие требует подтверждения пользователя (Human-in-the-Loop).
    Перед выполнением агент должен дождаться одобрения.
    """
    # TODO: Интеграция с SMTP или email API
    # Сейчас возвращаем заглушку
    
    return (
        f"✅ Email отправлен (заглушка):\n"
        f"- Кому: {to}\n"
        f"- Тема: {subject}\n"
        f"- Тело: {body[:100]}...\n"
        f"- Копия: {', '.join(cc) if cc else 'нет'}\n\n"
        "🚧 Это заглушка — реальная отправка email будет добавлена позже."
    )


@tool
def search_web(query: str) -> str:
    """
    Ищет информацию в интернете.
    
    Args:
        query: Поисковый запрос
    
    Returns:
        Результаты веб-поиска
    
    Используй, когда нужно найти актуальную информацию, которой нет в документах пользователя.
    """
    # TODO: Интеграция с поисковым API (Google, Bing, и т.д.)
    # Сейчас возвращаем заглушку
    
    return (
        f"🌐 Веб-поиск по запросу: '{query}'\n\n"
        "🚧 Это заглушка — реальный веб-поиск будет добавлен позже.\n\n"
        "В будущем здесь будут результаты из поисковой системы."
    )


# === Реестр инструментов ===

# Все инструменты, доступные агенту
ALL_TOOLS = [
    get_current_datetime,
    search_documents,
    create_jira_task,
    send_email,
    search_web,
]

# Инструменты, которые требуют подтверждения (Human-in-the-Loop)
HUMAN_APPROVAL_REQUIRED_TOOLS = [
    create_jira_task,
    send_email,
]


def get_tool_by_name(name: str):
    """Получает инструмент по имени."""
    for tool in ALL_TOOLS:
        if tool.name == name:
            return tool
    return None


def is_human_approval_required(tool_name: str) -> bool:
    """Проверяет, требует ли инструмент подтверждения пользователя."""
    for tool in HUMAN_APPROVAL_REQUIRED_TOOLS:
        if tool.name == tool_name:
            return True
    return False
