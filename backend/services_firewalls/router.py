"""
Rotas de dispositivos e integração com pfSense.

Este módulo expõe endpoints para:
- Cadastro e listagem de aliases no pfSense
- Listagem de servidores DHCP
- Listagem de mapeamentos estáticos DHCP
- Salvamento de dados DHCP no banco de dados
- Consulta de dispositivos cadastrados

Todos os endpoints retornam JSON.
"""
from fastapi import APIRouter, HTTPException, Query, Request, Depends, Body
from datetime import datetime
from typing import Optional
import requests
import config
from services_firewalls.pfsense_client import (
    cadastrar_alias_pfsense, listar_aliases_pfsense, obter_alias_pfsense,
    listar_clientes_dhcp_pfsense, listar_mapeamentos_staticos_dhcp_pfsense,
    cadastrar_mapeamento_statico_dhcp_pfsense, excluir_mapeamento_statico_dhcp_pfsense,
    atualizar_mapeamento_statico_dhcp_pfsense, listar_regras_firewall_pfsense,
    aplicar_mudancas_firewall_pfsense, aplicar_mudancas_dhcp_pfsense
)
from services_firewalls.dhcp_service import DhcpService
from services_firewalls.alias_service import AliasService
from services_firewalls.ip_assignment_service import ip_assignment_service
from services_firewalls.blocking_feedback_service import BlockingFeedbackService
from services_firewalls.request_utils import get_client_ip
from services_firewalls.institution_config_service import InstitutionConfigService
from db.models import DhcpStaticMapping
from db.session import SessionLocal
import ipaddress
from services_firewalls.dhcp_models import (
    DeviceSearchRequest, DeviceResponse, ServerResponse, DeviceStatisticsResponse,
    SaveDhcpResponse, DeviceSearchResponse, DeviceDetailResponse, BulkDeviceResponse,
    UserResponse, DeviceAssignmentRequest, DeviceAssignmentResponse, UserDevicesResponse,
    DeviceUsersResponse, AssignmentStatisticsResponse, DhcpStaticMappingCreateRequest,
    DhcpStaticMappingCreateResponse, DhcpStaticMappingDeleteResponse, DhcpStaticMappingUpdateRequest,
    DhcpStaticMappingUpdateResponse, DhcpSaveRequest, IpAddressListResponse, AllDevicesResponse,
    DeviceBlockRequest, DeviceUnblockRequest, DeviceBlockResponse
)
from services_firewalls.alias_models import (
    AliasCreateRequest, AliasUpdateRequest, AliasResponse, AliasListResponse,
    AliasStatisticsResponse, AliasSaveResponse, AliasAddressInfo, AliasAddAddressesRequest
)
from services_firewalls.user_device_service import UserDeviceService
from services_firewalls.permission_service import PermissionService
from db.models import DhcpServer, DhcpStaticMapping, User, UserDeviceAssignment, PfSenseFirewallRule
from db.enums import UserPermission
from pydantic import BaseModel
from typing import List, Optional
import json
import logging
from sqlalchemy import and_, or_, func
import requests

logger = logging.getLogger(__name__)

router = APIRouter()

# Mock de armazenamento em memória
DEVICES = []

class AliasCreateLegacy(BaseModel):
    """Modelo para cadastro de alias no pfSense (legado)."""
    name: str
    type: str
    descr: str
    address: List[str]
    detail: List[str]

class DhcpStaticMappingRequest(BaseModel):
    """Modelo para requisição de mapeamento estático DHCP."""
    parent_id: str
    id: int

# Endpoints Regras de Firewall
@router.get("/firewall/rules", summary="Listar regras de firewall do pfSense")
def list_firewall_rules(current_user_id: int = Query(..., description="ID do usuário que está fazendo a operação")):
    """
    Lista regras de firewall do pfSense via endpoint oficial /firewall/rules.
    Retorna 504 quando o pfSense está indisponível (timeout/conexão).
    
    Args:
        current_user_id (int): ID do usuário logado (para buscar configurações da instituição)
    """
    try:
        result = listar_regras_firewall_pfsense(user_id=current_user_id)
        # Normalizar para retornar apenas o array data
        data = result.get("data") if isinstance(result, dict) else result
        return data
    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
        raise HTTPException(status_code=504, detail=f"pfSense indisponível: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar regras de firewall: {e}")

@router.post("/firewall/apply", summary="Aplicar mudanças pendentes no firewall do pfSense")
def apply_firewall_changes(current_user_id: int = Query(..., description="ID do usuário que está fazendo a operação")):
    """
    Aplica as mudanças pendentes no firewall do pfSense.
    
    Este endpoint é equivalente a clicar no botão "Apply Changes" na interface web do pfSense.
    Deve ser chamado após fazer alterações em aliases, regras de firewall, etc.
    
    Args:
        current_user_id (int): ID do usuário logado (para buscar configurações da instituição)
    
    Retorna:
        Confirmação de que as mudanças foram aplicadas com sucesso.
        
    Nota:
        Este endpoint é chamado automaticamente após operações de bloqueio/liberação
        de dispositivos, mas pode ser chamado manualmente se necessário.
    """
    try:
        result = aplicar_mudancas_firewall_pfsense(user_id=current_user_id)
        return {
            "status": "ok",
            "message": "Mudanças aplicadas com sucesso no firewall",
            "result": result
        }
    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
        raise HTTPException(status_code=504, detail=f"pfSense indisponível: {e}")
    except Exception as e:
        logger.error(f"Erro ao aplicar mudanças no firewall: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao aplicar mudanças no firewall: {e}")

@router.post("/dhcp/apply", summary="Aplicar mudanças pendentes no servidor DHCP do pfSense")
def apply_dhcp_changes(current_user_id: int = Query(..., description="ID do usuário que está fazendo a operação")):
    """
    Aplica as mudanças pendentes no servidor DHCP do pfSense.
    
    Este endpoint é equivalente a clicar no botão "Apply Changes" após modificar
    configurações de DHCP (mapeamentos estáticos, etc.).
    
    Utiliza a API oficial do pfSense v2:
    POST /api/v2/services/dhcp_server/apply
    
    Args:
        current_user_id (int): ID do usuário logado (para buscar configurações da instituição)
    
    Retorna:
        Confirmação de que as mudanças DHCP foram aplicadas com sucesso.
        
    Exemplo de uso:
        POST /api/devices/dhcp/apply
        
    Nota:
        Este endpoint deve ser chamado após:
        - Criar novos mapeamentos estáticos DHCP
        - Atualizar mapeamentos existentes (se não usar apply=true)
        - Excluir mapeamentos (se não usar apply=true)
    """
    try:
        result = aplicar_mudancas_dhcp_pfsense(user_id=current_user_id)
        return {
            "status": "ok",
            "message": "Mudanças DHCP aplicadas com sucesso no pfSense",
            "result": result
        }
    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
        raise HTTPException(status_code=504, detail=f"pfSense indisponível: {e}")
    except Exception as e:
        logger.error(f"Erro ao aplicar mudanças DHCP: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao aplicar mudanças DHCP: {e}")

@router.post("/firewall/rules/save", summary="Sincronizar regras de firewall do pfSense com o banco de dados")
def save_firewall_rules(current_user_id: int = Query(..., description="ID do usuário que está fazendo a operação")):
    """
    Busca as regras no pfSense e salva/atualiza na tabela pfsense_firewall_rules.
    
    Args:
        current_user_id (int): ID do usuário logado (para buscar configurações da instituição)
    """
    try:
        result = listar_regras_firewall_pfsense(user_id=current_user_id)
        rules = result.get("data") if isinstance(result, dict) else (result or [])
        if not isinstance(rules, list):
            raise ValueError("Formato inesperado de retorno de regras")

        saved, updated = 0, 0
        from db.session import SessionLocal
        from datetime import datetime
        db = SessionLocal()
        try:
            # Buscar usuário para obter institution_id
            user = db.query(User).filter(User.id == current_user_id).first()
            if not user:
                raise HTTPException(status_code=404, detail="Usuário não encontrado")
            
            institution_id = user.institution_id
            
            # Se o usuário não tem institution_id, tentar detectar pela configuração do pfSense usado
            if not institution_id:
                # Tentar obter institution_id da configuração do pfSense que foi usada para buscar as regras
                try:
                    from services_firewalls.institution_config_service import InstitutionConfigService
                    config = InstitutionConfigService.get_user_institution_config(user_id=current_user_id)
                    if config and config.get('id'):
                        institution_id = config.get('id')
                        logger.info(f"Instituição detectada pela configuração do pfSense: {institution_id}")
                except Exception as e:
                    logger.warning(f"Não foi possível detectar institution_id: {e}")
            
            # Se ainda não temos institution_id, não podemos salvar regras de forma segura
            # (pode causar conflitos com outras instituições)
            if not institution_id:
                logger.warning(f"Usuário {current_user_id} não tem institution_id associado. Regras serão salvas sem institution_id.")
            
            for r in rules:
                pf_id = r.get("id")
                if pf_id is None:
                    continue
                # Buscar regra existente usando combinação pf_id + institution_id
                # Isso permite que diferentes instituições tenham regras com o mesmo pf_id
                existing_query = db.query(PfSenseFirewallRule).filter(PfSenseFirewallRule.pf_id == pf_id)
                if institution_id:
                    existing_query = existing_query.filter(PfSenseFirewallRule.institution_id == institution_id)
                else:
                    # Se não há institution_id, buscar apenas por pf_id (para compatibilidade com dados antigos)
                    existing_query = existing_query.filter(PfSenseFirewallRule.institution_id.is_(None))
                existing = existing_query.first()
                
                payload = {
                    'type': r.get('type'),
                    'interface': ", ".join(r.get('interface') or []) if isinstance(r.get('interface'), list) else (r.get('interface') or None),
                    'ipprotocol': r.get('ipprotocol'),
                    'protocol': r.get('protocol'),
                    'icmptype': r.get('icmptype'),
                    'source': r.get('source'),
                    'source_port': r.get('source_port'),
                    'destination': r.get('destination'),
                    'destination_port': r.get('destination_port'),
                    'descr': r.get('descr'),
                    'disabled': r.get('disabled') or False,
                    'log': r.get('log') or False,
                    'tag': r.get('tag'),
                    'statetype': r.get('statetype'),
                    'tcp_flags_any': r.get('tcp_flags_any') or False,
                    'tcp_flags_out_of': r.get('tcp_flags_out_of'),
                    'tcp_flags_set': r.get('tcp_flags_set'),
                    'gateway': r.get('gateway'),
                    'sched': r.get('sched'),
                    'dnpipe': r.get('dnpipe'),
                    'pdnpipe': r.get('pdnpipe'),
                    'defaultqueue': r.get('defaultqueue'),
                    'ackqueue': r.get('ackqueue'),
                    'floating': r.get('floating') or False,
                    'quick': r.get('quick') or False,
                    'direction': r.get('direction'),
                    'tracker': r.get('tracker'),
                    'associated_rule_id': r.get('associated_rule_id'),
                    'created_time': datetime.fromtimestamp(r.get('created_time')) if r.get('created_time') else None,
                    'created_by': r.get('created_by'),
                    'updated_time': datetime.fromtimestamp(r.get('updated_time')) if r.get('updated_time') else None,
                    'updated_by': r.get('updated_by'),
                    'institution_id': institution_id,
                }
                if existing:
                    for k, v in payload.items():
                        setattr(existing, k, v)
                    updated += 1
                else:
                    rec = PfSenseFirewallRule(pf_id=pf_id, **payload)
                    db.add(rec)
                    saved += 1
            db.commit()
        finally:
            db.close()

        return {"status": "success", "saved": saved, "updated": updated, "total": len(rules)}
    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
        raise HTTPException(status_code=504, detail=f"pfSense indisponível: {e}")
    except Exception as e:
        logger.error(f"Erro ao salvar regras de firewall: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao salvar regras de firewall: {e}")

@router.get("/firewall/rules-db", summary="Listar regras de firewall salvas no banco de dados")
def list_firewall_rules_db(current_user_id: int = Query(..., description="ID do usuário que está fazendo a operação")):
    """
    Lista regras de firewall salvas no banco de dados.
    
    Args:
        current_user_id (int): ID do usuário logado (para filtrar por instituição se for ADMIN)
    """
    try:
        from db.session import SessionLocal
        from db.models import User
        db = SessionLocal()
        try:
            # Buscar usuário para verificar permissão e instituição
            user = db.query(User).filter(User.id == current_user_id).first()
            if not user:
                raise HTTPException(status_code=404, detail="Usuário não encontrado")
            
            # Filtrar por instituição se for ADMIN
            query = db.query(PfSenseFirewallRule)
            if user.permission == UserPermission.ADMIN and user.institution_id:
                query = query.filter(PfSenseFirewallRule.institution_id == user.institution_id)
            
            rules = query.all()
            return [
                {
                    'id': r.id,
                    'pf_id': r.pf_id,
                    'type': r.type,
                    'interface': r.interface.split(', ') if r.interface else [],
                    'ipprotocol': r.ipprotocol,
                    'protocol': r.protocol,
                    'icmptype': r.icmptype,
                    'source': r.source,
                    'source_port': r.source_port,
                    'destination': r.destination,
                    'destination_port': r.destination_port,
                    'descr': r.descr,
                    'disabled': r.disabled,
                    'log': r.log,
                    'tag': r.tag,
                    'statetype': r.statetype,
                    'tcp_flags_any': r.tcp_flags_any,
                    'tcp_flags_out_of': r.tcp_flags_out_of,
                    'tcp_flags_set': r.tcp_flags_set,
                    'gateway': r.gateway,
                    'sched': r.sched,
                    'dnpipe': r.dnpipe,
                    'pdnpipe': r.pdnpipe,
                    'defaultqueue': r.defaultqueue,
                    'ackqueue': r.ackqueue,
                    'floating': r.floating,
                    'quick': r.quick,
                    'direction': r.direction,
                    'tracker': r.tracker,
                    'associated_rule_id': r.associated_rule_id,
                    'created_time': r.created_time,
                    'created_by': r.created_by,
                    'updated_time': r.updated_time,
                    'updated_by': r.updated_by,
                }
                for r in rules
            ]
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Erro ao listar regras no banco: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao listar regras no banco: {e}")

# Endpoints para aliases
@router.post("/alias", summary="Cadastrar alias no pfSense")
def add_alias(alias: AliasCreateLegacy, current_user_id: int = Query(..., description="ID do usuário que está fazendo a operação")):
    """
    Cadastra um novo alias no pfSense.
    Parâmetros:
        alias (AliasCreateLegacy): Dados do alias.
        current_user_id (int): ID do usuário logado (para buscar configurações da instituição)
    Retorna:
        JSON com resposta do pfSense.
    """
    try:
        from services_firewalls.pfsense_client import _get_pfsense_config
        pfsense_url, pfsense_key = _get_pfsense_config(user_id=current_user_id)
        
        result = cadastrar_alias_pfsense(
            name=alias.name,
            alias_type=alias.type,
            descr=alias.descr,
            address=alias.address,
            detail=alias.detail,
            pfsense_url=pfsense_url,
            pfsense_key=pfsense_key
        )
        return {"status": "ok", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao cadastrar alias no pfSense: {e}")

@router.get("/aliases/{name}", summary="Obter alias específico")
def get_alias_v2(name: str, current_user_id: int = Query(..., description="ID do usuário que está fazendo a consulta")):
    """
    Obtém um alias específico do pfSense pelo nome.
    
    Parâmetros:
        name (str): Nome do alias a ser buscado.
        current_user_id (int): ID do usuário logado (para buscar configurações da instituição)
    
    Retorna:
        JSON com dados do alias específico.
    
    Exemplo:
        GET /api/devices/aliases/Teste_API_IoT_EDU
    """
    try:
        from services_firewalls.pfsense_client import _get_pfsense_config
        pfsense_url, pfsense_key = _get_pfsense_config(user_id=current_user_id)
        
        result = obter_alias_pfsense(name, pfsense_url=pfsense_url, pfsense_key=pfsense_key)
        if result is None:
            raise HTTPException(status_code=404, detail=f"Alias '{name}' não encontrado")
        return {"status": "ok", "result": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter alias: {e}")

@router.get("/aliases", summary="Listar todos os aliases ou buscar por nome")
def get_aliases(
    name: Optional[str] = Query(None, description="Nome do alias (opcional)"),
    current_user_id: int = Query(..., description="ID do usuário que está fazendo a consulta")
):
    """
    Lista todos os aliases do pfSense ou busca um alias específico.
    
    Parâmetros:
        name (str, opcional): Nome do alias. Se fornecido, retorna apenas esse alias.
                            Se não fornecido, retorna todos os aliases.
        current_user_id (int): ID do usuário logado (para buscar configurações da instituição)
    
    Retorna:
        JSON com lista de aliases ou alias específico.
        
    Exemplos:
        GET /api/devices/aliases                    # Lista todos os aliases
        GET /api/devices/aliases?name=Teste_API_IoT_EDU  # Busca alias específico
    """
    try:
        from services_firewalls.pfsense_client import _get_pfsense_config
        pfsense_url, pfsense_key = _get_pfsense_config(user_id=current_user_id)
        
        if name:
            # Buscar alias específico
            result = obter_alias_pfsense(name, pfsense_url=pfsense_url, pfsense_key=pfsense_key)
            if result is None:
                raise HTTPException(status_code=404, detail=f"Alias '{name}' não encontrado")
            return {"status": "ok", "result": result}
        else:
            # Listar todos os aliases
            result = listar_aliases_pfsense(pfsense_url=pfsense_url, pfsense_key=pfsense_key)
            return {"status": "ok", "result": result}
    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
        # Retornar mensagem amigável para erros de conexão com pfSense
        raise HTTPException(status_code=504, detail=f"pfSense indisponível: {e}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter aliases: {e}")

# Endpoints DHCP
@router.get("/dhcp/servers", summary="Listar todos os servidores DHCP")
def list_dhcp_servers(current_user_id: int = Query(..., description="ID do usuário que está fazendo a consulta")):
    """
    Lista todos os servidores DHCP do pfSense.
    Acessa o endpoint /services/dhcp_servers.
    
    Args:
        current_user_id (int): ID do usuário logado (para buscar configurações da instituição)
    
    Retorna:
        JSON com lista de servidores DHCP e seus clientes.
    """
    try:
        result = listar_clientes_dhcp_pfsense(user_id=current_user_id)
        return {"status": "ok", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar servidores DHCP: {e}")

@router.get("/dhcp/static_mapping", summary="Listar mapeamentos estáticos DHCP")
def list_dhcp_static_mappings(
    parent_id: str = Query(..., description="ID da interface (ex: lan, wan, opt1)"), 
    id: int = Query(..., description="ID do mapeamento específico"),
    current_user_id: int = Query(..., description="ID do usuário que está fazendo a consulta")
):
    """
    Lista mapeamentos estáticos DHCP do pfSense.
    Acessa o endpoint /services/dhcp_server/static_mapping com parent_id e id como query parameters.
    
    Parâmetros:
        parent_id (str): ID da interface (ex: "lan", "wan", "opt1")
        id (int): ID do mapeamento específico
        current_user_id (int): ID do usuário logado (para buscar configurações da instituição)
    
    Exemplo:
        GET /api/devices/dhcp/static_mapping?parent_id=lan&id=6
    
    Retorna:
        JSON com mapeamento estático DHCP específico.
    """
    try:
        result = listar_mapeamentos_staticos_dhcp_pfsense(parent_id, id, user_id=current_user_id)
        return {"status": "ok", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar mapeamentos estáticos DHCP: {e}")

# Função auxiliar para atribuir IP do range da instituição
def _assign_ip_from_institution_range(institution_config: dict, user_id: int) -> Optional[str]:
    """Atribui um IP disponível do range da instituição"""
    try:
        import ipaddress
        from db.models import DhcpStaticMapping
        from db.session import SessionLocal
        
        ip_range_start = institution_config.get('ip_range_start')
        ip_range_end = institution_config.get('ip_range_end')
        institution_id = institution_config.get('institution_id')
        
        if not ip_range_start or not ip_range_end:
            logger.warning(f"Instituição não tem range de IPs configurado")
            return None
        
        range_start = ipaddress.ip_address(ip_range_start)
        range_end = ipaddress.ip_address(ip_range_end)
        
        # Buscar IPs já usados nesta instituição
        db = SessionLocal()
        try:
            used_ips = set()
            existing_mappings = db.query(DhcpStaticMapping).filter(
                DhcpStaticMapping.institution_id == institution_id
            ).all()
            for mapping in existing_mappings:
                if mapping.ipaddr:
                    try:
                        ip = ipaddress.ip_address(mapping.ipaddr)
                        if range_start <= ip <= range_end:
                            used_ips.add(str(ip))
                    except ValueError:
                        pass
            
            # Encontrar próximo IP disponível
            current_ip = range_start
            max_attempts = int(range_end) - int(range_start) + 1
            
            for _ in range(max_attempts):
                ip_str = str(current_ip)
                if ip_str not in used_ips:
                    logger.info(f"✅ IP {ip_str} disponível no range da instituição")
                    return ip_str
                current_ip = ipaddress.ip_address(int(current_ip) + 1)
            
            logger.warning(f"Nenhum IP disponível no range {ip_range_start} - {ip_range_end}")
            return None
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Erro ao atribuir IP do range da instituição: {e}")
        return None

def _suggest_available_ip_in_range(ip_range_start: str, ip_range_end: str, institution_id: int) -> Optional[str]:
    """Sugere um IP disponível dentro do range da instituição"""
    try:
        import ipaddress
        from db.models import DhcpStaticMapping
        from db.session import SessionLocal
        
        range_start = ipaddress.ip_address(ip_range_start)
        range_end = ipaddress.ip_address(ip_range_end)
        
        # Buscar IPs já usados nesta instituição
        db = SessionLocal()
        try:
            used_ips = set()
            existing_mappings = db.query(DhcpStaticMapping).filter(
                DhcpStaticMapping.institution_id == institution_id
            ).all()
            for mapping in existing_mappings:
                if mapping.ipaddr:
                    try:
                        ip = ipaddress.ip_address(mapping.ipaddr)
                        if range_start <= ip <= range_end:
                            used_ips.add(str(ip))
                    except ValueError:
                        pass
            
            # Encontrar primeiro IP disponível
            current_ip = range_start
            max_attempts = min(100, int(range_end) - int(range_start) + 1)  # Limitar a 100 tentativas
            
            for _ in range(max_attempts):
                ip_str = str(current_ip)
                if ip_str not in used_ips:
                    return ip_str
                current_ip = ipaddress.ip_address(int(current_ip) + 1)
            
            return None
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"Erro ao sugerir IP: {e}")
        return None

# Novos endpoints para gerenciamento de dados DHCP no banco
@router.post("/dhcp/save", summary="Salvar dados DHCP no banco de dados", response_model=SaveDhcpResponse)
def save_dhcp_data(
    request: DhcpSaveRequest,
    http_request: Request,
    current_user_id: int = Query(..., description="ID do usuário que está fazendo o cadastro")
):
    """
    Salva dados DHCP no banco de dados com parâmetros fornecidos pelo usuário.
    Detecta automaticamente a instituição/campus pelo IP de origem da requisição.
    
    Parâmetros obrigatórios:
        mac (str): Endereço MAC do dispositivo
        ipaddr (str): Endereço IP do dispositivo (opcional se auto_assign_ip=True)
        cid (str): ID do cliente (será replicado para hostname)
        descr (str): Descrição do dispositivo
        current_user_id (int): ID do usuário autenticado
    
    Retorna:
        Estatísticas da operação de salvamento.
    
    Exemplo de dados que serão salvos:
    {
      "parent_id": "lan",
      "id": 1,
      "mac": "bc:24:11:2c:0f:31",
      "ipaddr": "10.30.30.10",
      "cid": "lubuntu-live",
      "hostname": "lubuntu-live",
      "descr": "lubuntu-live-proxmox"
    }
    """
    try:
        # 1. Buscar instituição do usuário logado
        institution_id = None
        institution_config = None
        
        # Buscar instituição associada ao usuário
        user_config = InstitutionConfigService.get_user_institution_config(user_id=current_user_id)
        if user_config and user_config.get('institution_id'):
            institution_id = user_config.get('institution_id')
            institution_config = user_config
            logger.info(f"✅ Usando instituição do usuário logado: {institution_config.get('nome')} - {institution_config.get('cidade')} (ID: {institution_id})")
        else:
            # Se o usuário não tem instituição, tentar detectar pelo IP de origem (apenas se não for localhost)
            logger.info("ℹ️ Usuário não possui instituição associada, tentando detectar pelo IP de origem...")
            client_ip = get_client_ip(http_request)
            
            if client_ip and client_ip != "127.0.0.1":
                logger.info(f"🔍 Detectando instituição pelo IP de origem: {client_ip}")
                institution_id = InstitutionConfigService.get_institution_by_ip(client_ip)
                
                if institution_id:
                    logger.info(f"✅ Instituição identificada pelo IP: ID {institution_id} (IP origem: {client_ip})")
                    institution_config = InstitutionConfigService.get_institution_config(institution_id)
                    
                    # Associar automaticamente a instituição ao usuário
                    try:
                        from db.session import SessionLocal as UserSessionLocal
                        user_db = UserSessionLocal()
                        try:
                            user = user_db.query(User).filter(User.id == current_user_id).first()
                            if user and not user.institution_id:
                                user.institution_id = institution_id
                                user_db.commit()
                                logger.info(f"✅ Instituição {institution_id} associada automaticamente ao usuário {current_user_id}")
                        finally:
                            user_db.close()
                    except Exception as e:
                        logger.warning(f"⚠️ Erro ao associar instituição ao usuário: {e}")
                        # Não falhar a operação se a associação der erro
                else:
                    logger.warning(f"⚠️ Não foi possível identificar instituição pelo IP {client_ip}")
            elif client_ip == "127.0.0.1":
                logger.warning("⚠️ IP de origem é localhost (127.0.0.1) - não é possível detectar instituição automaticamente")
            else:
                logger.warning("⚠️ Não foi possível capturar IP de origem")
        
        # Se ainda não tem instituição, retornar erro com informações úteis
        if not institution_id or not institution_config:
            # Tentar obter informações sobre ranges disponíveis para mensagem de erro mais útil
            try:
                from db.session import SessionLocal as ErrSessionLocal
                from db.models import Institution as ErrInstitution
                err_db = ErrSessionLocal()
                try:
                    available_institutions = err_db.query(ErrInstitution).filter(ErrInstitution.is_active == True).all()
                    ranges_info = [f"{inst.nome} ({inst.cidade}): {inst.ip_range_start} - {inst.ip_range_end}" for inst in available_institutions]
                finally:
                    err_db.close()
            except:
                ranges_info = []
            
            error_detail = "Não foi possível identificar a rede/campus. "
            if client_ip:
                error_detail += f"Seu IP atual ({client_ip}) não está dentro de nenhum range configurado. "
            error_detail += "O usuário precisa ter uma instituição associada ou estar conectado à rede do campus. "
            if ranges_info:
                error_detail += f"\nRanges disponíveis: {', '.join(ranges_info)}"
            error_detail += "\nEntre em contato com o administrador para associar sua conta à instituição correta."
            
            raise HTTPException(status_code=400, detail=error_detail)
        
        logger.info(f"📋 Cadastrando dispositivo na instituição: {institution_config.get('nome')} (ID: {institution_id})")
        
        # 2. Determinar IP a ser usado (considerando range da instituição)
        assigned_ip = request.ipaddr
        
        # Se auto_assign_ip estiver ativado e não há IP fornecido, atribuir automaticamente
        if request.auto_assign_ip and not request.ipaddr:
            logger.info(f"Atribuindo IP automaticamente para MAC: {request.mac} (instituição: {institution_id})")
            
            # Atribuir IP usando o range da instituição
            if institution_config:
                assigned_ip = _assign_ip_from_institution_range(institution_config, current_user_id)
            else:
                # Fallback: usar serviço global
                assigned_ip = ip_assignment_service.assign_next_available_ip()
            
            if not assigned_ip:
                range_info = ""
                if institution_config:
                    range_info = f" (Range: {institution_config.get('ip_range_start')} - {institution_config.get('ip_range_end')})"
                raise HTTPException(
                    status_code=409,
                    detail=f"Não foi possível atribuir IP automaticamente. Range de IPs esgotado.{range_info}"
                )
            logger.info(f"IP {assigned_ip} atribuído automaticamente para MAC: {request.mac}")
        
        # Validar se IP foi fornecido ou atribuído
        if not assigned_ip:
            raise HTTPException(
                status_code=400,
                detail="IP é obrigatório. Forneça um IP ou ative a atribuição automática."
            )
        
        # Validar se o IP do dispositivo está no range da instituição do usuário
        if institution_config:
            try:
                import ipaddress
                ip_range_start = institution_config.get('ip_range_start')
                ip_range_end = institution_config.get('ip_range_end')
                
                if not ip_range_start or not ip_range_end:
                    logger.warning(f"⚠️ Instituição {institution_config.get('nome')} não tem range de IPs configurado")
                else:
                    device_ip_obj = ipaddress.ip_address(assigned_ip)
                    range_start = ipaddress.ip_address(ip_range_start)
                    range_end = ipaddress.ip_address(ip_range_end)
                    
                    if not (range_start <= device_ip_obj <= range_end):
                        # Sugerir um IP válido dentro do range
                        suggested_ip = _suggest_available_ip_in_range(ip_range_start, ip_range_end, institution_id)
                        error_detail = f"IP {assigned_ip} está fora do range da instituição {institution_config.get('nome')} - {institution_config.get('cidade')} (Range: {ip_range_start} - {ip_range_end})"
                        if suggested_ip:
                            error_detail += f". Sugestão de IP válido: {suggested_ip}"
                        raise HTTPException(
                            status_code=400,
                            detail=error_detail
                        )
                    logger.info(f"✅ IP {assigned_ip} validado - está dentro do range da instituição")
            except ValueError as e:
                logger.warning(f"⚠️ Erro ao validar IP {assigned_ip}: {e}")
                # Não falhar se houver erro na validação, apenas logar
            except HTTPException:
                raise
            except Exception as e:
                logger.warning(f"⚠️ Erro inesperado ao validar IP: {e}")
                # Não falhar se houver erro na validação, apenas logar
        
        # Criar dados DHCP com os parâmetros fornecidos
        dhcp_data = {
            "data": [
                {
                    "id": "lan",
                    "interface": "lan",
                    "enable": True,
                    "range_from": "10.30.30.254",
                    "range_to": "10.30.30.254",
                    "domain": "",
                    "failover_peerip": "",
                    "mac_allow": [],
                    "mac_deny": [],
                    "domainsearchlist": [],
                    "defaultleasetime": None,
                    "maxleasetime": None,
                    "gateway": "",
                    "dnsserver": None,
                    "winsserver": None,
                    "ntpserver": None,
                    "staticarp": False,
                    "ignorebootp": False,
                    "ignoreclientuids": False,
                    "nonak": False,
                    "disablepingcheck": False,
                    "dhcpleaseinlocaltime": False,
                    "statsgraph": False,
                    "denyunknown": None,
                    "pool": [],
                    "numberoptions": None,
                    "staticmap": [
                        {
                            "parent_id": "lan",
                            "id": 0,
                            "mac": request.mac,
                            "ipaddr": assigned_ip,
                            "cid": request.cid,
                            "hostname": request.cid.replace(" ", "-"),  # Replicar cid para hostname, substituindo espaços por hífens
                            "domain": "",
                            "domainsearchlist": [],
                            "defaultleasetime": None,
                            "maxleasetime": None,
                            "gateway": "",
                            "dnsserver": None,
                            "winsserver": None,
                            "ntpserver": None,
                            "arp_table_static_entry": False,
                            "descr": request.descr
                        }
                    ]
                }
            ]
        }
        
        # Primeiro, tentar salvar no pfSense
        pfsense_success = False
        pfsense_message = ""
        pfsense_id = None
        
        try:
            from services_firewalls.pfsense_client import cadastrar_mapeamento_statico_dhcp_pfsense
            
            # Preparar dados para pfSense
            pfsense_data = {
                "parent_id": "lan",
                "mac": request.mac,
                "ipaddr": assigned_ip,
                "cid": request.cid,
                "hostname": request.cid.replace(" ", "-"),  # Replicar cid para hostname, substituindo espaços por hífens
                "descr": request.descr
            }
            
            logger.info(f"Tentando salvar no pfSense: {pfsense_data}")
            
            # Cadastrar no pfSense usando configurações da instituição identificada
            pfsense_result = cadastrar_mapeamento_statico_dhcp_pfsense(
                pfsense_data, 
                verificar_existente=True,
                user_id=current_user_id,
                institution_id=institution_id
            )
            
            logger.info(f"Resultado do pfSense: {pfsense_result}")
            
            # Extrair o ID real do pfSense se disponível
            if isinstance(pfsense_result, dict) and 'id' in pfsense_result:
                pfsense_id = pfsense_result['id']
            elif isinstance(pfsense_result, list) and len(pfsense_result) > 0 and 'id' in pfsense_result[0]:
                pfsense_id = pfsense_result[0]['id']
            
            pfsense_success = True
            pfsense_message = "Dados salvos no pfSense com sucesso"
            
            # Aplicar mudanças DHCP automaticamente
            try:
                apply_result = aplicar_mudancas_dhcp_pfsense(user_id=current_user_id, institution_id=institution_id)
                logger.info(f"Mudanças DHCP aplicadas automaticamente após cadastro: {apply_result}")
            except Exception as apply_error:
                logger.warning(f"Erro ao aplicar mudanças DHCP automaticamente: {apply_error}")
                # Não falhar a operação se o apply der erro, apenas logar
            
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
            # Propagar para ser tratado como 504 no bloco externo
            raise
        except ValueError as e:
            # Erros de validação/conflito (ex: mapeamentos duplicados) devem retornar 409
            error_msg = str(e)
            if "Já existem mapeamentos DHCP" in error_msg or "já está em uso" in error_msg:
                logger.warning(f"Conflito ao salvar no pfSense: {e}")
                raise HTTPException(status_code=409, detail=error_msg)
            else:
                # Outros ValueError devem ser tratados como erro genérico
                logger.error(f"Erro de validação ao salvar no pfSense: {e}")
                pfsense_success = False
                pfsense_message = f"Erro ao salvar no pfSense: {e}"
        except Exception as e:
            logger.error(f"Erro ao salvar no pfSense: {e}")
            pfsense_success = False
            pfsense_message = f"Erro ao salvar no pfSense: {e}"
        
        # Só salvar no banco de dados se o pfSense foi bem-sucedido
        device_id = None
        if pfsense_success:
            # Atualizar o ID do pfSense nos dados antes de salvar
            if pfsense_id is not None:
                dhcp_data['data'][0]['staticmap'][0]['id'] = pfsense_id
            
            # Salvar no banco de dados com institution_id
            try:
                with DhcpService() as dhcp_service:
                    result = dhcp_service.save_dhcp_data(dhcp_data, institution_id=institution_id)
                    
                    # Buscar o dispositivo recém-criado para obter seu ID
                    # Fazer flush para garantir que o dispositivo está disponível na sessão
                    dhcp_service.db.flush()
                    
                    try:
                        # Buscar por MAC e institution_id para garantir que encontramos o dispositivo correto
                        from db.models import DhcpStaticMapping
                        device = dhcp_service.db.query(DhcpStaticMapping).filter(
                            DhcpStaticMapping.mac == request.mac,
                            DhcpStaticMapping.institution_id == institution_id
                        ).first()
                        
                        if not device:
                            # Se não encontrar com institution_id, tentar apenas por MAC
                            device = dhcp_service.find_device_by_mac(request.mac)
                        
                        if device:
                            device_id = device.id
                            logger.info(f"✅ Dispositivo encontrado após salvar: ID {device_id}, MAC {request.mac}, Institution: {institution_id}")
                        else:
                            logger.warning(f"⚠️ Dispositivo não encontrado após salvar (MAC: {request.mac}, Institution: {institution_id})")
                    except Exception as e:
                        logger.warning(f"⚠️ Erro ao buscar dispositivo após salvar: {e}")
                        # Continuar mesmo se não conseguir buscar o dispositivo
            except Exception as e:
                logger.error(f"❌ Erro ao salvar dados DHCP no banco: {e}", exc_info=True)
                raise
        else:
            # Se falhou no pfSense, não salvar no banco
            result = {
                'status': 'success',
                'servers_saved': 0,
                'mappings_saved': 0,
                'mappings_updated': 0,
                'timestamp': datetime.now().isoformat()
            }
        
        # Criar atribuição do dispositivo ao usuário que o cadastrou
        if device_id:
            try:
                from services_firewalls.user_device_service import UserDeviceService
                from db.session import SessionLocal as AssignmentSessionLocal
                
                # Usar sessão separada para evitar conflitos
                assignment_db = AssignmentSessionLocal()
                try:
                    # Verificar se já existe atribuição ativa
                    existing = assignment_db.query(UserDeviceAssignment).filter(
                        UserDeviceAssignment.user_id == current_user_id,
                        UserDeviceAssignment.device_id == device_id,
                        UserDeviceAssignment.is_active == True
                    ).first()
                    
                    if not existing:
                        # Criar nova atribuição
                        assignment = UserDeviceAssignment(
                            user_id=current_user_id,
                            device_id=device_id,
                            assigned_by=current_user_id,
                            notes="Dispositivo cadastrado automaticamente",
                            is_active=True
                        )
                        assignment_db.add(assignment)
                        assignment_db.commit()
                        logger.info(f"✅ Dispositivo {device_id} atribuído ao usuário {current_user_id}")
                    else:
                        logger.info(f"ℹ️  Dispositivo {device_id} já está atribuído ao usuário {current_user_id}")
                finally:
                    assignment_db.close()
            except Exception as e:
                logger.warning(f"⚠️  Erro ao atribuir dispositivo ao usuário: {e}")
                # Não falhar a operação se a atribuição der erro
        
        # Adicionar informação do pfSense ao resultado
        result['pfsense_saved'] = pfsense_success
        result['pfsense_message'] = pfsense_message
        result['pfsense_id'] = pfsense_id
        
        # Garantir que todos os campos necessários estão presentes
        if 'status' not in result:
            result['status'] = 'success'
        if 'servers_saved' not in result:
            result['servers_saved'] = 0
        if 'mappings_saved' not in result:
            result['mappings_saved'] = 0
        if 'mappings_updated' not in result:
            result['mappings_updated'] = 0
        if 'timestamp' not in result:
            result['timestamp'] = datetime.now().isoformat()
        
        logger.info(f"📊 Resultado final: {result}")
        
        return SaveDhcpResponse(**result)
    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
        logger.error(f"Erro de conexão com pfSense ao salvar DHCP: {e}", exc_info=True)
        raise HTTPException(status_code=504, detail=f"pfSense indisponível: {e}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao salvar dados DHCP: {e}", exc_info=True)
        import traceback
        logger.error(f"Traceback completo: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Erro ao salvar dados DHCP: {str(e)}")

@router.get("/dhcp/devices", summary="Listar dispositivos cadastrados no banco", response_model=BulkDeviceResponse)
def list_cadastred_devices(
    page: int = Query(1, ge=1, description="Número da página"),
    per_page: int = Query(20, ge=1, le=100, description="Itens por página"),
    server_id: Optional[str] = Query(None, description="Filtrar por servidor DHCP"),
    current_user_id: int = Query(..., description="ID do usuário que está fazendo a consulta")
):
    """
    Lista dispositivos cadastrados no banco de dados com paginação.
    
    Regras de negócio:
    - SUPERUSER: Vê todos os dispositivos
    - ADMIN: Vê apenas dispositivos da sua instituição
    - USER: Vê apenas seus próprios dispositivos
    
    Parâmetros:
        page (int): Número da página (padrão: 1)
        per_page (int): Itens por página (padrão: 20, máximo: 100)
        server_id (str, opcional): Filtrar por servidor DHCP
        current_user_id (int): ID do usuário que está fazendo a consulta
    
    Retorna:
        Lista paginada de dispositivos cadastrados.
    """
    try:
        # Determinar institution_id baseado na permissão do usuário
        institution_id = None
        with SessionLocal() as db:
            user = db.query(User).filter(User.id == current_user_id).first()
            if user:
                if user.permission == UserPermission.ADMIN:
                    # ADMIN vê apenas dispositivos da sua instituição
                    institution_id = user.institution_id
                    if not institution_id:
                        logger.warning(f"Usuário ADMIN {user.email} não possui institution_id associado")
                elif user.permission == UserPermission.SUPERUSER:
                    # SUPERUSER vê todos os dispositivos
                    institution_id = None
                else:
                    # USER vê apenas seus próprios dispositivos (será filtrado depois)
                    institution_id = None
        
        with DhcpService() as dhcp_service:
            if server_id:
                devices = dhcp_service.get_devices_by_server(server_id, institution_id=institution_id)
            else:
                devices = dhcp_service.get_all_devices(institution_id=institution_id)
            
            # Se for USER comum, filtrar apenas dispositivos atribuídos a ele
            if user and user.permission == UserPermission.USER:
                with UserDeviceService() as uds:
                    user_device_ids = [
                        assignment.device_id 
                        for assignment in uds.db.query(UserDeviceAssignment).filter(
                            and_(
                                UserDeviceAssignment.user_id == current_user_id,
                                UserDeviceAssignment.is_active == True
                            )
                        ).all()
                    ]
                    devices = [d for d in devices if d.id in user_device_ids]
            
            # Enriquecer com usuários atribuídos (ativos)
            with UserDeviceService() as uds:
                enriched_devices = []
                for dev in devices:
                    # Buscar usuários ativos (join explícito pela coluna user_id)
                    assignments = uds.db.query(UserDeviceAssignment).join(User, UserDeviceAssignment.user_id == User.id).filter(
                        and_(
                            UserDeviceAssignment.device_id == dev.id,
                            UserDeviceAssignment.is_active == True
                        )
                    ).all()
                    assigned_users = [
                        UserResponse(
                            id=a.user.id,
                            email=a.user.email,
                            nome=a.user.nome,
                            instituicao=a.user.instituicao,
                            permission=a.user.permission,
                            ultimo_login=a.user.ultimo_login,
                        ) for a in assignments
                    ]
                    # Calcular status de acesso baseado em alias/rules
                    status_acesso = None
                    try:
                        # Encontrar aliases que contenham o IP do dispositivo
                        from db.models import PfSenseAlias, PfSenseAliasAddress, PfSenseFirewallRule
                        alias_rows = uds.db.query(PfSenseAlias).join(
                            PfSenseAliasAddress, PfSenseAliasAddress.alias_id == PfSenseAlias.id
                        ).filter(PfSenseAliasAddress.address == dev.ipaddr).all()

                        found_pass = False
                        found_block = False
                        for alias in alias_rows:
                            name = alias.name
                            # Considerar também regras com negação (ex.: !alias)
                            match_tokens = [name, f'!{name}']
                            all_conds = []
                            for token in match_tokens:
                                all_conds.extend([
                                    PfSenseFirewallRule.source == token,
                                    PfSenseFirewallRule.destination == token,
                                    PfSenseFirewallRule.source.like(f'%,{token},%'),
                                    PfSenseFirewallRule.source.like(f'{token},%'),
                                    PfSenseFirewallRule.source.like(f'%,{token}'),
                                    PfSenseFirewallRule.destination.like(f'%,{token},%'),
                                    PfSenseFirewallRule.destination.like(f'{token},%'),
                                    PfSenseFirewallRule.destination.like(f'%,{token}')
                                ])
                            rules = uds.db.query(PfSenseFirewallRule).filter(
                                or_(*all_conds),
                                PfSenseFirewallRule.type.in_(['pass', 'block'])
                            ).all()
                            for r in rules:
                                if r.type == 'block':
                                    found_block = True
                                elif r.type == 'pass':
                                    found_pass = True
                        if found_block:
                            status_acesso = 'BLOQUEADO'
                        elif found_pass:
                            status_acesso = 'LIBERADO'
                        else:
                            # Se não encontrou nem block nem pass, está aguardando
                            # (tanto se tem aliases sem regras quanto se não tem aliases)
                            status_acesso = 'AGUARDANDO'
                    except Exception as _:
                        # Em caso de erro, manter None
                        status_acesso = status_acesso
                    # Copiar dev para DeviceResponse incluindo assigned_users
                    enriched_devices.append(DeviceResponse(
                        id=dev.id,
                        server_id=dev.server_id,
                        pf_id=dev.pf_id,
                        mac=dev.mac,
                        ipaddr=dev.ipaddr,
                        cid=dev.cid,
                        hostname=dev.hostname,
                        descr=dev.descr,
                        created_at=dev.created_at,
                        updated_at=dev.updated_at,
                        assigned_users=assigned_users,
                        status_acesso=status_acesso
                    ))
                devices = enriched_devices

            # Paginação simples
            total = len(devices)
            start = (page - 1) * per_page
            end = start + per_page
            paginated_devices = devices[start:end]
            
            return BulkDeviceResponse(
                devices=paginated_devices,
                total=total,
                page=page,
                per_page=per_page,
                has_next=end < total,
                has_prev=page > 1
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar dispositivos: {e}")

@router.get("/dhcp/devices/search", summary="Buscar dispositivos por termo", response_model=DeviceSearchResponse)
def search_devices(
    query: str = Query(..., description="Termo de busca (IP, MAC, descrição ou hostname)"),
    current_user_id: int = Query(..., description="ID do usuário que está fazendo a consulta")
):
    """
    Busca dispositivos cadastrados por IP, MAC, descrição ou hostname.
    
    Regras de negócio:
    - SUPERUSER: Busca em todos os dispositivos
    - ADMIN: Busca apenas em dispositivos da sua instituição
    - USER: Busca apenas em seus próprios dispositivos
    
    Parâmetros:
        query (str): Termo de busca
        current_user_id (int): ID do usuário que está fazendo a consulta
    
    Retorna:
        Lista de dispositivos encontrados.
    """
    try:
        # Determinar institution_id baseado na permissão do usuário
        institution_id = None
        with SessionLocal() as db:
            user = db.query(User).filter(User.id == current_user_id).first()
            if user:
                if user.permission == UserPermission.ADMIN:
                    institution_id = user.institution_id
                elif user.permission == UserPermission.USER:
                    # USER vê apenas seus próprios dispositivos (será filtrado depois)
                    institution_id = None
        
        with DhcpService() as dhcp_service:
            devices = dhcp_service.search_devices(query, institution_id=institution_id)
            
            # Se for USER comum, filtrar apenas dispositivos atribuídos a ele
            if user and user.permission == UserPermission.USER:
                with UserDeviceService() as uds:
                    user_device_ids = [
                        assignment.device_id 
                        for assignment in uds.db.query(UserDeviceAssignment).filter(
                            and_(
                                UserDeviceAssignment.user_id == current_user_id,
                                UserDeviceAssignment.is_active == True
                            )
                        ).all()
                    ]
                    devices = [d for d in devices if d.id in user_device_ids]
            
            return DeviceSearchResponse(
                devices=devices,
                total_found=len(devices),
                query=query
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar dispositivos: {e}")

@router.get("/dhcp/devices/ip/{ipaddr}", summary="Buscar dispositivo por IP", response_model=DeviceDetailResponse)
def get_device_by_ip(ipaddr: str):
    """
    Busca dispositivo específico por endereço IP.
    
    Parâmetros:
        ipaddr (str): Endereço IP do dispositivo
    
    Retorna:
        Detalhes do dispositivo e informações sobre duplicatas.
    """
    try:
        with DhcpService() as dhcp_service:
            device = dhcp_service.find_device_by_ip(ipaddr)
            if not device:
                raise HTTPException(status_code=404, detail=f"Dispositivo com IP {ipaddr} não encontrado")
            
            # Buscar servidor
            server = dhcp_service.db.query(DhcpServer).filter(
                DhcpServer.id == device.server_id
            ).first()
            
            # Verificar duplicatas (mesmo IP)
            duplicates = dhcp_service.db.query(DhcpStaticMapping).filter(
                and_(
                    DhcpStaticMapping.ipaddr == ipaddr,
                    DhcpStaticMapping.id != device.id
                )
            ).all()
            
            return DeviceDetailResponse(
                device=device,
                server=server,
                is_duplicate=len(duplicates) > 0,
                duplicates=duplicates
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar dispositivo: {e}")

@router.get("/dhcp/devices/mac/{mac}", summary="Buscar dispositivo por MAC", response_model=DeviceDetailResponse)
def get_device_by_mac(mac: str):
    """
    Busca dispositivo específico por endereço MAC.
    
    Parâmetros:
        mac (str): Endereço MAC do dispositivo
    
    Retorna:
        Detalhes do dispositivo e informações sobre duplicatas.
    """
    try:
        with DhcpService() as dhcp_service:
            device = dhcp_service.find_device_by_mac(mac)
            if not device:
                raise HTTPException(status_code=404, detail=f"Dispositivo com MAC {mac} não encontrado")
            
            # Buscar servidor
            server = dhcp_service.db.query(DhcpServer).filter(
                DhcpServer.id == device.server_id
            ).first()
            
            # Verificar duplicatas (mesmo MAC)
            duplicates = dhcp_service.db.query(DhcpStaticMapping).filter(
                and_(
                    DhcpStaticMapping.mac == mac,
                    DhcpStaticMapping.id != device.id
                )
            ).all()
            
            return DeviceDetailResponse(
                device=device,
                server=server,
                is_duplicate=len(duplicates) > 0,
                duplicates=duplicates
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar dispositivo: {e}")

@router.get("/dhcp/devices/{device_id}", summary="Buscar dispositivo por ID", response_model=DeviceDetailResponse)
def get_device_by_id(device_id: int):
    """
    Busca dispositivo específico por ID.
    
    Parâmetros:
        device_id (int): ID do dispositivo no banco de dados
    
    Retorna:
        Detalhes do dispositivo e informações sobre duplicatas.
    """
    try:
        with DhcpService() as dhcp_service:
            device = dhcp_service.db.query(DhcpStaticMapping).filter(
                DhcpStaticMapping.id == device_id
            ).first()
            
            if not device:
                raise HTTPException(status_code=404, detail=f"Dispositivo com ID {device_id} não encontrado")
            
            # Buscar servidor
            server = dhcp_service.db.query(DhcpServer).filter(
                DhcpServer.id == device.server_id
            ).first()
            
            # Verificar duplicatas (mesmo IP)
            duplicates = dhcp_service.db.query(DhcpStaticMapping).filter(
                and_(
                    DhcpStaticMapping.ipaddr == device.ipaddr,
                    DhcpStaticMapping.id != device.id
                )
            ).all()
            
            return DeviceDetailResponse(
                device=device,
                server=server,
                is_duplicate=len(duplicates) > 0,
                duplicates=duplicates
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar dispositivo: {e}")

@router.get("/dhcp/statistics", summary="Estatísticas de dispositivos", response_model=DeviceStatisticsResponse)
def get_device_statistics():
    """
    Retorna estatísticas dos dispositivos cadastrados no banco.
    
    Retorna:
        Estatísticas gerais e por servidor.
    """
    try:
        with DhcpService() as dhcp_service:
            stats = dhcp_service.get_device_statistics()
            return DeviceStatisticsResponse(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter estatísticas: {e}")

@router.get("/dhcp/ip-addresses", summary="Listar endereços IP usados e livres", response_model=IpAddressListResponse)
def get_ip_addresses(
    server_id: str = Query("lan", description="ID do servidor DHCP (ex: lan, wan)"),
    range_from: str = Query("10.30.30.1", description="IP inicial do range"),
    range_to: str = Query("10.30.30.100", description="IP final do range"),
    status_filter: Optional[str] = Query(None, description="Filtrar por status (used, free, all)")
):
    """
    Lista endereços IP usados e livres em um range DHCP.
    
    Parâmetros:
        server_id (str): ID do servidor DHCP (padrão: lan)
        range_from (str): IP inicial do range (padrão: 10.30.30.1)
        range_to (str): IP final do range (padrão: 10.30.30.254)
        status_filter (str, opcional): Filtrar por status (used, free, all)
    
    Retorna:
        Lista de endereços IP com status e informações.
        
    Exemplos:
        GET /api/devices/dhcp/ip-addresses
        GET /api/devices/dhcp/ip-addresses?server_id=lan&range_from=10.30.30.1&range_to=10.30.30.100
        GET /api/devices/dhcp/ip-addresses?status_filter=free
    """
    try:
        with DhcpService() as dhcp_service:
            result = dhcp_service.get_ip_address_list(server_id, range_from, range_to)
            
            # Aplicar filtro de status se especificado
            if status_filter and status_filter != "all":
                result['ip_addresses'] = [
                    ip for ip in result['ip_addresses'] 
                    if ip['status'] == status_filter
                ]
                # Atualizar contadores
                result['summary']['used'] = len([ip for ip in result['ip_addresses'] if ip['status'] == 'used'])
                result['summary']['free'] = len([ip for ip in result['ip_addresses'] if ip['status'] == 'free'])
                result['range_info']['used_ips'] = result['summary']['used']
                result['range_info']['free_ips'] = result['summary']['free']
            
            return IpAddressListResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar endereços IP: {e}")

# Novos endpoints para gerenciamento de atribuições usuário-dispositivo
@router.post("/assignments", summary="Atribuir dispositivo a usuário", response_model=DeviceAssignmentResponse)
def assign_device_to_user(assignment: DeviceAssignmentRequest):
    """
    Atribui um dispositivo DHCP a um usuário.
    
    Regras de negócio:
    - Usuários comuns (user): Podem atribuir dispositivos apenas a si mesmos
    - Gestores (manager): Podem atribuir dispositivos a qualquer usuário
    
    Parâmetros:
        assignment (DeviceAssignmentRequest): Dados da atribuição
    
    Retorna:
        Detalhes da atribuição criada.
    """
    try:
        # Verificar permissões
        with PermissionService() as perm_service:
            if not perm_service.can_assign_device(
                user_id=assignment.assigned_by or assignment.user_id,
                device_id=assignment.device_id,
                target_user_id=assignment.user_id
            ):
                raise HTTPException(
                    status_code=403,
                    detail="Você não tem permissão para atribuir este dispositivo a este usuário"
                )
        
        with UserDeviceService() as service:
            result = service.assign_device_to_user(
                user_id=assignment.user_id,
                device_id=assignment.device_id,
                notes=assignment.notes,
                assigned_by=assignment.assigned_by
            )
            
            # Buscar dados completos para resposta
            assignment_with_data = service.db.query(UserDeviceAssignment).filter(
                UserDeviceAssignment.id == result.id
            ).first()
            
            return DeviceAssignmentResponse(
                id=assignment_with_data.id,
                user_id=assignment_with_data.user_id,
                device_id=assignment_with_data.device_id,
                assigned_at=assignment_with_data.assigned_at,
                assigned_by=assignment_with_data.assigned_by,
                notes=assignment_with_data.notes,
                is_active=assignment_with_data.is_active,
                user=assignment_with_data.user,
                device=assignment_with_data.device
            )
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao atribuir dispositivo: {e}")

@router.delete("/assignments/{user_id}/{device_id}", summary="Remover atribuição de dispositivo")
def remove_device_from_user(user_id: int, device_id: int, current_user_id: int = Query(..., description="ID do usuário que está fazendo a remoção")):
    """
    Remove atribuição de um dispositivo de um usuário.
    
    Regras de negócio:
    - Usuários comuns (user): Podem remover apenas suas próprias atribuições
    - Gestores (manager): Podem remover atribuições de qualquer usuário
    
    Parâmetros:
        user_id (int): ID do usuário que tem o dispositivo
        device_id (int): ID do dispositivo
        current_user_id (int): ID do usuário que está fazendo a remoção
    
    Retorna:
        Confirmação da remoção.
    """
    try:
        # Verificar permissões
        with PermissionService() as perm_service:
            if not perm_service.can_remove_device_assignment(
                user_id=current_user_id,
                device_id=device_id,
                target_user_id=user_id
            ):
                raise HTTPException(
                    status_code=403,
                    detail="Você não tem permissão para remover esta atribuição"
                )
        
        with UserDeviceService() as service:
            result = service.remove_device_from_user(user_id, device_id)
            
            return {
                "status": "success",
                "message": f"Atribuição removida com sucesso",
                "user_id": user_id,
                "device_id": device_id,
                "removed_by": current_user_id
            }
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao remover atribuição: {e}")

@router.get("/users/{user_id}/devices", summary="Listar dispositivos de um usuário", response_model=UserDevicesResponse)
def get_user_devices(user_id: int, current_user_id: int = Query(..., description="ID do usuário que está fazendo a consulta"), include_inactive: bool = Query(False, description="Incluir atribuições inativas")):
    """
    Lista dispositivos atribuídos a um usuário.
    
    Regras de negócio:
    - Usuários comuns (user): Podem visualizar apenas seus próprios dispositivos
    - Gestores (manager): Podem visualizar dispositivos de qualquer usuário
    
    Parâmetros:
        user_id (int): ID do usuário cujos dispositivos serão listados
        current_user_id (int): ID do usuário que está fazendo a consulta
        include_inactive (bool): Se deve incluir atribuições inativas
    
    Retorna:
        Lista de dispositivos do usuário.
    """
    try:
        # Verificar permissões e buscar dispositivos
        with PermissionService() as perm_service:
            current_user = perm_service.verify_user_exists(current_user_id)
            
            # Se for ADMIN, garantir que só vê dispositivos da sua instituição
            institution_id = None
            if current_user.permission == UserPermission.ADMIN:
                institution_id = current_user.institution_id
                if not institution_id:
                    raise HTTPException(
                        status_code=400,
                        detail="Usuário ADMIN não possui instituição associada. Entre em contato com o administrador."
                    )
            
            devices = perm_service.get_user_devices_with_permission(current_user_id, user_id, institution_id=institution_id)
            user = perm_service.verify_user_exists(user_id)
        
        # Enriquecer dispositivos com status_acesso e contar atribuições ativas
        with UserDeviceService() as service:
            # Contar atribuições ativas
            active_assignments = service.db.query(UserDeviceAssignment).filter(
                and_(
                    UserDeviceAssignment.user_id == user_id,
                    UserDeviceAssignment.is_active == True
                )
            ).count()
            # Enriquecer cada device em DeviceResponse incluindo status_acesso
            enriched_devices = []
            for dev in devices:
                status_acesso = None
                try:
                    from db.models import PfSenseAlias, PfSenseAliasAddress, PfSenseFirewallRule
                    alias_rows = service.db.query(PfSenseAlias).join(
                        PfSenseAliasAddress, PfSenseAliasAddress.alias_id == PfSenseAlias.id
                    ).filter(PfSenseAliasAddress.address == dev.ipaddr).all()
                    found_pass, found_block = False, False
                    for alias in alias_rows:
                        name = alias.name
                        match_tokens = [name, f'!{name}']
                        all_conds = []
                        for token in match_tokens:
                            all_conds.extend([
                                PfSenseFirewallRule.source == token,
                                PfSenseFirewallRule.destination == token,
                                PfSenseFirewallRule.source.like(f'%,{token},%'),
                                PfSenseFirewallRule.source.like(f'{token},%'),
                                PfSenseFirewallRule.source.like(f'%,{token}'),
                                PfSenseFirewallRule.destination.like(f'%,{token},%'),
                                PfSenseFirewallRule.destination.like(f'{token},%'),
                                PfSenseFirewallRule.destination.like(f'%,{token}')
                            ])
                        rules = service.db.query(PfSenseFirewallRule).filter(
                            or_(*all_conds),
                            PfSenseFirewallRule.type.in_(['pass', 'block'])
                        ).all()
                        for r in rules:
                            if r.type == 'block':
                                found_block = True
                            elif r.type == 'pass':
                                found_pass = True
                    if found_block:
                        status_acesso = 'BLOQUEADO'
                    elif found_pass:
                        status_acesso = 'LIBERADO'
                    else:
                        # Se não encontrou nem block nem pass, está aguardando
                        # (tanto se tem aliases sem regras quanto se não tem aliases)
                        status_acesso = 'AGUARDANDO'
                except Exception:
                    status_acesso = status_acesso

                enriched_devices.append(DeviceResponse(
                    id=dev.id,
                    server_id=dev.server_id,
                    pf_id=dev.pf_id,
                    mac=dev.mac,
                    ipaddr=dev.ipaddr,
                    cid=dev.cid,
                    hostname=dev.hostname,
                    descr=dev.descr,
                    created_at=dev.created_at,
                    updated_at=dev.updated_at,
                    status_acesso=status_acesso,
                    assigned_users=[]
                ))
            
            return UserDevicesResponse(
                user=user,
                devices=enriched_devices,
                total_devices=len(devices),
                active_assignments=active_assignments
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar dispositivos do usuário: {e}")

@router.get("/devices", summary="Listar todos os dispositivos do sistema", response_model=AllDevicesResponse)
def get_all_devices(current_user_id: int = Query(..., description="ID do usuário que está fazendo a consulta")):
    """
    Lista todos os dispositivos cadastrados no sistema.
    
    Regras de negócio:
    - SUPERUSER: Vê todos os dispositivos de todas as instituições
    - ADMIN: Vê apenas dispositivos da sua instituição
    - USER: Não tem permissão para acessar este endpoint
    
    Parâmetros:
        current_user_id (int): ID do usuário que está fazendo a consulta
    
    Retorna:
        Lista completa de dispositivos com estatísticas do sistema.
    """
    try:
        # Verificar permissões
        with PermissionService() as perm_service:
            current_user = perm_service.verify_user_exists(current_user_id)
            if current_user.permission == UserPermission.USER:
                raise HTTPException(
                    status_code=403, 
                    detail="Apenas gestores e administradores podem visualizar todos os dispositivos do sistema"
                )
        
        # Determinar institution_id baseado na permissão
        institution_id = None
        if current_user.permission == UserPermission.ADMIN:
            # ADMIN vê apenas dispositivos da sua instituição
            institution_id = current_user.institution_id
            if not institution_id:
                raise HTTPException(
                    status_code=400,
                    detail="Usuário ADMIN não possui instituição associada. Entre em contato com o administrador."
                )
        # SUPERUSER vê todos (institution_id = None)
        
        # Buscar dispositivos filtrados por instituição
        with UserDeviceService() as service:
            query = service.db.query(DhcpStaticMapping)
            if institution_id is not None:
                query = query.filter(DhcpStaticMapping.institution_id == institution_id)
            all_devices = query.all()
            
            # Converter para DeviceResponse
            devices = []
            for device in all_devices:
                devices.append(DeviceResponse(
                    id=device.id,
                    server_id=device.server_id,
                    pf_id=device.pf_id,
                    mac=device.mac,
                    ipaddr=device.ipaddr,
                    cid=device.cid,
                    hostname=device.hostname,
                    descr=device.descr,
                    created_at=device.created_at,
                    updated_at=device.updated_at
                ))
            
            # Contar dispositivos online (simulado - pode ser implementado com ping ou status real)
            online_devices = len([d for d in devices if d.ipaddr])  # Simulação básica
            offline_devices = len(devices) - online_devices
            
            # Contar dispositivos atribuídos
            assigned_devices = service.db.query(UserDeviceAssignment).filter(
                UserDeviceAssignment.is_active == True
            ).distinct(UserDeviceAssignment.device_id).count()
            
            unassigned_devices = len(devices) - assigned_devices
            
            return AllDevicesResponse(
                devices=devices,
                total_devices=len(devices),
                online_devices=online_devices,
                offline_devices=offline_devices,
                assigned_devices=assigned_devices,
                unassigned_devices=unassigned_devices
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar todos os dispositivos: {e}")

@router.get("/devices/{device_id}/users", summary="Listar usuários de um dispositivo", response_model=DeviceUsersResponse)
def get_device_users(device_id: int, current_user_id: int = Query(..., description="ID do usuário que está fazendo a consulta"), include_inactive: bool = Query(False, description="Incluir atribuições inativas")):
    """
    Lista usuários atribuídos a um dispositivo.
    
    Regras de negócio:
    - Usuários comuns (user): Podem visualizar usuários apenas de dispositivos que possuem
    - Gestores (manager): Podem visualizar usuários de qualquer dispositivo
    
    Parâmetros:
        device_id (int): ID do dispositivo
        current_user_id (int): ID do usuário que está fazendo a consulta
        include_inactive (bool): Se deve incluir atribuições inativas
    
    Retorna:
        Lista de usuários do dispositivo.
    """
    try:
        # Verificar permissões e buscar usuários
        with PermissionService() as perm_service:
            users = perm_service.get_device_users_with_permission(current_user_id, device_id)
            device = perm_service.verify_device_exists(device_id)
        
        # Contar atribuições ativas
        with UserDeviceService() as service:
            active_assignments = service.db.query(UserDeviceAssignment).filter(
                and_(
                    UserDeviceAssignment.device_id == device_id,
                    UserDeviceAssignment.is_active == True
                )
            ).count()
            
            return DeviceUsersResponse(
                device=device,
                users=users,
                total_users=len(users),
                active_assignments=active_assignments
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar usuários do dispositivo: {e}")

@router.get("/assignments/search", summary="Buscar atribuições por termo")
def search_assignments(query: str = Query(..., description="Termo de busca (nome, email, IP, MAC, descrição)")):
    """
    Busca atribuições por termo.
    
    Parâmetros:
        query (str): Termo de busca
    
    Retorna:
        Lista de atribuições encontradas.
    """
    try:
        with UserDeviceService() as service:
            assignments = service.search_assignments(query)
            
            return {
                "assignments": assignments,
                "total_found": len(assignments),
                "query": query
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar atribuições: {e}")

@router.get("/assignments/statistics", summary="Estatísticas de atribuições", response_model=AssignmentStatisticsResponse)
def get_assignment_statistics():
    """
    Retorna estatísticas das atribuições usuário-dispositivo.
    
    Retorna:
        Estatísticas gerais das atribuições.
    """
    try:
        with UserDeviceService() as service:
            stats = service.get_assignment_statistics()
            return AssignmentStatisticsResponse(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter estatísticas: {e}")

@router.post("/dhcp/static_mapping", summary="Cadastrar mapeamento estático DHCP no pfSense", response_model=DhcpStaticMappingCreateResponse)
def create_dhcp_static_mapping(
    mapping: DhcpStaticMappingCreateRequest,
    current_user_id: int = Query(..., description="ID do usuário que está fazendo a operação")
):
    """
    Cadastra um novo mapeamento estático DHCP no pfSense e aplica as mudanças automaticamente.
    
    Este endpoint utiliza a API oficial do pfSense v2:
    POST /api/v2/services/dhcp_server/static_mapping
    
    ⚠️ **IMPORTANTE**: 
    - O endpoint verifica automaticamente se já existem mapeamentos com o mesmo IP ou MAC
    - As mudanças são aplicadas automaticamente após o cadastro bem-sucedido
    
    Parâmetros:
        mapping (DhcpStaticMappingCreateRequest): Dados do mapeamento estático DHCP
    
    Retorna:
        Resposta de sucesso ou erro da operação.
        
    Exemplo de uso:
        POST /api/devices/dhcp/static_mapping
        {
            "mac": "00:11:22:33:44:55",
            "ipaddr": "192.168.1.100",
            "cid": "device001",
            "hostname": "device-hostname",
            "descr": "Dispositivo IoT"
        }
        
    Nota: O campo parent_id é opcional e tem valor padrão "lan".
    """
    try:
        # Converter o modelo Pydantic para dict
        mapping_data = mapping.model_dump(exclude_none=True)
        
        # Cadastrar no pfSense com verificação de existência usando configurações da instituição
        result = cadastrar_mapeamento_statico_dhcp_pfsense(
            mapping_data, 
            verificar_existente=True,
            user_id=current_user_id
        )
        
        # Aplicar mudanças DHCP automaticamente
        try:
            apply_result = aplicar_mudancas_dhcp_pfsense(user_id=current_user_id)
            logger.info(f"Mudanças DHCP aplicadas automaticamente após cadastro: {apply_result}")
        except Exception as apply_error:
            logger.warning(f"Erro ao aplicar mudanças DHCP automaticamente: {apply_error}")
            # Não falhar a operação se o apply der erro, apenas logar
        
        return DhcpStaticMappingCreateResponse(
            success=True,
            message="Mapeamento estático DHCP cadastrado e aplicado com sucesso no pfSense",
            data=result
        )
    except ValueError as e:
        # Erro de validação (mapeamento já existe)
        logger.warning(f"Tentativa de cadastrar mapeamento duplicado: {e}")
        raise HTTPException(
            status_code=409, 
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Erro ao cadastrar mapeamento estático DHCP: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Erro ao cadastrar mapeamento estático DHCP no pfSense: {e}"
        )

@router.patch("/dhcp/static_mapping", summary="Atualizar mapeamento estático DHCP no pfSense e banco de dados local", response_model=DhcpStaticMappingUpdateResponse)
def update_dhcp_static_mapping(
    parent_id: str = Query("lan", description="ID do servidor DHCP pai (padrão: lan)"),
    mapping_id: int = Query(..., description="ID do mapeamento estático DHCP a ser atualizado"),
    update_data: DhcpStaticMappingUpdateRequest = Body(..., description="Dados para atualização"),
    apply: bool = Query(True, description="Aplicar a atualização imediatamente")
):
    """
    Atualiza um mapeamento estático DHCP no pfSense E no banco de dados local.
    
    Este endpoint:
    1. Atualiza o mapeamento no pfSense usando a API oficial v2
    2. Atualiza o registro correspondente no banco de dados local
    
    ⚠️ **IMPORTANTE**: Esta operação pode alterar dados existentes. Certifique-se de que
    os dados corretos estão sendo atualizados antes de confirmar.
    
    Parâmetros:
        parent_id (str): ID do servidor DHCP pai (padrão: "lan")
        mapping_id (int): ID do mapeamento estático DHCP a ser atualizado
        update_data (DhcpStaticMappingUpdateRequest): Dados para atualização (campos opcionais)
        apply (bool): Se deve aplicar a atualização imediatamente (padrão: True)
    
    Retorna:
        Resposta de sucesso ou erro da operação.
        
    Exemplo de uso:
        PATCH /api/devices/dhcp/static_mapping?parent_id=lan&mapping_id=5
        {
            "descr": "Nova descrição",
            "cid": "Novo CID"
        }
        
    Nota: O parâmetro apply=false pode ser usado para revisar a atualização antes de aplicá-la manualmente.
    """
    try:
        # Filtrar apenas campos que não são None
        update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
        
        if not update_dict:
            raise HTTPException(
                status_code=400,
                detail="Pelo menos um campo deve ser fornecido para atualização"
            )
        
        # Primeiro, atualizar no pfSense
        pfsense_result = atualizar_mapeamento_statico_dhcp_pfsense(
            parent_id=parent_id,
            mapping_id=mapping_id,
            update_data=update_dict,
            apply=apply
        )
        
        # Depois, atualizar no banco de dados local
        local_updated = False
        try:
            with DhcpService() as dhcp_service:
                # Buscar o mapeamento no banco local pelo pf_id
                mapping = dhcp_service.db.query(DhcpStaticMapping).filter(
                    DhcpStaticMapping.pf_id == mapping_id
                ).first()
                
                if mapping:
                    # Atualizar campos no banco local
                    for field, value in update_dict.items():
                        if hasattr(mapping, field):
                            setattr(mapping, field, value)
                    
                    mapping.updated_at = datetime.now()
                    dhcp_service.db.commit()
                    local_updated = True
                    logger.info(f"Mapeamento local atualizado: pf_id={mapping_id}, campos={list(update_dict.keys())}")
                else:
                    logger.warning(f"Mapeamento local não encontrado para pf_id={mapping_id}")
                    
        except Exception as local_error:
            logger.error(f"Erro ao atualizar no banco local (pf_id: {mapping_id}): {local_error}")
            # Não falhar a operação se o banco local der erro
        
        # Preparar mensagem baseada no resultado
        if local_updated:
            message = f"Mapeamento estático DHCP (ID: {mapping_id}) atualizado com sucesso no pfSense e banco de dados local"
        else:
            message = f"Mapeamento estático DHCP (ID: {mapping_id}) atualizado com sucesso no pfSense (não encontrado no banco local)"
        
        return DhcpStaticMappingUpdateResponse(
            success=True,
            message=message,
            parent_id=parent_id,
            mapping_id=mapping_id,
            applied=apply,
            local_updated=local_updated,
            data=pfsense_result
        )
        
    except Exception as e:
        logger.error(f"Erro ao atualizar mapeamento estático DHCP (parent_id: {parent_id}, mapping_id: {mapping_id}): {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Erro ao atualizar mapeamento estático DHCP: {e}"
        )

@router.delete("/dhcp/static_mapping", summary="Excluir mapeamento estático DHCP no pfSense e banco de dados local", response_model=DhcpStaticMappingDeleteResponse)
def delete_dhcp_static_mapping(
    parent_id: str = Query("lan", description="ID do servidor DHCP pai (padrão: lan)"),
    mapping_id: int = Query(..., description="ID do mapeamento estático DHCP a ser excluído"),
    apply: bool = Query(True, description="Aplicar a exclusão imediatamente")
):
    """
    Exclui um mapeamento estático DHCP no pfSense E no banco de dados local.
    
    Este endpoint:
    1. Exclui o mapeamento no pfSense usando a API oficial v2
    2. Remove o registro correspondente do banco de dados local
    
    ⚠️ **IMPORTANTE**: Esta operação é irreversível. Certifique-se de que o mapeamento
    correto está sendo excluído antes de confirmar.
    
    Parâmetros:
        parent_id (str): ID do servidor DHCP pai (padrão: "lan")
        mapping_id (int): ID do mapeamento estático DHCP a ser excluído
        apply (bool): Se deve aplicar a exclusão imediatamente (padrão: True)
    
    Retorna:
        Resposta de sucesso ou erro da operação.
        
    Exemplo de uso:
        DELETE /api/devices/dhcp/static_mapping?parent_id=lan&mapping_id=5
        
    Nota: O parâmetro apply=false pode ser usado para revisar a exclusão antes de aplicá-la manualmente.
    """
    try:
        # Primeiro, excluir no pfSense
        pfsense_result = excluir_mapeamento_statico_dhcp_pfsense(
            parent_id=parent_id,
            mapping_id=mapping_id,
            apply=apply
        )
        
        # Depois, excluir do banco de dados local
        local_deleted = False
        try:
            with DhcpService() as dhcp_service:
                # Buscar o mapeamento no banco local pelo pf_id
                mapping = dhcp_service.db.query(DhcpStaticMapping).filter(
                    DhcpStaticMapping.pf_id == mapping_id
                ).first()
                
                if mapping:
                    # Remover do banco local
                    dhcp_service.db.delete(mapping)
                    dhcp_service.db.commit()
                    local_deleted = True
                    logger.info(f"Mapeamento local excluído: pf_id={mapping_id}, MAC={mapping.mac}, IP={mapping.ipaddr}")
                else:
                    logger.warning(f"Mapeamento local não encontrado para pf_id={mapping_id}")
                    
        except Exception as local_error:
            logger.error(f"Erro ao excluir do banco local (pf_id: {mapping_id}): {local_error}")
            # Não falhar a operação se o banco local der erro
        
        # Preparar mensagem baseada no resultado
        if local_deleted:
            message = f"Mapeamento estático DHCP (ID: {mapping_id}) excluído com sucesso no pfSense e banco de dados local"
        else:
            message = f"Mapeamento estático DHCP (ID: {mapping_id}) excluído com sucesso no pfSense (não encontrado no banco local)"
        
        return DhcpStaticMappingDeleteResponse(
            success=True,
            message=message,
            parent_id=parent_id,
            mapping_id=mapping_id,
            applied=apply,
            local_deleted=local_deleted,
            data=pfsense_result
        )
        
    except Exception as e:
        logger.error(f"Erro ao excluir mapeamento estático DHCP (parent_id: {parent_id}, mapping_id: {mapping_id}): {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Erro ao excluir mapeamento estático DHCP: {e}"
        )

@router.post("/dhcp/sync", summary="Sincronizar IDs do pfSense com o banco de dados local")
def sync_pfsense_ids():
    """
    Sincroniza os IDs do pfSense com os pf_id do banco de dados local.
    
    Este endpoint:
    1. Busca todos os dados DHCP do pfSense
    2. Compara com os dados locais
    3. Atualiza os pf_id para corresponder aos IDs reais do pfSense
    4. Cria novos registros se necessário
    5. Atualiza registros existentes com IDs incorretos
    
    ⚠️ **IMPORTANTE**: Esta operação pode alterar os pf_id existentes.
    Use apenas quando houver inconsistências entre pfSense e banco local.
    
    Retorna:
        Estatísticas da sincronização realizada.
        
    Exemplo de resposta:
    {
        "status": "success",
        "servers_created": 0,
        "mappings_synced": 5,
        "mappings_created": 2,
        "mappings_updated": 1,
        "timestamp": "2024-01-15T10:30:00"
    }
    """
    try:
        # Buscar dados do pfSense
        dhcp_data = listar_clientes_dhcp_pfsense()
        
        # Sincronizar com banco local
        with DhcpService() as dhcp_service:
            result = dhcp_service.sync_pfsense_ids(dhcp_data)
        
        return {
            "status": "success",
            "message": "Sincronização de IDs do pfSense concluída com sucesso",
            "sync_result": result
        }
        
    except Exception as e:
        logger.error(f"Erro ao sincronizar IDs do pfSense: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao sincronizar IDs do pfSense: {e}"
        )

@router.get("/dhcp/static_mapping/check", summary="Verificar mapeamentos DHCP existentes")
def check_existing_dhcp_mappings(
    parent_id: str = Query("lan", description="ID do servidor DHCP pai (padrão: lan)"),
    ipaddr: Optional[str] = Query(None, description="Endereço IP para verificar"),
    mac: Optional[str] = Query(None, description="Endereço MAC para verificar")
):
    """
    Verifica se já existem mapeamentos estáticos DHCP com o mesmo IP ou MAC.
    
    Este endpoint é útil para verificar conflitos antes de tentar cadastrar
    um novo mapeamento DHCP.
    
    Parâmetros:
        parent_id (str, opcional): ID do servidor DHCP pai (padrão: "lan")
        ipaddr (str, opcional): Endereço IP para verificar
        mac (str, opcional): Endereço MAC para verificar
    
    Retorna:
        Informações sobre mapeamentos existentes encontrados.
        
    Exemplo de uso:
        GET /api/devices/dhcp/static_mapping/check?ipaddr=192.168.1.100
        GET /api/devices/dhcp/static_mapping/check?mac=00:11:22:33:44:55
        GET /api/devices/dhcp/static_mapping/check?parent_id=lan&ipaddr=192.168.1.100
    """
    try:
        from services_firewalls.pfsense_client import verificar_mapeamento_existente_pfsense
        
        if not ipaddr and not mac:
            raise HTTPException(
                status_code=400,
                detail="É necessário fornecer pelo menos um endereço IP ou MAC para verificar"
            )
        
        result = verificar_mapeamento_existente_pfsense(parent_id, ipaddr, mac)
        
        return {
            "parent_id": parent_id,
            "ipaddr_checked": ipaddr,
            "mac_checked": mac,
            "exists": result["exists"],
            "total_found": result["total_found"],
            "mappings": result["mappings"],
            "message": "Verificação concluída com sucesso"
        }
        
    except Exception as e:
        logger.error(f"Erro ao verificar mapeamentos existentes: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao verificar mapeamentos DHCP existentes: {e}"
        )

# Endpoints para gerenciamento de aliases no banco de dados
@router.post("/aliases-db/save", summary="Salvar aliases do pfSense no banco de dados", response_model=AliasSaveResponse)
def save_aliases_data(current_user_id: int = Query(..., description="ID do usuário que está fazendo a operação")):
    """
    Salva todos os aliases do pfSense no banco de dados local.
    
    Este endpoint:
    1. Busca todos os aliases do pfSense
    2. Salva/atualiza no banco de dados local
    3. Mantém sincronização entre pfSense e banco local
    
    Args:
        current_user_id (int): ID do usuário logado (para buscar configurações da instituição)
    
    Retorna:
        Estatísticas da operação de salvamento.
    """
    try:
        # Buscar aliases do pfSense usando configurações da instituição
        try:
            from services_firewalls.pfsense_client import _get_pfsense_config
            pfsense_url, pfsense_key = _get_pfsense_config(user_id=current_user_id)
            pfsense_aliases = listar_aliases_pfsense(pfsense_url=pfsense_url, pfsense_key=pfsense_key)
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            raise HTTPException(status_code=504, detail=f"pfSense indisponível: {e}")
        
        # Salvar no banco de dados
        with AliasService(user_id=current_user_id) as alias_service:
            result = alias_service.save_aliases_data(pfsense_aliases)
            
            # Adicionar informação do pfSense
            result['pfsense_saved'] = True
            result['pfsense_message'] = "Aliases sincronizados com sucesso"
            
            return AliasSaveResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Erro ao salvar aliases: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao salvar aliases: {e}")

@router.get("/aliases-db", summary="Listar aliases do banco de dados", response_model=AliasListResponse)
def list_aliases_from_db(
    page: int = Query(1, ge=1, description="Número da página"),
    per_page: int = Query(20, ge=1, le=100, description="Itens por página"),
    name: Optional[str] = Query(None, description="Filtrar por nome do alias"),
    current_user_id: int = Query(..., description="ID do usuário que está fazendo a consulta")
):
    """
    Lista aliases salvos no banco de dados local.
    
    Parâmetros:
        page (int): Número da página (padrão: 1)
        per_page (int): Itens por página (padrão: 20, máximo: 100)
        name (str, opcional): Filtrar por nome do alias
        current_user_id (int): ID do usuário logado (para buscar configurações da instituição)
    
    Retorna:
        Lista paginada de aliases com endereços.
    """
    try:
        with AliasService(user_id=current_user_id) as alias_service:
            if name:
                aliases = [alias_service.get_alias_by_name(name)] if alias_service.get_alias_by_name(name) else []
            else:
                aliases = alias_service.get_all_aliases()
            
            # Paginação simples
            total = len(aliases)
            start = (page - 1) * per_page
            end = start + per_page
            paginated_aliases = aliases[start:end]
            
            return AliasListResponse(
                aliases=paginated_aliases,
                total=total,
                page=page,
                per_page=per_page,
                has_next=end < total,
                has_prev=page > 1
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar aliases: {e}")

@router.get("/aliases-db/search", summary="Buscar aliases por termo")
def search_aliases(
    query: str = Query(..., description="Termo de busca (nome ou descrição)"),
    current_user_id: int = Query(..., description="ID do usuário que está fazendo a consulta")
):
    """
    Busca aliases por nome ou descrição.
    
    Parâmetros:
        query (str): Termo de busca
        current_user_id (int): ID do usuário logado (para buscar configurações da instituição)
    
    Retorna:
        Lista de aliases encontrados.
    """
    try:
        with AliasService(user_id=current_user_id) as alias_service:
            aliases = alias_service.search_aliases(query)
            
            return {
                "aliases": aliases,
                "total_found": len(aliases),
                "query": query
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar aliases: {e}")

@router.get("/aliases-db/statistics", summary="Estatísticas de aliases", response_model=AliasStatisticsResponse)
def get_alias_statistics(current_user_id: int = Query(..., description="ID do usuário que está fazendo a consulta")):
    """
    Retorna estatísticas dos aliases cadastrados no banco.
    
    Args:
        current_user_id (int): ID do usuário logado (para buscar configurações da instituição)
    
    Retorna:
        Estatísticas gerais dos aliases.
    """
    try:
        with AliasService(user_id=current_user_id) as alias_service:
            stats = alias_service.get_alias_statistics()
            return AliasStatisticsResponse(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter estatísticas: {e}")

@router.post("/aliases-db/create", summary="Criar novo alias", response_model=AliasResponse)
def create_new_alias(alias: AliasCreateRequest, current_user_id: int = Query(..., description="ID do usuário que está fazendo a operação")):
    """
    Cria um novo alias no pfSense e no banco de dados local.
    
    Parâmetros:
        alias (AliasCreateRequest): Dados do alias
        current_user_id (int): ID do usuário logado (para buscar configurações da instituição)
    
    Retorna:
        Dados do alias criado.
    """
    try:
        with AliasService(user_id=current_user_id) as alias_service:
            # Converter para dict
            alias_data = {
                'name': alias.name,
                'alias_type': alias.alias_type,
                'descr': alias.descr,
                'addresses': [
                    {
                        'address': addr.address,
                        'detail': addr.detail
                    }
                    for addr in alias.addresses
                ]
            }
            
            result = alias_service.create_alias(alias_data)
            
            if result['success']:
                # Buscar o alias criado
                created_alias = alias_service.get_alias_by_name(alias.name)
                return AliasResponse(**created_alias)
            else:
                raise HTTPException(status_code=400, detail=result.get('message', 'Erro ao criar alias'))
                
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
        raise HTTPException(status_code=504, detail=f"pfSense indisponível: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao criar alias: {e}")

@router.patch("/aliases-db/{alias_name}", summary="Atualizar alias existente", response_model=AliasResponse)
def update_alias(alias_name: str, update_data: AliasUpdateRequest, current_user_id: int = Query(..., description="ID do usuário que está fazendo a operação")):
    """
    Atualiza um alias existente no banco de dados e no pfSense.
    
    Este endpoint:
    1. Busca o alias pelo nome no banco de dados
    2. Atualiza os campos fornecidos no banco local
    3. Sincroniza as mudanças com o pfSense
    4. Retorna o alias atualizado
    
    Args:
        alias_name: Nome do alias a ser atualizado
        update_data: Dados para atualização (campos opcionais)
        current_user_id: ID do usuário logado (para buscar configurações da instituição)
        
    Returns:
        Dados do alias atualizado
        
    Exemplo:
        PATCH /api/devices/aliases-db/meu_alias?current_user_id=1
        {
            "descr": "Nova descrição",
            "addresses": [
                {"address": "192.168.1.100", "detail": "Novo dispositivo"}
            ]
        }
    """
    try:
        with AliasService(user_id=current_user_id) as alias_service:
            result = alias_service.update_alias(alias_name, update_data.dict(exclude_unset=True))
            
            # Buscar o alias atualizado para retornar
            updated_alias = alias_service.get_alias_by_name(alias_name)
            
            if not updated_alias:
                raise HTTPException(status_code=404, detail="Alias não encontrado após atualização")
            
            return AliasResponse(**updated_alias)
            
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar alias: {e}")

@router.post("/aliases-db/{alias_name}/add-addresses", summary="Adicionar endereços a um alias existente", response_model=AliasResponse)
def add_addresses_to_alias(
    alias_name: str, 
    add_data: AliasAddAddressesRequest,
    current_user_id: int = Query(..., description="ID do usuário que está fazendo a operação")
):
    """
    Adiciona novos endereços a um alias existente sem substituir os atuais.
    
    Este endpoint:
    1. Busca o alias pelo nome no banco de dados
    2. Adiciona os novos endereços aos existentes
    3. Sincroniza as mudanças com o pfSense
    4. Retorna o alias atualizado
    
    Args:
        alias_name: Nome do alias
        add_data: Dados com os novos endereços
        current_user_id (int): ID do usuário logado (para buscar configurações da instituição)
        
    Returns:
        Dados do alias atualizado
        
    Exemplo:
        POST /api/devices/aliases-db/meu_alias/add-addresses
        {
            "addresses": [
                {"address": "192.168.1.100", "detail": "Novo dispositivo 1"},
                {"address": "192.168.1.101", "detail": "Novo dispositivo 2"}
            ]
        }
    """
    try:
        with AliasService(user_id=current_user_id) as alias_service:
            result = alias_service.add_addresses_to_alias(alias_name, add_data.dict()['addresses'])
            
            # Buscar o alias atualizado para retornar
            updated_alias = alias_service.get_alias_by_name(alias_name)
            
            if not updated_alias:
                raise HTTPException(status_code=404, detail="Alias não encontrado após atualização")
            
            return AliasResponse(**updated_alias)
            
    except ValueError as e:
        # Erros funcionais (alias não encontrado, etc.)
        raise HTTPException(status_code=404, detail=str(e))
    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
        # Erros de conexão com pfSense: resposta 504 mais amigável
        raise HTTPException(status_code=504, detail=f"pfSense indisponível: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao adicionar endereços: {e}")

@router.get("/aliases-db/{alias_name}", summary="Obter alias específico por nome", response_model=AliasResponse)
def get_alias_by_name(
    alias_name: str,
    current_user_id: int = Query(..., description="ID do usuário que está fazendo a consulta")
):
    """
    Obtém um alias específico pelo nome.
    Filtra por instituição do usuário.
    
    Args:
        alias_name: Nome do alias
        current_user_id: ID do usuário logado (para buscar configurações da instituição)
        
    Returns:
        Dados do alias
        
    Exemplo:
        GET /api/devices/aliases-db/Teste_API_IoT_EDU?current_user_id=1
    """
    try:
        with AliasService(user_id=current_user_id) as alias_service:
            alias = alias_service.get_alias_by_name(alias_name)
            
            if not alias:
                raise HTTPException(status_code=404, detail=f"Alias '{alias_name}' não encontrado")
            
            return AliasResponse(**alias)
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar alias: {e}")

@router.patch("/dhcp/static_mapping/by_mac", summary="Atualizar mapeamento estático DHCP por MAC", response_model=DhcpStaticMappingUpdateResponse)
def update_dhcp_static_mapping_by_mac(
    mac: str = Query(..., description="Endereço MAC do dispositivo"),
    update_data: DhcpStaticMappingUpdateRequest = Body(..., description="Dados para atualização"),
    apply: bool = Query(True, description="Aplicar a atualização imediatamente")
):
    """
    Atualiza um mapeamento estático DHCP usando MAC como identificador.
    
    Este endpoint:
    1. Busca o dispositivo no banco local pelo MAC
    2. Obtém o pf_id atual do pfSense
    3. Atualiza no pfSense usando o pf_id atual
    4. Atualiza no banco local
    
    Parâmetros:
        mac (str): Endereço MAC do dispositivo
        update_data (DhcpStaticMappingUpdateRequest): Dados para atualização
        apply (bool): Se deve aplicar a atualização imediatamente
    
    Retorna:
        Resposta de sucesso ou erro da operação.
    """
    try:
        # Filtrar apenas campos que não são None
        update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
        
        if not update_dict:
            raise HTTPException(
                status_code=400,
                detail="Pelo menos um campo deve ser fornecido para atualização"
            )
        
        # Buscar dispositivo no banco local pelo MAC
        with DhcpService() as dhcp_service:
            mapping = dhcp_service.db.query(DhcpStaticMapping).filter(
                DhcpStaticMapping.mac == mac
            ).first()
            
            if not mapping:
                raise HTTPException(
                    status_code=404,
                    detail=f"Dispositivo com MAC {mac} não encontrado no banco local"
                )
            
            # Obter pf_id atual do pfSense
            current_pf_id = mapping.pf_id
            if current_pf_id is None:
                raise HTTPException(
                    status_code=400,
                    detail=f"Dispositivo com MAC {mac} não possui pf_id válido"
                )
            
            # Sanitizar hostname (remover espaços e caracteres inválidos)
            if 'hostname' in update_dict:
                update_dict['hostname'] = update_dict['hostname'].replace(' ', '-').replace('_', '-')
            
            # Atualizar no pfSense
            pfsense_result = atualizar_mapeamento_statico_dhcp_pfsense(
                parent_id="lan",
                mapping_id=current_pf_id,
                update_data=update_dict,
                apply=apply
            )
            
            # Atualizar no banco local
            for field, value in update_dict.items():
                if hasattr(mapping, field):
                    setattr(mapping, field, value)
            
            mapping.updated_at = datetime.now()
            dhcp_service.db.commit()
            
            logger.info(f"Mapeamento atualizado por MAC: {mac}, pf_id={current_pf_id}, campos={list(update_dict.keys())}")
            
            return DhcpStaticMappingUpdateResponse(
                success=True,
                message=f"Dispositivo {mac} atualizado com sucesso",
                parent_id="lan",
                mapping_id=current_pf_id,
                applied=apply,
                local_updated=True,
                data=pfsense_result
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao atualizar mapeamento por MAC {mac}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao atualizar dispositivo {mac}: {e}"
        )

@router.delete("/dhcp/static_mapping/by_mac", summary="Excluir mapeamento estático DHCP por MAC", response_model=DhcpStaticMappingDeleteResponse)
def delete_dhcp_static_mapping_by_mac(
    mac: str = Query(..., description="Endereço MAC do dispositivo"),
    apply: bool = Query(True, description="Aplicar a exclusão imediatamente")
):
    """
    Exclui um mapeamento estático DHCP usando MAC como identificador.
    
    Este endpoint:
    1. Busca o dispositivo no banco local pelo MAC
    2. Obtém o pf_id atual do pfSense
    3. Exclui no pfSense usando o pf_id atual
    4. Remove do banco local
    
    Parâmetros:
        mac (str): Endereço MAC do dispositivo
        apply (bool): Se deve aplicar a exclusão imediatamente
    
    Retorna:
        Resposta de sucesso ou erro da operação.
    """
    try:
        # Buscar dispositivo no banco local pelo MAC
        with DhcpService() as dhcp_service:
            mapping = dhcp_service.db.query(DhcpStaticMapping).filter(
                DhcpStaticMapping.mac == mac
            ).first()
            
            if not mapping:
                raise HTTPException(
                    status_code=404,
                    detail=f"Dispositivo com MAC {mac} não encontrado no banco local"
                )
            
            # Obter pf_id atual do pfSense
            current_pf_id = mapping.pf_id
            if current_pf_id is None:
                raise HTTPException(
                    status_code=400,
                    detail=f"Dispositivo com MAC {mac} não possui pf_id válido"
                )
            
            # Primeiro, remover todas as associações de usuários (hard delete)
            from db.models import UserDeviceAssignment
            assignments = dhcp_service.db.query(UserDeviceAssignment).filter(
                UserDeviceAssignment.device_id == mapping.id
            ).all()
            
            for assignment in assignments:
                dhcp_service.db.delete(assignment)
                logger.info(f"Removida associação: user_id={assignment.user_id}, device_id={assignment.device_id}")
            
            # Excluir no pfSense
            pfsense_result = excluir_mapeamento_statico_dhcp_pfsense(
                parent_id="lan",
                mapping_id=current_pf_id,
                apply=apply
            )
            
            # Remover do banco local
            dhcp_service.db.delete(mapping)
            dhcp_service.db.commit()
            
            logger.info(f"Mapeamento excluído por MAC: {mac}, pf_id={current_pf_id}")
            
            return DhcpStaticMappingDeleteResponse(
                success=True,
                message=f"Dispositivo {mac} excluído com sucesso",
                parent_id="lan",
                mapping_id=current_pf_id,
                applied=apply,
                local_deleted=True,
                data=pfsense_result
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao excluir mapeamento por MAC {mac}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao excluir dispositivo {mac}: {e}"
        )

@router.get("/dhcp/status", summary="Obter status online/offline dos dispositivos DHCP")
def get_dhcp_status(current_user_id: int = Query(..., description="ID do usuário que está fazendo a consulta")):
    """
    Obtém o status online/offline dos dispositivos através do servidor DHCP do pfSense.
    
    Args:
        current_user_id: ID do usuário logado (para buscar configurações da instituição)
    
    Returns:
        Lista de dispositivos com status online/offline
    """
    try:
        # Buscar configurações do pfSense da instituição do usuário
        from services_firewalls.institution_config_service import InstitutionConfigService
        from services_firewalls.pfsense_client import _get_pfsense_config
        
        pfsense_url, pfsense_key = _get_pfsense_config(user_id=current_user_id)
        
        # URL do endpoint de leases DHCP do pfSense
        url = f"{pfsense_url}status/dhcp_server/leases"
        headers = {
            "X-API-Key": pfsense_key,
            "Content-Type": "application/json"
        }
        
        response = requests.get(url, headers=headers, timeout=30, verify=False)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get("code") == 200 and data.get("status") == "ok":
            # Processar os dados para um formato mais limpo
            devices_status = []
            for device in data.get("data", []):
                devices_status.append({
                    "ip": device.get("ip"),
                    "mac": device.get("mac"),
                    "hostname": device.get("hostname"),
                    "online_status": device.get("online_status"),
                    "active_status": device.get("active_status"),
                    "interface": device.get("if"),
                    "starts": device.get("starts"),
                    "ends": device.get("ends"),
                    "description": device.get("descr")
                })
            
            return {
                "success": True,
                "message": f"Status de {len(devices_status)} dispositivos obtido com sucesso",
                "total_devices": len(devices_status),
                "devices": devices_status
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Erro na resposta do pfSense: {data.get('message', 'Erro desconhecido')}"
            )
            
    except requests.exceptions.Timeout:
        logger.warning("Timeout ao conectar com pfSense para obter status DHCP")
        raise HTTPException(
            status_code=504,
            detail="pfSense não respondeu a tempo. Verifique a conectividade."
        )
    except requests.exceptions.ConnectionError:
        logger.warning("Erro de conexão com pfSense para obter status DHCP")
        raise HTTPException(
            status_code=503,
            detail="pfSense indisponível. Verifique se o servidor está acessível e as credenciais estão corretas."
        )
    except Exception as e:
        logger.error(f"Erro ao obter status DHCP: {e}")
        
        # Se for erro de autenticação ou configuração, dar dica mais específica
        if "401" in str(e) or "403" in str(e):
            raise HTTPException(
                status_code=503,
                detail="Erro de autenticação com pfSense. Verifique as configurações da instituição no banco de dados."
            )
        elif "404" in str(e):
            raise HTTPException(
                status_code=503,
                detail="Endpoint não encontrado no pfSense. Verifique as configurações da instituição no banco de dados (pfsense_base_url)."
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Erro interno ao obter status dos dispositivos: {str(e)}"
            )

@router.get("/pfsense/health", summary="Verificar status de conexão com pfSense")
def check_pfsense_health(current_user_id: int = Query(..., description="ID do usuário que está fazendo a consulta")):
    """
    Verifica se o pfSense está online e acessível.
    
    Args:
        current_user_id: ID do usuário logado (para buscar configurações da instituição)
    
    Returns:
        Status de saúde do pfSense (online/offline)
    """
    try:
        from services_firewalls.pfsense_client import _get_pfsense_config
        import requests
        
        pfsense_url, pfsense_key = _get_pfsense_config(user_id=current_user_id)
        
        if not pfsense_url or not pfsense_key:
            return {
                "status": "offline",
                "message": "Configurações do pfSense não encontradas",
                "online": False
            }
        
        # Tentar fazer uma requisição simples para verificar se o pfSense está respondendo
        # Usar um endpoint que sabemos que funciona: services/dhcp_servers
        # A URL do banco pode vir como "http://192.168.59.2/api/v2/" ou "http://192.168.59.2/api/v2"
        # Garantir que termine com barra para construir corretamente (como usado em pfsense_client.py)
        base_url = pfsense_url.rstrip('/') + '/'
        url = f"{base_url}services/dhcp_servers"
        headers = {
            "X-API-Key": pfsense_key,
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=10, verify=False)
            
            # Se conseguir resposta (mesmo que seja erro de autenticação), significa que está online
            # Erro 401/403 significa que o servidor está respondendo, apenas não autorizado
            # Status 200 significa que está online e funcionando
            if response.status_code == 200:
                return {
                    "status": "online",
                    "message": "pfSense está online e respondendo",
                    "online": True
                }
            elif response.status_code in [401, 403]:
                # Servidor respondeu mas não autorizado - ainda significa que está online
                return {
                    "status": "online",
                    "message": "pfSense está online (erro de autenticação)",
                    "online": True
                }
            else:
                # Outros códigos de status podem indicar problema, mas servidor está respondendo
                return {
                    "status": "online",
                    "message": f"pfSense está respondendo (status {response.status_code})",
                    "online": True
                }
        except requests.exceptions.Timeout:
            return {
                "status": "offline",
                "message": "pfSense não respondeu a tempo (timeout)",
                "online": False
            }
        except requests.exceptions.ConnectionError:
            return {
                "status": "offline",
                "message": "Não foi possível conectar com pfSense",
                "online": False
            }
        except Exception as e:
            logger.error(f"Erro ao verificar pfSense: {e}", exc_info=True)
            return {
                "status": "offline",
                "message": f"Erro ao verificar pfSense: {str(e)}",
                "online": False
            }
            
    except Exception as e:
        logger.error(f"Erro ao verificar saúde do pfSense: {e}", exc_info=True)
        return {
            "status": "offline",
            "message": f"Erro interno: {str(e)}",
            "online": False
        }

@router.get("/ip-assignment/range-info", summary="Obter informações do range de IPs")
def get_ip_range_info():
    """Retorna informações sobre o range de IPs configurado"""
    try:
        info = ip_assignment_service.get_range_info()
        return {
            "success": True,
            "message": "Informações do range de IPs obtidas com sucesso",
            "data": info
        }
    except Exception as e:
        logger.error(f"Erro ao obter informações do range de IPs: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno ao obter informações do range: {str(e)}"
        )

@router.get("/ip-assignment/available", summary="Listar IPs disponíveis")
def get_available_ips(count: int = Query(10, ge=1, le=50, description="Número de IPs a retornar")):
    """Retorna lista de IPs disponíveis para atribuição"""
    try:
        available_ips = ip_assignment_service.get_available_ips(count)
        return {
            "success": True,
            "message": f"{len(available_ips)} IPs disponíveis encontrados",
            "count": len(available_ips),
            "available_ips": available_ips
        }
    except Exception as e:
        logger.error(f"Erro ao obter IPs disponíveis: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno ao obter IPs disponíveis: {str(e)}"
        )

@router.post("/ip-assignment/assign", summary="Atribuir próximo IP disponível")
def assign_next_ip():
    """Atribui automaticamente o próximo IP disponível no range"""
    try:
        assigned_ip = ip_assignment_service.assign_next_available_ip()
        
        if not assigned_ip:
            raise HTTPException(
                status_code=409,
                detail="Nenhum IP disponível no range configurado"
            )
        
        return {
            "success": True,
            "message": f"IP {assigned_ip} atribuído com sucesso",
            "assigned_ip": assigned_ip,
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao atribuir IP: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno ao atribuir IP: {str(e)}"
        )

@router.post("/ip-assignment/reserve", summary="Reservar IP específico")
def reserve_specific_ip(ip: str = Body(..., description="IP a ser reservado")):
    """Reserva um IP específico se estiver disponível"""
    try:
        success = ip_assignment_service.reserve_ip(ip)
        
        if not success:
            raise HTTPException(
                status_code=409,
                detail=f"IP {ip} não está disponível para reserva"
            )
        
        return {
            "success": True,
            "message": f"IP {ip} reservado com sucesso",
            "reserved_ip": ip,
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao reservar IP {ip}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno ao reservar IP: {str(e)}"
        )

@router.delete("/ip-assignment/release/{ip}", summary="Liberar IP atribuído")
def release_ip(ip: str):
    """Libera um IP que foi atribuído"""
    try:
        success = ip_assignment_service.release_ip(ip)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"IP {ip} não estava atribuído"
            )
        
        return {
            "success": True,
            "message": f"IP {ip} liberado com sucesso",
            "released_ip": ip,
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao liberar IP {ip}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno ao liberar IP: {str(e)}"
        )

@router.get("/ip-assignment/validate", summary="Validar configuração do range")
def validate_ip_range():
    """Valida se o range de IPs está configurado corretamente"""
    try:
        is_valid, message = ip_assignment_service.validate_ip_range()
        
        return {
            "success": is_valid,
            "message": message,
            "is_valid": is_valid
        }
    except Exception as e:
        logger.error(f"Erro ao validar range de IPs: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno ao validar range: {str(e)}"
        )

@router.post("/ip-assignment/refresh", summary="Recarregar IPs do banco de dados")
def refresh_ip_assignments():
    """Recarrega IPs existentes do banco de dados (dhcp_static_mappings)"""
    try:
        ip_assignment_service.refresh_from_db()
        info = ip_assignment_service.get_range_info()
        
        return {
            "success": True,
            "message": "IPs recarregados do banco de dados com sucesso",
            "data": info
        }
    except Exception as e:
        logger.error(f"Erro ao recarregar IPs do banco: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno ao recarregar IPs: {str(e)}"
        )

@router.get("/devices/ips", summary="Listar IPs de dispositivos cadastrados")
def get_device_ips():
    """Retorna lista de IPs de dispositivos já cadastrados no sistema"""
    try:
        db = SessionLocal()
        try:
            # Buscar dispositivos com IPs válidos
            devices = db.query(DhcpStaticMapping).filter(
                DhcpStaticMapping.ipaddr.isnot(None),
                DhcpStaticMapping.ipaddr != ""
            ).all()
            
            device_ips = []
            for device in devices:
                device_ips.append({
                    "ip": device.ipaddr,
                    "mac": device.mac,
                    "hostname": device.hostname or device.cid or "Sem nome",
                    "description": device.descr or "",
                    "created_at": device.created_at.isoformat() if device.created_at else None
                })
            
            # Ordenar por IP para facilitar visualização
            device_ips.sort(key=lambda x: ipaddress.ip_address(x["ip"]))
            
            return {
                "success": True,
                "message": f"{len(device_ips)} IPs de dispositivos encontrados",
                "count": len(device_ips),
                "device_ips": device_ips
            }
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Erro ao buscar IPs de dispositivos: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno ao buscar IPs de dispositivos: {str(e)}"
        )

# Endpoints para bloqueio/liberação de dispositivos
@router.post("/devices/{device_id}/block", response_model=DeviceBlockResponse, summary="Bloquear dispositivo")
def block_device(device_id: int, request: DeviceBlockRequest, current_user_id: int = Query(..., description="ID do usuário que está fazendo a operação")):
    """
    Bloqueia um dispositivo específico com motivo.
    
    Parâmetros:
        device_id (int): ID do dispositivo no banco de dados
        request (DeviceBlockRequest): Dados do bloqueio incluindo motivo
        current_user_id (int): ID do usuário logado (para buscar configurações da instituição)
    
    Retorna:
        Confirmação do bloqueio com detalhes atualizados
    """
    try:
        db = SessionLocal()
        try:
            # Buscar o dispositivo
            device = db.query(DhcpStaticMapping).filter(DhcpStaticMapping.id == device_id).first()
            if not device:
                raise HTTPException(
                    status_code=404,
                    detail=f"Dispositivo com ID {device_id} não encontrado"
                )
            
            # Buscar a instituição do administrador logado
            from services_firewalls.institution_config_service import InstitutionConfigService
            admin_institution_config = InstitutionConfigService.get_user_institution_config(user_id=current_user_id)
            
            if not admin_institution_config:
                raise HTTPException(
                    status_code=403,
                    detail="Administrador não possui instituição associada"
                )
            
            admin_institution_id = admin_institution_config.get('institution_id')
            
            # Garantir que o dispositivo tenha institution_id (usar a do administrador se não tiver)
            if not device.institution_id:
                logger.info(f"Dispositivo {device_id} não tem institution_id, atribuindo institution_id {admin_institution_id} do administrador")
                device.institution_id = admin_institution_id
            elif device.institution_id != admin_institution_id:
                # Verificar se o administrador tem permissão para gerenciar dispositivos de outras instituições
                admin_user = db.query(User).filter(User.id == current_user_id).first()
                if admin_user and admin_user.permission != UserPermission.SUPERUSER:
                    raise HTTPException(
                        status_code=403,
                        detail=f"Dispositivo pertence a outra instituição. Você só pode gerenciar dispositivos da sua instituição."
                    )
            
            # Atualizar status de bloqueio
            device.is_blocked = True
            device.reason = request.reason
            device.updated_at = func.now()
            
            # Salvar no banco
            db.commit()
            db.refresh(device)
            
            # Aplicar bloqueio no pfSense
            device_ip = device.ipaddr
            
            # Identificar a instituição do IP do dispositivo (não do administrador)
            from services_firewalls.institution_config_service import InstitutionConfigService
            device_institution_id = InstitutionConfigService.get_institution_by_ip(device_ip)
            
            if not device_institution_id:
                raise HTTPException(
                    status_code=400,
                    detail=f"IP {device_ip} não pertence a nenhuma instituição ativa"
                )
            
            # Buscar configuração da instituição do dispositivo
            device_institution_config = InstitutionConfigService.get_institution_config(device_institution_id)
            if not device_institution_config:
                raise HTTPException(
                    status_code=404,
                    detail=f"Configuração da instituição do dispositivo não encontrada"
                )
            
            logger.info(f"🚫 Bloqueando dispositivo {device_ip} - Instituição do dispositivo: {device_institution_id} ({device_institution_config.get('nome')} - {device_institution_config.get('cidade')})")
            logger.info(f"   Administrador logado: {admin_institution_id} ({admin_institution_config.get('nome')} - {admin_institution_config.get('cidade')})")
            
            try:
                # Usar a instituição do IP do dispositivo para buscar o alias correto
                with AliasService(user_id=current_user_id, institution_id=device_institution_id) as alias_service:
                    # Remover do alias "Autorizados" se existir
                    authorized_alias = alias_service.get_alias_by_name("Autorizados")
                    if authorized_alias:
                        authorized_addresses = [addr['address'] for addr in authorized_alias['addresses']]
                        if device_ip in authorized_addresses:
                            logger.info(f"Removendo IP {device_ip} do alias Autorizados")
                            new_addresses = []
                            for addr in authorized_alias['addresses']:
                                if addr['address'] != device_ip:
                                    new_addresses.append(addr)
                            
                            alias_service.update_alias("Autorizados", {'addresses': new_addresses})
                            logger.info(f"IP {device_ip} removido do alias Autorizados")
                    
                    # Validar se o IP pertence à rede da instituição do dispositivo antes de bloquear
                    import ipaddress
                    ip_range_start = device_institution_config.get('ip_range_start')
                    ip_range_end = device_institution_config.get('ip_range_end')
                    
                    if ip_range_start and ip_range_end:
                        try:
                            device_ip_obj = ipaddress.ip_address(device_ip)
                            range_start = ipaddress.ip_address(ip_range_start)
                            range_end = ipaddress.ip_address(ip_range_end)
                            
                            if not (range_start <= device_ip_obj <= range_end):
                                raise HTTPException(
                                    status_code=400,
                                    detail=f"IP {device_ip} não pertence à rede da instituição {device_institution_config.get('nome')} - {device_institution_config.get('cidade')} (Range: {ip_range_start} - {ip_range_end})"
                                )
                            logger.info(f"✅ IP {device_ip} validado - pertence à rede da instituição do dispositivo")
                        except ValueError as e:
                            logger.warning(f"⚠️ Erro ao validar IP {device_ip}: {e}")
                            raise HTTPException(
                                status_code=400,
                                detail=f"IP {device_ip} inválido: {str(e)}"
                            )
                    
                    # Adicionar ao alias "Bloqueados" da instituição do dispositivo
                    blocked_alias = alias_service.get_alias_by_name("Bloqueados")
                    if not blocked_alias:
                        # Criar alias Bloqueados se não existir
                        alias_service.create_alias({
                            'name': 'Bloqueados',
                            'alias_type': 'host',
                            'descr': 'Dispositivos bloqueados por motivos administrativos',
                            'addresses': [{'address': device_ip, 'detail': f'Bloqueado manualmente - {request.reason}'}]
                        })
                    else:
                        # Filtrar apenas IPs que pertencem à rede da instituição do dispositivo
                        if ip_range_start and ip_range_end:
                            try:
                                range_start = ipaddress.ip_address(ip_range_start)
                                range_end = ipaddress.ip_address(ip_range_end)
                                filtered_addresses = []
                                for addr in blocked_alias['addresses']:
                                    try:
                                        addr_ip = ipaddress.ip_address(addr['address'])
                                        if range_start <= addr_ip <= range_end:
                                            filtered_addresses.append(addr['address'])
                                        else:
                                            logger.warning(f"⚠️ IP {addr['address']} não pertence à rede da instituição, será removido do alias local")
                                    except ValueError:
                                        filtered_addresses.append(addr['address'])
                                
                                # Se há IPs fora do range, atualizar o alias
                                blocked_addresses = [addr['address'] for addr in blocked_alias['addresses']]
                                if len(filtered_addresses) != len(blocked_addresses):
                                    logger.info(f"🔄 Atualizando alias 'Bloqueados' para conter apenas IPs da instituição {admin_institution_id}")
                                    filtered_address_data = [
                                        addr for addr in blocked_alias['addresses']
                                        if addr['address'] in filtered_addresses
                                    ]
                                    if device_ip not in filtered_addresses:
                                        filtered_address_data.append({
                                            'address': device_ip,
                                            'detail': f'Bloqueado manualmente - {request.reason}'
                                        })
                                    alias_service.update_alias("Bloqueados", {'addresses': filtered_address_data})
                                else:
                                    # Verificar se já está bloqueado
                                    if device_ip not in blocked_addresses:
                                        alias_service.add_addresses_to_alias("Bloqueados", [{
                                            'address': device_ip,
                                            'detail': f'Bloqueado manualmente - {request.reason}'
                                        }])
                            except Exception as filter_error:
                                logger.error(f"Erro ao filtrar IPs do alias: {filter_error}")
                                # Continuar sem filtrar se houver erro
                                blocked_addresses = [addr['address'] for addr in blocked_alias['addresses']]
                                if device_ip not in blocked_addresses:
                                    alias_service.add_addresses_to_alias("Bloqueados", [{
                                        'address': device_ip,
                                        'detail': f'Bloqueado manualmente - {request.reason}'
                                    }])
                        else:
                            # Se não há range configurado, adicionar normalmente
                            blocked_addresses = [addr['address'] for addr in blocked_alias['addresses']]
                            if device_ip not in blocked_addresses:
                                alias_service.add_addresses_to_alias("Bloqueados", [{
                                    'address': device_ip,
                                    'detail': f'Bloqueado manualmente - {request.reason}'
                                }])
                    
                    logger.info(f"IP {device_ip} adicionado ao alias Bloqueados no pfSense")
                    
            except Exception as pfsense_error:
                logger.error(f"Erro ao aplicar bloqueio no pfSense: {pfsense_error}")
                # Continuar mesmo se falhar no pfSense
            
            # Criar feedback administrativo no histórico
            try:
                feedback_service = BlockingFeedbackService()
                feedback = feedback_service.create_admin_blocking_feedback(
                    dhcp_mapping_id=device_id,
                    admin_reason=request.reason,
                    admin_name=request.reason_by or "Administrador",
                    problem_resolved=None
                )
                
                if feedback:
                    logger.info(f"Feedback administrativo criado com ID: {feedback.id}")
                else:
                    logger.warning(f"Falha ao criar feedback administrativo para dispositivo {device_id}")
            except Exception as feedback_error:
                logger.error(f"Erro ao criar feedback administrativo: {feedback_error}")
                # Não falha o bloqueio se o feedback não for criado
            
            logger.info(f"Dispositivo {device_id} ({device.ipaddr}) bloqueado. Motivo: {request.reason}")
            
            return DeviceBlockResponse(
                success=True,
                message=f"Dispositivo {device.ipaddr} bloqueado com sucesso",
                device_id=device.id,
                is_blocked=True,
                reason=device.reason,
                updated_at=device.updated_at
            )
            
        finally:
            db.close()
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao bloquear dispositivo {device_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno ao bloquear dispositivo: {str(e)}"
        )

@router.post("/devices/{device_id}/unblock", response_model=DeviceBlockResponse, summary="Liberar dispositivo")
def unblock_device(device_id: int, request: DeviceUnblockRequest, current_user_id: int = Query(..., description="ID do usuário que está fazendo a operação")):
    """
    Libera um dispositivo bloqueado.
    
    Parâmetros:
        device_id (int): ID do dispositivo no banco de dados
        request (DeviceUnblockRequest): Dados da liberação
        current_user_id (int): ID do usuário logado (para buscar configurações da instituição)
    
    Retorna:
        Confirmação da liberação com detalhes atualizados
    """
    try:
        db = SessionLocal()
        try:
            # Buscar o dispositivo
            device = db.query(DhcpStaticMapping).filter(DhcpStaticMapping.id == device_id).first()
            if not device:
                raise HTTPException(
                    status_code=404,
                    detail=f"Dispositivo com ID {device_id} não encontrado"
                )
            
            # Buscar a instituição do administrador logado
            from services_firewalls.institution_config_service import InstitutionConfigService
            admin_institution_config = InstitutionConfigService.get_user_institution_config(user_id=current_user_id)
            
            if not admin_institution_config:
                raise HTTPException(
                    status_code=403,
                    detail="Administrador não possui instituição associada"
                )
            
            admin_institution_id = admin_institution_config.get('institution_id')
            
            # Garantir que o dispositivo tenha institution_id (usar a do administrador se não tiver)
            if not device.institution_id:
                logger.info(f"Dispositivo {device_id} não tem institution_id, atribuindo institution_id {admin_institution_id} do administrador")
                device.institution_id = admin_institution_id
            elif device.institution_id != admin_institution_id:
                # Verificar se o administrador tem permissão para gerenciar dispositivos de outras instituições
                admin_user = db.query(User).filter(User.id == current_user_id).first()
                if admin_user and admin_user.permission != UserPermission.SUPERUSER:
                    raise HTTPException(
                        status_code=403,
                        detail=f"Dispositivo pertence a outra instituição. Você só pode gerenciar dispositivos da sua instituição."
                    )
            
            # Atualizar status de bloqueio
            device.is_blocked = False
            device.reason = None  # Limpar motivo ao liberar
            device.updated_at = func.now()
            
            # Salvar no banco
            db.commit()
            db.refresh(device)
            
            # Aplicar liberação no pfSense
            device_ip = device.ipaddr
            
            # Identificar a instituição do IP do dispositivo (não do administrador)
            from services_firewalls.institution_config_service import InstitutionConfigService
            device_institution_id = InstitutionConfigService.get_institution_by_ip(device_ip)
            
            if not device_institution_id:
                raise HTTPException(
                    status_code=400,
                    detail=f"IP {device_ip} não pertence a nenhuma instituição ativa"
                )
            
            # Buscar configuração da instituição do dispositivo
            device_institution_config = InstitutionConfigService.get_institution_config(device_institution_id)
            if not device_institution_config:
                raise HTTPException(
                    status_code=404,
                    detail=f"Configuração da instituição do dispositivo não encontrada"
                )
            
            logger.info(f"🔓 Liberando dispositivo {device_ip} - Instituição do dispositivo: {device_institution_id} ({device_institution_config.get('nome')} - {device_institution_config.get('cidade')})")
            logger.info(f"   Administrador logado: {admin_institution_id} ({admin_institution_config.get('nome')} - {admin_institution_config.get('cidade')})")
            
            try:
                # Usar a instituição do IP do dispositivo para buscar o alias correto
                with AliasService(user_id=current_user_id, institution_id=device_institution_id) as alias_service:
                    # Verificar se o institution_id está sendo usado corretamente
                    logger.info(f"✅ AliasService inicializado com institution_id: {alias_service.institution_id}, user_id: {alias_service.user_id}")
                    # Remover do alias "Bloqueados" se existir
                    blocked_alias = alias_service.get_alias_by_name("Bloqueados")
                    if blocked_alias:
                        blocked_addresses = [addr['address'] for addr in blocked_alias['addresses']]
                        if device_ip in blocked_addresses:
                            logger.info(f"Removendo IP {device_ip} do alias Bloqueados")
                            new_addresses = []
                            for addr in blocked_alias['addresses']:
                                if addr['address'] != device_ip:
                                    new_addresses.append(addr)
                            
                            alias_service.update_alias("Bloqueados", {'addresses': new_addresses})
                            logger.info(f"IP {device_ip} removido do alias Bloqueados")
                    
                    # Adicionar ao alias "Autorizados"
                    # Garantir que está buscando com o institution_id correto da instituição do dispositivo
                    logger.info(f"🔍 Buscando alias 'Autorizados' para instituição do dispositivo: {device_institution_id}")
                    authorized_alias = alias_service.get_alias_by_name("Autorizados")
                    
                    if authorized_alias:
                        logger.info(f"✅ Alias 'Autorizados' encontrado no banco (ID: {authorized_alias.get('id')}, institution_id: {device_institution_id})")
                    else:
                        logger.warning(f"⚠️ Alias 'Autorizados' não encontrado no banco para instituição {device_institution_id}")
                    
                    # Se não encontrou no banco, tentar buscar diretamente no pfSense e sincronizar
                    if not authorized_alias:
                        logger.info(f"Alias 'Autorizados' não encontrado no banco para instituição {device_institution_id}, tentando buscar no pfSense")
                        try:
                            # Tentar buscar no pfSense diretamente usando a instituição do dispositivo
                            from services_firewalls.pfsense_client import obter_alias_pfsense
                            pfsense_alias = obter_alias_pfsense(
                                name="Autorizados",
                                user_id=current_user_id,
                                institution_id=device_institution_id
                            )
                            
                            if pfsense_alias and isinstance(pfsense_alias, dict):
                                # Alias existe no pfSense, sincronizar com o banco
                                logger.info(f"✅ Alias 'Autorizados' encontrado no pfSense, sincronizando com banco (institution_id: {device_institution_id})")
                                
                                # Filtrar apenas IPs que pertencem à rede da instituição do dispositivo
                                import ipaddress
                                ip_range_start = device_institution_config.get('ip_range_start')
                                ip_range_end = device_institution_config.get('ip_range_end')
                                
                                # Preparar dados do alias para salvar
                                alias_data = {
                                    'id': pfsense_alias.get('id'),
                                    'name': pfsense_alias.get('name'),
                                    'type': pfsense_alias.get('type'),
                                    'descr': pfsense_alias.get('descr'),
                                    'address': pfsense_alias.get('address', []),
                                    'detail': pfsense_alias.get('detail', [])
                                }
                                
                                if ip_range_start and ip_range_end:
                                    try:
                                        range_start = ipaddress.ip_address(ip_range_start)
                                        range_end = ipaddress.ip_address(ip_range_end)
                                        
                                        # Filtrar endereços que pertencem à rede da instituição
                                        original_addresses = alias_data.get('address', [])
                                        original_details = alias_data.get('detail', [])
                                        
                                        filtered_addresses = []
                                        filtered_details = []
                                        
                                        for i, addr in enumerate(original_addresses):
                                            try:
                                                addr_ip = ipaddress.ip_address(addr)
                                                if range_start <= addr_ip <= range_end:
                                                    filtered_addresses.append(addr)
                                                    # Manter o detail correspondente se existir
                                                    if i < len(original_details):
                                                        filtered_details.append(original_details[i])
                                                    else:
                                                        filtered_details.append('')
                                                    logger.debug(f"✅ IP {addr} pertence à rede da instituição, mantendo")
                                                else:
                                                    logger.warning(f"⚠️ IP {addr} não pertence à rede da instituição (Range: {ip_range_start} - {ip_range_end}), removendo")
                                            except ValueError:
                                                # Se não for um IP válido, manter (pode ser uma rede ou hostname)
                                                filtered_addresses.append(addr)
                                                if i < len(original_details):
                                                    filtered_details.append(original_details[i])
                                                else:
                                                    filtered_details.append('')
                                        
                                        # Atualizar alias_data com apenas os IPs filtrados
                                        alias_data['address'] = filtered_addresses
                                        alias_data['detail'] = filtered_details
                                        
                                        logger.info(f"🔍 Filtrados {len(original_addresses)} IPs para {len(filtered_addresses)} IPs da rede da instituição")
                                    except Exception as filter_error:
                                        logger.error(f"Erro ao filtrar IPs do alias do pfSense: {filter_error}")
                                        # Continuar sem filtrar se houver erro
                                
                                # Salvar no banco com institution_id correto da instituição do dispositivo
                                logger.info(f"💾 Salvando alias no banco com institution_id: {device_institution_id}")
                                alias_service.save_aliases_data({'data': [alias_data]})
                                # Buscar novamente após sincronização
                                authorized_alias = alias_service.get_alias_by_name("Autorizados")
                                if authorized_alias:
                                    logger.info(f"✅ Alias 'Autorizados' encontrado após sincronização (ID: {authorized_alias.get('id')})")
                                else:
                                    logger.warning(f"⚠️ Alias 'Autorizados' ainda não encontrado após sincronização")
                            else:
                                logger.info(f"ℹ️ Alias 'Autorizados' não encontrado no pfSense, será criado")
                        except Exception as sync_error:
                            logger.warning(f"Erro ao sincronizar alias do pfSense: {sync_error}")
                    
                    # Se ainda não encontrou, criar o alias
                    if not authorized_alias:
                        logger.info(f"🔨 Criando alias 'Autorizados' para instituição {device_institution_id} ({device_institution_config.get('nome')} - {device_institution_config.get('cidade')})")
                        try:
                            result = alias_service.create_alias({
                                'name': 'Autorizados',
                                'alias_type': 'host',
                                'descr': 'Dispositivos autorizados na rede',
                                'addresses': [{'address': device_ip, 'detail': 'Dispositivo liberado'}]
                            })
                            logger.info(f"✅ Alias 'Autorizados' criado com sucesso: {result}")
                            # Buscar novamente após criação
                            authorized_alias = alias_service.get_alias_by_name("Autorizados")
                            if authorized_alias:
                                logger.info(f"✅ Alias 'Autorizados' encontrado após criação (ID: {authorized_alias.get('id')}, institution_id: {device_institution_id})")
                            else:
                                logger.warning(f"⚠️ Alias 'Autorizados' criado mas não encontrado imediatamente após criação")
                        except ValueError as e:
                            # Se o alias já existe (pode ter sido criado por outra thread/processo)
                            if "já existe" in str(e):
                                logger.info(f"Alias 'Autorizados' já existe, buscando novamente")
                                authorized_alias = alias_service.get_alias_by_name("Autorizados")
                            else:
                                logger.error(f"Erro ao criar alias 'Autorizados': {e}")
                                raise HTTPException(
                                    status_code=500,
                                    detail=f"Erro ao criar alias 'Autorizados': {str(e)}"
                                )
                        except Exception as create_error:
                            logger.error(f"Erro ao criar alias 'Autorizados': {create_error}")
                            raise HTTPException(
                                status_code=500,
                                detail=f"Erro ao criar alias 'Autorizados': {str(create_error)}"
                            )
                    
                    # Se encontrou o alias, validar e adicionar o IP
                    if authorized_alias:
                        # Validar se o IP pertence à rede da instituição do dispositivo antes de adicionar
                        import ipaddress
                        ip_range_start = device_institution_config.get('ip_range_start')
                        ip_range_end = device_institution_config.get('ip_range_end')
                        
                        if ip_range_start and ip_range_end:
                            try:
                                device_ip_obj = ipaddress.ip_address(device_ip)
                                range_start = ipaddress.ip_address(ip_range_start)
                                range_end = ipaddress.ip_address(ip_range_end)
                                
                                if not (range_start <= device_ip_obj <= range_end):
                                    raise HTTPException(
                                        status_code=400,
                                        detail=f"IP {device_ip} não pertence à rede da instituição {device_institution_config.get('nome')} - {device_institution_config.get('cidade')} (Range: {ip_range_start} - {ip_range_end})"
                                    )
                                logger.info(f"✅ IP {device_ip} validado - pertence à rede da instituição do dispositivo")
                            except ValueError as e:
                                logger.warning(f"⚠️ Erro ao validar IP {device_ip}: {e}")
                                raise HTTPException(
                                    status_code=400,
                                    detail=f"IP {device_ip} inválido: {str(e)}"
                                )
                        else:
                            logger.warning(f"⚠️ Instituição do dispositivo não tem range de IPs configurado, pulando validação")
                        
                        # Filtrar apenas IPs que pertencem à rede da instituição do dispositivo
                        authorized_addresses = [addr['address'] for addr in authorized_alias['addresses']]
                        
                        # Filtrar IPs que não pertencem à rede da instituição do dispositivo
                        if ip_range_start and ip_range_end:
                            try:
                                range_start = ipaddress.ip_address(ip_range_start)
                                range_end = ipaddress.ip_address(ip_range_end)
                                filtered_addresses = []
                                for addr in authorized_alias['addresses']:
                                    try:
                                        addr_ip = ipaddress.ip_address(addr['address'])
                                        if range_start <= addr_ip <= range_end:
                                            filtered_addresses.append(addr['address'])
                                        else:
                                            logger.warning(f"⚠️ IP {addr['address']} não pertence à rede da instituição, será removido do alias local")
                                    except ValueError:
                                        # Se não for um IP válido, manter (pode ser uma rede ou hostname)
                                        filtered_addresses.append(addr['address'])
                                
                                # Se há IPs fora do range, atualizar o alias no banco para refletir apenas os IPs corretos
                                if len(filtered_addresses) != len(authorized_addresses):
                                    logger.info(f"🔄 Atualizando alias 'Autorizados' para conter apenas IPs da instituição {admin_institution_id}")
                                    # Manter apenas os endereços filtrados
                                    filtered_address_data = [
                                        addr for addr in authorized_alias['addresses']
                                        if addr['address'] in filtered_addresses
                                    ]
                                    # Adicionar o novo IP se não estiver na lista
                                    if device_ip not in filtered_addresses:
                                        filtered_address_data.append({
                                            'address': device_ip,
                                            'detail': 'Dispositivo liberado'
                                        })
                                    
                                    # Atualizar o alias no banco e no pfSense
                                    alias_service.update_alias("Autorizados", {'addresses': filtered_address_data})
                                    logger.info(f"✅ Alias 'Autorizados' atualizado com IPs da instituição {admin_institution_id}")
                                else:
                                    # Se o IP não está na lista, adicionar
                                    if device_ip not in authorized_addresses:
                                        logger.info(f"Adicionando IP {device_ip} ao alias 'Autorizados' existente")
                                        try:
                                            alias_service.add_addresses_to_alias("Autorizados", [{
                                                'address': device_ip,
                                                'detail': 'Dispositivo liberado'
                                            }])
                                            logger.info(f"IP {device_ip} adicionado ao alias Autorizados no pfSense")
                                        except ValueError as e:
                                            if "não encontrado" in str(e):
                                                logger.error(f"Alias 'Autorizados' não encontrado ao tentar adicionar endereço: {e}")
                                                raise HTTPException(
                                                    status_code=500,
                                                    detail=f"Erro ao adicionar IP ao alias 'Autorizados': {str(e)}"
                                                )
                                            else:
                                                raise
                                    else:
                                        logger.info(f"IP {device_ip} já está no alias Autorizados")
                            except Exception as filter_error:
                                logger.error(f"Erro ao filtrar IPs do alias: {filter_error}")
                                # Continuar sem filtrar se houver erro
                                if device_ip not in authorized_addresses:
                                    alias_service.add_addresses_to_alias("Autorizados", [{
                                        'address': device_ip,
                                        'detail': 'Dispositivo liberado'
                                    }])
                        else:
                            # Se não há range configurado, adicionar normalmente
                            if device_ip not in authorized_addresses:
                                logger.info(f"Adicionando IP {device_ip} ao alias 'Autorizados' existente")
                                alias_service.add_addresses_to_alias("Autorizados", [{
                                    'address': device_ip,
                                    'detail': 'Dispositivo liberado'
                                }])
                            else:
                                logger.info(f"IP {device_ip} já está no alias Autorizados")
                    else:
                        raise HTTPException(
                            status_code=500,
                            detail="Não foi possível encontrar ou criar o alias 'Autorizados'"
                        )
                    
                    logger.info(f"IP {device_ip} processado no alias Autorizados no pfSense")
                    
            except Exception as pfsense_error:
                logger.error(f"Erro ao aplicar liberação no pfSense: {pfsense_error}")
                # Continuar mesmo se falhar no pfSense
            
            logger.info(f"Dispositivo {device_id} ({device.ipaddr}) liberado")
            
            return DeviceBlockResponse(
                success=True,
                message=f"Dispositivo {device.ipaddr} liberado com sucesso",
                device_id=device.id,
                is_blocked=False,
                reason=None,
                updated_at=device.updated_at
            )
            
        finally:
            db.close()
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao liberar dispositivo {device_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno ao liberar dispositivo: {str(e)}"
        )

@router.get("/devices/{device_id}/block-status", response_model=DeviceBlockResponse, summary="Verificar status de bloqueio")
def get_device_block_status(device_id: int):
    """
    Verifica o status de bloqueio de um dispositivo.
    
    Parâmetros:
        device_id (int): ID do dispositivo no banco de dados
    
    Retorna:
        Status atual de bloqueio do dispositivo
    """
    try:
        db = SessionLocal()
        try:
            # Buscar o dispositivo
            device = db.query(DhcpStaticMapping).filter(DhcpStaticMapping.id == device_id).first()
            if not device:
                raise HTTPException(
                    status_code=404,
                    detail=f"Dispositivo com ID {device_id} não encontrado"
                )
            
            return DeviceBlockResponse(
                success=True,
                message=f"Status do dispositivo {device.ipaddr}",
                device_id=device.id,
                is_blocked=device.is_blocked,
                reason=device.reason,
                updated_at=device.updated_at
            )
            
        finally:
            db.close()
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao verificar status do dispositivo {device_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno ao verificar status: {str(e)}"
        )

@router.get("/", summary="Listar dispositivos cadastrados")
def list_devices():
    """
    Lista todos os dispositivos cadastrados em memória.
    Retorna:
        Lista de dispositivos (mock).
    """
    return DEVICES

