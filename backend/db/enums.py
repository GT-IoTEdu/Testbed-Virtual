"""
Enums para o sistema de permissões e tipos de dados.
"""
from enum import Enum

class UserPermission(str, Enum):
    """Tipos de permissão de usuário."""
    USER = "USER"        # Usuário comum - pode gerenciar apenas seus dispositivos
    MANAGER = "MANAGER"  # Gestor - pode gerenciar todos os dispositivos

class DeviceStatus(str, Enum):
    """Status de dispositivos."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"

class IncidentSeverity(str, Enum):
    """Níveis de severidade para incidentes."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class IncidentStatus(str, Enum):
    """Status de incidentes."""
    NEW = "new"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    FALSE_POSITIVE = "false_positive"
    ESCALATED = "escalated"

class ZeekLogType(str, Enum):
    """Tipos de logs do Zeek."""
    HTTP = "http.log"
    DNS = "dns.log"
    CONN = "conn.log"
    SSL = "ssl.log"
    FILES = "files.log"
    WEIRD = "weird.log"
    NOTICE = "notice.log"

class FeedbackStatus(str, Enum):
    """Status do feedback de bloqueio."""
    PENDING = "pending"
    REVIEWED = "reviewed"
    ACTION_REQUIRED = "action_required"