# app/rag/client.py

import logging
from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models
from langchain_openai import OpenAIEmbeddings

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

COLLECTION_NAME = "smart_agent_documents"
EMBEDDING_MODEL = settings.OPENAI_EMBEDDINGS_MODEL


class RAGClient:
    """Управляет подключениями к Qdrant и моделям эмбеддингов."""
    
    def __init__(self):
        self.qdrant: AsyncQdrantClient | None = None
        self.embeddings: OpenAIEmbeddings | None = None
        self._is_initialized = False

    async def initialize(self) -> None:
        """Инициализирует клиенты, если это еще не сделано."""

        if self._is_initialized:
            return

        logger.info("🚀 Инициализация RAG клиентов (Qdrant + Embeddings)...")
        
        # 1. Создаем асинхронный клиент Qdrant
        self.qdrant = AsyncQdrantClient(
            url=f"http://{settings.QDRANT_HOST}:{settings.QDRANT_PORT}",
            prefer_grpc=False,
        )
        
        # 2. Проверяем/создаем коллекцию
        collections = await self.qdrant.get_collections()
        collection_names = [c.name for c in collections.collections]
        
        if COLLECTION_NAME not in collection_names:
            logger.info(f"📦 Создание коллекции Qdrant: {COLLECTION_NAME}")

            await self.qdrant.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=models.VectorParams(
                    size=1536,
                    distance=models.Distance.COSINE,
                ),
            )
            logger.info("✅ Коллекция создана.")
        else:
            logger.info("✅ Коллекция уже существует.")
            
        # 3. Инициализируем эмбеддинги
        self.embeddings = OpenAIEmbeddings(
            model=EMBEDDING_MODEL,
            openai_api_key=settings.OPENAI_API_KEY,
            openai_api_base=settings.OPENAI_EMBEDDINGS_URL,
        )
        
        self._is_initialized = True
        logger.info("✅ RAG клиенты успешно инициализированы.")


# Глобальный инстанс клиента
rag_client = RAGClient()
