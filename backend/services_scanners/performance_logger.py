"""
Sistema de logging de performance para medir tempos de detecção e bloqueio.

Este módulo registra métricas de performance incluindo:
- Tempos de detecção e bloqueio
- Consumo de CPU e memória RAM
- Endpoints envolvidos no processo
- Sincronizações com pfSense
"""
import logging
import psutil
import os
import threading
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class PerformanceLogger:
    """
    Logger de performance que registra métricas em arquivo log_test.txt
    """
    
    def __init__(self, log_file: str = "log_test.txt"):
        """
        Inicializa o logger de performance.
        
        Args:
            log_file: Nome do arquivo de log
        """
        self.log_file = Path(log_file)
        self.lock = threading.Lock()
        self.process = psutil.Process(os.getpid())
        
        # Criar arquivo de log se não existir
        self._initialize_log_file()
    
    def _initialize_log_file(self):
        """Inicializa o arquivo de log com cabeçalho"""
        if not self.log_file.exists():
            with open(self.log_file, 'w', encoding='utf-8') as f:
                f.write("=" * 100 + "\n")
                f.write("LOG DE TESTE - SISTEMA DE DETECÇÃO E BLOQUEIO AUTOMÁTICO\n")
                f.write("=" * 100 + "\n")
                f.write(f"Iniciado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 100 + "\n\n")
    
    def _get_system_metrics(self) -> Dict[str, Any]:
        """
        Obtém métricas do sistema (CPU e memória).
        
        Returns:
            Dicionário com métricas
        """
        try:
            cpu_percent = self.process.cpu_percent(interval=0.1)
            memory_info = self.process.memory_info()
            memory_percent = self.process.memory_percent()
            
            # Métricas do sistema
            system_cpu = psutil.cpu_percent(interval=0.1)
            system_memory = psutil.virtual_memory()
            
            return {
                'process_cpu_percent': cpu_percent,
                'process_memory_mb': memory_info.rss / (1024 * 1024),  # MB
                'process_memory_percent': memory_percent,
                'system_cpu_percent': system_cpu,
                'system_memory_percent': system_memory.percent,
                'system_memory_available_mb': system_memory.available / (1024 * 1024),
                'system_memory_total_mb': system_memory.total / (1024 * 1024)
            }
        except Exception as e:
            logger.warning(f"Erro ao obter métricas do sistema: {e}")
            return {
                'process_cpu_percent': 0,
                'process_memory_mb': 0,
                'process_memory_percent': 0,
                'system_cpu_percent': 0,
                'system_memory_percent': 0,
                'system_memory_available_mb': 0,
                'system_memory_total_mb': 0
            }
    
    def log_event(
        self,
        event_type: str,
        description: str,
        incident_id: Optional[int] = None,
        device_ip: Optional[str] = None,
        endpoint: Optional[str] = None,
        duration_seconds: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Registra um evento no log de performance.
        
        Args:
            event_type: Tipo do evento (ex: "DETECTION", "BLOCKING", "SYNC")
            description: Descrição do evento
            incident_id: ID do incidente (opcional)
            device_ip: IP do dispositivo (opcional)
            endpoint: Endpoint chamado (opcional)
            duration_seconds: Duração em segundos (opcional)
            metadata: Metadados adicionais (opcional)
        """
        timestamp = datetime.now()
        metrics = self._get_system_metrics()
        
        log_entry = {
            'timestamp': timestamp.isoformat(),
            'event_type': event_type,
            'description': description,
            'incident_id': incident_id,
            'device_ip': device_ip,
            'endpoint': endpoint,
            'duration_seconds': duration_seconds,
            'metrics': metrics,
            'metadata': metadata or {}
        }
        
        # Formatar entrada de log
        log_lines = [
            "\n" + "=" * 100,
            f"TIMESTAMP: {timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}",
            f"TIPO: {event_type}",
            f"DESCRIÇÃO: {description}",
        ]
        
        if incident_id:
            log_lines.append(f"INCIDENTE ID: {incident_id}")
        
        if device_ip:
            log_lines.append(f"IP DO DISPOSITIVO: {device_ip}")
        
        if endpoint:
            log_lines.append(f"ENDPOINT: {endpoint}")
        
        if duration_seconds is not None:
            log_lines.append(f"DURAÇÃO: {duration_seconds:.3f}s ({self._format_duration(duration_seconds)})")
        
        log_lines.extend([
            "",
            "MÉTRICAS DO SISTEMA:",
            f"  CPU (Processo): {metrics['process_cpu_percent']:.2f}%",
            f"  CPU (Sistema): {metrics['system_cpu_percent']:.2f}%",
            f"  Memória RAM (Processo): {metrics['process_memory_mb']:.2f} MB ({metrics['process_memory_percent']:.2f}%)",
            f"  Memória RAM (Sistema): {metrics['system_memory_percent']:.2f}% usado "
            f"({metrics['system_memory_available_mb']:.0f} MB disponíveis de {metrics['system_memory_total_mb']:.0f} MB)",
        ])
        
        if metadata:
            log_lines.append("")
            log_lines.append("METADADOS:")
            for key, value in metadata.items():
                log_lines.append(f"  {key}: {value}")
        
        log_lines.append("=" * 100)
        
        # Escrever no arquivo de log
        with self.lock:
            try:
                with open(self.log_file, 'a', encoding='utf-8') as f:
                    f.write("\n".join(log_lines) + "\n")
                    f.flush()  # Garantir que é escrito imediatamente
            except Exception as e:
                logger.error(f"Erro ao escrever no log de performance: {e}")
        
        # Também logar no logger padrão
        logger.info(f"📊 [{event_type}] {description} - Duração: {duration_seconds:.3f}s" if duration_seconds else f"📊 [{event_type}] {description}")
    
    def log_detection(
        self,
        incident_id: int,
        device_ip: str,
        detected_at: datetime,
        incident_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Registra evento de detecção.
        
        Args:
            incident_id: ID do incidente
            device_ip: IP do dispositivo
            detected_at: Timestamp da detecção
            incident_type: Tipo do incidente
            metadata: Metadados adicionais
        """
        self.log_event(
            event_type="DETECTION",
            description=f"Incidente detectado: {incident_type}",
            incident_id=incident_id,
            device_ip=device_ip,
            metadata={
                'detected_at': detected_at.isoformat(),
                'incident_type': incident_type,
                **(metadata or {})
            }
        )
    
    def log_blocking(
        self,
        incident_id: int,
        device_ip: str,
        blocked_at: datetime,
        duration_seconds: float,
        endpoint: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Registra evento de bloqueio.
        
        Args:
            incident_id: ID do incidente
            device_ip: IP do dispositivo
            blocked_at: Timestamp do bloqueio
            duration_seconds: Duração do processo de bloqueio
            endpoint: Endpoint chamado
            metadata: Metadados adicionais
        """
        self.log_event(
            event_type="BLOCKING",
            description=f"Dispositivo bloqueado automaticamente",
            incident_id=incident_id,
            device_ip=device_ip,
            endpoint=endpoint,
            duration_seconds=duration_seconds,
            metadata={
                'blocked_at': blocked_at.isoformat(),
                **(metadata or {})
            }
        )
    
    def log_endpoint_call(
        self,
        endpoint: str,
        method: str,
        duration_seconds: float,
        success: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Registra chamada de endpoint.
        
        Args:
            endpoint: Endpoint chamado
            method: Método HTTP
            duration_seconds: Duração da chamada
            success: Se foi bem-sucedido
            metadata: Metadados adicionais
        """
        self.log_event(
            event_type="ENDPOINT_CALL",
            description=f"{method} {endpoint} - {'Sucesso' if success else 'Falha'}",
            endpoint=f"{method} {endpoint}",
            duration_seconds=duration_seconds,
            metadata={
                'success': success,
                'method': method,
                **(metadata or {})
            }
        )
    
    def log_sync(
        self,
        sync_type: str,
        duration_seconds: float,
        success: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Registra sincronização com pfSense.
        
        Args:
            sync_type: Tipo de sincronização (ex: "ALIAS_UPDATE", "FIREWALL_RULE")
            duration_seconds: Duração da sincronização
            success: Se foi bem-sucedido
            metadata: Metadados adicionais
        """
        self.log_event(
            event_type="SYNC",
            description=f"Sincronização com pfSense: {sync_type} - {'Sucesso' if success else 'Falha'}",
            duration_seconds=duration_seconds,
            metadata={
                'sync_type': sync_type,
                'success': success,
                **(metadata or {})
            }
        )
    
    def log_processing(
        self,
        processing_type: str,
        duration_seconds: float,
        items_processed: int = 0,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Registra processamento em lote.
        
        Args:
            processing_type: Tipo de processamento
            duration_seconds: Duração do processamento
            items_processed: Número de itens processados
            metadata: Metadados adicionais
        """
        self.log_event(
            event_type="PROCESSING",
            description=f"Processamento: {processing_type} - {items_processed} itens processados",
            duration_seconds=duration_seconds,
            metadata={
                'processing_type': processing_type,
                'items_processed': items_processed,
                **(metadata or {})
            }
        )
    
    def log_timing_summary(
        self,
        incident_id: int,
        device_ip: str,
        detected_at: datetime,
        blocked_at: datetime,
        processing_at: Optional[datetime] = None
    ):
        """
        Registra resumo de tempos de detecção e bloqueio.
        
        Args:
            incident_id: ID do incidente
            device_ip: IP do dispositivo
            detected_at: Timestamp da detecção
            blocked_at: Timestamp do bloqueio
            processing_at: Timestamp do processamento (opcional)
        """
        # Calcular tempos
        ttd_seconds = None
        ttb_seconds = None
        ttp_seconds = None
        
        if processing_at:
            ttp_seconds = (processing_at - detected_at).total_seconds()
        
        ttb_seconds = (blocked_at - detected_at).total_seconds()
        
        metadata = {
            'detected_at': detected_at.isoformat(),
            'blocked_at': blocked_at.isoformat(),
            'ttb_seconds': ttb_seconds,
            'ttb_readable': self._format_duration(ttb_seconds)
        }
        
        if processing_at:
            metadata['processing_at'] = processing_at.isoformat()
            metadata['ttp_seconds'] = ttp_seconds
            metadata['ttp_readable'] = self._format_duration(ttp_seconds)
        
        self.log_event(
            event_type="TIMING_SUMMARY",
            description=f"Resumo de tempos - TtB: {self._format_duration(ttb_seconds)}",
            incident_id=incident_id,
            device_ip=device_ip,
            metadata=metadata
        )
    
    def _format_duration(self, seconds: float) -> str:
        """Formata duração em formato legível"""
        if seconds is None:
            return "N/A"
        
        total_seconds = int(seconds)
        milliseconds = int((seconds - total_seconds) * 1000)
        
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        secs = total_seconds % 60
        
        parts = []
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0:
            parts.append(f"{minutes}m")
        if secs > 0 or len(parts) == 0:
            parts.append(f"{secs}s")
        if milliseconds > 0 and len(parts) < 3:
            parts.append(f"{milliseconds}ms")
        
        return " ".join(parts) if parts else "0s"
    
    def log_test_start(self, test_description: str):
        """Registra início de um teste"""
        with self.lock:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write("\n\n")
                f.write("=" * 100 + "\n")
                f.write(f"INÍCIO DE TESTE: {test_description}\n")
                f.write("=" * 100 + "\n")
                f.write(f"Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 100 + "\n\n")
    
    def log_test_end(self, summary: Dict[str, Any]):
        """Registra fim de um teste com resumo"""
        with self.lock:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write("\n\n")
                f.write("=" * 100 + "\n")
                f.write("RESUMO DO TESTE\n")
                f.write("=" * 100 + "\n")
                for key, value in summary.items():
                    f.write(f"{key}: {value}\n")
                f.write("=" * 100 + "\n\n")


# Instância global do logger
_performance_logger: Optional[PerformanceLogger] = None
_performance_logger_lock = threading.Lock()


def get_performance_logger(log_file: str = "log_test.txt") -> PerformanceLogger:
    """
    Obtém instância global do logger de performance.
    
    Args:
        log_file: Nome do arquivo de log
        
    Returns:
        Instância do PerformanceLogger
    """
    global _performance_logger
    
    with _performance_logger_lock:
        if _performance_logger is None:
            _performance_logger = PerformanceLogger(log_file)
        
        return _performance_logger


def reset_performance_logger():
    """Reseta a instância global do logger (útil para testes)"""
    global _performance_logger
    with _performance_logger_lock:
        _performance_logger = None

