# app/tools/agent_tools.py
#--------------------------------------------

from typing import List, Literal, Optional
from datetime import datetime
from langchain_core.tools import tool

import uuid
import logging

from app.rag.service import rag_service

logger = logging.getLogger(__name__)


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
async def search_documents(query: str, user_id: str, limit: int = 5) -> str:
    """
    Ищет релевантные фрагменты в загруженных документах пользователя.
    
    ВАЖНО: Используй этот инструмент ВСЕГДА, когда пользователь спрашивает о:
    - Содержимом файлов, PDF или текстовых документов
    - Внутренних кодах, паролях, инструкциях, правилах
    - Специфичных данных компании, проекта или сотрудников
    
    Args:
        query: Поисковый запрос (вопрос пользователя или ключевые слова)
        user_id: ID пользователя (ОБЯЗАТЕЛЬНО для фильтрации по его документам)
        limit: Максимальное количество результатов (по умолчанию 5)
    
    Returns:
        Отформатированная строка с найденными фрагментами и именами файлов.
    """

    logger.info(f"🔍 RAG Поиск: user={user_id}, query='{query}'")
    
    try:
        results = await rag_service.search(query=query, user_id=user_id, limit=limit)
        
        if not results:
            return "📄 В ваших документах не найдено информации, соответствующей запросу."
        
        formatted_results = []
        for i, res in enumerate(results, 1):
            formatted_results.append(
                f"[Фрагмент {i}] Файл: {res['filename']}\n"
                f"Содержимое: {res['content']}\n"
                f"(Релевантность: {res['score']:.2f})"
            )
            
        return "📄 Найденная информация в документах:\n\n" + "\n---\n".join(formatted_results)
        
    except Exception as e:
        logger.error(f"❌ Ошибка RAG поиска: {e}")
        return f"⚠️ Произошла ошибка при поиске в документах: {str(e)}"


# === Инструменты действий (требуют подтверждения) ===

@tool
def create_jira_task(
    title: str,
    description: str,
    priority: Literal["low", "medium", "high", "critical"] = "medium",
    assignee: Optional[str] = None,
) -> str:
    """
    Создаёт задачу в Jira.
    
    Args:
        title: Заголовок задачи (обязательно)
        description: Описание задачи (обязательно)
        priority: Приоритет задачи. Строго одно из: "low", "medium", "high", "critical". По умолчанию "medium".
        assignee: Исполнитель (опционально)
    
    Returns:
        Информация о созданной задаче.
    
    Используй этот инструмент, когда пользователь явно просит создать задачу в Jira 
    и предоставил заголовок и описание.
    """

    # 🚀 ГЕНЕРИРУЕМ УНИКАЛЬНЫЙ ID ПРЯМО ЗДЕСЬ
    # LLM НЕ МОЖЕТ это угадать. Если этот ID появится в ответе, код точно выполнялся.
    real_task_id = f"JIRA-{uuid.uuid4().hex[:8].upper()}"
    
    # 🚀 ПИШЕМ В КОНСОЛЬ СЕРВЕРА
    logger.warning(f"🛠️ [TOOL EXECUTED] create_jira_task | ID: {real_task_id} | Title: {title}")
    

    # TODO: Интеграция с Jira API
    # Сейчас возвращаем заглушку
    
    task_info = {
        "task_id": real_task_id,
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
    
    Используй этот инструмент, когда пользователь явно просит отправить email 
    и предоставил email получателя, тему письма и тело письма
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
