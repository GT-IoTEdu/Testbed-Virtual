"""
Modelos Pydantic para aliases do pfSense.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class AliasAddressInfo(BaseModel):
    """Informações sobre um endereço de alias."""
    address: str = Field(..., description="Endereço IP, rede ou porta")
    detail: Optional[str] = Field(None, description="Detalhes do endereço")

class PfSenseAliasInfo(BaseModel):
    """Informações sobre um alias do pfSense."""
    id: int = Field(..., description="ID do alias no pfSense")
    name: str = Field(..., description="Nome do alias")
    type: str = Field(..., description="Tipo do alias")
    descr: str = Field(..., description="Descrição do alias")
    address: List[str] = Field(..., description="Lista de endereços")
    detail: List[str] = Field(..., description="Lista de detalhes")

class AliasCreateRequest(BaseModel):
    """Modelo para criação de alias."""
    name: str = Field(..., description="Nome do alias")
    alias_type: str = Field(..., description="Tipo do alias (host, network, port, url, urltable)")
    descr: str = Field(..., description="Descrição do alias")
    addresses: List[AliasAddressInfo] = Field(..., description="Lista de endereços")

class AliasUpdateRequest(BaseModel):
    """Modelo para atualização de alias."""
    alias_type: Optional[str] = Field(None, description="Tipo do alias")
    descr: Optional[str] = Field(None, description="Descrição do alias")
    addresses: Optional[List[AliasAddressInfo]] = Field(None, description="Lista de endereços")

class AliasResponse(BaseModel):
    """Resposta de alias."""
    id: int
    pf_id: Optional[int] = Field(None, description="ID do alias no pfSense (pode ser None para aliases locais)")
    name: str
    alias_type: str
    descr: str
    addresses: List[AliasAddressInfo]
    created_at: datetime
    updated_at: datetime

class AliasListResponse(BaseModel):
    """Resposta de listagem de aliases."""
    aliases: List[AliasResponse]
    total: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool

class AliasStatisticsResponse(BaseModel):
    """Estatísticas de aliases."""
    total_aliases: int
    aliases_by_type: dict
    total_addresses: int
    created_today: int
    updated_today: int

class AliasSaveResponse(BaseModel):
    """Resposta de salvamento de aliases."""
    status: str
    aliases_saved: int
    aliases_updated: int
    addresses_saved: int
    addresses_updated: int
    timestamp: datetime
    pfsense_saved: bool
    pfsense_message: str

class AliasAddAddressesRequest(BaseModel):
    """Modelo para adicionar endereços a um alias existente."""
    addresses: List[AliasAddressInfo] = Field(..., description="Lista de novos endereços para adicionar")
