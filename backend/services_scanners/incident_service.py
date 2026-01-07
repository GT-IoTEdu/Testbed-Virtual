"""
Serviço para gerenciar incidentes de segurança no banco de dados.
"""
import json
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc

from db.models import ZeekIncident
from db.enums import IncidentSeverity, IncidentStatus, ZeekLogType
from db.session import get_db_session

logger = logging.getLogger(__name__)

class IncidentService:
    """Serviço para gerenciar incidentes de segurança."""
    
    def __init__(self):
        """Inicializa o serviço de incidentes."""
        pass
    
    def save_incident(self, incident_data: Dict[str, Any]) -> Optional[ZeekIncident]:
        """
        Salva um incidente no banco de dados.
        
        Args:
            incident_data: Dados do incidente
            
        Returns:
            Incidente salvo ou None em caso de erro
        """
        try:
            with get_db_session() as db:
                # Verifica se já existe um incidente similar (para evitar duplicatas)
                existing = self._find_similar_incident(db, incident_data)
                if existing:
                    logger.info(f"Incidente similar já existe: {existing.id}")
                    return existing
                
                # Cria novo incidente
                incident = ZeekIncident(
                    device_ip=incident_data.get('device_ip', 'unknown'),
                    device_name=incident_data.get('device_name'),
                    incident_type=incident_data.get('incident_type', 'Unknown'),
                    severity=IncidentSeverity(incident_data.get('severity', 'medium')),
                    status=IncidentStatus(incident_data.get('status', 'new')),
                    description=incident_data.get('description', ''),
                    detected_at=incident_data.get('detected_at', datetime.now()),
                    zeek_log_type=ZeekLogType(incident_data.get('zeek_log_type', 'notice.log')),
                    raw_log_data=json.dumps(incident_data.get('raw_log_data', {})) if incident_data.get('raw_log_data') else None,
                    action_taken=incident_data.get('action_taken'),
                    assigned_to=incident_data.get('assigned_to'),
                    notes=incident_data.get('notes')
                )
                
                db.add(incident)
                db.commit()
                db.refresh(incident)
                
                logger.info(f"Incidente salvo com ID: {incident.id}")
                
                # Verificar se é um incidente de atacante e aplicar bloqueio automático
                if "Atacante" in incident.incident_type:
                    logger.info(f"Incidente de atacante detectado (ID: {incident.id}). Aplicando bloqueio automático...")
                    self._apply_auto_block(incident)
                
                return incident
                
        except Exception as e:
            logger.error(f"Erro ao salvar incidente: {e}")
            return None
    
    def get_incidents(
        self, 
        device_ip: Optional[str] = None,
        severity: Optional[str] = None,
        status: Optional[str] = None,
        log_type: Optional[str] = None,
        hours_ago: Optional[int] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[ZeekIncident]:
        """
        Busca incidentes com filtros.
        
        Args:
            device_ip: Filtrar por IP do dispositivo
            severity: Filtrar por severidade
            status: Filtrar por status
            log_type: Filtrar por tipo de log
            hours_ago: Buscar incidentes das últimas N horas
            limit: Limite de resultados
            offset: Offset para paginação
            
        Returns:
            Lista de incidentes
        """
        try:
            with get_db_session() as db:
                query = db.query(ZeekIncident)
                
                # Aplica filtros
                if device_ip:
                    query = query.filter(ZeekIncident.device_ip == device_ip)
                
                if severity:
                    query = query.filter(ZeekIncident.severity == IncidentSeverity(severity))
                
                if status:
                    query = query.filter(ZeekIncident.status == IncidentStatus(status))
                
                if log_type:
                    query = query.filter(ZeekIncident.zeek_log_type == ZeekLogType(log_type))
                
                if hours_ago:
                    since = datetime.now() - timedelta(hours=hours_ago)
                    query = query.filter(ZeekIncident.detected_at >= since)
                
                # Ordena por data de detecção (mais recentes primeiro)
                query = query.order_by(desc(ZeekIncident.detected_at))
                
                # Aplica paginação
                incidents = query.offset(offset).limit(limit).all()
                
                logger.info(f"Encontrados {len(incidents)} incidentes")
                return incidents
                
        except Exception as e:
            logger.error(f"Erro ao buscar incidentes: {e}")
            return []
    
    def get_incident_by_id(self, incident_id: int) -> Optional[ZeekIncident]:
        """
        Busca um incidente por ID.
        
        Args:
            incident_id: ID do incidente
            
        Returns:
            Incidente ou None se não encontrado
        """
        try:
            with get_db_session() as db:
                incident = db.query(ZeekIncident).filter(ZeekIncident.id == incident_id).first()
                return incident
        except Exception as e:
            logger.error(f"Erro ao buscar incidente {incident_id}: {e}")
            return None
    
    def update_incident_status(self, incident_id: int, status: str, notes: Optional[str] = None) -> bool:
        """
        Atualiza o status de um incidente.
        
        Args:
            incident_id: ID do incidente
            status: Novo status
            notes: Observações adicionais
            
        Returns:
            True se atualizado com sucesso, False caso contrário
        """
        try:
            with get_db_session() as db:
                incident = db.query(ZeekIncident).filter(ZeekIncident.id == incident_id).first()
                if not incident:
                    logger.warning(f"Incidente {incident_id} não encontrado")
                    return False
                
                incident.status = IncidentStatus(status)
                if notes:
                    incident.notes = notes
                incident.updated_at = datetime.now()
                
                db.commit()
                logger.info(f"Status do incidente {incident_id} atualizado para {status}")
                return True
                
        except Exception as e:
            logger.error(f"Erro ao atualizar incidente {incident_id}: {e}")
            return False
    
    def assign_incident(self, incident_id: int, user_id: int) -> bool:
        """
        Atribui um incidente a um usuário.
        
        Args:
            incident_id: ID do incidente
            user_id: ID do usuário
            
        Returns:
            True se atribuído com sucesso, False caso contrário
        """
        try:
            with get_db_session() as db:
                incident = db.query(ZeekIncident).filter(ZeekIncident.id == incident_id).first()
                if not incident:
                    logger.warning(f"Incidente {incident_id} não encontrado")
                    return False
                
                incident.assigned_to = user_id
                incident.updated_at = datetime.now()
                
                db.commit()
                logger.info(f"Incidente {incident_id} atribuído ao usuário {user_id}")
                return True
                
        except Exception as e:
            logger.error(f"Erro ao atribuir incidente {incident_id}: {e}")
            return False
    
    def get_incident_stats(self, hours_ago: int = 24) -> Dict[str, Any]:
        """
        Retorna estatísticas dos incidentes.
        
        Args:
            hours_ago: Período em horas para as estatísticas
            
        Returns:
            Dicionário com estatísticas
        """
        try:
            with get_db_session() as db:
                since = datetime.now() - timedelta(hours=hours_ago)
                
                # Total de incidentes
                total = db.query(ZeekIncident).filter(ZeekIncident.detected_at >= since).count()
                
                # Por severidade
                severity_stats = {}
                for severity in IncidentSeverity:
                    count = db.query(ZeekIncident).filter(
                        and_(ZeekIncident.detected_at >= since, ZeekIncident.severity == severity)
                    ).count()
                    severity_stats[severity.value] = count
                
                # Por status
                status_stats = {}
                for status in IncidentStatus:
                    count = db.query(ZeekIncident).filter(
                        and_(ZeekIncident.detected_at >= since, ZeekIncident.status == status)
                    ).count()
                    status_stats[status.value] = count
                
                # Por tipo de log
                log_type_stats = {}
                for log_type in ZeekLogType:
                    count = db.query(ZeekIncident).filter(
                        and_(ZeekIncident.detected_at >= since, ZeekIncident.zeek_log_type == log_type)
                    ).count()
                    log_type_stats[log_type.value] = count
                
                # Top IPs com mais incidentes
                from sqlalchemy import func
                top_ips = db.query(
                    ZeekIncident.device_ip,
                    func.count(ZeekIncident.id).label('count')
                ).filter(
                    ZeekIncident.detected_at >= since
                ).group_by(
                    ZeekIncident.device_ip
                ).order_by(
                    desc('count')
                ).limit(10).all()
                
                return {
                    'total_incidents': total,
                    'severity_stats': severity_stats,
                    'status_stats': status_stats,
                    'log_type_stats': log_type_stats,
                    'top_ips': [{'ip': ip, 'count': count} for ip, count in top_ips],
                    'period_hours': hours_ago,
                    'generated_at': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Erro ao gerar estatísticas: {e}")
            return {}
    
    def _find_similar_incident(self, db: Session, incident_data: Dict[str, Any]) -> Optional[ZeekIncident]:
        """
        Busca incidentes similares para evitar duplicatas.
        
        Args:
            db: Sessão do banco de dados
            incident_data: Dados do incidente
            
        Returns:
            Incidente similar ou None
        """
        try:
            # Busca por incidente do mesmo tipo, IP e severidade nas últimas 1 hora
            since = datetime.now() - timedelta(hours=1)
            
            similar = db.query(ZeekIncident).filter(
                and_(
                    ZeekIncident.device_ip == incident_data.get('device_ip'),
                    ZeekIncident.incident_type == incident_data.get('incident_type'),
                    ZeekIncident.severity == IncidentSeverity(incident_data.get('severity', 'medium')),
                    ZeekIncident.detected_at >= since
                )
            ).first()
            
            return similar
            
        except Exception as e:
            logger.error(f"Erro ao buscar incidente similar: {e}")
            return None
    
    def _apply_auto_block(self, incident: ZeekIncident) -> bool:
        """
        Aplica bloqueio automático para incidentes de atacante.
        
        Args:
            incident: Incidente de atacante
            
        Returns:
            True se bloqueio foi aplicado com sucesso, False caso contrário
        """
        try:
            device_ip = incident.device_ip
            logger.info(f"Aplicando bloqueio automático para IP {device_ip} (Incidente {incident.id})")
            
            # Importar serviços necessários
            from services_firewalls.alias_service import AliasService
            from services_firewalls.blocking_feedback_service import BlockingFeedbackService
            
            # Aplicar bloqueio usando AliasService
            with AliasService() as alias_service:
                # Verificar se o IP já está bloqueado
                blocked_alias = alias_service.get_alias_by_name("Bloqueados")
                if blocked_alias:
                    blocked_addresses = [addr['address'] for addr in blocked_alias['addresses']]
                    if device_ip in blocked_addresses:
                        logger.info(f"IP {device_ip} já está bloqueado")
                        return True
                
                # Remover do alias "Autorizados" se existir
                authorized_alias = alias_service.get_alias_by_name("Autorizados")
                if authorized_alias:
                    authorized_addresses = [addr['address'] for addr in authorized_alias['addresses']]
                    if device_ip in authorized_addresses:
                        logger.info(f"Removendo IP {device_ip} do alias Autorizados")
                        
                        # Criar nova lista sem o IP
                        new_addresses = []
                        for addr in authorized_alias['addresses']:
                            if addr['address'] != device_ip:
                                new_addresses.append(addr)
                        
                        # Atualizar alias Autorizados
                        alias_service.update_alias("Autorizados", {
                            'addresses': new_addresses
                        })
                        logger.info(f"IP {device_ip} removido do alias Autorizados")
                
                # Adicionar ao alias "Bloqueados"
                logger.info(f"Adicionando IP {device_ip} ao alias Bloqueados")
                
                # Verificar se alias Bloqueados existe
                if not blocked_alias:
                    # Criar alias Bloqueados se não existir
                    logger.info("Criando alias Bloqueados no pfSense e banco de dados")
                    create_result = alias_service.create_alias({
                        'name': 'Bloqueados',
                        'alias_type': 'host',
                        'descr': 'Dispositivos bloqueados por incidentes de segurança',
                        'addresses': [{'address': device_ip, 'detail': f'Bloqueado automaticamente - Incidente {incident.id}'}]
                    })
                    
                    if not create_result.get('success'):
                        logger.error(f"Erro ao criar alias Bloqueados: {create_result}")
                        return False
                    
                    logger.info("Alias Bloqueados criado com sucesso")
                else:
                    # Adicionar IP ao alias existente
                    logger.info(f"Adicionando IP {device_ip} ao alias Bloqueados existente")
                    add_result = alias_service.add_addresses_to_alias("Bloqueados", [{
                        'address': device_ip, 
                        'detail': f'Bloqueado automaticamente - Incidente {incident.id}'
                    }])
                    
                    if not add_result.get('success'):
                        logger.error(f"Erro ao adicionar IP ao alias Bloqueados: {add_result}")
                        return False
                    
                    logger.info(f"IP {device_ip} adicionado ao alias Bloqueados com sucesso")
            
            # Atualizar status do incidente
            self.update_incident_status(
                incident.id, 
                "resolved", 
                f"Dispositivo bloqueado automaticamente por ser identificado como atacante"
            )
            
            # Criar feedback administrativo
            try:
                feedback_service = BlockingFeedbackService()
                
                # Buscar dispositivo no banco DHCP para obter o ID
                from db.models import DhcpStaticMapping
                from db.session import SessionLocal
                
                db = SessionLocal()
                try:
                    device = db.query(DhcpStaticMapping).filter(
                        DhcpStaticMapping.ipaddr == device_ip
                    ).first()
                    
                    if device:
                        feedback = feedback_service.create_admin_blocking_feedback(
                            dhcp_mapping_id=device.id,
                            admin_reason=f"Bloqueio automático por incidente de segurança - Incidente {incident.id}: {incident.incident_type}",
                            admin_name="Sistema Automático",
                            problem_resolved=None
                        )
                        
                        if feedback:
                            logger.info(f"Feedback administrativo criado com ID: {feedback.id}")
                        else:
                            logger.warning(f"Falha ao criar feedback administrativo para dispositivo {device_ip}")
                    else:
                        logger.warning(f"Dispositivo com IP {device_ip} não encontrado no banco DHCP")
                finally:
                    db.close()
                    
            except Exception as feedback_error:
                logger.error(f"Erro ao criar feedback administrativo: {feedback_error}")
                # Não falha o bloqueio se o feedback não for criado
            
            logger.info(f"Bloqueio automático concluído com sucesso para IP {device_ip}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao aplicar bloqueio automático: {e}")
            return False
