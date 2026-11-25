# app/rag/__init__.py

from app.rag.client import COLLECTION_NAME, EMBEDDING_MODEL, rag_client
from app.rag.service import RAGService, rag_service

__all__ = [
    "rag_client",
    "rag_service",
    "RAGService",
    "COLLECTION_NAME",
    "EMBEDDING_MODEL",
]
