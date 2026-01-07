from __future__ import annotations
"""
Modelos Pydantic para endpoints de DHCP.

Este módulo define os modelos de dados para:
- Requisições de busca de dispositivos
- Respostas de dispositivos DHCP
- Estatísticas de dispositivos
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from db.enums import UserPermission

class DeviceSearchRequest(BaseModel):
    """Modelo para requisição de busca de dispositivos."""
    query: str = Field(..., description="Termo de busca (IP, MAC, descrição ou hostname)")
    server_id: Optional[str] = Field(None, description="ID do servidor DHCP (opcional)")

class DeviceResponse(BaseModel):
    """Modelo para resposta de dispositivo DHCP."""
    id: int
    server_id: int
    pf_id: int
    mac: str
    ipaddr: str
    cid: Optional[str]
    hostname: Optional[str]
    descr: Optional[str]
    created_at: datetime
    updated_at: datetime
    # Usuários atribuídos (ativos) a este dispositivo
    assigned_users: List['UserResponse'] = Field(default_factory=list)
    # Status de acesso (LIBERADO, BLOQUEADO, DESCONHECIDO)
    status_acesso: Optional[str] = Field(None, description="Status de acesso baseado em alias e regra de firewall")

    class Config:
        from_attributes = True

class ServerResponse(BaseModel):
    """Modelo para resposta de servidor DHCP."""
    id: int
    server_id: str
    interface: str
    enable: bool
    range_from: Optional[str]
    range_to: Optional[str]
    domain: Optional[str]
    gateway: Optional[str]
    dnsserver: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class DeviceStatisticsResponse(BaseModel):
    """Modelo para resposta de estatísticas de dispositivos."""
    total_devices: int
    total_servers: int
    devices_by_server: Dict[str, int]
    last_update: str

class SaveDhcpResponse(BaseModel):
    """Modelo para resposta de salvamento de dados DHCP."""
    status: str
    servers_saved: int
    mappings_saved: int
    mappings_updated: int
    timestamp: str
    pfsense_saved: Optional[bool] = None
    pfsense_message: Optional[str] = None
    pfsense_id: Optional[int] = None

class DeviceSearchResponse(BaseModel):
    """Modelo para resposta de busca de dispositivos."""
    devices: List[DeviceResponse]
    total_found: int
    query: str

class DeviceDetailResponse(BaseModel):
    """Modelo para resposta detalhada de dispositivo."""
    device: DeviceResponse
    server: ServerResponse
    is_duplicate: bool = Field(False, description="Se o dispositivo tem duplicatas (mesmo IP ou MAC)")
    duplicates: List[DeviceResponse] = Field(default_factory=list, description="Lista de dispositivos duplicados")

class BulkDeviceResponse(BaseModel):
    """Modelo para resposta de múltiplos dispositivos."""
    devices: List[DeviceResponse]
    total: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool

class UserResponse(BaseModel):
    """Modelo para resposta de usuário."""
    id: int
    email: str
    nome: Optional[str]
    instituicao: Optional[str]
    permission: Optional[UserPermission]
    ultimo_login: Optional[datetime]

    class Config:
        from_attributes = True

class DeviceAssignmentRequest(BaseModel):
    """Modelo para requisição de atribuição de dispositivo."""
    user_id: int = Field(..., description="ID do usuário")
    device_id: int = Field(..., description="ID do dispositivo")
    notes: Optional[str] = Field(None, description="Observações sobre a atribuição")
    assigned_by: Optional[int] = Field(None, description="ID do usuário que está fazendo a atribuição")

class DeviceAssignmentResponse(BaseModel):
    """Modelo para resposta de atribuição de dispositivo."""
    id: int
    user_id: int
    device_id: int
    assigned_at: datetime
    assigned_by: Optional[int]
    notes: Optional[str]
    is_active: bool
    user: UserResponse
    device: DeviceResponse

    class Config:
        from_attributes = True

class UserDevicesResponse(BaseModel):
    """Modelo para resposta de dispositivos de um usuário."""
    user: UserResponse
    devices: List[DeviceResponse]
    total_devices: int
    active_assignments: int

class DeviceUsersResponse(BaseModel):
    """Modelo para resposta de usuários de um dispositivo."""
    device: DeviceResponse
    users: List[UserResponse]
    total_users: int
    active_assignments: int

class AssignmentStatisticsResponse(BaseModel):
    """Modelo para resposta de estatísticas de atribuições."""
    total_assignments: int
    active_assignments: int
    inactive_assignments: int
    users_with_devices: int
    devices_with_users: int
    assignments_by_institution: Dict[str, int]

class DeviceBlockRequest(BaseModel):
    """Modelo para requisição de bloqueio de dispositivo."""
    device_id: int = Field(..., description="ID do dispositivo no banco de dados")
    reason: str = Field(..., min_length=5, max_length=500, description="Motivo do bloqueio (5-500 caracteres)")
    reason_by: Optional[str] = Field(None, max_length=100, description="Nome do administrador que está bloqueando")

class DeviceUnblockRequest(BaseModel):
    """Modelo para requisição de liberação de dispositivo."""
    device_id: int = Field(..., description="ID do dispositivo no banco de dados")

class DeviceBlockResponse(BaseModel):
    """Modelo para resposta de bloqueio/liberação de dispositivo."""
    success: bool
    message: str
    device_id: int
    is_blocked: bool
    reason: Optional[str] = None
    updated_at: Optional[datetime] = None

class DhcpSaveRequest(BaseModel):
    """Modelo para requisição de salvamento de dados DHCP com parâmetros do usuário."""
    mac: str = Field(..., description="Endereço MAC do dispositivo")
    ipaddr: Optional[str] = Field(None, description="Endereço IP do dispositivo (opcional se auto_assign_ip=True)")
    cid: str = Field(..., description="ID do cliente (será replicado para hostname)")
    descr: str = Field(..., description="Descrição do dispositivo")
    auto_assign_ip: Optional[bool] = Field(False, description="Se True, atribui IP automaticamente")

class DhcpStaticMappingCreateRequest(BaseModel):
    """Modelo para criação de mapeamento estático DHCP no pfSense."""
    parent_id: str = Field("lan", description="ID do servidor DHCP pai (padrão: lan)")
    mac: str = Field(..., description="Endereço MAC do dispositivo")
    ipaddr: str = Field(..., description="Endereço IP do dispositivo")
    cid: str = Field(..., description="ID do cliente")
    hostname: Optional[str] = Field(None, description="Nome do host")
    domain: Optional[str] = Field(None, description="Domínio")
    domainsearchlist: Optional[List[str]] = Field(None, description="Lista de domínios para busca")
    defaultleasetime: Optional[int] = Field(7200, description="Tempo de lease padrão em segundos")
    maxleasetime: Optional[int] = Field(86400, description="Tempo máximo de lease em segundos")
    gateway: Optional[str] = Field(None, description="Gateway")
    dnsserver: Optional[List[str]] = Field(None, description="Servidores DNS")
    winsserver: Optional[List[str]] = Field(None, description="Servidores WINS")
    ntpserver: Optional[List[str]] = Field(None, description="Servidores NTP")
    arp_table_static_entry: Optional[bool] = Field(True, description="Entrada estática na tabela ARP")
    descr: Optional[str] = Field(None, description="Descrição do dispositivo")

class DhcpStaticMappingCreateResponse(BaseModel):
    """Resposta de criação de mapeamento estático DHCP."""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None

class DhcpStaticMappingDeleteResponse(BaseModel):
    """Resposta de exclusão de mapeamento estático DHCP."""
    success: bool
    message: str
    parent_id: str
    mapping_id: int
    applied: bool
    local_deleted: bool = Field(False, description="Se o registro foi excluído do banco de dados local")
    data: Optional[Dict[str, Any]] = None

class DhcpStaticMappingUpdateRequest(BaseModel):
    """Modelo para atualização de mapeamento estático DHCP no pfSense."""
    mac: Optional[str] = Field(None, description="Endereço MAC do dispositivo")
    ipaddr: Optional[str] = Field(None, description="Endereço IP do dispositivo")
    cid: Optional[str] = Field(None, description="ID do cliente")
    hostname: Optional[str] = Field(None, description="Nome do host")
    domain: Optional[str] = Field(None, description="Domínio")
    domainsearchlist: Optional[List[str]] = Field(None, description="Lista de domínios para busca")
    defaultleasetime: Optional[int] = Field(None, description="Tempo de lease padrão em segundos")
    maxleasetime: Optional[int] = Field(None, description="Tempo máximo de lease em segundos")
    gateway: Optional[str] = Field(None, description="Gateway")
    dnsserver: Optional[List[str]] = Field(None, description="Servidores DNS")
    winsserver: Optional[List[str]] = Field(None, description="Servidores WINS")
    ntpserver: Optional[List[str]] = Field(None, description="Servidores NTP")
    arp_table_static_entry: Optional[bool] = Field(None, description="Entrada estática na tabela ARP")
    descr: Optional[str] = Field(None, description="Descrição do dispositivo")

class DhcpStaticMappingUpdateResponse(BaseModel):
    """Resposta de atualização de mapeamento estático DHCP."""
    success: bool
    message: str
    parent_id: str
    mapping_id: int
    applied: bool
    local_updated: bool = Field(False, description="Se o registro foi atualizado no banco de dados local")
    data: Optional[Dict[str, Any]] = None

class IpAddressInfo(BaseModel):
    """Informações sobre um endereço IP."""
    ip: str
    status: str  # "used", "free", "reserved"
    mac: Optional[str] = None
    hostname: Optional[str] = None
    description: Optional[str] = None
    last_seen: Optional[str] = None

class DhcpRangeInfo(BaseModel):
    """Informações sobre o range DHCP."""
    server_id: str
    interface: str
    range_from: str
    range_to: str
    total_ips: int
    used_ips: int
    free_ips: int
    reserved_ips: int

class IpAddressListResponse(BaseModel):
    """Resposta de listagem de endereços IP."""
    range_info: DhcpRangeInfo
    ip_addresses: List[IpAddressInfo]
    summary: Dict[str, int]

class AllDevicesResponse(BaseModel):
    """Modelo para resposta de todos os dispositivos do sistema."""
    devices: List[DeviceResponse]
    total_devices: int
    online_devices: int
    offline_devices: int
    assigned_devices: int
    unassigned_devices: int
