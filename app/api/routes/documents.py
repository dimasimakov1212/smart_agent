# app/api/routes/documents.py
#--------------------------------------------

import logging
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status

from app.api.deps import get_document_service, get_document_repo
from app.api.schemas import DocumentResponse, DocumentListResponse
from app.db.repositories import DocumentRepository
from app.services.document_service import DocumentService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post(
    "/upload",
    # response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Загрузить и обработать документ",
    description="Загружает файл, извлекает текст, чанкает и сохраняет векторы в Qdrant.",
)
async def upload_document(
    user_id: str,
    file: UploadFile = File(..., description="Файл для загрузки (PDF, TXT и т.д.)"),
    service: DocumentService = Depends(get_document_service),
):
    """
    Тонкий роутер: только HTTP-валидация и делегирование бизнес-логики в сервис.
    """

    # Читаем содержимое файла
    content = await file.read()
    file_size = len(content)
    
    if file_size == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Файл пуст")
    
    filename = file.filename or "unknown"
    file_type = filename.split(".")[-1].lower() if "." in filename else "unknown"
    
    # Обработка документа
    try:
        document = await service.upload_and_process_document(
            content=content,
            filename=filename,
            file_type=file_type,
            file_size=file_size,
            user_id=user_id,
        )
        return document
        
    except ValueError as e:
        logger.error(f"❌ Ошибка валидации документа '{filename}': {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    
    except Exception as e:
        logger.error(f"❌ Критическая ошибка обработки документа '{filename}': {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Ошибка при векторизации и сохранении документа"
        )


@router.get(
    "/user/{user_id}",
    response_model=DocumentListResponse,
    summary="Получить документы пользователя",
)
async def get_user_documents(
    user_id: str,
    limit: int = 50,
    offset: int = 0,
    repo: DocumentRepository = Depends(get_document_repo),
):
    """Получает список документов пользователя с пагинацией."""

    documents, total = await repo.get_user_documents(user_id=user_id, limit=limit, offset=offset)
    
    return DocumentListResponse(
        documents=documents,
        total=total,
    )


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
    summary="Получить документ по ID",
)
async def get_document(
    document_id: int,
    repo: DocumentRepository = Depends(get_document_repo),
):
    """Получает документ по ID."""
    
    document = await repo.get_document_by_id(document_id)
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with id {document_id} not found",
        )
    
    return document