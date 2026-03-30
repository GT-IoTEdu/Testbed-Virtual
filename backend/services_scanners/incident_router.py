"""
Roteador FastAPI para endpoints de incidentes de segurança.
"""
import logging
import asyncio
import json
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

from .incident_service import IncidentService
from .incident_events import get_event_manager
from db.models import Incident
from db.enums import IncidentSeverity, IncidentStatus, ZeekLogType
from services_firewalls.alias_service import AliasService
from services_firewalls.blocking_feedback_service import BlockingFeedbackService

logger = logging.getLogger(__name__)

# Cria o roteador
router = APIRouter(prefix="/incidents", tags=["Incidentes de Segurança"])

# Instância do serviço
incident_service = IncidentService()

# Modelos Pydantic para validação
class IncidentCreate(BaseModel):
    device_ip: str
    device_name: Optional[str] = None
    incident_type: str
    severity: str
    description: str
    detected_at: Optional[datetime] = None
    zeek_log_type: str
    raw_log_data: Optional[dict] = None
    action_taken: Optional[str] = None
    notes: Optional[str] = None

class IncidentUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None
    action_taken: Optional[str] = None

class IncidentResponse(BaseModel):
    id: int
    device_ip: str
    device_name: Optional[str]
    incident_type: str
    severity: str
    status: str
    description: str
    detected_at: str
    zeek_log_type: str
    action_taken: Optional[str]
    assigned_to: Optional[int]
    notes: Optional[str]
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True

class AutoBlockRequest(BaseModel):
    incident_id: int
    reason: Optional[str] = "Bloqueio automático por incidente de segurança"
    admin_name: Optional[str] = "Sistema Automático"

@router.get("/stream", summary="Stream de eventos de novos incidentes (SSE)")
async def stream_incidents(token: Optional[str] = Query(None, description="Token JWT para autenticação (opcional)")):
    """
    Endpoint Server-Sent Events (SSE) para notificações em tempo real de novos incidentes.
    
    O cliente recebe eventos apenas quando novos incidentes são detectados e salvos no banco.
    Não há polling - a conexão permanece aberta e eventos são enviados apenas quando necessário.
    
    Nota: EventSource não suporta headers customizados, então o token é passado via query parameter.
    
    Uso no frontend:
    ```javascript
    const token = localStorage.getItem('token');
    const eventSource = new EventSource(`/api/incidents/stream?token=${token}`);
    eventSource.onmessage = (event) => {
      const incident = JSON.parse(event.data);
      // Atualizar view com novo incidente
    };
    ```
    """
    async def event_generator():
        """Gera eventos SSE para clientes conectados"""
        event_manager = get_event_manager()
        client_id, queue = event_manager.create_client_queue()
        
        try:
            # Enviar evento de conexão
            yield f"data: {json.dumps({'type': 'connected', 'message': 'Conectado ao stream de incidentes'})}\n\n"
            
            # Manter conexão aberta e enviar eventos quando chegarem
            while True:
                try:
                    # Aguardar evento com timeout para verificar se conexão ainda está ativa
                    event_data = await asyncio.wait_for(queue.get(), timeout=30.0)
                    
                    # Formatar como SSE
                    sse_data = json.dumps(event_data)
                    yield f"data: {sse_data}\n\n"
                    
                except asyncio.TimeoutError:
                    # Enviar heartbeat para manter conexão ativa
                    yield f": heartbeat\n\n"
                    continue
                except Exception as e:
                    logger.error(f"Erro no stream SSE: {e}")
                    break
                    
        except asyncio.CancelledError:
            logger.debug(f"Cliente SSE desconectado: {client_id}")
        except Exception as e:
            logger.error(f"Erro no stream SSE: {e}", exc_info=True)
        finally:
            event_manager.remove_client_queue(client_id)
            logger.debug(f"Stream SSE finalizado para cliente: {client_id}")
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Desabilita buffering no nginx
        }
    )


@router.get("/", summary="Lista incidentes (paginado)")
async def get_incidents(
    device_ip: Optional[str] = Query(None, description="Filtrar por IP do dispositivo"),
    severity: Optional[str] = Query(None, description="Filtrar por severidade"),
    status: Optional[str] = Query(None, description="Filtrar por status"),
    log_type: Optional[str] = Query(None, description="Filtrar por tipo de log"),
    hours_ago: Optional[int] = Query(168, ge=1, le=720, description="Buscar incidentes das últimas N horas"),
    limit: int = Query(10, ge=1, le=100, description="Itens por página"),
    offset: int = Query(0, ge=0, description="Offset para paginação")
):
    """
    Lista incidentes de segurança (tabela incidents) com filtros e paginação.
    Retorna { "items": [...], "total": N } (mais recentes primeiro).
    """
    try:
        incidents, total = incident_service.get_incidents(
            device_ip=device_ip,
            severity=severity,
            status=status,
            log_type=log_type,
            hours_ago=hours_ago,
            limit=limit,
            offset=offset
        )
        return {"items": [incident.to_dict() for incident in incidents], "total": total}
    except Exception as e:
        logger.error(f"Erro ao listar incidentes: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno ao buscar incidentes: {str(e)}"
        )

@router.get("/{incident_id}", response_model=IncidentResponse, summary="Busca incidente por ID")
async def get_incident(incident_id: int):
    """
    Busca um incidente específico por ID.
    """
    try:
        incident = incident_service.get_incident_by_id(incident_id)
        
        if not incident:
            raise HTTPException(
                status_code=404,
                detail=f"Incidente {incident_id} não encontrado"
            )
        
        return incident.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao buscar incidente {incident_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno ao buscar incidente: {str(e)}"
        )

@router.post("/", response_model=IncidentResponse, summary="Cria novo incidente")
async def create_incident(incident_data: IncidentCreate):
    """
    Cria um novo incidente de segurança.
    """
    try:
        # Valida severidade
        try:
            IncidentSeverity(incident_data.severity)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Severidade inválida: {incident_data.severity}. Valores válidos: {[s.value for s in IncidentSeverity]}"
            )
        
        # Valida tipo de log
        try:
            ZeekLogType(incident_data.zeek_log_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Tipo de log inválido: {incident_data.zeek_log_type}. Valores válidos: {[lt.value for lt in ZeekLogType]}"
            )
        
        # Converte para dicionário
        data_dict = incident_data.dict()
        if incident_data.detected_at is None:
            data_dict['detected_at'] = datetime.now()
        
        # Salva o incidente
        incident = incident_service.save_incident(data_dict)
        
        if not incident:
            raise HTTPException(
                status_code=500,
                detail="Erro ao salvar incidente"
            )
        
        return incident.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao criar incidente: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno ao criar incidente: {str(e)}"
        )

@router.put("/{incident_id}", summary="Atualiza incidente")
async def update_incident(incident_id: int, update_data: IncidentUpdate):
    """
    Atualiza um incidente existente.
    """
    try:
        # Verifica se o incidente existe
        incident = incident_service.get_incident_by_id(incident_id)
        if not incident:
            raise HTTPException(
                status_code=404,
                detail=f"Incidente {incident_id} não encontrado"
            )
        
        # Valida status se fornecido
        if update_data.status:
            try:
                IncidentStatus(update_data.status)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Status inválido: {update_data.status}. Valores válidos: {[s.value for s in IncidentStatus]}"
                )
            
            # Atualiza status
            success = incident_service.update_incident_status(
                incident_id, 
                update_data.status, 
                update_data.notes
            )
            
            if not success:
                raise HTTPException(
                    status_code=500,
                    detail="Erro ao atualizar status do incidente"
                )
        
        # Busca o incidente atualizado
        updated_incident = incident_service.get_incident_by_id(incident_id)
        
        return {
            "message": "Incidente atualizado com sucesso",
            "incident": updated_incident.to_dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao atualizar incidente {incident_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno ao atualizar incidente: {str(e)}"
        )

@router.post("/{incident_id}/assign", summary="Atribui incidente a usuário")
async def assign_incident(incident_id: int, user_id: int):
    """
    Atribui um incidente a um usuário específico.
    """
    try:
        success = incident_service.assign_incident(incident_id, user_id)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Incidente {incident_id} não encontrado"
            )
        
        return {
            "message": f"Incidente {incident_id} atribuído ao usuário {user_id} com sucesso"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao atribuir incidente {incident_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno ao atribuir incidente: {str(e)}"
        )

@router.get("/stats/summary", summary="Estatísticas dos incidentes")
async def get_incident_stats(
    hours_ago: int = Query(24, ge=1, le=168, description="Período para estatísticas em horas")
):
    """
    Retorna estatísticas dos incidentes.
    """
    try:
        stats = incident_service.get_incident_stats(hours_ago)
        
        return stats
        
    except Exception as e:
        logger.error(f"Erro ao gerar estatísticas: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno ao gerar estatísticas: {str(e)}"
        )

@router.post("/process-batch", summary="Processar incidentes em lote para bloqueio automático")
async def process_incidents_batch(
    limit: int = Query(50, ge=1, le=200, description="Número máximo de incidentes a processar")
):
    """
    Processa incidentes não processados em lote para bloqueio automático.
    
    Este endpoint:
    1. Busca incidentes não processados (processed_at IS NULL)
    2. Para cada incidente de "Atacante", aplica bloqueio automático
    3. Marca os incidentes como processados
    4. Retorna estatísticas do processamento
    
    IMPORTANTE: Este endpoint resolve o problema de incidentes simultâneos,
    pois processa todos os incidentes pendentes de uma vez.
    """
    try:
        endpoint_start = datetime.now()
        logger.info(f"Iniciando processamento em lote de incidentes (limite: {limit})")
        
        # Log de performance - chamada do endpoint
        try:
            from services_scanners.performance_logger import get_performance_logger
            perf_logger = get_performance_logger()
            perf_logger.log_event(
                event_type="ENDPOINT_CALL",
                description=f"POST /api/incidents/process-batch - limit={limit}",
                endpoint="POST /api/incidents/process-batch"
            )
        except Exception as e:
            logger.warning(f"Erro ao registrar log de performance: {e}")
        
        result = incident_service.process_incidents_for_auto_blocking(limit)
        
        endpoint_duration = (datetime.now() - endpoint_start).total_seconds()
        
        # Log de performance - fim do endpoint
        try:
            from services_scanners.performance_logger import get_performance_logger
            perf_logger = get_performance_logger()
            perf_logger.log_endpoint_call(
                endpoint="/api/incidents/process-batch",
                method="POST",
                duration_seconds=endpoint_duration,
                success=result.get('success', False),
                metadata={
                    'limit': limit,
                    'processed_count': result.get('processed_count', 0),
                    'blocked_count': result.get('blocked_count', 0)
                }
            )
        except Exception as e:
            logger.warning(f"Erro ao registrar log de performance: {e}")
        
        if result['success']:
            return {
                "success": True,
                "message": result['message'],
                "statistics": {
                    "processed_count": result['processed_count'],
                    "blocked_count": result['blocked_count'],
                    "skipped_count": result['skipped_count'],
                    "error_count": result['error_count']
                },
                "processed_incidents": result.get('processed_incidents', [])
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Erro no processamento em lote: {result.get('error', 'Erro desconhecido')}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro no endpoint de processamento em lote: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno no processamento em lote: {str(e)}"
        )

@router.get("/processing-stats", summary="Estatísticas de processamento de incidentes")
async def get_processing_stats(
    hours_ago: int = Query(24, ge=1, le=168, description="Período para estatísticas em horas")
):
    """
    Retorna estatísticas do processamento de incidentes para bloqueio automático.
    
    Mostra:
    - Total de incidentes
    - Quantos foram processados
    - Quantos estão pendentes
    - Taxa de processamento
    - Incidentes de atacante processados vs pendentes
    """
    try:
        stats = incident_service.get_processing_stats(hours_ago)
        
        if not stats:
            raise HTTPException(
                status_code=500,
                detail="Erro ao gerar estatísticas de processamento"
            )
        
        return {
            "success": True,
            "statistics": stats,
            "message": f"Estatísticas de processamento das últimas {hours_ago} horas"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao gerar estatísticas de processamento: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno ao gerar estatísticas: {str(e)}"
        )

@router.get("/unprocessed", summary="Listar incidentes não processados")
async def get_unprocessed_incidents(
    limit: int = Query(100, ge=1, le=500, description="Número máximo de incidentes a retornar")
):
    """
    Lista incidentes que ainda não foram processados para bloqueio automático.
    
    Útil para verificar quantos incidentes estão pendentes de processamento.
    """
    try:
        incidents = incident_service.get_unprocessed_incidents(limit)
        
        return {
            "success": True,
            "count": len(incidents),
            "incidents": [incident.to_dict() for incident in incidents],
            "message": f"Encontrados {len(incidents)} incidentes não processados"
        }
        
    except Exception as e:
        logger.error(f"Erro ao buscar incidentes não processados: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno ao buscar incidentes não processados: {str(e)}"
        )

@router.post("/auto-block", summary="Bloqueio automático por incidente")
async def auto_block_device(request: AutoBlockRequest):
    """
    Bloqueia automaticamente um dispositivo baseado em um incidente de segurança.
    
    IMPORTANTE: O bloqueio só é aplicado se o incident_type contém a palavra "Atacante".
    Exemplos que serão bloqueados:
    - "SQL Injection - Atacante"
    - "Malware - Atacante"
    - "Ataque DDoS - Atacante"
    
    Exemplos que NÃO serão bloqueados:
    - "SQL Injection - Vítima"
    - "Security Notice: CaptureLoss::Too_Little_Traffic"
    
    Este endpoint:
    1. Busca o incidente pelo ID
    2. Verifica se o incident_type contém "Atacante"
    3. Se contém "Atacante": Remove o IP do alias "Autorizados" 
    4. Se contém "Atacante": Adiciona o IP ao alias "Bloqueados"
    5. Atualiza o status do incidente
    6. Cria feedback administrativo
    """
    try:
        endpoint_start = datetime.now()
        
        # Log de performance - chamada do endpoint
        try:
            from services_scanners.performance_logger import get_performance_logger
            perf_logger = get_performance_logger()
            perf_logger.log_event(
                event_type="ENDPOINT_CALL",
                description=f"POST /api/incidents/auto-block - incident_id={request.incident_id}",
                endpoint="POST /api/incidents/auto-block",
                incident_id=request.incident_id
            )
        except Exception as e:
            logger.warning(f"Erro ao registrar log de performance: {e}")
        
        # Buscar o incidente
        incident = incident_service.get_incident_by_id(request.incident_id)
        if not incident:
            raise HTTPException(
                status_code=404,
                detail=f"Incidente {request.incident_id} não encontrado"
            )
        
        device_ip = incident.device_ip
        incident_type = incident.incident_type
        logger.info(f"Iniciando bloqueio automático para IP {device_ip} baseado no incidente {request.incident_id} (Tipo: {incident_type})")
        
        # Verificar se o incidente é de um atacante (contém "Atacante" ou "Attacker")
        is_attacker = "Atacante" in incident_type or "Attacker" in incident_type
        
        if not is_attacker:
            logger.info(f"Incidente {request.incident_id} não é de um atacante (Tipo: {incident_type}). Bloqueio automático não aplicado.")
            return {
                "success": False,
                "message": f"Bloqueio automático não aplicado - dispositivo não é identificado como atacante",
                "device_ip": device_ip,
                "incident_id": request.incident_id,
                "incident_type": incident_type,
                "reason": "Dispositivo não é atacante",
                "blocked": False
            }
        
        logger.info(f"Dispositivo {device_ip} identificado como atacante. Aplicando bloqueio automático.")
        
        # Usar o método do serviço para aplicar bloqueio (que já tem logging de performance)
        blocking_result = incident_service._apply_auto_block(incident)
        
        endpoint_duration = (datetime.now() - endpoint_start).total_seconds()
        
        # Log de performance - fim do endpoint
        try:
            from services_scanners.performance_logger import get_performance_logger
            perf_logger = get_performance_logger()
            perf_logger.log_endpoint_call(
                endpoint="/api/incidents/auto-block",
                method="POST",
                duration_seconds=endpoint_duration,
                success=blocking_result,
                metadata={
                    'incident_id': request.incident_id,
                    'device_ip': device_ip,
                    'incident_type': incident_type
                }
            )
        except Exception as e:
            logger.warning(f"Erro ao registrar log de performance: {e}")
        
        if blocking_result:
            return {
                "success": True,
                "message": f"Dispositivo {device_ip} bloqueado automaticamente com sucesso",
                "device_ip": device_ip,
                "incident_id": request.incident_id,
                "incident_type": incident_type,
                "blocked": True
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Falha ao aplicar bloqueio automático para IP {device_ip}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        endpoint_duration = (datetime.now() - endpoint_start).total_seconds() if 'endpoint_start' in locals() else 0
        
        # Log de performance - erro
        try:
            from services_scanners.performance_logger import get_performance_logger
            perf_logger = get_performance_logger()
            perf_logger.log_endpoint_call(
                endpoint="/api/incidents/auto-block",
                method="POST",
                duration_seconds=endpoint_duration,
                success=False,
                metadata={
                    'incident_id': request.incident_id if 'request' in locals() else None,
                    'error': str(e)
                }
            )
        except:
            pass
        
        logger.error(f"Erro no bloqueio automático: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno no bloqueio automático: {str(e)}"
        )

@router.get("/{incident_id}/blocking-times", summary="Tempos de detecção e bloqueio de um incidente")
async def get_incident_blocking_times(incident_id: int):
    """
    Obtém os tempos de detecção (TtD) e bloqueio (TtB) para um incidente específico.
    
    - **TtD (Time to Detection)**: Tempo desde a detecção até o processamento do incidente
    - **TtB (Time to Block)**: Tempo desde a detecção até o bloqueio efetivo do dispositivo
    
    Retorna os tempos em segundos e formato legível (ex: "2h 15m 30s").
    """
    try:
        result = incident_service.get_blocking_times(incident_id)
        
        if 'error' in result:
            raise HTTPException(
                status_code=404 if 'não encontrado' in result['error'] else 500,
                detail=result['error']
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao obter tempos de bloqueio: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao calcular tempos de bloqueio: {str(e)}"
        )

@router.get("/blocking-times/all", summary="Tempos de detecção e bloqueio de todos os incidentes")
async def get_all_blocking_times(
    limit: int = Query(100, ge=1, le=500, description="Número máximo de incidentes a retornar")
):
    """
    Obtém os tempos de detecção (TtD) e bloqueio (TtB) para todos os incidentes bloqueados.
    
    - **TtD (Time to Detection)**: Tempo desde a detecção até o processamento do incidente
    - **TtB (Time to Block)**: Tempo desde a detecção até o bloqueio efetivo do dispositivo
    
    Retorna os tempos em segundos e formato legível (ex: "2h 15m 30s").
    """
    try:
        results = incident_service.get_all_blocking_times(limit)
        return results
        
    except Exception as e:
        logger.error(f"Erro ao obter tempos de bloqueio: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao calcular tempos de bloqueio: {str(e)}"
        )
