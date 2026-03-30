import requests
import json
import config
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger("pfsense_client")

def _get_pfsense_config(
    pfsense_url: Optional[str] = None, 
    pfsense_key: Optional[str] = None,
    user_id: Optional[int] = None,
    institution_id: Optional[int] = None
) -> tuple[str, str]:
    """
    Obtém configurações do pfSense, buscando do banco se necessário.
    
    Prioridade:
    1. Parâmetros fornecidos diretamente (pfsense_url, pfsense_key)
    2. Configurações da instituição do usuário (se user_id fornecido)
    3. Configurações da instituição (se institution_id fornecido)
    4. Configurações globais do config (fallback)
    
    Args:
        pfsense_url: URL base do pfSense (opcional)
        pfsense_key: Chave API do pfSense (opcional)
        user_id: ID do usuário para buscar configurações da instituição (opcional)
        institution_id: ID da instituição para buscar configurações (opcional)
        
    Returns:
        Tupla (url, key) com as configurações do pfSense
    """
    # Se já foram fornecidas diretamente, usar
    if pfsense_url and pfsense_key:
        return pfsense_url, pfsense_key
    
    # Tentar buscar do banco de dados
    try:
        from services_firewalls.institution_config_service import InstitutionConfigService
        
        institution_config = None
        
        if user_id:
            institution_config = InstitutionConfigService.get_user_institution_config(user_id=user_id)
        elif institution_id:
            institution_config = InstitutionConfigService.get_institution_config(institution_id)
        
        if institution_config:
            url = institution_config.get('pfsense_base_url')
            key = institution_config.get('pfsense_key')
            if url and key:
                logger.debug(f"Usando configurações do pfSense da instituição {institution_config.get('nome')}")
                return url, key
    except Exception as e:
        logger.warning(f"Erro ao buscar configurações da instituição, usando config global: {e}")
    
    # Fallback para config global
    url = pfsense_url or config.PFSENSE_API_URL
    key = pfsense_key or config.PFSENSE_API_KEY
    
    if not url or not key:
        raise ValueError("Configurações do pfSense não encontradas. Configure pfsense_url e pfsense_key, ou configure no banco de dados (tabela institutions), ou use variáveis de ambiente.")
    
    return url, key

def cadastrar_alias_pfsense(
    name, 
    alias_type, 
    descr, 
    address, 
    detail, 
    pfsense_url: Optional[str] = None, 
    pfsense_key: Optional[str] = None,
    user_id: Optional[int] = None,
    institution_id: Optional[int] = None
):
    """
    Cadastra um novo alias no pfSense.
    
    Parâmetros:
        name (str): Nome do alias.
        alias_type (str): Tipo do alias (host, network, port, etc.).
        descr (str): Descrição do alias.
        address (list): Lista de endereços IP ou redes.
        detail (list): Lista de detalhes para cada endereço.
        pfsense_url (str, opcional): URL base do pfSense (usa config se não fornecido).
        pfsense_key (str, opcional): Chave API do pfSense (usa config se não fornecido).
        user_id (int, opcional): ID do usuário para buscar configurações da instituição.
        institution_id (int, opcional): ID da instituição para buscar configurações.
    
    Retorna:
        dict: Resposta JSON da API do pfSense.
    """
    base_url, api_key = _get_pfsense_config(pfsense_url, pfsense_key, user_id, institution_id)
    url = f"{base_url}firewall/alias"
    headers = {
        "X-API-Key": api_key,
        "Content-Type": "application/json"
    }
    data = {
        "name": name,
        "type": alias_type,
        "descr": descr,
        "address": address,
        "detail": detail
    }
    
    try:
        response = requests.post(url, json=data, headers=headers, timeout=10, verify=False)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Erro ao cadastrar alias no pfSense: {e}\nURL: {url}\nHeaders: {headers}\nPayload: {data}")
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"Resposta do pfSense: {e.response.text}")
        raise

def obter_alias_pfsense(
    name, 
    pfsense_url: Optional[str] = None, 
    pfsense_key: Optional[str] = None,
    user_id: Optional[int] = None,
    institution_id: Optional[int] = None
):
    """
    Obtém um alias específico do pfSense.
    
    Parâmetros:
        name (str): Nome do alias.
        pfsense_url (str, opcional): URL base do pfSense (usa config se não fornecido).
        pfsense_key (str, opcional): Chave API do pfSense (usa config se não fornecido).
        user_id (int, opcional): ID do usuário para buscar configurações da instituição.
        institution_id (int, opcional): ID da instituição para buscar configurações.
    
    Retorna:
        dict: Dados do alias ou None se não encontrado.
    """
    base_url, api_key = _get_pfsense_config(pfsense_url, pfsense_key, user_id, institution_id)
    # Usar o mesmo endpoint que funciona para listar todos os aliases
    url = f"{base_url}firewall/aliases"
    headers = {"X-API-Key": api_key}
    
    try:
        response = requests.get(url, headers=headers, timeout=10, verify=False)
        response.raise_for_status()
        result = response.json()
        
        # Filtrar pelo nome do alias
        if result and isinstance(result, list):
            for alias in result:
                if alias.get("name") == name:
                    return alias
        elif result and isinstance(result, dict) and result.get("data"):
            for alias in result["data"]:
                if alias.get("name") == name:
                    return alias
        
        return None
    except Exception as e:
        logger.error(f"Erro ao obter alias '{name}' do pfSense: {e}\nURL: {url}\nHeaders: {headers}")
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"Resposta do pfSense: {e.response.text}")
        raise

def listar_aliases_pfsense(
    pfsense_url: Optional[str] = None, 
    pfsense_key: Optional[str] = None,
    user_id: Optional[int] = None,
    institution_id: Optional[int] = None
):
    """
    Lista todos os aliases do pfSense.
    
    Parâmetros:
        pfsense_url (str, opcional): URL base do pfSense (usa config se não fornecido).
        pfsense_key (str, opcional): Chave API do pfSense (usa config se não fornecido).
        user_id (int, opcional): ID do usuário para buscar configurações da instituição.
        institution_id (int, opcional): ID da instituição para buscar configurações.
    
    Retorna:
        dict: Resposta JSON da API do pfSense contendo todos os aliases.
    """
    base_url, api_key = _get_pfsense_config(pfsense_url, pfsense_key, user_id, institution_id)
    url = f"{base_url}firewall/aliases"
    headers = {"X-API-Key": api_key}
    
    try:
        response = requests.get(url, headers=headers, timeout=10, verify=False)
        response.raise_for_status()
        return response.json()
    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
        logger.error(f"Timeout/Conexão ao listar aliases do pfSense: {e}")
        raise
    except Exception as e:
        logger.error(f"Erro ao listar aliases do pfSense: {e}\nURL: {url}\nHeaders: {headers}")
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"Resposta do pfSense: {e.response.text}")
        raise

def listar_clientes_dhcp_pfsense(
    pfsense_url: Optional[str] = None, 
    pfsense_key: Optional[str] = None,
    user_id: Optional[int] = None,
    institution_id: Optional[int] = None
):
    """
    Lista todos os servidores DHCP e seus clientes do pfSense.
    
    Parâmetros:
        pfsense_url (str, opcional): URL base do pfSense (usa config se não fornecido).
        pfsense_key (str, opcional): Chave API do pfSense (usa config se não fornecido).
        user_id (int, opcional): ID do usuário para buscar configurações da instituição.
        institution_id (int, opcional): ID da instituição para buscar configurações.
    
    Retorna:
        dict: Resposta JSON da API do pfSense contendo informações dos servidores DHCP e clientes.
    """
    base_url, api_key = _get_pfsense_config(pfsense_url, pfsense_key, user_id, institution_id)
    url = f"{base_url}services/dhcp_servers"
    headers = {
        "X-API-Key": api_key
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10, verify=False)
        response.raise_for_status()
        return response.json()
    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
        logger.error(f"Timeout/Conexão ao listar clientes DHCP no pfSense: {e}")
        raise
    except Exception as e:
        logger.error(f"Erro ao listar clientes DHCP no pfSense: {e}\nURL: {url}\nHeaders: {headers}")
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"Resposta do pfSense: {e.response.text}")
        raise

def listar_mapeamentos_staticos_dhcp_pfsense(
    parent_id, 
    mapping_id,
    pfsense_url: Optional[str] = None, 
    pfsense_key: Optional[str] = None,
    user_id: Optional[int] = None,
    institution_id: Optional[int] = None
):
    """
    Lista mapeamentos estáticos DHCP do pfSense.
    
    Parâmetros:
        parent_id (str): ID da interface (ex: "lan", "wan", "opt1")
        mapping_id (int): ID do mapeamento específico
        pfsense_url (str, opcional): URL base do pfSense (usa config se não fornecido).
        pfsense_key (str, opcional): Chave API do pfSense (usa config se não fornecido).
        user_id (int, opcional): ID do usuário para buscar configurações da instituição.
        institution_id (int, opcional): ID da instituição para buscar configurações.
    
    Retorna:
        dict: Resposta JSON da API do pfSense contendo o mapeamento específico.
    """
    base_url, api_key = _get_pfsense_config(pfsense_url, pfsense_key, user_id, institution_id)
    url = f"{base_url}services/dhcp_server/static_mapping"
    headers = {
        "X-API-Key": api_key
    }
    
    # Usar query parameters em vez de body
    params = {
        "parent_id": parent_id,
        "id": mapping_id
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10, verify=False)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Erro ao listar mapeamentos estáticos DHCP no pfSense: {e}\nURL: {url}\nHeaders: {headers}\nParams: {params}")
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"Resposta do pfSense: {e.response.text}")
        raise

def listar_regras_firewall_pfsense(
    pfsense_url: Optional[str] = None, 
    pfsense_key: Optional[str] = None,
    user_id: Optional[int] = None,
    institution_id: Optional[int] = None
):
    """
    Lista todas as regras de firewall do pfSense.
    
    Args:
        pfsense_url (str, opcional): URL base do pfSense (usa config se não fornecido).
        pfsense_key (str, opcional): Chave API do pfSense (usa config se não fornecido).
        user_id (int, opcional): ID do usuário para buscar configurações da instituição.
        institution_id (int, opcional): ID da instituição para buscar configurações.
    
    Retorna:
        dict|list: Resposta JSON da API do pfSense contendo as regras.
    """
    base_url, api_key = _get_pfsense_config(pfsense_url, pfsense_key, user_id, institution_id)
    url = f"{base_url}firewall/rules"
    headers = {"X-API-Key": api_key}
    try:
        response = requests.get(url, headers=headers, timeout=10, verify=False)
        response.raise_for_status()
        return response.json()
    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
        logger.error(f"Timeout/Conexão ao listar regras de firewall no pfSense: {e}")
        raise
    except Exception as e:
        logger.error(f"Erro ao listar regras de firewall do pfSense: {e}\nURL: {url}\nHeaders: {headers}")
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"Resposta do pfSense: {e.response.text}")
        raise

def verificar_mapeamento_existente_pfsense(
    parent_id, 
    ipaddr=None, 
    mac=None,
    pfsense_url: Optional[str] = None,
    pfsense_key: Optional[str] = None,
    user_id: Optional[int] = None,
    institution_id: Optional[int] = None
):
    """
    Verifica se já existe um mapeamento estático DHCP com o mesmo IP ou MAC.
    
    Parâmetros:
        parent_id (str): ID do servidor DHCP pai
        ipaddr (str, opcional): Endereço IP para verificar
        mac (str, opcional): Endereço MAC para verificar
        pfsense_url (str, opcional): URL base do pfSense (usa config se não fornecido)
        pfsense_key (str, opcional): Chave API do pfSense (usa config se não fornecido)
        user_id (int, opcional): ID do usuário para buscar configurações da instituição
        institution_id (int, opcional): ID da instituição para buscar configurações
    
    Retorna:
        dict: Informações sobre mapeamentos existentes encontrados
    """
    base_url, api_key = _get_pfsense_config(pfsense_url, pfsense_key, user_id, institution_id)
    url = f"{base_url}services/dhcp_servers"
    headers = {"X-API-Key": api_key}
    
    try:
        response = requests.get(url, headers=headers, timeout=10, verify=False)
        response.raise_for_status()
        result = response.json()
        
        existing_mappings = []
        
        # Procurar no servidor específico
        if result and isinstance(result, dict) and result.get("data"):
            for server in result["data"]:
                if server.get("id") == parent_id and server.get("staticmap"):
                    for mapping in server["staticmap"]:
                        # Verificar por IP
                        if ipaddr and mapping.get("ipaddr") == ipaddr:
                            existing_mappings.append({
                                "type": "ip",
                                "mapping": mapping,
                                "server_id": parent_id
                            })
                        
                        # Verificar por MAC
                        if mac and mapping.get("mac") == mac:
                            existing_mappings.append({
                                "type": "mac",
                                "mapping": mapping,
                                "server_id": parent_id
                            })
        
        return {
            "exists": len(existing_mappings) > 0,
            "mappings": existing_mappings,
            "total_found": len(existing_mappings)
        }
        
    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
        logger.error(f"Timeout/Conexão ao verificar mapeamentos existentes no pfSense: {e}")
        raise
    except Exception as e:
        logger.error(f"Erro ao verificar mapeamentos existentes: {e}")
        raise

def cadastrar_mapeamento_statico_dhcp_pfsense(
    mapping_data, 
    verificar_existente=True,
    pfsense_url: Optional[str] = None, 
    pfsense_key: Optional[str] = None,
    user_id: Optional[int] = None,
    institution_id: Optional[int] = None
):
    """
    Cadastra um novo mapeamento estático DHCP no pfSense.
    
    Parâmetros:
        mapping_data (dict): Dados do mapeamento estático DHCP conforme documentação oficial:
        {
            "parent_id": "string",
            "mac": "string", 
            "ipaddr": "string",
            "cid": "string",
            "hostname": "string",
            "domain": "string",
            "domainsearchlist": ["string"],
            "defaultleasetime": 7200,
            "maxleasetime": 86400,
            "gateway": "string",
            "dnsserver": ["string"],
            "winsserver": ["string"],
            "ntpserver": ["string"],
            "arp_table_static_entry": true,
            "descr": "string"
        }
        verificar_existente (bool): Se deve verificar mapeamentos existentes antes de cadastrar
        pfsense_url (str, opcional): URL base do pfSense (usa config se não fornecido).
        pfsense_key (str, opcional): Chave API do pfSense (usa config se não fornecido).
        user_id (int, opcional): ID do usuário para buscar configurações da instituição.
        institution_id (int, opcional): ID da instituição para buscar configurações.
    
    Retorna:
        dict: Resposta JSON da API do pfSense.
    """
    base_url, api_key = _get_pfsense_config(pfsense_url, pfsense_key, user_id, institution_id)
    
    # Verificar mapeamentos existentes se solicitado
    if verificar_existente:
        parent_id = mapping_data.get("parent_id")
        ipaddr = mapping_data.get("ipaddr")
        mac = mapping_data.get("mac")
        
        if parent_id and (ipaddr or mac):
            existing_check = verificar_mapeamento_existente_pfsense(
                parent_id, 
                ipaddr, 
                mac, 
                pfsense_url=base_url, 
                pfsense_key=api_key,
                user_id=user_id,
                institution_id=institution_id
            )
            
            if existing_check["exists"]:
                # Retornar erro informando sobre mapeamentos existentes
                error_msg = "Já existem mapeamentos DHCP com os mesmos dados:"
                for mapping_info in existing_check["mappings"]:
                    mapping = mapping_info["mapping"]
                    if mapping_info["type"] == "ip":
                        error_msg += f"\n- IP {mapping.get('ipaddr')} já está em uso pelo dispositivo {mapping.get('cid', 'N/A')} (MAC: {mapping.get('mac', 'N/A')})"
                    elif mapping_info["type"] == "mac":
                        error_msg += f"\n- MAC {mapping.get('mac')} já está em uso pelo dispositivo {mapping.get('cid', 'N/A')} (IP: {mapping.get('ipaddr', 'N/A')})"
                
                raise ValueError(error_msg)
    
    url = f"{base_url}services/dhcp_server/static_mapping"
    headers = {
        "X-API-Key": api_key,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, json=mapping_data, headers=headers, timeout=10, verify=False)
        response.raise_for_status()
        return response.json()
    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
        logger.error(f"Timeout/Conexão ao cadastrar mapeamento DHCP no pfSense: {e}")
        raise
    except Exception as e:
        logger.error(f"Erro ao cadastrar mapeamento estático DHCP no pfSense: {e}\nURL: {url}\nHeaders: {headers}\nPayload: {mapping_data}")
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"Resposta do pfSense: {e.response.text}")
        raise

def atualizar_alias_pfsense(
    alias_id: int, 
    name: str, 
    alias_type=None, 
    descr=None, 
    address=None, 
    detail=None,
    pfsense_url: Optional[str] = None, 
    pfsense_key: Optional[str] = None,
    user_id: Optional[int] = None,
    institution_id: Optional[int] = None
):
    """
    Atualiza um alias existente no pfSense.
    
    Parâmetros:
        alias_id (int): ID do alias no pfSense
        name (str): Nome do alias a ser atualizado.
        alias_type (str, opcional): Novo tipo do alias (host, network, port, etc.).
        descr (str, opcional): Nova descrição do alias.
        address (list, opcional): Nova lista de endereços IP ou redes.
        detail (list, opcional): Nova lista de detalhes para cada endereço.
        pfsense_url (str, opcional): URL base do pfSense (usa config se não fornecido).
        pfsense_key (str, opcional): Chave API do pfSense (usa config se não fornecido).
        user_id (int, opcional): ID do usuário para buscar configurações da instituição.
        institution_id (int, opcional): ID da instituição para buscar configurações.
    
    Retorna:
        dict: Resposta JSON da API do pfSense.
    """
    base_url, api_key = _get_pfsense_config(pfsense_url, pfsense_key, user_id, institution_id)
    
    # Validação explícita para evitar URLs None
    if not base_url or base_url == "None" or not api_key:
        raise ValueError(
            f"Configurações do pfSense inválidas ou não encontradas. "
            f"base_url={base_url}, user_id={user_id}, institution_id={institution_id}. "
            "Verifique se o usuário tem uma instituição associada e se a instituição possui configurações do pfSense no banco de dados."
        )
    
    url = f"{base_url}firewall/alias"
    headers = {
        "X-API-Key": api_key,
        "Content-Type": "application/json"
    }
    
    # Construir payload com id obrigatório
    data = {
        "id": alias_id,
        "name": name
    }
    
    if alias_type is not None:
        data["type"] = alias_type
    if descr is not None:
        data["descr"] = descr
    if address is not None:
        data["address"] = address
    if detail is not None:
        data["detail"] = detail
    
    try:
        sync_start = datetime.now()
        response = requests.patch(url, json=data, headers=headers, timeout=10, verify=False)
        response.raise_for_status()
        result = response.json()
        sync_duration = (datetime.now() - sync_start).total_seconds()
        
        # Log de performance
        try:
            from services_scanners.performance_logger import get_performance_logger
            perf_logger = get_performance_logger()
            perf_logger.log_sync(
                sync_type="ALIAS_UPDATE",
                duration_seconds=sync_duration,
                success=True,
                metadata={
                    'alias_id': alias_id,
                    'alias_name': name,
                    'endpoint': 'pfsense_client.atualizar_alias_pfsense'
                }
            )
        except Exception as perf_err:
            logger.warning(f"Erro ao registrar log de performance: {perf_err}")
        
        return result
    except Exception as e:
        sync_duration = (datetime.now() - sync_start).total_seconds() if 'sync_start' in locals() else 0
        
        # Log de performance - erro
        try:
            from services_scanners.performance_logger import get_performance_logger
            perf_logger = get_performance_logger()
            perf_logger.log_sync(
                sync_type="ALIAS_UPDATE",
                duration_seconds=sync_duration,
                success=False,
                metadata={
                    'alias_id': alias_id,
                    'alias_name': name,
                    'error': str(e),
                    'endpoint': 'pfsense_client.atualizar_alias_pfsense'
                }
            )
        except:
            pass
        
        logger.error(f"Erro ao atualizar alias '{name}' (ID: {alias_id}) no pfSense: {e}\nURL: {url}\nHeaders: {headers}\nPayload: {data}")
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"Resposta do pfSense: {e.response.text}")
        raise

def excluir_mapeamento_statico_dhcp_pfsense(parent_id: str, mapping_id: int, apply: bool = False):
    """
    Exclui um mapeamento estático DHCP no pfSense.
    
    Este endpoint utiliza a API oficial do pfSense v2:
    DELETE /api/v2/services/dhcp_server/static_mapping
    
    Parâmetros:
        parent_id (str): ID do servidor DHCP pai (ex: "lan", "wan", "opt1")
        mapping_id (int): ID do mapeamento estático DHCP a ser excluído
        apply (bool): Se deve aplicar a exclusão imediatamente (padrão: False)
    
    Retorna:
        dict: Resposta JSON da API do pfSense.
        
    Exemplo:
        excluir_mapeamento_statico_dhcp_pfsense(parent_id="lan", mapping_id=5, apply=True)
    """
    url = f"{config.PFSENSE_API_URL}services/dhcp_server/static_mapping"
    headers = {
        "X-API-Key": config.PFSENSE_API_KEY
    }
    
    # Parâmetros de query conforme documentação oficial
    params = {
        "parent_id": parent_id,
        "id": mapping_id,
        "apply": apply
    }
    
    try:
        response = requests.delete(url, headers=headers, params=params, timeout=10, verify=False)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Erro ao excluir mapeamento estático DHCP (parent_id: {parent_id}, mapping_id: {mapping_id}) no pfSense: {e}\nURL: {url}\nHeaders: {headers}\nParams: {params}")
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"Resposta do pfSense: {e.response.text}")
        raise

def atualizar_mapeamento_statico_dhcp_pfsense(parent_id: str, mapping_id: int, update_data: dict, apply: bool = False):
    """
    Atualiza um mapeamento estático DHCP no pfSense.
    
    Este endpoint utiliza a API oficial do pfSense v2:
    PATCH /api/v2/services/dhcp_server/static_mapping
    
    Parâmetros:
        parent_id (str): ID do servidor DHCP pai (ex: "lan", "wan", "opt1")
        mapping_id (int): ID do mapeamento estático DHCP a ser atualizado
        update_data (dict): Dados para atualização (campos opcionais):
        {
            "mac": "string",
            "ipaddr": "string",
            "cid": "string",
            "hostname": "string",
            "domain": "string",
            "domainsearchlist": ["string"],
            "defaultleasetime": 7200,
            "maxleasetime": 86400,
            "gateway": "string",
            "dnsserver": ["string"],
            "winsserver": ["string"],
            "ntpserver": ["string"],
            "arp_table_static_entry": true,
            "descr": "string"
        }
        apply (bool): Se deve aplicar a atualização imediatamente (padrão: False)
    
    Retorna:
        dict: Resposta JSON da API do pfSense.
        
    Exemplo:
        atualizar_mapeamento_statico_dhcp_pfsense(
            parent_id="lan", 
            mapping_id=5, 
            update_data={"descr": "Nova descrição", "cid": "Novo CID"},
            apply=True
        )
    """
    url = f"{config.PFSENSE_API_URL}services/dhcp_server/static_mapping"
    headers = {
        "X-API-Key": config.PFSENSE_API_KEY,
        "Content-Type": "application/json"
    }
    
    # Adicionar ID e parent_id ao payload
    payload = {
        "id": mapping_id,
        "parent_id": parent_id,
        **update_data
    }
    
    # Parâmetros de query para apply
    params = {"apply": apply}
    
    try:
        response = requests.patch(url, json=payload, headers=headers, params=params, timeout=10, verify=False)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Erro ao atualizar mapeamento estático DHCP (parent_id: {parent_id}, mapping_id: {mapping_id}) no pfSense: {e}\nURL: {url}\nHeaders: {headers}\nPayload: {payload}\nParams: {params}")
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"Resposta do pfSense: {e.response.text}")
        raise

def aplicar_mudancas_firewall_pfsense(
    pfsense_url: Optional[str] = None, 
    pfsense_key: Optional[str] = None,
    user_id: Optional[int] = None,
    institution_id: Optional[int] = None
):
    """
    Aplica as mudanças pendentes no firewall do pfSense.
    
    Este endpoint é necessário para efetivar as alterações feitas nos aliases,
    regras de firewall, etc. Equivalente a clicar no botão "Apply Changes" na interface web.
    
    Utiliza a API oficial do pfSense v2:
    POST /api/v2/firewall/apply
    
    Parâmetros:
        pfsense_url (str, opcional): URL base do pfSense (usa config se não fornecido).
        pfsense_key (str, opcional): Chave API do pfSense (usa config se não fornecido).
        user_id (int, opcional): ID do usuário para buscar configurações da instituição.
        institution_id (int, opcional): ID da instituição para buscar configurações.
    
    Retorna:
        dict: Resposta JSON da API do pfSense com informações sobre a aplicação das mudanças.
        
    Raises:
        Exception: Em caso de erro na comunicação com a API do pfSense.
        
    Exemplo:
        resultado = aplicar_mudancas_firewall_pfsense()
        if resultado.get('code') == 200:
            print("Mudanças aplicadas com sucesso!")
    """
    base_url, api_key = _get_pfsense_config(pfsense_url, pfsense_key, user_id, institution_id)
    url = f"{base_url}firewall/apply"
    headers = {
        "X-API-Key": api_key,
        "Content-Type": "application/json"
    }
    
    try:
        logger.info("Aplicando mudanças pendentes no firewall do pfSense...")
        response = requests.post(url, headers=headers, timeout=30, verify=False)
        response.raise_for_status()
        result = response.json()
        logger.info(f"Mudanças aplicadas com sucesso no pfSense: {result}")
        return result
    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
        sync_duration = (datetime.now() - sync_start).total_seconds() if 'sync_start' in locals() else 0
        
        # Log de performance - erro
        try:
            from services_scanners.performance_logger import get_performance_logger
            perf_logger = get_performance_logger()
            perf_logger.log_sync(
                sync_type="FIREWALL_APPLY",
                duration_seconds=sync_duration,
                success=False,
                metadata={
                    'error': str(e),
                    'error_type': 'Timeout/Connection',
                    'endpoint': 'pfsense_client.aplicar_mudancas_firewall_pfsense'
                }
            )
        except:
            pass
        
        logger.error(f"Timeout/Conexão ao aplicar mudanças no firewall do pfSense: {e}")
        raise
    except Exception as e:
        sync_duration = (datetime.now() - sync_start).total_seconds() if 'sync_start' in locals() else 0
        
        # Log de performance - erro
        try:
            from services_scanners.performance_logger import get_performance_logger
            perf_logger = get_performance_logger()
            perf_logger.log_sync(
                sync_type="FIREWALL_APPLY",
                duration_seconds=sync_duration,
                success=False,
                metadata={
                    'error': str(e),
                    'endpoint': 'pfsense_client.aplicar_mudancas_firewall_pfsense'
                }
            )
        except:
            pass
        
        logger.error(f"Erro ao aplicar mudanças no firewall do pfSense: {e}\nURL: {url}\nHeaders: {headers}")
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"Resposta do pfSense: {e.response.text}")
        raise

def aplicar_mudancas_dhcp_pfsense(
    pfsense_url: Optional[str] = None, 
    pfsense_key: Optional[str] = None,
    user_id: Optional[int] = None,
    institution_id: Optional[int] = None
):
    """
    Aplica as mudanças pendentes no servidor DHCP do pfSense.
    
    Este endpoint é necessário para efetivar as alterações feitas nos mapeamentos estáticos DHCP.
    Equivalente a clicar no botão "Apply Changes" após modificar configurações DHCP.
    
    Utiliza a API oficial do pfSense v2:
    POST /api/v2/services/dhcp_server/apply
    
    Parâmetros:
        pfsense_url (str, opcional): URL base do pfSense (usa config se não fornecido).
        pfsense_key (str, opcional): Chave API do pfSense (usa config se não fornecido).
        user_id (int, opcional): ID do usuário para buscar configurações da instituição.
        institution_id (int, opcional): ID da instituição para buscar configurações.
    
    Retorna:
        dict: Resposta JSON da API do pfSense com informações sobre a aplicação das mudanças.
        
    Raises:
        Exception: Em caso de erro na comunicação com a API do pfSense.
        
    Exemplo:
        resultado = aplicar_mudancas_dhcp_pfsense()
        if resultado.get('code') == 200:
            print("Mudanças DHCP aplicadas com sucesso!")
    """
    base_url, api_key = _get_pfsense_config(pfsense_url, pfsense_key, user_id, institution_id)
    url = f"{base_url}services/dhcp_server/apply"
    headers = {
        "X-API-Key": api_key,
        "Content-Type": "application/json"
    }
    
    try:
        logger.info("Aplicando mudanças pendentes no servidor DHCP do pfSense...")
        response = requests.post(url, headers=headers, timeout=30, verify=False)
        response.raise_for_status()
        result = response.json()
        logger.info(f"Mudanças DHCP aplicadas com sucesso no pfSense: {result}")
        return result
    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
        logger.error(f"Timeout/Conexão ao aplicar mudanças DHCP no pfSense: {e}")
        raise
    except Exception as e:
        logger.error(f"Erro ao aplicar mudanças DHCP no pfSense: {e}\nURL: {url}\nHeaders: {headers}")
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"Resposta do pfSense: {e.response.text}")
        raise

