"""
Utilitários para processamento de requisições HTTP.
"""
from fastapi import Request
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def get_client_ip(request: Request) -> Optional[str]:
    """
    Captura o IP real do cliente, considerando proxies e load balancers.
    
    Prioridade:
    1. X-Forwarded-For (primeiro IP da lista)
    2. X-Real-IP
    3. request.client.host (IP direto)
    
    Args:
        request: Objeto Request do FastAPI
        
    Returns:
        IP do cliente como string ou None se não conseguir determinar
    """
    try:
        # Verificar header X-Forwarded-For (comum em proxies/load balancers)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # X-Forwarded-For pode conter múltiplos IPs separados por vírgula
            # O primeiro é geralmente o IP original do cliente
            client_ip = forwarded_for.split(",")[0].strip()
            logger.debug(f"IP capturado via X-Forwarded-For: {client_ip}")
            return client_ip
        
        # Verificar header X-Real-IP (nginx e outros proxies)
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            client_ip = real_ip.strip()
            logger.debug(f"IP capturado via X-Real-IP: {client_ip}")
            return client_ip
        
        # Fallback para IP direto da conexão
        if request.client and request.client.host:
            client_ip = request.client.host
            logger.debug(f"IP capturado via request.client.host: {client_ip}")
            return client_ip
        
        logger.warning("Não foi possível determinar o IP do cliente")
        return None
        
    except Exception as e:
        logger.error(f"Erro ao capturar IP do cliente: {e}")
        return None

