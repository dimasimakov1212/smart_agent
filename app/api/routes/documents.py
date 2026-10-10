# app/api/routes/documents.py
#--------------------------------------------

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status

from app.api.deps import get_document_repo
from app.api.schemas import DocumentResponse, DocumentListResponse
from app.db.repositories import DocumentRepository

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post(
    "/upload",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Загрузить документ",
    description="Загружает файл и создаёт запись в базе данных.",
)
async def upload_document(
    user_id: str,
    file: UploadFile = File(...),
    repo: DocumentRepository = Depends(get_document_repo),
):
    """Загружает документ и сохраняет метаданные в БД"""

    content = await file.read()
    file_size = len(content)
    
    filename = file.filename or "unknown"
    file_type = filename.split(".")[-1].lower() if "." in filename else "unknown"
    
    document = await repo.create_document(
        filename=filename,
        file_type=file_type,
        file_size=file_size,
        user_id=user_id,
        metadata_json={"original_filename": filename},
    )
    
    return document


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

    documents = await repo.get_user_documents(user_id=user_id, limit=limit, offset=offset)
    
    return DocumentListResponse(
        documents=documents,
        total=len(documents),
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