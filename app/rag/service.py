# app/rag/service.py

import logging
import uuid
from typing import List, Dict, Any

from qdrant_client.http import models

from app.rag.client import rag_client, COLLECTION_NAME

logger = logging.getLogger(__name__)


class RAGService:
    """Бизнес-логика для работы с векторным поиском."""

    async def add_documents(self, texts: List[str], metadatas: List[Dict[str, Any]]) -> int:
        """Векторизует тексты и сохраняет их в Qdrant."""

        if not texts:
            return 0
            
        logger.info(f"🚀 Генерация эмбеддингов для {len(texts)} чанков...")
        
        # Используем уже инициализированный клиент
        vectors = await rag_client.embeddings.aembed_documents(texts)
        
        points = [
            models.PointStruct(
                id=str(uuid.uuid4()),
                vector=vector,
                payload=metadata
            )
            for vector, metadata in zip(vectors, metadatas)
        ]
        
        logger.info(f"📥 Upsert {len(points)} точек в Qdrant...")

        await rag_client.qdrant.upsert(
            collection_name=COLLECTION_NAME,
            points=points,
        )

        logger.info("✅ Чанки успешно сохранены в Qdrant.")

        return len(points)

    async def search(
        self, 
        query: str, 
        user_id: str, 
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Ищет релевантные документы в Qdrant с фильтрацией по user_id."""
        
        search_filter = models.Filter(
            must=[
                models.FieldCondition(
                    key="user_id",
                    match=models.MatchValue(value=user_id)
                )
            ]
        )
        
        # Генерируем вектор запроса
        query_vector = await rag_client.embeddings.aembed_query(query)
        
        response = await rag_client.qdrant.query_points(
            collection_name=COLLECTION_NAME,
            query=query_vector,
            query_filter=search_filter,
            limit=limit,
            with_payload=True,
        )
        
        formatted_results = []
        # response.points содержит список найденных точек (ScoredPoint)
        for hit in response.points:
            formatted_results.append({
                "score": hit.score,
                "filename": hit.payload.get("filename", "Unknown"),
                "content": hit.payload.get("text_content", ""),
            })
            
        return formatted_results


# Глобальный инстанс сервиса
rag_service = RAGService()
