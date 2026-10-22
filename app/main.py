# app/main.py
#--------------------------------------------

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from app.api.routes import documents, conversations, chat, actions
from app.core.config import get_settings
from app.graph.builder import build_graph
import app.graph.builder as builder_module


settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # === Startup ===
    print("🚀 Инициализация LangGraph Checkpointer в PostgreSQL...")
    
    # возвращает контекстный менеджер, управляющий пулом соединений
    async with AsyncPostgresSaver.from_conn_string(settings.DATABASE_URL_CHECKPOINT) as checkpointer:
        
        await checkpointer.setup()
        print("✅ Checkpointer таблицы созданы/проверены.")
        
        # Собираем граф с активным чекпоинтером
        builder_module.graph = build_graph(checkpointer)
        print("✅ LangGraph успешно скомпилирован с AsyncPostgresSaver.")
        
        yield  

    print("🛑 Завершение работы Smart Agent API... (Пул соединений закрыт)")


# Создание FastAPI приложения
app = FastAPI(
    title="Smart Agent API",
    description="AI Agent with RAG, LangGraph and Human-in-the-Loop",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc",  # ReDoc
    openapi_url="/openapi.json",  # OpenAPI schema
)


# === Middleware ===

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене указать конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# === Routes ===

app.include_router(documents.router)
app.include_router(conversations.router)
app.include_router(chat.router)
app.include_router(actions.router)


# === Base Endpoints ===

@app.get(
    "/",
    tags=["base"],
    summary="Root endpoint",
    description="Базовая информация о API"
)
async def root():
    """Возвращает базовую информацию о API."""
    return {
        "message": "Smart Agent API",
        "version": "0.1.0",
        "docs": "/docs",
        "environment": settings.APP_ENV,
    }


@app.get(
    "/health",
    tags=["base"],
    summary="Health check",
    description="Проверка работоспособности сервиса"
)
async def health_check():
    """
    Health check endpoint.
    Используется для мониторинга и load balancer'ов.
    """
    return {
        "status": "healthy",
        "version": "0.1.0",
    }


@app.get(
    "/info",
    tags=["base"],
    summary="Service info",
    description="Детальная информация о сервисе"
)
async def service_info():
    """Возвращает детальную информацию о сервисе и его окружении."""
    return {
        "service": "Smart Agent",
        "version": "0.1.0",
        "environment": settings.APP_ENV,
        "debug": settings.DEBUG,
        "database": {
            "host": settings.POSTGRES_HOST,
            "port": settings.POSTGRES_PORT,
            "name": settings.POSTGRES_DB,
        },
        "qdrant": {
            "host": settings.QDRANT_HOST,
            "port": settings.QDRANT_PORT,
        },
    }
