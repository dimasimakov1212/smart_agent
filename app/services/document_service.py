# app/services/document_service.py

import logging
from io import BytesIO
from typing import List, Dict, Any

from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.rag.service import rag_service
from app.db.repositories import DocumentRepository
from app.db.models import Document

logger = logging.getLogger(__name__)


class DocumentService:
    def __init__(self, doc_repo: DocumentRepository):
        self.doc_repo = doc_repo
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            length_function=len,
        )

    async def upload_and_process_document(
        self,
        content: bytes,
        filename: str,
        file_type: str,
        file_size: int,
        user_id: str,
    ) -> Document:
        """
        Полный цикл обработки документа: БД -> Текст -> Чанки -> Qdrant -> Обновление БД.
        """
        
        # 1. Создаем базовую запись в БД
        document = await self.doc_repo.create_document(
            filename=filename,
            file_type=file_type,
            file_size=file_size,
            user_id=user_id,
            metadata_json={"original_filename": filename},
        )
        
        # 2. Извлекаем текст
        text = self._extract_text(content, file_type)
        if not text.strip():
            raise ValueError("Не удалось извлечь текст из файла или файл пуст")

        # 3. Чанкинг
        langchain_docs = self.text_splitter.create_documents([text])
        
        texts = []
        metadatas: List[Dict[str, Any]] = []
        
        for i, doc in enumerate(langchain_docs):
            texts.append(doc.page_content)
            metadatas.append({
                "document_id": document.id,
                "user_id": user_id,
                "filename": filename,
                "chunk_index": i,
                "text_content": doc.page_content
            })

        # 4. Сохранение в Qdrant
        chunks_count = await rag_service.add_documents(texts, metadatas)
        
        # 5. Обновляем счетчик чанков в БД (метод уже есть в твоем репозитории!)
        await self.doc_repo.update_document_tokens(document.id, chunks_count)

        logger.warning(f"✅ [SERVICE] Документ '{filename}' полностью обработан, создано {chunks_count} чанков.")

        return document

    def _extract_text(self, file_content: bytes, file_type: str) -> str:
        if file_type == "pdf":
            reader = PdfReader(BytesIO(file_content))
            return "\n".join([page.extract_text() or "" for page in reader.pages])
        else:
            return file_content.decode("utf-8", errors="ignore")
