"""
Router para gerenciar feedback de bloqueio de dispositivos.
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timedelta

from db.enums import FeedbackStatus
from services_firewalls.blocking_feedback_service import BlockingFeedbackService

router = APIRouter()
feedback_service = BlockingFeedbackService()

# Pydantic models para request/response
class FeedbackCreate(BaseModel):
    """Modelo para criação de feedback."""
    dhcp_mapping_id: int = Field(..., description="ID do mapeamento DHCP")
    user_feedback: str = Field(..., min_length=1, max_length=2000, description="Feedback detalhado do usuário")
    feedback_by: str = Field(..., min_length=1, max_length=100, description="Nome/identificação do usuário")
    problem_resolved: Optional[bool] = Field(None, description="Se o problema foi resolvido")

class FeedbackUpdate(BaseModel):
    """Modelo para atualização de feedback."""
    status: FeedbackStatus = Field(..., description="Novo status do feedback")
    admin_notes: Optional[str] = Field(None, max_length=2000, description="Notas administrativas")
    admin_reviewed_by: Optional[str] = Field(None, max_length=100, description="Quem revisou o feedback")

class FeedbackResponse(BaseModel):
    """Modelo de resposta para feedback."""
    id: int
    dhcp_mapping_id: int
    user_feedback: Optional[str]
    problem_resolved: Optional[bool]
    feedback_date: Optional[str]
    feedback_by: Optional[str]
    admin_notes: Optional[str]
    admin_review_date: Optional[str]
    admin_reviewed_by: Optional[str]
    status: Optional[str]
    created_at: Optional[str]
    updated_at: Optional[str]

class FeedbackStatsResponse(BaseModel):
    """Modelo de resposta para estatísticas."""
    total_feedbacks: int
    status_stats: dict
    resolved_stats: dict
    generated_at: str

@router.post("/feedback/", response_model=FeedbackResponse)
async def create_feedback(feedback_data: FeedbackCreate):
    """
    Cria um novo feedback de bloqueio.
    
    Args:
        feedback_data: Dados do feedback
        
    Returns:
        Feedback criado
    """
    try:
        feedback = feedback_service.create_feedback(
            dhcp_mapping_id=feedback_data.dhcp_mapping_id,
            user_feedback=feedback_data.user_feedback,
            feedback_by=feedback_data.feedback_by,
            problem_resolved=feedback_data.problem_resolved
        )
        
        if not feedback:
            raise HTTPException(status_code=400, detail="Erro ao criar feedback")
        
        return FeedbackResponse(**feedback.to_dict())
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.get("/feedback/dhcp/{dhcp_mapping_id}", response_model=List[FeedbackResponse])
async def get_feedback_by_dhcp(
    dhcp_mapping_id: int,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """
    Busca feedback por mapeamento DHCP.
    
    Args:
        dhcp_mapping_id: ID do mapeamento DHCP
        limit: Limite de resultados (1-100)
        offset: Offset para paginação
        
    Returns:
        Lista de feedbacks
    """
    try:
        feedbacks = feedback_service.get_feedback_by_dhcp_mapping(
            dhcp_mapping_id=dhcp_mapping_id,
            limit=limit,
            offset=offset
        )
        
        return [FeedbackResponse(**feedback.to_dict()) for feedback in feedbacks]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.get("/feedback/status/{status}", response_model=List[FeedbackResponse])
async def get_feedback_by_status(
    status: FeedbackStatus,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """
    Busca feedback por status.
    
    Args:
        status: Status do feedback
        limit: Limite de resultados (1-100)
        offset: Offset para paginação
        
    Returns:
        Lista de feedbacks
    """
    try:
        feedbacks = feedback_service.get_feedback_by_status(
            status=status,
            limit=limit,
            offset=offset
        )
        
        return [FeedbackResponse(**feedback.to_dict()) for feedback in feedbacks]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.get("/feedback/user/{feedback_by}", response_model=List[FeedbackResponse])
async def get_feedback_by_user(
    feedback_by: str,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """
    Busca feedback por usuário.
    
    Args:
        feedback_by: Nome/identificação do usuário
        limit: Limite de resultados (1-100)
        offset: Offset para paginação
        
    Returns:
        Lista de feedbacks
    """
    try:
        feedbacks = feedback_service.get_feedback_by_user(
            feedback_by=feedback_by,
            limit=limit,
            offset=offset
        )
        
        return [FeedbackResponse(**feedback.to_dict()) for feedback in feedbacks]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.put("/feedback/{feedback_id}/status", response_model=dict)
async def update_feedback_status(
    feedback_id: int,
    update_data: FeedbackUpdate
):
    """
    Atualiza o status do feedback.
    
    Args:
        feedback_id: ID do feedback
        update_data: Dados da atualização
        
    Returns:
        Confirmação da atualização
    """
    try:
        success = feedback_service.update_feedback_status(
            feedback_id=feedback_id,
            status=update_data.status,
            admin_notes=update_data.admin_notes,
            admin_reviewed_by=update_data.admin_reviewed_by
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Feedback não encontrado")
        
        return {"message": "Status atualizado com sucesso", "feedback_id": feedback_id}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.get("/feedback/stats", response_model=FeedbackStatsResponse)
async def get_feedback_stats():
    """
    Retorna estatísticas dos feedbacks.
    
    Returns:
        Estatísticas dos feedbacks
    """
    try:
        stats = feedback_service.get_feedback_stats()
        
        if not stats:
            raise HTTPException(status_code=500, detail="Erro ao gerar estatísticas")
        
        return FeedbackStatsResponse(**stats)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.get("/feedback/recent", response_model=List[FeedbackResponse])
async def get_recent_feedback(
    days: int = Query(7, ge=1, le=30)
):
    """
    Busca feedbacks recentes.
    
    Args:
        days: Número de dias para buscar (1-30)
        
    Returns:
        Lista de feedbacks recentes
    """
    try:
        feedbacks = feedback_service.get_recent_feedback(days=days)
        
        return [FeedbackResponse(**feedback.to_dict()) for feedback in feedbacks]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.post("/feedback/admin-block", response_model=FeedbackResponse)
async def create_admin_blocking_feedback(feedback_data: dict):
    """
    Cria um feedback de bloqueio administrativo.
    
    Args:
        feedback_data: Dados do bloqueio administrativo
        
    Returns:
        Feedback criado
    """
    try:
        feedback = feedback_service.create_admin_blocking_feedback(
            dhcp_mapping_id=feedback_data.get('dhcp_mapping_id'),
            admin_reason=feedback_data.get('admin_reason', ''),
            admin_name=feedback_data.get('admin_name', 'Administrador'),
            problem_resolved=feedback_data.get('problem_resolved', None)
        )
        
        if not feedback:
            raise HTTPException(status_code=400, detail="Erro ao criar feedback administrativo")
        
        return FeedbackResponse(**feedback.to_dict())
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.patch("/feedback/{feedback_id}", response_model=FeedbackResponse)
async def update_feedback_resolution(feedback_id: int, update_data: dict):
    """
    Atualiza o status de resolução de um feedback.
    
    Args:
        feedback_id: ID do feedback
        update_data: Dados da atualização (problem_resolved)
        
    Returns:
        Feedback atualizado
    """
    try:
        feedback = feedback_service.update_feedback_resolution(
            feedback_id=feedback_id,
            problem_resolved=update_data.get('problem_resolved')
        )
        
        if not feedback:
            raise HTTPException(status_code=404, detail="Feedback não encontrado")
        
        return FeedbackResponse(**feedback.to_dict())
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.get("/feedback/{feedback_id}", response_model=FeedbackResponse)
async def get_feedback_by_id(feedback_id: int):
    """
    Busca feedback por ID.
    
    Args:
        feedback_id: ID do feedback
        
    Returns:
        Feedback encontrado
    """
    try:
        from sqlalchemy.orm import Session
        from db.session import get_db_session
        from db.models import BlockingFeedbackHistory
        
        with get_db_session() as db:
            feedback = db.query(BlockingFeedbackHistory).filter(
                BlockingFeedbackHistory.id == feedback_id
            ).first()
            
            if not feedback:
                raise HTTPException(status_code=404, detail="Feedback não encontrado")
            
            return FeedbackResponse(**feedback.to_dict())
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")
