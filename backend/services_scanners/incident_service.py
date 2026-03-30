"""
Serviço para gerenciar incidentes de segurança no banco de dados.
"""
import json
import logging
import time
import threading
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc

from db.models import Incident
from db.enums import IncidentSeverity, IncidentStatus, ZeekLogType
from db.session import get_db_session

logger = logging.getLogger(__name__)

class IncidentService:
    """Serviço para gerenciar incidentes de segurança."""
    
    def __init__(self):
        """Inicializa o serviço de incidentes."""
        pass
    
    def save_incident(self, incident_data: Dict[str, Any]) -> Optional[Incident]:
        """
        Salva um incidente no banco de dados.
        
        Args:
            incident_data: Dados do incidente
            
        Returns:
            Incidente salvo ou None em caso de erro
        """
        try:
            with get_db_session() as db:
                # Verifica se já existe um incidente exatamente igual (mesmo tipo, IP e timestamp muito próximo)
                existing = self._find_exact_duplicate(db, incident_data)
                if existing:
                    # Se for exatamente igual, atualizar o incidente existente em vez de criar novo
                    logger.info(
                        f"🔄 [IncidentService] Incidente exatamente igual encontrado (ID={existing.id}) - "
                        f"atualizando em vez de criar novo"
                    )
                    
                    # Atualizar campos que podem ter mudado
                    if incident_data.get('description'):
                        existing.description = incident_data.get('description')
                    if incident_data.get('raw_log_data'):
                        existing.raw_log_data = json.dumps(incident_data.get('raw_log_data', {})) if incident_data.get('raw_log_data') else None
                    if incident_data.get('action_taken'):
                        existing.action_taken = incident_data.get('action_taken')
                    
                    existing.updated_at = datetime.now()
                    db.commit()
                    db.refresh(existing)
                    
                    logger.info(f"✅ [IncidentService] Incidente atualizado - ID: {existing.id}")
                    return existing
                
                # Cria novo incidente
                logger.debug(f"💾 [IncidentService] Criando novo incidente: Tipo='{incident_data.get('incident_type')}', IP={incident_data.get('device_ip')}")
                
                incident = Incident(
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
                
                logger.info(f"✅ [IncidentService] Incidente criado com sucesso - ID: {incident.id}, Tipo: {incident.incident_type}, IP: {incident.device_ip}")
                
                # Log detalhado com timestamps para medição de tempos
                saved_at = datetime.now()
                detected_at = incident.detected_at
                time_since_detection = None
                if detected_at:
                    time_since_detection = (saved_at - detected_at).total_seconds()
                
                logger.info(
                    f"⏱️ [TIMING] Incidente salvo - "
                    f"ID: {incident.id}, "
                    f"IP: {incident.device_ip}, "
                    f"Tipo: {incident.incident_type}, "
                    f"Detectado em: {detected_at}, "
                    f"Salvo em: {saved_at}, "
                    f"Tempo desde detecção: {time_since_detection:.3f}s"
                )
                
                # Log de performance para detecção
                try:
                    from .performance_logger import get_performance_logger
                    perf_logger = get_performance_logger()
                    perf_logger.log_detection(
                        incident_id=incident.id,
                        device_ip=incident.device_ip,
                        detected_at=detected_at,
                        incident_type=incident.incident_type,
                        metadata={
                            'saved_at': saved_at.isoformat(),
                            'time_since_detection_seconds': time_since_detection
                        }
                    )
                except Exception as e:
                    logger.warning(f"Erro ao registrar log de performance: {e}")
                
                # Processar automaticamente se for incidente de atacante
                # Verifica tanto "Atacante" (português) quanto "Attacker" (inglês) para compatibilidade
                is_attacker = "Atacante" in incident.incident_type or "Attacker" in incident.incident_type
                
                logger.debug(f"🔍 Verificando se incidente {incident.id} é de atacante: incident_type='{incident.incident_type}', is_attacker={is_attacker}")
                
                if is_attacker:
                    logger.info(f"🔒 Incidente de atacante detectado (ID: {incident.id}, Tipo: '{incident.incident_type}'). Processando para bloqueio automático...")
                    
                    # Processar automaticamente em background (assíncrono via thread)
                    def process_auto_block():
                        try:
                            # Pequeno delay para garantir que o commit foi finalizado
                            time.sleep(0.5)
                            
                            # Buscar o incidente novamente para garantir que está no banco
                            with get_db_session() as db:
                                fresh_incident = db.query(Incident).filter(Incident.id == incident.id).first()
                                if not fresh_incident:
                                    logger.error(f"❌ Incidente {incident.id} não encontrado no banco após criação")
                                    return
                                
                                # Verificar se já foi processado (evitar processamento duplicado)
                                if fresh_incident.processed_at is not None:
                                    logger.info(f"ℹ️ Incidente {incident.id} já foi processado anteriormente")
                                    return
                                
                                # Marcar como processado primeiro (evita reprocessamento)
                                processed_at = self._mark_incident_as_processed(fresh_incident.id)
                                if not processed_at:
                                    logger.error(f"❌ Falha ao marcar incidente {incident.id} como processado")
                                    return
                                
                                # Aplicar bloqueio diretamente no incidente
                                logger.info(f"🔒 Aplicando bloqueio automático diretamente no incidente {fresh_incident.id}")
                                blocking_success = self._apply_auto_block(fresh_incident)
                                
                                if blocking_success:
                                    logger.info(f"✅ Bloqueio automático aplicado com sucesso para incidente {fresh_incident.id} (IP: {fresh_incident.device_ip})")
                                else:
                                    logger.error(f"❌ Falha ao aplicar bloqueio automático para incidente {fresh_incident.id} (IP: {fresh_incident.device_ip})")
                                    
                        except Exception as e:
                            logger.error(f"❌ Erro ao processar bloqueio automático em background para incidente {incident.id}: {e}", exc_info=True)
                            # Tentar processar via batch como fallback
                            try:
                                logger.info(f"🔄 Tentando processar via batch como fallback...")
                                result = self.process_incidents_for_auto_blocking(limit=10)
                                if result.get('blocked_count', 0) > 0:
                                    logger.info(f"✅ Bloqueio aplicado via batch para incidente {incident.id}")
                                else:
                                    logger.warning(f"⚠️ Nenhum bloqueio aplicado via batch para incidente {incident.id}")
                            except Exception as fallback_error:
                                logger.error(f"❌ Erro no fallback de processamento em batch: {fallback_error}")
                    
                    thread = threading.Thread(target=process_auto_block, daemon=True)
                    thread.start()
                    logger.info(f"Processamento automático iniciado em background para incidente {incident.id}")
                else:
                    logger.info(f"Incidente salvo com ID: {incident.id}. Não é de atacante, não será bloqueado automaticamente.")
                
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
    ) -> List[Incident]:
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
                query = db.query(Incident)
                
                # Aplica filtros
                if device_ip:
                    query = query.filter(Incident.device_ip == device_ip)
                
                if severity:
                    query = query.filter(Incident.severity == IncidentSeverity(severity))
                
                if status:
                    query = query.filter(Incident.status == IncidentStatus(status))
                
                if log_type:
                    query = query.filter(Incident.zeek_log_type == ZeekLogType(log_type))
                
                if hours_ago:
                    since = datetime.now() - timedelta(hours=hours_ago)
                    query = query.filter(Incident.detected_at >= since)
                
                # Ordena por data de detecção (mais recentes primeiro)
                query = query.order_by(desc(Incident.detected_at))
                
                # Total com os mesmos filtros (para paginação)
                total = query.count()
                # Aplica paginação
                incidents = query.offset(offset).limit(limit).all()

                logger.info(f"Encontrados {len(incidents)} incidentes (total: {total})")
                return incidents, total

        except Exception as e:
            logger.error(f"Erro ao buscar incidentes: {e}")
            return [], 0

    def get_incident_by_id(self, incident_id: int) -> Optional[Incident]:
        """
        Busca um incidente por ID.
        
        Args:
            incident_id: ID do incidente
            
        Returns:
            Incidente ou None se não encontrado
        """
        try:
            with get_db_session() as db:
                incident = db.query(Incident).filter(Incident.id == incident_id).first()
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
                incident = db.query(Incident).filter(Incident.id == incident_id).first()
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
                incident = db.query(Incident).filter(Incident.id == incident_id).first()
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
                total = db.query(Incident).filter(Incident.detected_at >= since).count()
                
                # Por severidade
                severity_stats = {}
                for severity in IncidentSeverity:
                    count = db.query(Incident).filter(
                        and_(Incident.detected_at >= since, Incident.severity == severity)
                    ).count()
                    severity_stats[severity.value] = count
                
                # Por status
                status_stats = {}
                for status in IncidentStatus:
                    count = db.query(Incident).filter(
                        and_(Incident.detected_at >= since, Incident.status == status)
                    ).count()
                    status_stats[status.value] = count
                
                # Por tipo de log
                log_type_stats = {}
                for log_type in ZeekLogType:
                    count = db.query(Incident).filter(
                        and_(Incident.detected_at >= since, Incident.zeek_log_type == log_type)
                    ).count()
                    log_type_stats[log_type.value] = count
                
                # Top IPs com mais incidentes
                from sqlalchemy import func
                top_ips = db.query(
                    Incident.device_ip,
                    func.count(Incident.id).label('count')
                ).filter(
                    Incident.detected_at >= since
                ).group_by(
                    Incident.device_ip
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
    
    def _find_exact_duplicate(self, db: Session, incident_data: Dict[str, Any]) -> Optional[Incident]:
        """
        Busca incidente exatamente igual (mesmo tipo, IP e timestamp muito próximo - menos de 1 segundo).
        Se encontrar, retorna para atualizar em vez de criar novo.
        
        Args:
            db: Sessão do banco de dados
            incident_data: Dados do incidente
            
        Returns:
            Incidente exatamente igual ou None
        """
        try:
            incident_type = incident_data.get('incident_type', '')
            severity = IncidentSeverity(incident_data.get('severity', 'medium'))
            device_ip = incident_data.get('device_ip')
            detected_at = incident_data.get('detected_at', datetime.now())
            
            # Converter detected_at para datetime se for string
            if isinstance(detected_at, str):
                try:
                    detected_at = datetime.fromisoformat(detected_at.replace('Z', '+00:00'))
                except:
                    detected_at = datetime.now()
            
            # Buscar incidente exatamente igual (mesmo tipo, IP, severidade e timestamp muito próximo - menos de 1 segundo)
            # Isso evita duplicatas exatas, mas permite múltiplos incidentes do mesmo tipo/IP se houver diferença de tempo
            since = detected_at - timedelta(seconds=1)
            until = detected_at + timedelta(seconds=1)
            
            duplicate = db.query(Incident).filter(
                and_(
                    Incident.device_ip == device_ip,
                    Incident.incident_type == incident_type,
                    Incident.severity == severity,
                    Incident.detected_at >= since,
                    Incident.detected_at <= until
                )
            ).order_by(Incident.detected_at.desc()).first()
            
            if duplicate:
                time_diff = (detected_at - duplicate.detected_at).total_seconds()
                logger.debug(
                    f"🔍 [IncidentService] Incidente exatamente igual encontrado: "
                    f"ID={duplicate.id}, Tipo: '{duplicate.incident_type}', IP: {duplicate.device_ip}, "
                    f"Diferença de tempo: {time_diff:.3f}s"
                )
            
            return duplicate
            
        except Exception as e:
            logger.error(f"❌ [IncidentService] Erro ao buscar incidente duplicado: {e}", exc_info=True)
            return None
    
    def apply_auto_block_for_device(
        self,
        device_ip: str,
        institution_id: Optional[int],
        source_type: str,
        source_id: int,
        description: str,
        detected_at: Optional[datetime] = None,
    ) -> bool:
        """
        Aplica bloqueio automático para um IP (alias Bloqueados + feedback).
        Usado por Zeek (incidentes) e Suricata (alertas de severidade alta).

        Args:
            device_ip: IP a bloquear (origem do ataque).
            institution_id: ID da instituição (se None, tenta obter pelo IP).
            source_type: "zeek" ou "suricata".
            source_id: ID do incidente ou do alerta.
            description: Motivo do bloqueio (ex: tipo do incidente ou assinatura).
            detected_at: Data/hora da detecção (opcional, para logs).

        Returns:
            True se o bloqueio foi aplicado com sucesso, False caso contrário.
        """
        try:
            # Rejeitar IP inválido (pfSense não aceita "N/A", vazio ou valores não-IP)
            device_ip = (device_ip or "").strip()
            if not device_ip or device_ip.upper() == "N/A":
                logger.warning("Bloqueio automático ignorado: IP inválido (vazio ou N/A)")
                return False
            if "." not in device_ip and ":" not in device_ip:
                logger.warning("Bloqueio automático ignorado: valor não é um IP válido: %s", device_ip[:50])
                return False
            blocking_start = datetime.now()
            from services_firewalls.alias_service import AliasService
            from services_firewalls.blocking_feedback_service import BlockingFeedbackService
            from services_firewalls.institution_config_service import InstitutionConfigService

            if not institution_id:
                institution_id = InstitutionConfigService.get_institution_by_ip(device_ip)
            if not institution_id:
                institutions = InstitutionConfigService.get_all_institutions()
                if institutions:
                    institution_id = institutions[0]['id']
                else:
                    logger.error("Nenhuma instituição ativa. Bloqueio não pode prosseguir.")
                    return False

            try:
                from .performance_logger import get_performance_logger
                perf_logger = get_performance_logger()
                perf_logger.log_event(
                    event_type="BLOCKING_START",
                    description=f"Iniciando bloqueio automático para IP {device_ip} ({source_type} {source_id})",
                    incident_id=source_id if source_type == "zeek" else None,
                    device_ip=device_ip,
                    endpoint=f"IncidentService.apply_auto_block_for_device({source_type})"
                )
            except Exception as e:
                logger.warning(f"Erro ao registrar log de performance: {e}")

            detail = f"Bloqueado automaticamente - {source_type.title()} {source_id}"
            with AliasService(institution_id=institution_id) as alias_service:
                blocked_alias = alias_service.get_alias_by_name("Bloqueados")
                if not blocked_alias:
                    create_result = alias_service.create_alias({
                        'name': 'Bloqueados',
                        'alias_type': 'host',
                        'descr': 'Dispositivos bloqueados por incidentes de segurança',
                        'addresses': [{'address': device_ip, 'detail': detail}]
                    })
                    if not create_result.get('success'):
                        logger.error(f"Erro ao criar alias Bloqueados: {create_result}")
                        return False
                else:
                    add_result = alias_service.add_addresses_to_alias("Bloqueados", [
                        {'address': device_ip, 'detail': detail}
                    ])
                    if not add_result.get('success'):
                        logger.error(f"Erro ao adicionar IP ao alias Bloqueados: {add_result}")
                        return False

            feedback_service = BlockingFeedbackService()
            from db.models import DhcpStaticMapping
            from db.session import SessionLocal
            db = SessionLocal()
            try:
                device = db.query(DhcpStaticMapping).filter(DhcpStaticMapping.ipaddr == device_ip).first()
                if device:
                    feedback_service.create_admin_blocking_feedback(
                        dhcp_mapping_id=device.id,
                        admin_reason=f"Bloqueio automático ({source_type}) - {source_type.title()} {source_id}: {description[:200]}",
                        admin_name="Sistema Automático",
                        problem_resolved=None
                    )
                else:
                    logger.warning(f"Dispositivo com IP {device_ip} não encontrado no banco DHCP")
            finally:
                db.close()

            if detected_at:
                try:
                    from .performance_logger import get_performance_logger
                    perf_logger = get_performance_logger()
                    perf_logger.log_blocking(
                        incident_id=source_id if source_type == "zeek" else None,
                        device_ip=device_ip,
                        blocked_at=blocking_start,
                        duration_seconds=(datetime.now() - blocking_start).total_seconds(),
                        endpoint=f"IncidentService.apply_auto_block_for_device({source_type})",
                        metadata={'source_type': source_type, 'source_id': source_id, 'detected_at': detected_at.isoformat()}
                    )
                except Exception as e:
                    logger.warning(f"Erro ao registrar log de performance: {e}")

            logger.info(f"Bloqueio automático concluído para IP {device_ip} ({source_type} {source_id})")
            return True
        except Exception as e:
            logger.error(f"Erro ao aplicar bloqueio para IP {device_ip}: {e}", exc_info=True)
            return False

    def _apply_auto_block(self, incident: Incident) -> bool:
        """
        Aplica bloqueio automático para incidentes de atacante (Zeek).
        Delega para apply_auto_block_for_device e atualiza status do incidente.
        """
        try:
            device_ip = incident.device_ip
            blocking_start = datetime.now()

            if incident.detected_at:
                time_since_detection = (blocking_start - incident.detected_at).total_seconds()
                logger.info(
                    f"⏱️ [TIMING] Iniciando bloqueio automático - "
                    f"Incidente ID: {incident.id}, IP: {device_ip}, "
                    f"Detectado: {incident.detected_at}, Tempo desde detecção: {time_since_detection:.3f}s"
                )
            logger.info(f"Aplicando bloqueio automático para IP {device_ip} (Incidente {incident.id})")

            try:
                from .performance_logger import get_performance_logger
                perf_logger = get_performance_logger()
                perf_logger.log_event(
                    event_type="BLOCKING_START",
                    description=f"Iniciando bloqueio automático para IP {device_ip}",
                    incident_id=incident.id,
                    device_ip=device_ip,
                    endpoint="IncidentService._apply_auto_block"
                )
            except Exception as e:
                logger.warning(f"Erro ao registrar log de performance: {e}")

            from services_firewalls.institution_config_service import InstitutionConfigService
            institution_id = InstitutionConfigService.get_institution_by_ip(device_ip)
            if not institution_id:
                institutions = InstitutionConfigService.get_all_institutions()
                institution_id = institutions[0]['id'] if institutions else None
            if not institution_id:
                logger.error("Nenhuma instituição ativa. Bloqueio não pode prosseguir.")
                return False

            success = self.apply_auto_block_for_device(
                device_ip=device_ip,
                institution_id=institution_id,
                source_type="zeek",
                source_id=incident.id,
                description=incident.incident_type,
                detected_at=incident.detected_at,
            )
            if success:
                self.update_incident_status(
                    incident.id,
                    "resolved",
                    "Dispositivo bloqueado automaticamente por ser identificado como atacante"
                )
                blocking_end = datetime.now()
                logger.info(
                    f"⏱️ [TIMING] Bloqueio automático concluído - IP: {device_ip}, "
                    f"Duração: {(blocking_end - blocking_start).total_seconds():.3f}s"
                )
            return success
        except Exception as e:
            logger.error(f"Erro geral ao aplicar bloqueio automático: {e}", exc_info=True)
            return False
    
    def get_unprocessed_incidents(self, limit: int = 100) -> List[Incident]:
        """
        Busca incidentes não processados para bloqueio automático.
        
        Args:
            limit: Limite de incidentes a retornar
            
        Returns:
            Lista de incidentes não processados
        """
        try:
            with get_db_session() as db:
                incidents = db.query(Incident).filter(
                    and_(
                        Incident.processed_at.is_(None),  # Não processados
                        Incident.status != IncidentStatus.RESOLVED  # Não resolvidos
                    )
                ).order_by(Incident.detected_at.asc()).limit(limit).all()
                
                logger.info(f"Encontrados {len(incidents)} incidentes não processados")
                return incidents
                
        except Exception as e:
            logger.error(f"Erro ao buscar incidentes não processados: {e}")
            return []
    
    def process_incidents_for_auto_blocking(self, limit: int = 50) -> Dict[str, Any]:
        """
        Processa incidentes em lote para bloqueio automático.
        
        Args:
            limit: Limite de incidentes a processar por vez
            
        Returns:
            Dicionário com estatísticas do processamento
        """
        try:
            processing_start = datetime.now()
            logger.info(f"🚀 Iniciando processamento em lote de incidentes para bloqueio automático (limite: {limit})")
            
            # Log de performance - início do processamento
            try:
                from .performance_logger import get_performance_logger
                perf_logger = get_performance_logger()
                perf_logger.log_event(
                    event_type="PROCESSING_START",
                    description=f"Iniciando processamento em lote de incidentes (limite: {limit})",
                    endpoint="IncidentService.process_incidents_for_auto_blocking"
                )
            except Exception as e:
                logger.warning(f"Erro ao registrar log de performance: {e}")
            
            # Buscar incidentes não processados
            unprocessed_incidents = self.get_unprocessed_incidents(limit)
            
            if not unprocessed_incidents:
                logger.info("✅ Nenhum incidente não processado encontrado")
                return {
                    'success': True,
                    'processed_count': 0,
                    'blocked_count': 0,
                    'skipped_count': 0,
                    'error_count': 0,
                    'message': 'Nenhum incidente para processar'
                }
            
            stats = {
                'processed_count': 0,
                'blocked_count': 0,
                'skipped_count': 0,
                'error_count': 0,
                'processed_incidents': []
            }
            
            for incident in unprocessed_incidents:
                try:
                    stats['processed_count'] += 1
                    
                    processing_start = datetime.now()
                    
                    # Log de início do processamento
                    if incident.detected_at:
                        time_since_detection = (processing_start - incident.detected_at).total_seconds()
                        logger.info(
                            f"⏱️ [TIMING] Iniciando processamento - "
                            f"Incidente ID: {incident.id}, "
                            f"IP: {incident.device_ip}, "
                            f"Detectado em: {incident.detected_at}, "
                            f"Início processamento: {processing_start}, "
                            f"Tempo desde detecção: {time_since_detection:.3f}s"
                        )
                    
                    # Marcar como processado primeiro (para evitar reprocessamento)
                    processed_at = self._mark_incident_as_processed(incident.id)
                    
                    # Verificar se é incidente de atacante
                    # Verifica tanto "Atacante" (português) quanto "Attacker" (inglês) para compatibilidade
                    is_attacker = "Atacante" in incident.incident_type or "Attacker" in incident.incident_type
                    
                    if is_attacker:
                        logger.info(f"🔒 Processando incidente de atacante (ID: {incident.id}, IP: {incident.device_ip}, Tipo: '{incident.incident_type}')")
                        
                        # Aplicar bloqueio automático
                        blocking_success = self._apply_auto_block(incident)
                        
                        # Log de conclusão do processamento
                        processing_end = datetime.now()
                        processing_duration = (processing_end - processing_start).total_seconds()
                        logger.info(
                            f"⏱️ [TIMING] Processamento concluído - "
                            f"Incidente ID: {incident.id}, "
                            f"Duração: {processing_duration:.3f}s, "
                            f"Bloqueio: {'sucesso' if blocking_success else 'falhou'}"
                        )
                        
                        if blocking_success:
                            stats['blocked_count'] += 1
                            logger.info(f"✅ Bloqueio aplicado com sucesso para IP {incident.device_ip}")
                        else:
                            stats['error_count'] += 1
                            logger.error(f"❌ Falha ao aplicar bloqueio para IP {incident.device_ip}")
                        
                        stats['processed_incidents'].append({
                            'id': incident.id,
                            'device_ip': incident.device_ip,
                            'incident_type': incident.incident_type,
                            'action': 'blocked' if blocking_success else 'blocking_failed'
                        })
                    else:
                        stats['skipped_count'] += 1
                        logger.info(f"⏭️ Incidente não é de atacante (ID: {incident.id}, Tipo: {incident.incident_type})")
                        
                        stats['processed_incidents'].append({
                            'id': incident.id,
                            'device_ip': incident.device_ip,
                            'incident_type': incident.incident_type,
                            'action': 'skipped'
                        })
                        
                except Exception as e:
                    stats['error_count'] += 1
                    logger.error(f"❌ Erro ao processar incidente {incident.id}: {e}")
                    
                    stats['processed_incidents'].append({
                        'id': incident.id,
                        'device_ip': incident.device_ip,
                        'incident_type': incident.incident_type,
                        'action': 'error',
                        'error': str(e)
                    })
            
            processing_end = datetime.now()
            processing_duration = (processing_end - processing_start).total_seconds()
            
            logger.info(f"📊 Processamento concluído: {stats['processed_count']} processados, {stats['blocked_count']} bloqueados, {stats['skipped_count']} ignorados, {stats['error_count']} erros")
            
            # Log de performance - fim do processamento
            try:
                from .performance_logger import get_performance_logger
                perf_logger = get_performance_logger()
                perf_logger.log_processing(
                    processing_type="AUTO_BLOCKING_BATCH",
                    duration_seconds=processing_duration,
                    items_processed=stats['processed_count'],
                    metadata={
                        'blocked_count': stats['blocked_count'],
                        'skipped_count': stats['skipped_count'],
                        'error_count': stats['error_count'],
                        'endpoint': 'IncidentService.process_incidents_for_auto_blocking'
                    }
                )
            except Exception as e:
                logger.warning(f"Erro ao registrar log de performance: {e}")
            
            return {
                'success': True,
                **stats,
                'message': f'Processamento concluído: {stats["blocked_count"]} dispositivos bloqueados'
            }
            
        except Exception as e:
            logger.error(f"❌ Erro no processamento em lote: {e}")
            return {
                'success': False,
                'error': str(e),
                'processed_count': 0,
                'blocked_count': 0,
                'skipped_count': 0,
                'error_count': 0
            }
    
    def _mark_incident_as_processed(self, incident_id: int) -> Optional[datetime]:
        """
        Marca um incidente como processado.
        
        Args:
            incident_id: ID do incidente
            
        Returns:
            Timestamp do processamento ou None em caso de erro
        """
        try:
            with get_db_session() as db:
                incident = db.query(Incident).filter(Incident.id == incident_id).first()
                if not incident:
                    logger.warning(f"Incidente {incident_id} não encontrado")
                    return None
                
                processed_at = datetime.now()
                incident.processed_at = processed_at
                incident.updated_at = processed_at
                
                db.commit()
                
                # Log detalhado
                if incident.detected_at:
                    time_since_detection = (processed_at - incident.detected_at).total_seconds()
                    logger.info(
                        f"⏱️ [TIMING] Incidente marcado como processado - "
                        f"ID: {incident_id}, "
                        f"Detectado: {incident.detected_at}, "
                        f"Processado: {processed_at}, "
                        f"TtP: {time_since_detection:.3f}s"
                    )
                else:
                    logger.debug(f"Incidente {incident_id} marcado como processado em {processed_at}")
                
                return processed_at
                
        except Exception as e:
            logger.error(f"Erro ao marcar incidente {incident_id} como processado: {e}")
            return None
    
    def get_processing_stats(self, hours_ago: int = 24) -> Dict[str, Any]:
        """
        Retorna estatísticas do processamento de incidentes.
        
        Args:
            hours_ago: Período em horas para as estatísticas
            
        Returns:
            Dicionário com estatísticas de processamento
        """
        try:
            with get_db_session() as db:
                since = datetime.now() - timedelta(hours=hours_ago)
                
                # Total de incidentes no período
                total = db.query(Incident).filter(Incident.detected_at >= since).count()
                
                # Processados
                processed = db.query(Incident).filter(
                    and_(
                        Incident.detected_at >= since,
                        Incident.processed_at.isnot(None)
                    )
                ).count()
                
                # Não processados
                unprocessed = db.query(Incident).filter(
                    and_(
                        Incident.detected_at >= since,
                        Incident.processed_at.is_(None)
                    )
                ).count()
                
                # Incidentes de atacante processados
                attacker_processed = db.query(Incident).filter(
                    and_(
                        Incident.detected_at >= since,
                        Incident.processed_at.isnot(None),
                        Incident.incident_type.like('%Atacante%')
                    )
                ).count()
                
                # Incidentes de atacante não processados
                attacker_unprocessed = db.query(Incident).filter(
                    and_(
                        Incident.detected_at >= since,
                        Incident.processed_at.is_(None),
                        Incident.incident_type.like('%Atacante%')
                    )
                ).count()
                
                return {
                    'total_incidents': total,
                    'processed_count': processed,
                    'unprocessed_count': unprocessed,
                    'attacker_processed': attacker_processed,
                    'attacker_unprocessed': attacker_unprocessed,
                    'processing_rate': round((processed / total * 100) if total > 0 else 0, 2),
                    'period_hours': hours_ago,
                    'generated_at': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Erro ao gerar estatísticas de processamento: {e}")
            return {}
    
    def get_blocking_times(self, incident_id: int) -> Dict[str, Any]:
        """
        Calcula os tempos de detecção (TtD) e até bloqueio (TtB) para um incidente.
        
        TtD (Time to Detection): Tempo desde detected_at até processed_at
        TtB (Time to Block): Tempo desde detected_at até feedback_date no BlockingFeedbackHistory
        
        Args:
            incident_id: ID do incidente
            
        Returns:
            Dicionário com tempos calculados em segundos e formato legível
        """
        try:
            with get_db_session() as db:
                # Buscar o incidente
                incident = db.query(Incident).filter(Incident.id == incident_id).first()
                if not incident:
                    logger.warning(f"Incidente {incident_id} não encontrado")
                    return {'error': 'Incidente não encontrado'}
                
                # Buscar feedback de bloqueio relacionado
                from db.models import DhcpStaticMapping, BlockingFeedbackHistory
                
                device = db.query(DhcpStaticMapping).filter(
                    DhcpStaticMapping.ipaddr == incident.device_ip
                ).first()
                
                feedback = None
                if device:
                    feedback = db.query(BlockingFeedbackHistory).filter(
                        BlockingFeedbackHistory.dhcp_mapping_id == device.id,
                        BlockingFeedbackHistory.feedback_by == "Sistema Automático"
                    ).order_by(BlockingFeedbackHistory.created_at.desc()).first()
                
                # Calcular TtD (Time to Detection) - tempo até processar
                ttd_seconds = None
                ttd_readable = None
                if incident.processed_at and incident.detected_at:
                    delta = incident.processed_at - incident.detected_at
                    ttd_seconds = delta.total_seconds()
                    ttd_readable = self._format_time_delta(delta)
                
                # Calcular TtB (Time to Block) - tempo até bloquear
                ttb_seconds = None
                ttb_readable = None
                if feedback and feedback.created_at and incident.detected_at:
                    delta = feedback.created_at - incident.detected_at
                    ttb_seconds = delta.total_seconds()
                    ttb_readable = self._format_time_delta(delta)
                
                result = {
                    'incident_id': incident_id,
                    'device_ip': incident.device_ip,
                    'incident_type': incident.incident_type,
                    'detected_at': incident.detected_at.isoformat() if incident.detected_at else None,
                    'processed_at': incident.processed_at.isoformat() if incident.processed_at else None,
                    'blocked_at': feedback.created_at.isoformat() if feedback and feedback.created_at else None,
                    'ttd': {
                        'seconds': round(ttd_seconds, 3) if ttd_seconds else None,
                        'readable': ttd_readable
                    },
                    'ttb': {
                        'seconds': round(ttb_seconds, 3) if ttb_seconds else None,
                        'readable': ttb_readable
                    },
                    'blocked': feedback is not None
                }
                
                logger.info(f"Tempos calculados para incidente {incident_id}: TtD={ttd_readable}, TtB={ttb_readable}")
                return result
                
        except Exception as e:
            logger.error(f"Erro ao calcular tempos de bloqueio: {e}")
            return {'error': str(e)}
    
    def _format_time_delta(self, delta: timedelta) -> str:
        """
        Formata um timedelta para formato legível.
        
        Args:
            delta: Objeto timedelta
            
        Returns:
            String formatada (ex: "2h 15m 30s" ou "45m 12s")
        """
        total_seconds = int(delta.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        parts = []
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0:
            parts.append(f"{minutes}m")
        if seconds > 0 or len(parts) == 0:
            parts.append(f"{seconds}s")
        
        return " ".join(parts)
    
    def get_all_blocking_times(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Calcula tempos de detecção e bloqueio para todos os incidentes bloqueados.
        
        Args:
            limit: Número máximo de incidentes a retornar
            
        Returns:
            Lista de dicionários com tempos calculados
        """
        try:
            with get_db_session() as db:
                from db.models import DhcpStaticMapping, BlockingFeedbackHistory
                
                # Buscar incidentes processados de atacante
                incidents = db.query(Incident).filter(
                    Incident.processed_at.isnot(None),
                    Incident.incident_type.like('%Atacante%')
                ).order_by(Incident.detected_at.desc()).limit(limit).all()
                
                results = []
                for incident in incidents:
                    # Buscar feedback relacionado
                    device = db.query(DhcpStaticMapping).filter(
                        DhcpStaticMapping.ipaddr == incident.device_ip
                    ).first()
                    
                    feedback = None
                    if device:
                        feedback = db.query(BlockingFeedbackHistory).filter(
                            BlockingFeedbackHistory.dhcp_mapping_id == device.id,
                            BlockingFeedbackHistory.feedback_by == "Sistema Automático"
                        ).order_by(BlockingFeedbackHistory.created_at.desc()).first()
                    
                    # Calcular TtD
                    ttd_seconds = None
                    ttd_readable = None
                    if incident.processed_at and incident.detected_at:
                        delta = incident.processed_at - incident.detected_at
                        ttd_seconds = delta.total_seconds()
                        ttd_readable = self._format_time_delta(delta)
                    
                    # Calcular TtB
                    ttb_seconds = None
                    ttb_readable = None
                    if feedback and feedback.created_at and incident.detected_at:
                        delta = feedback.created_at - incident.detected_at
                        ttb_seconds = delta.total_seconds()
                        ttb_readable = self._format_time_delta(delta)
                    
                    results.append({
                        'incident_id': incident.id,
                        'device_ip': incident.device_ip,
                        'incident_type': incident.incident_type,
                        'detected_at': incident.detected_at.isoformat() if incident.detected_at else None,
                        'processed_at': incident.processed_at.isoformat() if incident.processed_at else None,
                        'blocked_at': feedback.created_at.isoformat() if feedback and feedback.created_at else None,
                        'ttd': {
                            'seconds': round(ttd_seconds, 3) if ttd_seconds else None,
                            'readable': ttd_readable
                        },
                        'ttb': {
                            'seconds': round(ttb_seconds, 3) if ttb_seconds else None,
                            'readable': ttb_readable
                        },
                        'blocked': feedback is not None
                    })
                
                logger.info(f"Calculados tempos para {len(results)} incidentes")
                return results
                
        except Exception as e:
            logger.error(f"Erro ao calcular tempos de bloqueio: {e}")
            return []