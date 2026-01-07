"""
Roteador FastAPI para endpoints de incidentes de segurança.
"""
import logging
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from .incident_service import IncidentService
from db.models import ZeekIncident
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

@router.get("/", response_model=List[IncidentResponse], summary="Lista incidentes")
async def get_incidents(
    device_ip: Optional[str] = Query(None, description="Filtrar por IP do dispositivo"),
    severity: Optional[str] = Query(None, description="Filtrar por severidade"),
    status: Optional[str] = Query(None, description="Filtrar por status"),
    log_type: Optional[str] = Query(None, description="Filtrar por tipo de log"),
    hours_ago: Optional[int] = Query(24, ge=1, le=168, description="Buscar incidentes das últimas N horas"),
    limit: int = Query(100, ge=1, le=1000, description="Limite de resultados"),
    offset: int = Query(0, ge=0, description="Offset para paginação")
):
    """
    Lista incidentes de segurança com filtros opcionais.
    
    - **device_ip**: Filtrar por IP específico do dispositivo
    - **severity**: Filtrar por nível de severidade (low, medium, high, critical)
    - **status**: Filtrar por status (new, investigating, resolved, false_positive, escalated)
    - **log_type**: Filtrar por tipo de log do Zeek
    - **hours_ago**: Buscar incidentes das últimas N horas
    - **limit**: Número máximo de resultados (1-1000)
    - **offset**: Número de resultados para pular (paginação)
    """
    try:
        incidents = incident_service.get_incidents(
            device_ip=device_ip,
            severity=severity,
            status=status,
            log_type=log_type,
            hours_ago=hours_ago,
            limit=limit,
            offset=offset
        )
        
        return [incident.to_dict() for incident in incidents]
        
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
        
        # Verificar se o incidente é de um atacante (contém "Atacante")
        is_attacker = "Atacante" in incident_type
        
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
        
        # Verificar se o IP já está bloqueado
        with AliasService() as alias_service:
            # Verificar se está no alias "Bloqueados"
            blocked_alias = alias_service.get_alias_by_name("Bloqueados")
            if blocked_alias:
                blocked_addresses = [addr['address'] for addr in blocked_alias['addresses']]
                if device_ip in blocked_addresses:
                    logger.warning(f"IP {device_ip} já está bloqueado")
                    return {
                        "success": True,
                        "message": f"IP {device_ip} já estava bloqueado",
                        "device_ip": device_ip,
                        "incident_id": request.incident_id,
                        "already_blocked": True
                    }
            
            # Remover do alias "Autorizados" se existir
            authorized_alias = alias_service.get_alias_by_name("Autorizados")
            if authorized_alias:
                authorized_addresses = [addr['address'] for addr in authorized_alias['addresses']]
                if device_ip in authorized_addresses:
                    logger.info(f"Removendo IP {device_ip} do alias Autorizados")
                    
                    # Criar nova lista sem o IP
                    new_addresses = []
                    new_details = []
                    for addr in authorized_alias['addresses']:
                        if addr['address'] != device_ip:
                            new_addresses.append(addr)
                            new_details.append(addr.get('detail', ''))
                    
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
                    'addresses': [{'address': device_ip, 'detail': f'Bloqueado automaticamente - Incidente {request.incident_id}'}]
                })
                
                if create_result.get('success'):
                    logger.info("Alias Bloqueados criado com sucesso")
                else:
                    logger.error(f"Erro ao criar alias Bloqueados: {create_result}")
                    raise HTTPException(
                        status_code=500,
                        detail="Erro ao criar alias Bloqueados no pfSense"
                    )
            else:
                # Adicionar IP ao alias existente
                logger.info(f"Adicionando IP {device_ip} ao alias Bloqueados existente")
                add_result = alias_service.add_addresses_to_alias("Bloqueados", [{
                    'address': device_ip, 
                    'detail': f'Bloqueado automaticamente - Incidente {request.incident_id}'
                }])
                
                if add_result.get('success'):
                    logger.info(f"IP {device_ip} adicionado ao alias Bloqueados com sucesso")
                else:
                    logger.error(f"Erro ao adicionar IP ao alias Bloqueados: {add_result}")
                    raise HTTPException(
                        status_code=500,
                        detail="Erro ao adicionar IP ao alias Bloqueados no pfSense"
                    )
        
        # Atualizar status do incidente
        incident_service.update_incident_status(
            request.incident_id, 
            "resolved", 
            f"Dispositivo bloqueado automaticamente. Motivo: {request.reason}"
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
                        admin_reason=f"{request.reason} - Incidente {request.incident_id}: {incident.incident_type}",
                        admin_name=request.admin_name,
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
        
        logger.info(f"Bloqueio automático concluído para IP {device_ip}")
        
        return {
            "success": True,
            "message": f"Dispositivo {device_ip} bloqueado automaticamente com sucesso",
            "device_ip": device_ip,
            "incident_id": request.incident_id,
            "incident_type": incident.incident_type,
            "reason": request.reason,
            "already_blocked": False
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro no bloqueio automático: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno no bloqueio automático: {str(e)}"
        )
