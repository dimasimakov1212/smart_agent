# app/rag/__init__.py

from app.rag.client import rag_client, COLLECTION_NAME, EMBEDDING_MODEL
from app.rag.service import rag_service, RAGService

__all__ = [
    "rag_client",
    "rag_service",
    "RAGService",
    "COLLECTION_NAME",
    "EMBEDDING_MODEL",
]
