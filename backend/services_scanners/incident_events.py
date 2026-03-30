"""
Sistema de eventos para notificações em tempo real de novos incidentes
Usa asyncio.Queue para comunicação entre monitor e clientes SSE
"""
import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class IncidentEventManager:
    """Gerenciador de eventos para notificações de novos incidentes"""
    
    def __init__(self):
        """Inicializa o gerenciador de eventos"""
        # Fila de eventos para cada cliente SSE
        self._event_queues: Dict[str, asyncio.Queue] = {}
        # Contador de clientes
        self._client_counter = 0
        
    def create_client_queue(self) -> tuple[str, asyncio.Queue]:
        """Cria uma nova fila de eventos para um cliente SSE"""
        client_id = f"client_{self._client_counter}_{datetime.now().timestamp()}"
        self._client_counter += 1
        queue = asyncio.Queue()
        self._event_queues[client_id] = queue
        logger.debug(f"📡 [EventManager] Cliente SSE criado: {client_id}")
        return client_id, queue
    
    def remove_client_queue(self, client_id: str):
        """Remove a fila de eventos de um cliente"""
        if client_id in self._event_queues:
            del self._event_queues[client_id]
            logger.debug(f"📡 [EventManager] Cliente SSE removido: {client_id}")
    
    async def broadcast_new_incident(self, incident_data: Dict[str, Any]):
        """Envia notificação de novo incidente para todos os clientes conectados"""
        if not self._event_queues:
            return
        
        event_data = {
            'type': 'new_incident',
            'data': incident_data,
            'timestamp': datetime.now().isoformat()
        }
        
        # Enviar para todos os clientes conectados
        disconnected_clients = []
        for client_id, queue in self._event_queues.items():
            try:
                await queue.put(event_data)
                logger.debug(f"📡 [EventManager] Evento enviado para cliente {client_id}")
            except Exception as e:
                logger.warning(f"⚠️ [EventManager] Erro ao enviar evento para {client_id}: {e}")
                disconnected_clients.append(client_id)
        
        # Remover clientes desconectados
        for client_id in disconnected_clients:
            self.remove_client_queue(client_id)
        
        if self._event_queues:
            logger.info(f"📡 [EventManager] Novo incidente notificado para {len(self._event_queues)} cliente(s) SSE")


# Instância global do gerenciador de eventos
_event_manager: Optional[IncidentEventManager] = None


def get_event_manager() -> IncidentEventManager:
    """Retorna a instância global do gerenciador de eventos"""
    global _event_manager
    if _event_manager is None:
        _event_manager = IncidentEventManager()
    return _event_manager

