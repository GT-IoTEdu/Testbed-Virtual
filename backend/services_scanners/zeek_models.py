"""
Modelos de dados para integração com Zeek Network Security Monitor
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class ZeekLogType(str, Enum):
    """Tipos de logs disponíveis no Zeek"""
    HTTP = "http.log"
    DNS = "dns.log"
    CONN = "conn.log"
    SSL = "ssl.log"
    FILES = "files.log"
    WEIRD = "weird.log"
    NOTICE = "notice.log"


class ZeekSeverity(str, Enum):
    """Níveis de severidade para ocorrências"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ZeekIncidentStatus(str, Enum):
    """Status de uma ocorrência"""
    NEW = "new"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    FALSE_POSITIVE = "false_positive"


class ZeekHttpLog(BaseModel):
    """Modelo para logs HTTP do Zeek"""
    ts: float = Field(description="Timestamp do evento")
    uid: str = Field(description="Unique identifier da conexão")
    id_orig_h: str = Field(description="IP de origem")
    id_orig_p: int = Field(description="Porta de origem")
    id_resp_h: str = Field(description="IP de destino")
    id_resp_p: int = Field(description="Porta de destino")
    trans_depth: Optional[int] = Field(default=None, description="Profundidade da transação")
    method: Optional[str] = Field(default=None, description="Método HTTP")
    host: Optional[str] = Field(default=None, description="Host HTTP")
    uri: Optional[str] = Field(default=None, description="URI solicitada")
    referrer: Optional[str] = Field(default=None, description="Referrer HTTP")
    version: Optional[str] = Field(default=None, description="Versão HTTP")
    user_agent: Optional[str] = Field(default=None, description="User Agent")
    origin: Optional[str] = Field(default=None, description="Origin header")
    request_body_len: Optional[int] = Field(default=None, description="Tamanho do corpo da requisição")
    response_body_len: Optional[int] = Field(default=None, description="Tamanho do corpo da resposta")
    status_code: Optional[int] = Field(default=None, description="Código de status HTTP")
    status_msg: Optional[str] = Field(default=None, description="Mensagem de status HTTP")
    info_code: Optional[int] = Field(default=None, description="Código de informação")
    info_msg: Optional[str] = Field(default=None, description="Mensagem de informação")
    tags: Optional[List[str]] = Field(default=None, description="Tags associadas")
    username: Optional[str] = Field(default=None, description="Nome de usuário")
    password: Optional[str] = Field(default=None, description="Senha")
    proxied: Optional[List[str]] = Field(default=None, description="Proxies utilizados")
    orig_fuids: Optional[List[str]] = Field(default=None, description="File UIDs originais")
    orig_filenames: Optional[List[str]] = Field(default=None, description="Nomes de arquivo originais")
    orig_mime_types: Optional[List[str]] = Field(default=None, description="Tipos MIME originais")
    resp_fuids: Optional[List[str]] = Field(default=None, description="File UIDs de resposta")
    resp_filenames: Optional[List[str]] = Field(default=None, description="Nomes de arquivo de resposta")
    resp_mime_types: Optional[List[str]] = Field(default=None, description="Tipos MIME de resposta")


class ZeekDnsLog(BaseModel):
    """Modelo para logs DNS do Zeek"""
    ts: float = Field(description="Timestamp do evento")
    uid: str = Field(description="Unique identifier da conexão")
    id_orig_h: str = Field(description="IP de origem")
    id_orig_p: int = Field(description="Porta de origem")
    id_resp_h: str = Field(description="IP de destino")
    id_resp_p: int = Field(description="Porta de destino")
    proto: str = Field(description="Protocolo (tcp/udp)")
    trans_id: Optional[int] = Field(default=None, description="ID da transação DNS")
    rtt: Optional[float] = Field(default=None, description="Round trip time")
    query: Optional[str] = Field(default=None, description="Query DNS")
    qclass: Optional[int] = Field(default=None, description="Classe da query")
    qclass_name: Optional[str] = Field(default=None, description="Nome da classe")
    qtype: Optional[int] = Field(default=None, description="Tipo da query")
    qtype_name: Optional[str] = Field(default=None, description="Nome do tipo")
    rcode: Optional[int] = Field(default=None, description="Response code")
    rcode_name: Optional[str] = Field(default=None, description="Nome do response code")
    AA: Optional[bool] = Field(default=None, description="Authoritative Answer")
    TC: Optional[bool] = Field(default=None, description="Truncated")
    RD: Optional[bool] = Field(default=None, description="Recursion Desired")
    RA: Optional[bool] = Field(default=None, description="Recursion Available")
    Z: Optional[int] = Field(default=None, description="Reserved field")
    answers: Optional[List[str]] = Field(default=None, description="Respostas DNS")
    TTLs: Optional[List[float]] = Field(default=None, description="Time to Live das respostas")
    rejected: Optional[bool] = Field(default=None, description="Query rejeitada")


class ZeekConnLog(BaseModel):
    """Modelo para logs de conexão do Zeek"""
    ts: float = Field(description="Timestamp do evento")
    uid: str = Field(description="Unique identifier da conexão")
    id_orig_h: str = Field(description="IP de origem")
    id_orig_p: int = Field(description="Porta de origem")
    id_resp_h: str = Field(description="IP de destino")
    id_resp_p: int = Field(description="Porta de destino")
    proto: str = Field(description="Protocolo")
    service: Optional[str] = Field(default=None, description="Serviço detectado")
    duration: Optional[float] = Field(default=None, description="Duração da conexão")
    orig_bytes: Optional[int] = Field(default=None, description="Bytes enviados pelo originador")
    resp_bytes: Optional[int] = Field(default=None, description="Bytes enviados pelo respondedor")
    conn_state: Optional[str] = Field(default=None, description="Estado da conexão")
    local_orig: Optional[bool] = Field(default=None, description="Originador é local")
    local_resp: Optional[bool] = Field(default=None, description="Respondedor é local")
    missed_bytes: Optional[int] = Field(default=None, description="Bytes perdidos")
    history: Optional[str] = Field(default=None, description="Histórico da conexão")
    orig_pkts: Optional[int] = Field(default=None, description="Pacotes do originador")
    orig_ip_bytes: Optional[int] = Field(default=None, description="Bytes IP do originador")
    resp_pkts: Optional[int] = Field(default=None, description="Pacotes do respondedor")
    resp_ip_bytes: Optional[int] = Field(default=None, description="Bytes IP do respondedor")
    tunnel_parents: Optional[List[str]] = Field(default=None, description="Túneis pais")


class ZeekIncident(BaseModel):
    """Modelo para uma ocorrência/incidente baseado em logs do Zeek"""
    id: Optional[int] = Field(default=None, description="ID único do incidente")
    device_name: Optional[str] = Field(default=None, description="Nome do dispositivo")
    device_ip: str = Field(description="IP do dispositivo envolvido")
    incident_type: str = Field(description="Tipo de ocorrência")
    severity: ZeekSeverity = Field(description="Severidade do incidente")
    action_taken: Optional[str] = Field(default=None, description="Ação tomada")
    description: str = Field(description="Descrição detalhada")
    detected_at: datetime = Field(description="Quando foi detectado")
    status: ZeekIncidentStatus = Field(default=ZeekIncidentStatus.NEW, description="Status atual")
    raw_log_data: Optional[Dict[str, Any]] = Field(default=None, description="Dados brutos do log")
    zeek_log_type: ZeekLogType = Field(description="Tipo de log do Zeek")
    created_at: Optional[datetime] = Field(default=None, description="Quando foi criado no sistema")
    updated_at: Optional[datetime] = Field(default=None, description="Última atualização")


class ZeekLogRequest(BaseModel):
    """Modelo para requisições de logs do Zeek"""
    logfile: ZeekLogType = Field(description="Tipo de log a ser consultado")
    maxlines: int = Field(default=10, ge=1, le=1000, description="Número máximo de linhas")
    filter_ip: Optional[str] = Field(default=None, description="Filtrar por IP específico")
    start_time: Optional[datetime] = Field(default=None, description="Timestamp inicial")
    end_time: Optional[datetime] = Field(default=None, description="Timestamp final")


class ZeekLogResponse(BaseModel):
    """Modelo para resposta de logs do Zeek"""
    success: bool = Field(description="Se a requisição foi bem-sucedida")
    message: Optional[str] = Field(default=None, description="Mensagem de erro ou sucesso")
    log_type: ZeekLogType = Field(description="Tipo de log retornado")
    total_lines: int = Field(description="Total de linhas retornadas")
    logs: List[Dict[str, Any]] = Field(description="Lista de logs")
    incidents: List[ZeekIncident] = Field(default=[], description="Incidentes detectados")
