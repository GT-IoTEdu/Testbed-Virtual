"""
Monitor simplificado de logs do Zeek - focado em notice.log
Objetivo: Conectar ao Zeek, ler notice.log, atualizar banco e view
"""
import logging
import time
import threading
from datetime import datetime, timedelta
from typing import Optional, Dict, Set

from .zeek_service import ZeekService
from .zeek_models import ZeekLogType, ZeekLogRequest

logger = logging.getLogger(__name__)


class ZeekMonitor:
    """Monitor que busca notice.log do Zeek e detecta incidentes"""
    
    def __init__(
        self,
        check_interval_seconds: int = 3,
        hours_ago: int = 1,
        maxlines: int = 500,
        institution_id: Optional[int] = None
    ):
        """Inicializa o monitor"""
        # Buscar instituição se não fornecida
        if not institution_id:
            try:
                from services_firewalls.institution_config_service import InstitutionConfigService
                institutions = InstitutionConfigService.get_all_institutions()
                if institutions:
                    institution_id = institutions[0]['id']
                    logger.info(f"🔍 [Monitor] Usando instituição: {institutions[0]['nome']} (ID: {institution_id})")
            except Exception as e:
                logger.error(f"❌ [Monitor] Erro ao buscar instituições: {e}", exc_info=True)
        
        # Criar serviço Zeek
        self.zeek_service = ZeekService(institution_id=institution_id) if institution_id else ZeekService()
        self.institution_id = institution_id
        
        # Validar configurações
        if not self.zeek_service.api_token:
            logger.error(f"❌ [Monitor] Token do Zeek não configurado!")
        if not self.zeek_service.base_url:
            logger.error(f"❌ [Monitor] URL do Zeek não configurada!")
        
        # Configurações
        self.check_interval = check_interval_seconds
        self.hours_ago = hours_ago
        self.maxlines = maxlines
        
        # Estado do monitor
        self.is_running = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.last_check_time: Optional[datetime] = None
        self.last_timestamp: Optional[datetime] = None
        
        # Cache de IDs de logs processados (evita duplicatas)
        self.processed_log_ids: Set[str] = set()
        self.processed_log_ids_max_size = 10000
        
        # Estatísticas
        self.stats = {
            'total_checks': 0,
            'total_logs_processed': 0,
            'total_incidents': 0,
            'errors': 0,
            'file_not_found_count': 0,
            'endpoint_not_found_count': 0
        }
        
        logger.info(
            f"✅ [Monitor] ZeekMonitor criado - "
            f"URL: {self.zeek_service.base_url}, "
            f"Token: {'✅' if self.zeek_service.api_token else '❌'}, "
            f"Intervalo: {check_interval_seconds}s"
        )
    
    def start(self):
        """Inicia o monitoramento em background"""
        if self.is_running:
            logger.warning("⚠️ [Monitor] Já está em execução")
            return
        
        # Validar configurações antes de iniciar
        if not self.zeek_service.api_token or not self.zeek_service.base_url:
            logger.error(f"❌ [Monitor] Não é possível iniciar: configurações inválidas")
            return
        
        logger.info(f"⚡ [Monitor] Iniciando monitoramento - URL: {self.zeek_service.base_url}, Intervalo: {self.check_interval}s")
        
        self.is_running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True, name="ZeekMonitor")
        self.monitor_thread.start()
        logger.info(f"✅ [Monitor] Thread de monitoramento iniciada")
    
    def stop(self):
        """Para o monitoramento"""
        if not self.is_running:
            return
        
        self.is_running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("⏹️ [Monitor] Monitor parado")
    
    def _monitor_loop(self):
        """Loop principal do monitor - continua indefinidamente, nunca para"""
        logger.info("🔄 [Monitor] Loop de monitoramento iniciado - verificando notice.log a cada 3 segundos")
        logger.info("ℹ️ [Monitor] O monitor continuará tentando mesmo se notice.log não existir ainda")
        
        if not self.zeek_service.api_token:
            logger.error("❌ [Monitor] Token não configurado - monitor não pode funcionar")
            self.is_running = False
            return
        
        check_count = 0
        
        while self.is_running:
            try:
                self._check_logs()
                check_count += 1
                
                # Log resumo a cada 20 verificações (aproximadamente 1 minuto)
                if check_count % 20 == 0:
                    logger.info(
                        f"📊 [Monitor] Resumo - Verificações: {self.stats['total_checks']}, "
                        f"Logs processados: {self.stats['total_logs_processed']}, "
                        f"Incidentes salvos: {self.stats['total_incidents']}, "
                        f"Arquivo não encontrado: {self.stats['file_not_found_count']}x"
                    )
                
            except Exception as e:
                # Erros críticos - logar mas continuar tentando (NUNCA PARAR)
                self.stats['errors'] += 1
                logger.error(f"❌ [Monitor] Erro no loop: {e}", exc_info=True)
                # NÃO PARAR - continuar tentando mesmo com erros
            
            if self.is_running:
                time.sleep(self.check_interval)
        
        logger.warning("⏹️ [Monitor] Loop de monitoramento finalizado")
    
    def _check_logs(self):
        """Verifica logs do Zeek - apenas notice.log"""
        self.stats['total_checks'] += 1
        self.last_check_time = datetime.now()
        
        try:
            # Determinar timestamp inicial
            end_time = datetime.now()
            if self.last_timestamp:
                start_time = self.last_timestamp + timedelta(seconds=1)
            else:
                # Primeira verificação: buscar das últimas horas
                start_time = end_time - timedelta(hours=self.hours_ago)
                if self.stats['total_checks'] == 1:
                    logger.info(f"🔍 [Monitor] Primeira verificação - buscando logs das últimas {self.hours_ago} horas")
            
            # Criar requisição
            request = ZeekLogRequest(
                logfile=ZeekLogType.NOTICE,
                maxlines=self.maxlines,
                start_time=start_time,
                end_time=end_time
            )
            
            # Buscar logs do Zeek
            response = self.zeek_service.get_logs(request)
            
            if not response.success:
                # Tratar erro mas continuar tentando
                self._handle_error(response)
                return
            
            # Se chegou aqui, o arquivo existe e a requisição foi bem-sucedida
            # Processar logs encontrados
            if response.logs:
                logger.info(f"📊 [Monitor] {len(response.logs)} log(s) encontrado(s) em notice.log - processando...")
                self._process_logs_batch(response.logs, end_time)
            else:
                # Arquivo existe mas não há logs novos
                logger.debug(f"ℹ️ [Monitor] Arquivo notice.log existe mas não há logs novos")
                # Atualizar timestamp para não reprocessar
                if not self.last_timestamp:
                    self.last_timestamp = end_time - timedelta(seconds=2)
            
        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"❌ [Monitor] Erro ao verificar logs: {e}", exc_info=True)
            # Continuar tentando mesmo com erro
    
    def _handle_error(self, response):
        """Trata erros de forma inteligente - nunca para o monitor"""
        error_msg = response.message.lower()
        
        if 'log file not found' in error_msg or 'file not found' in error_msg:
            # Arquivo não existe ainda - NORMAL, continuar tentando
            self.stats['file_not_found_count'] += 1
            # Log apenas na primeira vez e depois a cada 100 tentativas
            if self.stats['file_not_found_count'] == 1:
                logger.info(f"ℹ️ [Monitor] Arquivo notice.log ainda não foi criado pelo Zeek - continuando a verificar...")
            elif self.stats['file_not_found_count'] % 100 == 0:
                logger.debug(f"ℹ️ [Monitor] Arquivo notice.log não encontrado ({self.stats['file_not_found_count']}x) - aguardando criação pelo Zeek")
            # NÃO atualizar timestamp - quando o arquivo for criado, buscar desde o início
            return
        
        elif 'endpoint não encontrado' in error_msg or 'endpoint not found' in error_msg:
            # Endpoint não existe - problema de configuração, mas continuar tentando
            self.stats['endpoint_not_found_count'] += 1
            if self.stats['endpoint_not_found_count'] % 50 == 0:
                logger.error(
                    f"❌ [Monitor] Endpoint não encontrado ({self.stats['endpoint_not_found_count']}x): {response.message}\n"
                    f"   Verifique se alert_data.php existe em {self.zeek_service.base_url}/alert_data.php\n"
                    f"   Monitor continuará tentando..."
                )
            return
        
        else:
            # Outros erros - logar mas continuar
            self.stats['errors'] += 1
            if self.stats['errors'] % 20 == 0:
                logger.warning(f"⚠️ [Monitor] Erro ({self.stats['errors']}x): {response.message}")
    
    def _process_logs_batch(self, logs: list, end_time: datetime):
        """Processa logs em lote e salva incidentes no banco"""
        if not logs:
            return
        
        processed_count = 0
        incidents_saved = 0
        last_log_ts = None
        
        for log in logs:
            try:
                # Normalizar log
                normalized = self.zeek_service._normalize_log_fields(log)
                
                # Extrair timestamp
                ts = normalized.get('ts')
                if ts:
                    if isinstance(ts, dict) and 'raw' in ts:
                        ts = ts['raw']
                    elif isinstance(ts, (int, float)):
                        ts = float(ts)
                    else:
                        continue
                    
                    log_time = datetime.fromtimestamp(ts)
                    if last_log_ts is None or log_time > last_log_ts:
                        last_log_ts = log_time
                
                # Criar ID único do log para evitar duplicatas
                log_id = self._create_log_id(normalized)
                if log_id in self.processed_log_ids:
                    continue  # Já processado
                
                # Detectar incidente no log
                incident = self.zeek_service._detect_notice_incident(normalized)
                if incident:
                    logger.info(f"🔍 [Monitor] Incidente detectado: {incident.incident_type} - IP: {incident.device_ip}")
                    
                    # Salvar incidente no banco de dados
                    try:
                        saved_incident = self.zeek_service._save_incident_to_database(incident, normalized)
                        if saved_incident:
                            incidents_saved += 1
                            self.stats['total_incidents'] += 1
                            logger.info(f"✅ [Monitor] Incidente salvo no banco - ID: {saved_incident.id}, Tipo: {incident.incident_type}, IP: {incident.device_ip}")
                            
                            # Notificar clientes SSE sobre novo incidente (em thread separada)
                            try:
                                from .incident_events import get_event_manager
                                
                                event_manager = get_event_manager()
                                incident_data = {
                                    'id': saved_incident.id,
                                    'incident_type': saved_incident.incident_type,
                                    'device_ip': saved_incident.device_ip,
                                    'severity': saved_incident.severity.value if hasattr(saved_incident.severity, 'value') else str(saved_incident.severity),
                                    'status': saved_incident.status.value if hasattr(saved_incident.status, 'value') else str(saved_incident.status),
                                    'description': saved_incident.description,
                                    'detected_at': saved_incident.detected_at.isoformat() if saved_incident.detected_at else None,
                                    'created_at': saved_incident.created_at.isoformat() if hasattr(saved_incident, 'created_at') and saved_incident.created_at else None
                                }
                                
                                # Executar broadcast em thread separada (não bloqueia o monitor)
                                def notify_clients():
                                    try:
                                        import asyncio
                                        # Criar novo loop para esta thread
                                        try:
                                            loop = asyncio.get_event_loop()
                                        except RuntimeError:
                                            loop = asyncio.new_event_loop()
                                            asyncio.set_event_loop(loop)
                                        
                                        # Executar broadcast
                                        if loop.is_running():
                                            # Se o loop já está rodando, criar task
                                            asyncio.create_task(event_manager.broadcast_new_incident(incident_data))
                                        else:
                                            # Se não está rodando, executar diretamente
                                            loop.run_until_complete(event_manager.broadcast_new_incident(incident_data))
                                    except Exception as e:
                                        logger.debug(f"⚠️ [Monitor] Erro ao notificar clientes SSE: {e}")
                                
                                notification_thread = threading.Thread(target=notify_clients, daemon=True)
                                notification_thread.start()
                            except Exception as e:
                                logger.debug(f"⚠️ [Monitor] Erro ao notificar clientes SSE (não crítico): {e}")
                        else:
                            logger.debug(f"⚠️ [Monitor] Incidente não foi salvo (duplicado ou erro)")
                    except Exception as e:
                        logger.error(f"❌ [Monitor] Erro ao salvar incidente no banco: {e}", exc_info=True)
                        self.stats['errors'] += 1
                
                # Marcar como processado
                self.processed_log_ids.add(log_id)
                processed_count += 1
                
            except Exception as e:
                logger.error(f"❌ [Monitor] Erro ao processar log: {e}", exc_info=True)
                continue
        
        # Limpar cache se ficar muito grande
        if len(self.processed_log_ids) > self.processed_log_ids_max_size:
            sorted_ids = sorted(self.processed_log_ids)
            self.processed_log_ids = set(sorted_ids[-self.processed_log_ids_max_size // 2:])
        
        # Atualizar timestamp do último log processado
        if last_log_ts:
            self.last_timestamp = last_log_ts + timedelta(seconds=1)
            logger.debug(f"✅ [Monitor] Timestamp atualizado para {self.last_timestamp}")
        else:
            # Se não conseguiu extrair timestamp, usar end_time
            self.last_timestamp = end_time - timedelta(seconds=2)
        
        # Atualizar estatísticas
        self.stats['total_logs_processed'] += processed_count
        
        if processed_count > 0:
            logger.info(
                f"📊 [Monitor] Processados {processed_count} log(s), "
                f"{incidents_saved} incidente(s) salvo(s) no banco de dados"
            )
    
    def _create_log_id(self, log: dict) -> str:
        """Cria ID único para o log (evita duplicatas)"""
        ts = log.get('ts')
        if isinstance(ts, dict):
            ts = ts.get('raw', '')
        note = str(log.get('note', ''))
        src = str(log.get('src', ''))
        dst = str(log.get('dst', ''))
        return f"{ts}_{note}_{src}_{dst}"
    
    def get_status(self) -> dict:
        """Retorna status do monitor"""
        return {
            'is_running': self.is_running,
            'check_interval_seconds': self.check_interval,
            'last_check_time': self.last_check_time.isoformat() if self.last_check_time else None,
            'last_timestamp': self.last_timestamp.isoformat() if self.last_timestamp else None,
            'stats': self.stats.copy()
        }


# Instância global
_global_monitor: Optional[ZeekMonitor] = None


def start_zeek_monitor(
    check_interval_seconds: int = 3,
    hours_ago: int = 1,
    maxlines: int = 500
) -> ZeekMonitor:
    """Inicia o monitor global"""
    global _global_monitor
    
    logger.info(f"🚀 Iniciando monitor do Zeek (intervalo: {check_interval_seconds}s, maxlines: {maxlines})")
    
    if _global_monitor is None:
        _global_monitor = ZeekMonitor(
            check_interval_seconds=check_interval_seconds,
            hours_ago=hours_ago,
            maxlines=maxlines
        )
        logger.info("✅ Instância do monitor criada")
    
    if not _global_monitor.is_running:
        _global_monitor.start()
        logger.info("✅ Monitor iniciado com sucesso")
    else:
        logger.warning("⚠️ Monitor já está rodando")
    
    return _global_monitor


def stop_zeek_monitor():
    """Para o monitor global"""
    global _global_monitor
    if _global_monitor and _global_monitor.is_running:
        _global_monitor.stop()


def get_zeek_monitor() -> Optional[ZeekMonitor]:
    """Retorna a instância global"""
    return _global_monitor
