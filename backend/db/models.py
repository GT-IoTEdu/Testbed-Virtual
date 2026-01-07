from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, func, Index, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
try:
    from db.enums import UserPermission, IncidentSeverity, IncidentStatus, ZeekLogType, FeedbackStatus
except ImportError:  # Suporte a execução via `python -m backend.db.*`
    from .enums import UserPermission, IncidentSeverity, IncidentStatus, ZeekLogType, FeedbackStatus
from datetime import datetime

Base = declarative_base()

class User(Base):
    """
    Modelo SQLAlchemy para usuários autenticados via CAFe.
    Utilizado para armazenar informações de login, instituição e nome.
    
    Campos:
        id (int): Chave primária.
        email (str): E-mail do usuário (único).
        nome (str): Nome do usuário.
        instituicao (str): Instituição de origem do usuário.
        permission (str): Nível de permissão (user/manager).
        ultimo_login (datetime): Data/hora do último login.
    """
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    nome = Column(String(255))
    instituicao = Column(String(255))
    google_sub = Column(String(255), unique=True, index=True, nullable=True)
    picture = Column(String(512), nullable=True)
    permission = Column(Enum(UserPermission), default=UserPermission.USER, nullable=False)
    ultimo_login = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relacionamentos
    device_assignments = relationship("UserDeviceAssignment", back_populates="user", foreign_keys="[UserDeviceAssignment.user_id]")

    def __init__(self, email, nome=None, instituicao=None, permission=UserPermission.USER, google_sub=None, picture=None):
        self.email = email
        self.nome = nome
        self.instituicao = instituicao
        self.permission = permission
        self.google_sub = google_sub
        self.picture = picture
    
    def is_manager(self) -> bool:
        """Verifica se o usuário é gestor."""
        return self.permission == UserPermission.MANAGER
    
    def can_manage_device(self, device_user_id: int) -> bool:
        """
        Verifica se o usuário pode gerenciar um dispositivo.
        
        Args:
            device_user_id: ID do usuário proprietário do dispositivo
            
        Returns:
            True se pode gerenciar, False caso contrário
        """
        # Gestores podem gerenciar todos os dispositivos
        if self.is_manager():
            return True
        
        # Usuários comuns só podem gerenciar seus próprios dispositivos
        return self.id == device_user_id

class DhcpServer(Base):
    """
    Modelo SQLAlchemy para servidores DHCP do pfSense.
    Armazena informações dos servidores DHCP configurados.
    
    Campos:
        id (int): Chave primária.
        server_id (str): ID do servidor no pfSense (ex: 'lan', 'wan').
        interface (str): Interface do servidor.
        enable (bool): Se o servidor está habilitado.
        range_from (str): IP inicial do range DHCP.
        range_to (str): IP final do range DHCP.
        domain (str): Domínio do servidor DHCP.
        gateway (str): Gateway padrão.
        dnsserver (str): Servidor DNS.
        created_at (datetime): Data/hora de criação.
        updated_at (datetime): Data/hora da última atualização.
    """
    __tablename__ = 'dhcp_servers'
    id = Column(Integer, primary_key=True, index=True)
    server_id = Column(String(50), unique=True, index=True, nullable=False)
    interface = Column(String(50), nullable=False)
    enable = Column(Boolean, default=True)
    range_from = Column(String(15))
    range_to = Column(String(15))
    domain = Column(String(255))
    gateway = Column(String(15))
    dnsserver = Column(String(15))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relacionamento com mapeamentos estáticos
    static_mappings = relationship("DhcpStaticMapping", back_populates="server", cascade="all, delete-orphan")

class DhcpStaticMapping(Base):
    """
    Modelo SQLAlchemy para mapeamentos estáticos DHCP.
    Armazena informações de dispositivos com IP fixo.
    
    Campos:
        id (int): Chave primária.
        server_id (int): ID do servidor DHCP (chave estrangeira).
        pf_id (int): ID no pfSense.
        mac (str): Endereço MAC do dispositivo.
        ipaddr (str): Endereço IP estático.
        cid (str): Client ID.
        hostname (str): Nome do host.
        descr (str): Descrição do dispositivo.
        is_blocked (bool): Se o dispositivo está bloqueado.
        reason (str): Motivo do bloqueio.
        created_at (datetime): Data/hora de criação.
        updated_at (datetime): Data/hora da última atualização.
    """
    __tablename__ = 'dhcp_static_mappings'
    id = Column(Integer, primary_key=True, index=True)
    server_id = Column(Integer, ForeignKey('dhcp_servers.id'), nullable=False)
    pf_id = Column(Integer, nullable=False)  # ID no pfSense
    mac = Column(String(17), index=True, nullable=False)  # Formato: XX:XX:XX:XX:XX:XX
    ipaddr = Column(String(15), index=True, nullable=False)
    cid = Column(String(255))
    hostname = Column(String(255))
    descr = Column(Text)
    is_blocked = Column(Boolean, default=False, nullable=False)
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relacionamento com servidor DHCP
    server = relationship("DhcpServer", back_populates="static_mappings")
    
    # Relacionamento com usuários
    user_assignments = relationship("UserDeviceAssignment", back_populates="device")
    
    def __repr__(self):
        return f"<DhcpStaticMapping(mac='{self.mac}', ipaddr='{self.ipaddr}', descr='{self.descr}')>"

class UserDeviceAssignment(Base):
    """
    Modelo SQLAlchemy para relacionamento entre usuários e dispositivos DHCP.
    Tabela de associação many-to-many entre User e DhcpStaticMapping.
    
    Campos:
        id (int): Chave primária.
        user_id (int): ID do usuário (chave estrangeira).
        device_id (int): ID do dispositivo DHCP (chave estrangeira).
        assigned_at (datetime): Data/hora da atribuição.
        assigned_by (int): ID do usuário que fez a atribuição (opcional).
        notes (str): Observações sobre a atribuição.
        is_active (bool): Se a atribuição está ativa.
    """
    __tablename__ = 'user_device_assignments'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    device_id = Column(Integer, ForeignKey('dhcp_static_mappings.id'), nullable=False)
    assigned_at = Column(DateTime, default=func.now())
    assigned_by = Column(Integer, ForeignKey('users.id'), nullable=True)  # Quem fez a atribuição
    notes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Relacionamentos
    user = relationship("User", foreign_keys=[user_id], back_populates="device_assignments")
    device = relationship("DhcpStaticMapping", back_populates="user_assignments")
    assigned_by_user = relationship("User", foreign_keys=[assigned_by], overlaps="device_assignments")
    
    # Índice único para evitar duplicatas
    __table_args__ = (
        Index('idx_user_device_unique', 'user_id', 'device_id', unique=True),
    )
    
    def __repr__(self):
        return f"<UserDeviceAssignment(user_id={self.user_id}, device_id={self.device_id}, active={self.is_active})>" 

class PfSenseAlias(Base):
    """Modelo para aliases do pfSense."""
    __tablename__ = "pfsense_aliases"
    
    id = Column(Integer, primary_key=True, index=True)
    pf_id = Column(Integer, unique=True, index=True, comment="ID do alias no pfSense")
    name = Column(String(255), unique=True, index=True, nullable=False, comment="Nome do alias")
    alias_type = Column(String(50), nullable=False, comment="Tipo do alias (host, network, port, url, urltable)")
    descr = Column(Text, comment="Descrição do alias")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class PfSenseAliasAddress(Base):
    """Modelo para endereços dos aliases do pfSense."""
    __tablename__ = "pfsense_alias_addresses"
    
    id = Column(Integer, primary_key=True, index=True)
    alias_id = Column(Integer, ForeignKey("pfsense_aliases.id"), nullable=False)
    address = Column(String(255), nullable=False, comment="Endereço IP, rede ou porta")
    detail = Column(Text, comment="Detalhes do endereço")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relacionamento
    alias = relationship("PfSenseAlias", back_populates="addresses")

# Adicionar relacionamento no modelo PfSenseAlias
PfSenseAlias.addresses = relationship("PfSenseAliasAddress", back_populates="alias", cascade="all, delete-orphan") 

class PfSenseFirewallRule(Base):
    """Modelo para regras de firewall do pfSense."""
    __tablename__ = "pfsense_firewall_rules"

    id = Column(Integer, primary_key=True, index=True)
    pf_id = Column(Integer, unique=True, index=True, nullable=False)
    type = Column(String(32), nullable=True)
    interface = Column(String(255), nullable=True)  # lista como CSV
    ipprotocol = Column(String(16), nullable=True)
    protocol = Column(String(16), nullable=True)
    icmptype = Column(String(64), nullable=True)
    source = Column(String(255), nullable=True)
    source_port = Column(String(64), nullable=True)
    destination = Column(String(255), nullable=True)
    destination_port = Column(String(64), nullable=True)
    descr = Column(Text, nullable=True)
    disabled = Column(Boolean, default=False)
    log = Column(Boolean, default=False)
    tag = Column(String(128), nullable=True)
    statetype = Column(String(64), nullable=True)
    tcp_flags_any = Column(Boolean, default=False)
    tcp_flags_out_of = Column(String(64), nullable=True)
    tcp_flags_set = Column(String(64), nullable=True)
    gateway = Column(String(64), nullable=True)
    sched = Column(String(64), nullable=True)
    dnpipe = Column(String(64), nullable=True)
    pdnpipe = Column(String(64), nullable=True)
    defaultqueue = Column(String(64), nullable=True)
    ackqueue = Column(String(64), nullable=True)
    floating = Column(Boolean, default=False)
    quick = Column(Boolean, default=False)
    direction = Column(String(32), nullable=True)
    tracker = Column(Integer, nullable=True)
    associated_rule_id = Column(Integer, nullable=True)
    created_time = Column(DateTime, nullable=True)
    created_by = Column(String(255), nullable=True)
    updated_time = Column(DateTime, nullable=True)
    updated_by = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class ZeekIncident(Base):
    """
    Modelo SQLAlchemy para incidentes de segurança detectados pelo Zeek.
    Armazena informações sobre incidentes de segurança capturados nos logs.
    
    Campos:
        id (int): Chave primária.
        device_ip (str): IP do dispositivo envolvido no incidente.
        device_name (str): Nome do dispositivo (opcional).
        incident_type (str): Tipo de incidente detectado.
        severity (IncidentSeverity): Nível de severidade do incidente.
        status (IncidentStatus): Status atual do incidente.
        description (str): Descrição detalhada do incidente.
        detected_at (datetime): Quando o incidente foi detectado.
        zeek_log_type (ZeekLogType): Tipo de log do Zeek que gerou o incidente.
        raw_log_data (str): Dados brutos do log em JSON.
        action_taken (str): Ação tomada em resposta ao incidente.
        assigned_to (int): ID do usuário responsável pela investigação.
        notes (str): Observações adicionais sobre o incidente.
        created_at (datetime): Data/hora de criação do registro.
        updated_at (datetime): Data/hora da última atualização.
    """
    __tablename__ = 'zeek_incidents'
    
    id = Column(Integer, primary_key=True, index=True)
    device_ip = Column(String(15), index=True, nullable=False, comment="IP do dispositivo envolvido")
    device_name = Column(String(255), nullable=True, comment="Nome do dispositivo")
    incident_type = Column(String(255), nullable=False, comment="Tipo de incidente")
    severity = Column(Enum(IncidentSeverity), nullable=False, comment="Nível de severidade")
    status = Column(Enum(IncidentStatus), default=IncidentStatus.NEW, nullable=False, comment="Status do incidente")
    description = Column(Text, nullable=False, comment="Descrição detalhada")
    detected_at = Column(DateTime, nullable=False, comment="Data/hora da detecção")
    zeek_log_type = Column(Enum(ZeekLogType), nullable=False, comment="Tipo de log do Zeek")
    raw_log_data = Column(Text, nullable=True, comment="Dados brutos do log em JSON")
    action_taken = Column(Text, nullable=True, comment="Ação tomada")
    assigned_to = Column(Integer, ForeignKey('users.id'), nullable=True, comment="Usuário responsável")
    notes = Column(Text, nullable=True, comment="Observações adicionais")
    created_at = Column(DateTime, default=func.now(), comment="Data de criação")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="Data de atualização")
    
    # Relacionamento com usuário responsável
    assigned_user = relationship("User", foreign_keys=[assigned_to])
    
    # Índices para otimização de consultas
    __table_args__ = (
        Index('idx_incident_device_ip', 'device_ip'),
        Index('idx_incident_severity', 'severity'),
        Index('idx_incident_status', 'status'),
        Index('idx_incident_detected_at', 'detected_at'),
        Index('idx_incident_log_type', 'zeek_log_type'),
        Index('idx_incident_device_severity', 'device_ip', 'severity'),
    )
    
    def __repr__(self):
        return f"<ZeekIncident(id={self.id}, type='{self.incident_type}', severity='{self.severity}', device_ip='{self.device_ip}')>"
    
    def to_dict(self):
        """Converte o incidente para dicionário."""
        return {
            'id': self.id,
            'device_ip': self.device_ip,
            'device_name': self.device_name,
            'incident_type': self.incident_type,
            'severity': self.severity.value if self.severity else None,
            'status': self.status.value if self.status else None,
            'description': self.description,
            'detected_at': self.detected_at.isoformat() if self.detected_at else None,
            'zeek_log_type': self.zeek_log_type.value if self.zeek_log_type else None,
            'action_taken': self.action_taken,
            'assigned_to': self.assigned_to,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

class BlockingFeedbackHistory(Base):
    """
    Modelo SQLAlchemy para histórico de feedback de bloqueio de dispositivos.
    Permite que usuários forneçam feedback sobre resolução de problemas de bloqueio.
    
    Campos:
        id (int): Chave primária.
        dhcp_mapping_id (int): ID do mapeamento DHCP (chave estrangeira).
        user_feedback (str): Feedback detalhado do usuário.
        problem_resolved (bool): Se o problema foi resolvido (NULL = não respondido).
        feedback_date (datetime): Data/hora do feedback.
        feedback_by (str): Nome/identificação do usuário que forneceu o feedback.
        admin_notes (str): Anotações da equipe de rede sobre o feedback.
        admin_review_date (datetime): Data/hora da revisão administrativa.
        admin_reviewed_by (str): Quem revisou o feedback.
        status (FeedbackStatus): Status atual do feedback.
        created_at (datetime): Data/hora de criação.
        updated_at (datetime): Data/hora da última atualização.
    """
    __tablename__ = 'blocking_feedback_history'
    
    id = Column(Integer, primary_key=True, index=True)
    dhcp_mapping_id = Column(Integer, ForeignKey('dhcp_static_mappings.id'), nullable=False, comment="ID do mapeamento DHCP")
    user_feedback = Column(Text, nullable=True, comment="Feedback detalhado do usuário")
    problem_resolved = Column(Boolean, nullable=True, comment="NULL = não respondido, TRUE = resolvido, FALSE = não resolvido")
    feedback_date = Column(DateTime, default=func.now(), comment="Data/hora do feedback")
    feedback_by = Column(String(100), nullable=True, comment="Nome/identificação do usuário que forneceu o feedback")
    admin_notes = Column(Text, nullable=True, comment="Anotações da equipe de rede sobre o feedback")
    admin_review_date = Column(DateTime, nullable=True, comment="Data/hora da revisão administrativa")
    admin_reviewed_by = Column(String(100), nullable=True, comment="Quem revisou o feedback")
    status = Column(Enum(FeedbackStatus), default=FeedbackStatus.PENDING, nullable=False, comment="Status atual do feedback")
    created_at = Column(DateTime, default=func.now(), comment="Data/hora de criação")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="Data/hora da última atualização")
    
    # Relacionamento com mapeamento DHCP
    dhcp_mapping = relationship("DhcpStaticMapping", backref="feedback_history")
    
    # Índices para otimização de consultas
    __table_args__ = (
        Index('idx_feedback_dhcp_mapping', 'dhcp_mapping_id'),
        Index('idx_feedback_status', 'status'),
        Index('idx_feedback_date', 'feedback_date'),
        Index('idx_feedback_by', 'feedback_by'),
        Index('idx_feedback_reviewed_by', 'admin_reviewed_by'),
    )
    
    def __repr__(self):
        return f"<BlockingFeedbackHistory(id={self.id}, dhcp_mapping_id={self.dhcp_mapping_id}, status='{self.status}')>"
    
    def to_dict(self):
        """Converte o feedback para dicionário."""
        return {
            'id': self.id,
            'dhcp_mapping_id': self.dhcp_mapping_id,
            'user_feedback': self.user_feedback,
            'problem_resolved': self.problem_resolved,
            'feedback_date': self.feedback_date.isoformat() if self.feedback_date else None,
            'feedback_by': self.feedback_by,
            'admin_notes': self.admin_notes,
            'admin_review_date': self.admin_review_date.isoformat() if self.admin_review_date else None,
            'admin_reviewed_by': self.admin_reviewed_by,
            'status': self.status.value if self.status else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }