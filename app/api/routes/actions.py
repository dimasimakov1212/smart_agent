# app/api/routes/actions.py
#--------------------------------------------

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_chat_service, get_pending_action_repo
from app.api.schemas import PendingActionResponse, ApprovalRequest
from app.core.exceptions import ActionAlreadyResolvedError, ActionNotFoundError
from app.db.repositories import PendingActionRepository
from app.services.chat_service import ChatService

router = APIRouter(prefix="/actions", tags=["actions"])


@router.get(
    "/{action_id}",
    response_model=PendingActionResponse,
    summary="Получить pending action",
    description="Возвращает информацию о действии, ожидающем подтверждения.",
)
async def get_pending_action(
    action_id: int,
    repo: PendingActionRepository = Depends(get_pending_action_repo),
):
    """Получает pending action по ID."""

    action = await repo.get_pending_action(action_id)
    
    if not action:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Action with id {action_id} not found",
        )
    
    return action


@router.post(
    "/{action_id}/approve",
    response_model=PendingActionResponse,
    summary="Одобрить действие",
    description="Одобряет действие агента",
)
async def approve_action(
    action_id: int,
    request: ApprovalRequest,
    service: ChatService = Depends(get_chat_service),
):
    """Одобряет действие и ВОЗОБНОВЛЯЕТ выполнение LangGraph."""
    try:
        result = await service.resume_action(
            action_id=action_id,
            user_id=request.user_id,
            approved=True,
            feedback=request.feedback,
        )
    except ActionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ActionAlreadyResolvedError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Возвращаем обновлённое действие из БД для удобства клиента
    # (Оно уже обновлено внутри service.resume_action)
    updated_action = await service.actions.get_pending_action(action_id)
    return updated_action


@router.post(
    "/{action_id}/reject",
    response_model=PendingActionResponse,
    summary="Отклонить действие",
    description="Отклоняет действие агента",
)
async def reject_action(
    action_id: int,
    request: ApprovalRequest,
    service: ChatService = Depends(get_chat_service),
):
    """Отклоняет действие и ВОЗОБНОВЛЯЕТ выполнение LangGraph с фидбеком."""
    try:
        result = await service.resume_action(
            action_id=action_id,
            user_id=request.user_id,
            approved=False,
            feedback=request.feedback,
        )
    except ActionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ActionAlreadyResolvedError as e:
        raise HTTPException(status_code=400, detail=str(e))

    updated_action = await service.actions.get_pending_action(action_id)
    return updated_action
