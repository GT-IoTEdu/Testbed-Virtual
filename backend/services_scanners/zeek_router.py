"""
Roteador FastAPI para endpoints do Zeek
"""
import logging
from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse

from .zeek_service import ZeekService
from .zeek_models import (
    ZeekLogType, ZeekLogRequest, ZeekLogResponse, 
    ZeekIncident, ZeekSeverity, ZeekIncidentStatus
)

logger = logging.getLogger(__name__)

# Cria o roteador
router = APIRouter(prefix="/zeek", tags=["Zeek Network Monitor"])

# Instância do serviço Zeek
zeek_service = ZeekService()


def get_zeek_service() -> ZeekService:
    """Dependency para obter instância do ZeekService"""
    return zeek_service


@router.get("/health", summary="Verifica saúde da API Zeek")
async def health_check(service: ZeekService = Depends(get_zeek_service)):
    """
    Verifica se a API do Zeek está respondendo
    """
    try:
        success, message = service.test_connection()
        
        return JSONResponse(
            status_code=200 if success else 503,
            content={
                "status": "healthy" if success else "unhealthy",
                "message": message,
                "timestamp": datetime.now().isoformat()
            }
        )
    except Exception as e:
        logger.error(f"Erro no health check do Zeek: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": f"Erro interno: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
        )


@router.get("/logs", response_model=ZeekLogResponse, summary="Busca logs do Zeek")
async def get_logs(
    logfile: ZeekLogType = Query(ZeekLogType.HTTP, description="Tipo de log"),
    maxlines: int = Query(10, ge=1, le=1000, description="Número máximo de linhas"),
    filter_ip: Optional[str] = Query(None, description="Filtrar por IP específico"),
    hours_ago: Optional[int] = Query(None, ge=1, le=168, description="Buscar logs das últimas N horas"),
    service: ZeekService = Depends(get_zeek_service)
):
    """
    Busca logs do Zeek Network Monitor
    
    - **logfile**: Tipo de log (http.log, dns.log, conn.log, etc.)
    - **maxlines**: Número máximo de linhas a retornar (1-1000)
    - **filter_ip**: Filtrar logs por IP específico
    - **hours_ago**: Buscar logs das últimas N horas (1-168)
    """
    try:
        # Calcula timestamps se especificado
        start_time = None
        end_time = None
        
        if hours_ago:
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=hours_ago)
        
        # Cria a requisição
        request = ZeekLogRequest(
            logfile=logfile,
            maxlines=maxlines,
            filter_ip=filter_ip,
            start_time=start_time,
            end_time=end_time
        )
        
        # Busca os logs
        response = service.get_logs(request)
        
        return response
        
    except Exception as e:
        logger.error(f"Erro ao buscar logs do Zeek: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno ao buscar logs: {str(e)}"
        )


@router.get("/incidents", response_model=List[ZeekIncident], summary="Lista incidentes detectados")
async def get_incidents(
    logfile: Optional[ZeekLogType] = Query(None, description="Filtrar por tipo de log"),
    severity: Optional[ZeekSeverity] = Query(None, description="Filtrar por severidade"),
    status: Optional[ZeekIncidentStatus] = Query(None, description="Filtrar por status"),
    device_ip: Optional[str] = Query(None, description="Filtrar por IP do dispositivo"),
    hours_ago: int = Query(24, ge=1, le=168, description="Buscar incidentes das últimas N horas"),
    maxlines: int = Query(50, ge=1, le=1000, description="Número máximo de logs a analisar"),
    service: ZeekService = Depends(get_zeek_service)
):
    """
    Lista incidentes de segurança detectados nos logs do Zeek
    
    - **logfile**: Filtrar por tipo de log específico
    - **severity**: Filtrar por nível de severidade
    - **status**: Filtrar por status do incidente
    - **device_ip**: Filtrar por IP do dispositivo
    - **hours_ago**: Buscar incidentes das últimas N horas
    - **maxlines**: Número máximo de logs a analisar por tipo
    """
    try:
        all_incidents = []
        
        # Define quais tipos de logs analisar
        log_types_to_analyze = [logfile] if logfile else [
            ZeekLogType.HTTP, 
            ZeekLogType.DNS, 
            ZeekLogType.CONN,
            ZeekLogType.NOTICE
        ]
        
        # Calcula timestamps
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours_ago)
        
        # Analisa cada tipo de log
        for log_type in log_types_to_analyze:
            try:
                request = ZeekLogRequest(
                    logfile=log_type,
                    maxlines=maxlines,
                    filter_ip=device_ip,
                    start_time=start_time,
                    end_time=end_time
                )
                
                response = service.get_logs(request)
                
                if response.success:
                    all_incidents.extend(response.incidents)
                else:
                    logger.warning(f"Falha ao analisar logs {log_type.value}: {response.message}")
                    
            except Exception as e:
                logger.error(f"Erro ao analisar logs {log_type.value}: {e}")
                continue
        
        # Aplica filtros
        filtered_incidents = all_incidents
        
        if severity:
            filtered_incidents = [i for i in filtered_incidents if i.severity == severity]
        
        if status:
            filtered_incidents = [i for i in filtered_incidents if i.status == status]
        
        # Ordena por timestamp (mais recentes primeiro)
        filtered_incidents.sort(key=lambda x: x.detected_at, reverse=True)
        
        return filtered_incidents
        
    except Exception as e:
        logger.error(f"Erro ao buscar incidentes: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno ao buscar incidentes: {str(e)}"
        )


@router.get("/log-types", response_model=List[str], summary="Lista tipos de logs disponíveis")
async def get_log_types(service: ZeekService = Depends(get_zeek_service)):
    """
    Lista os tipos de logs disponíveis no Zeek
    """
    try:
        return service.get_available_log_types()
    except Exception as e:
        logger.error(f"Erro ao listar tipos de logs: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno: {str(e)}"
        )


@router.get("/stats", summary="Estatísticas dos logs")
async def get_stats(
    hours_ago: int = Query(24, ge=1, le=168, description="Período para estatísticas"),
    service: ZeekService = Depends(get_zeek_service)
):
    """
    Retorna estatísticas dos logs do Zeek
    """
    try:
        stats = {
            "period_hours": hours_ago,
            "timestamp": datetime.now().isoformat(),
            "log_types": {},
            "incidents_by_severity": {
                "low": 0,
                "medium": 0,
                "high": 0,
                "critical": 0
            },
            "top_affected_ips": {},
            "total_incidents": 0
        }
        
        # Calcula timestamps
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours_ago)
        
        # Analisa cada tipo de log
        for log_type in [ZeekLogType.HTTP, ZeekLogType.DNS, ZeekLogType.CONN]:
            try:
                request = ZeekLogRequest(
                    logfile=log_type,
                    maxlines=100,  # Amostra para estatísticas
                    start_time=start_time,
                    end_time=end_time
                )
                
                response = service.get_logs(request)
                
                if response.success:
                    stats["log_types"][log_type.value] = {
                        "total_logs": response.total_lines,
                        "incidents": len(response.incidents)
                    }
                    
                    # Conta incidentes por severidade
                    for incident in response.incidents:
                        severity_key = incident.severity.value
                        stats["incidents_by_severity"][severity_key] += 1
                        stats["total_incidents"] += 1
                        
                        # Conta IPs mais afetados
                        ip = incident.device_ip
                        if ip not in stats["top_affected_ips"]:
                            stats["top_affected_ips"][ip] = 0
                        stats["top_affected_ips"][ip] += 1
                        
            except Exception as e:
                logger.error(f"Erro ao calcular stats para {log_type.value}: {e}")
                stats["log_types"][log_type.value] = {
                    "total_logs": 0,
                    "incidents": 0,
                    "error": str(e)
                }
        
        # Ordena IPs mais afetados
        sorted_ips = sorted(
            stats["top_affected_ips"].items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:10]  # Top 10
        stats["top_affected_ips"] = dict(sorted_ips)
        
        return stats
        
    except Exception as e:
        logger.error(f"Erro ao calcular estatísticas: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno: {str(e)}"
        )
