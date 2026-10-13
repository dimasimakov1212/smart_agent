# app/api/routes/actions.py
#--------------------------------------------

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_pending_action_repo, get_conversation_repo
from app.api.schemas import PendingActionResponse, ApprovalRequest
from app.db.repositories import PendingActionRepository, ConversationRepository

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
    action_repo: PendingActionRepository = Depends(get_pending_action_repo),
    conv_repo: ConversationRepository = Depends(get_conversation_repo),
):
    """
    Одобряет действие агента.
    
    Логика:
    1. Проверяем, что action существует и в статусе 'pending'
    2. Обновляем статус на 'approved'
    3. Resume LangGraph с результатом действия
    4. Добавляем сообщение в тред о том, что действие одобрено
    """
    # Получаем action
    action = await action_repo.get_pending_action(action_id)
    if not action:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Action with id {action_id} not found",
        )
    
    # Проверяем статус
    if action.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Action is already {action.status}, cannot approve",
        )
    
    # Одобряем действие
    await action_repo.approve_action(
        action_id=action_id,
        approved_by=request.user_id,
        result={"approved": True, "feedback": request.feedback},
    )
    
    # Добавляем сообщение в тред
    feedback_text = f" (с комментарием: {request.feedback})" if request.feedback else ""
    await conv_repo.add_message(
        thread_id=action.thread_id,
        role="system",
        content=f"✅ Действие '{action.action_type}' одобрено пользователем {request.user_id}{feedback_text}",
    )
    
    # TODO: В будущем здесь будет resume LangGraph
    # response = graph.invoke(Command(resume={"action_approved": True}), config)
    
    # Получаем обновлённый action для возврата
    updated_action = await action_repo.get_pending_action(action_id)
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
    action_repo: PendingActionRepository = Depends(get_pending_action_repo),
    conv_repo: ConversationRepository = Depends(get_conversation_repo),
):
    """
    Отклоняет действие агента.
    
    Логика:
    1. Проверяем, что action существует и в статусе 'pending'
    2. Обновляем статус на 'rejected'
    3. Resume LangGraph с фидбеком пользователя
    4. Добавляем сообщение в тред о том, что действие отклонено
    """
    # Получаем action
    action = await action_repo.get_pending_action(action_id)
    if not action:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Action with id {action_id} not found",
        )
    
    # Проверяем статус
    if action.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Action is already {action.status}, cannot reject",
        )
    
    # Отклоняем действие
    await action_repo.reject_action(
        action_id=action_id,
        rejected_by=request.user_id,
    )
    
    # Добавляем сообщение в тред
    feedback_text = f" Причина: {request.feedback}" if request.feedback else ""
    await conv_repo.add_message(
        thread_id=action.thread_id,
        role="system",
        content=f"❌ Действие '{action.action_type}' отклонено пользователем {request.user_id}.{feedback_text}",
    )
    
    # TODO: В будущем здесь будет resume LangGraph с фидбеком
    # response = graph.invoke(Command(resume={"action_rejected": True, "feedback": request.feedback}), config)
    
    # Получаем обновлённый action для возврата
    updated_action = await action_repo.get_pending_action(action_id)
    return updated_action