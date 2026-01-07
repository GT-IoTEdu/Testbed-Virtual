"""
Serviço para gerenciar feedback de bloqueio de dispositivos.
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, asc

from db.models import BlockingFeedbackHistory, DhcpStaticMapping
from db.enums import FeedbackStatus
from db.session import get_db_session

logger = logging.getLogger(__name__)

class BlockingFeedbackService:
    """Serviço para gerenciar feedback de bloqueio de dispositivos."""
    
    def __init__(self):
        """Inicializa o serviço de feedback."""
        pass
    
    def create_feedback(
        self, 
        dhcp_mapping_id: int,
        user_feedback: str,
        feedback_by: str,
        problem_resolved: Optional[bool] = None
    ) -> Optional[BlockingFeedbackHistory]:
        """
        Cria um novo feedback de bloqueio.
        
        Args:
            dhcp_mapping_id: ID do mapeamento DHCP
            user_feedback: Feedback detalhado do usuário
            feedback_by: Nome/identificação do usuário
            problem_resolved: Se o problema foi resolvido (opcional)
            
        Returns:
            Feedback criado ou None em caso de erro
        """
        try:
            with get_db_session() as db:
                # Verifica se o mapeamento DHCP existe
                dhcp_mapping = db.query(DhcpStaticMapping).filter(
                    DhcpStaticMapping.id == dhcp_mapping_id
                ).first()
                
                if not dhcp_mapping:
                    logger.error(f"Mapeamento DHCP {dhcp_mapping_id} não encontrado")
                    return None
                
                # Cria o feedback
                feedback = BlockingFeedbackHistory(
                    dhcp_mapping_id=dhcp_mapping_id,
                    user_feedback=user_feedback,
                    feedback_by=feedback_by,
                    problem_resolved=problem_resolved,
                    status=FeedbackStatus.PENDING
                )
                
                db.add(feedback)
                db.commit()
                db.refresh(feedback)
                
                logger.info(f"Feedback de bloqueio criado com ID: {feedback.id}")
                return feedback
                
        except Exception as e:
            logger.error(f"Erro ao criar feedback de bloqueio: {e}")
            return None
    
    def get_feedback_by_dhcp_mapping(
        self, 
        dhcp_mapping_id: int,
        limit: int = 10,
        offset: int = 0
    ) -> List[BlockingFeedbackHistory]:
        """
        Busca feedback por mapeamento DHCP.
        
        Args:
            dhcp_mapping_id: ID do mapeamento DHCP
            limit: Limite de resultados
            offset: Offset para paginação
            
        Returns:
            Lista de feedback
        """
        try:
            with get_db_session() as db:
                feedbacks = db.query(BlockingFeedbackHistory).filter(
                    BlockingFeedbackHistory.dhcp_mapping_id == dhcp_mapping_id
                ).order_by(desc(BlockingFeedbackHistory.feedback_date)).offset(offset).limit(limit).all()
                
                logger.info(f"Encontrados {len(feedbacks)} feedbacks para mapeamento {dhcp_mapping_id}")
                return feedbacks
                
        except Exception as e:
            logger.error(f"Erro ao buscar feedback por mapeamento: {e}")
            return []
    
    def get_feedback_by_status(
        self, 
        status: FeedbackStatus,
        limit: int = 50,
        offset: int = 0
    ) -> List[BlockingFeedbackHistory]:
        """
        Busca feedback por status.
        
        Args:
            status: Status do feedback
            limit: Limite de resultados
            offset: Offset para paginação
            
        Returns:
            Lista de feedback
        """
        try:
            with get_db_session() as db:
                feedbacks = db.query(BlockingFeedbackHistory).filter(
                    BlockingFeedbackHistory.status == status
                ).order_by(desc(BlockingFeedbackHistory.feedback_date)).offset(offset).limit(limit).all()
                
                logger.info(f"Encontrados {len(feedbacks)} feedbacks com status {status}")
                return feedbacks
                
        except Exception as e:
            logger.error(f"Erro ao buscar feedback por status: {e}")
            return []
    
    def get_feedback_by_user(
        self, 
        feedback_by: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[BlockingFeedbackHistory]:
        """
        Busca feedback por usuário.
        
        Args:
            feedback_by: Nome/identificação do usuário
            limit: Limite de resultados
            offset: Offset para paginação
            
        Returns:
            Lista de feedback
        """
        try:
            with get_db_session() as db:
                feedbacks = db.query(BlockingFeedbackHistory).filter(
                    BlockingFeedbackHistory.feedback_by == feedback_by
                ).order_by(desc(BlockingFeedbackHistory.feedback_date)).offset(offset).limit(limit).all()
                
                logger.info(f"Encontrados {len(feedbacks)} feedbacks do usuário {feedback_by}")
                return feedbacks
                
        except Exception as e:
            logger.error(f"Erro ao buscar feedback por usuário: {e}")
            return []
    
    def update_feedback_status(
        self, 
        feedback_id: int,
        status: FeedbackStatus,
        admin_notes: Optional[str] = None,
        admin_reviewed_by: Optional[str] = None
    ) -> bool:
        """
        Atualiza o status do feedback.
        
        Args:
            feedback_id: ID do feedback
            status: Novo status
            admin_notes: Notas administrativas (opcional)
            admin_reviewed_by: Quem revisou (opcional)
            
        Returns:
            True se atualizado com sucesso, False caso contrário
        """
        try:
            with get_db_session() as db:
                feedback = db.query(BlockingFeedbackHistory).filter(
                    BlockingFeedbackHistory.id == feedback_id
                ).first()
                
                if not feedback:
                    logger.warning(f"Feedback {feedback_id} não encontrado")
                    return False
                
                feedback.status = status
                feedback.updated_at = datetime.now()
                
                if admin_notes:
                    feedback.admin_notes = admin_notes
                
                if admin_reviewed_by:
                    feedback.admin_reviewed_by = admin_reviewed_by
                    feedback.admin_review_date = datetime.now()
                
                db.commit()
                logger.info(f"Status do feedback {feedback_id} atualizado para {status}")
                return True
                
        except Exception as e:
            logger.error(f"Erro ao atualizar status do feedback {feedback_id}: {e}")
        return False

    def create_admin_blocking_feedback(
        self, 
        dhcp_mapping_id: int,
        admin_reason: str,
        admin_name: str,
        problem_resolved: bool = None
    ) -> Optional[BlockingFeedbackHistory]:
        """
        Cria um feedback de bloqueio administrativo.
        
        Args:
            dhcp_mapping_id: ID do mapeamento DHCP
            admin_reason: Motivo do bloqueio fornecido pelo administrador
            admin_name: Nome do administrador que bloqueou
            problem_resolved: Se o problema foi resolvido (padrão None para não respondido)
            
        Returns:
            Feedback criado ou None em caso de erro
        """
        try:
            with get_db_session() as db:
                # Verifica se o mapeamento DHCP existe
                dhcp_mapping = db.query(DhcpStaticMapping).filter(
                    DhcpStaticMapping.id == dhcp_mapping_id
                ).first()
                
                if not dhcp_mapping:
                    logger.error(f"Mapeamento DHCP {dhcp_mapping_id} não encontrado")
                    return None
                
                # Cria o feedback administrativo
                feedback = BlockingFeedbackHistory(
                    dhcp_mapping_id=dhcp_mapping_id,
                    user_feedback=f"Bloqueio administrativo: {admin_reason}",
                    feedback_by=admin_name,
                    problem_resolved=problem_resolved,
                    admin_notes=f"Dispositivo bloqueado por administrador. Motivo: {admin_reason}",
                    admin_reviewed_by=admin_name,
                    admin_review_date=datetime.now(),
                    status=FeedbackStatus.REVIEWED  # Bloqueios administrativos já são considerados revisados
                )
                
                db.add(feedback)
                db.commit()
                db.refresh(feedback)
                
                logger.info(f"Feedback de bloqueio administrativo criado com ID: {feedback.id}")
                return feedback
                
        except Exception as e:
            logger.error(f"Erro ao criar feedback de bloqueio administrativo: {e}")
            return None

    def get_feedback_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas dos feedbacks.
        
        Returns:
            Dicionário com estatísticas
        """
        try:
            with get_db_session() as db:
                # Total de feedbacks
                total = db.query(BlockingFeedbackHistory).count()
                
                # Por status
                status_stats = {}
                for status in FeedbackStatus:
                    count = db.query(BlockingFeedbackHistory).filter(
                        BlockingFeedbackHistory.status == status
                    ).count()
                    status_stats[status.value] = count
                
                # Por resolução
                resolved_count = db.query(BlockingFeedbackHistory).filter(
                    BlockingFeedbackHistory.problem_resolved == True
                ).count()
                
                not_resolved_count = db.query(BlockingFeedbackHistory).filter(
                    BlockingFeedbackHistory.problem_resolved == False
                ).count()
                
                pending_count = db.query(BlockingFeedbackHistory).filter(
                    BlockingFeedbackHistory.problem_resolved.is_(None)
                ).count()
                
                return {
                    'total_feedbacks': total,
                    'status_stats': status_stats,
                    'resolved_stats': {
                        'resolved': resolved_count,
                        'not_resolved': not_resolved_count,
                        'pending': pending_count
                    },
                    'generated_at': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Erro ao gerar estatísticas de feedback: {e}")
            return {}
    
    def get_recent_feedback(self, days: int = 7) -> List[BlockingFeedbackHistory]:
        """
        Busca feedbacks recentes.
        
        Args:
            days: Número de dias para buscar
            
        Returns:
            Lista de feedbacks recentes
        """
        try:
            with get_db_session() as db:
                since = datetime.now() - timedelta(days=days)
                
                feedbacks = db.query(BlockingFeedbackHistory).filter(
                    BlockingFeedbackHistory.feedback_date >= since
                ).order_by(desc(BlockingFeedbackHistory.feedback_date)).all()
                
                logger.info(f"Encontrados {len(feedbacks)} feedbacks dos últimos {days} dias")
                return feedbacks
                
        except Exception as e:
            logger.error(f"Erro ao buscar feedbacks recentes: {e}")
            return []

    def update_feedback_resolution(self, feedback_id: int, problem_resolved: bool) -> Optional[BlockingFeedbackHistory]:
        """
        Atualiza o status de resolução de um feedback.
        
        Args:
            feedback_id: ID do feedback
            problem_resolved: Se o problema foi resolvido
            
        Returns:
            Feedback atualizado ou None se não encontrado
        """
        try:
            with get_db_session() as db:
                feedback = db.query(BlockingFeedbackHistory).filter(
                    BlockingFeedbackHistory.id == feedback_id
                ).first()
                
                if not feedback:
                    logger.error(f"Feedback {feedback_id} não encontrado")
                    return None
                
                feedback.problem_resolved = problem_resolved
                feedback.updated_at = datetime.now()
                
                db.commit()
                db.refresh(feedback)
                
                logger.info(f"Feedback {feedback_id} atualizado: problem_resolved={problem_resolved}")
                return feedback
                
        except Exception as e:
            logger.error(f"Erro ao atualizar feedback {feedback_id}: {e}")
            return None
