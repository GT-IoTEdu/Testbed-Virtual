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
    institution_id = Column(Integer, ForeignKey('institutions.id'), nullable=True, comment="ID da instituição/campus que o usuário gerencia")
    google_sub = Column(String(255), unique=True, index=True, nullable=True)
    picture = Column(String(512), nullable=True)
    permission = Column(Enum(UserPermission), default=UserPermission.USER, nullable=False)
    ultimo_login = Column(DateTime, default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True, nullable=False, comment="Indica se o usuário está ativo no sistema")

    # Relacionamentos
    device_assignments = relationship("UserDeviceAssignment", back_populates="user", foreign_keys="[UserDeviceAssignment.user_id]")
    institution = relationship("Institution", back_populates="managers")

    def __init__(self, email, nome=None, instituicao=None, permission=UserPermission.USER, google_sub=None, picture=None, is_active=True):
        self.email = email
        self.nome = nome
        self.instituicao = instituicao
        self.permission = permission
        self.google_sub = google_sub
        self.picture = picture
        self.is_active = is_active
    
    def is_manager(self) -> bool:
        """Verifica se o usuário é administrador (gestor de instituição)."""
        return self.permission == UserPermission.ADMIN
    
    def is_admin(self) -> bool:
        """Verifica se o usuário é superusuário (administrador do sistema)."""
        return self.permission == UserPermission.SUPERUSER
    
    def is_superuser(self) -> bool:
        """Verifica se o usuário é superusuário."""
        return self.permission == UserPermission.SUPERUSER
    
    def is_active_user(self) -> bool:
        """Verifica se o usuário está ativo no sistema."""
        return self.is_active
    
    def activate(self) -> None:
        """Ativa o usuário no sistema."""
        self.is_active = True
    
    def deactivate(self) -> None:
        """Desativa o usuário no sistema."""
        self.is_active = False
    
    def toggle_active_status(self) -> bool:
        """Alterna o status de ativação do usuário."""
        self.is_active = not self.is_active
        return self.is_active
    
    def to_dict(self):
        """Converte o usuário para dicionário."""
        return {
            'id': self.id,
            'email': self.email,
            'nome': self.nome,
            'instituicao': self.instituicao,
            'permission': self.permission.value if self.permission else None,
            'ultimo_login': self.ultimo_login.isoformat() if self.ultimo_login else None,
            'is_active': self.is_active,
            'google_sub': self.google_sub,
            'picture': self.picture,
            'is_admin': self.is_admin(),
            'is_manager': self.is_manager(),
            'is_user': self.permission == UserPermission.USER,
            'is_active_user': self.is_active_user()
        }
    
    def can_manage_device(self, device_user_id: int) -> bool:
        """
        Verifica se o usuário pode gerenciar um dispositivo.
        
        Args:
            device_user_id: ID do usuário proprietário do dispositivo
            
        Returns:
            True se pode gerenciar, False caso contrário
        """
        # Administradores e gestores podem gerenciar todos os dispositivos
        if self.is_admin_or_manager():
            return True
        
        # Usuários comuns só podem gerenciar seus próprios dispositivos
        return self.id == device_user_id
    
    def can_manage_user_permissions(self) -> bool:
        """
        Verifica se o usuário pode gerenciar permissões de outros usuários.
        
        Returns:
            True se pode gerenciar permissões, False caso contrário
        """
        return self.is_admin()
    
    def can_promote_user(self, target_user: 'User') -> bool:
        """
        Verifica se o usuário pode promover outro usuário.
        
        Args:
            target_user: Usuário que será promovido
            
        Returns:
            True se pode promover, False caso contrário
        """
        # Apenas administradores podem promover usuários
        if not self.is_admin():
            return False
        
        # Não pode promover outro administrador
        if target_user.is_admin():
            return False
        
        # Não pode promover a si mesmo
        if self.id == target_user.id:
            return False
        
        return True
    
    def can_demote_user(self, target_user: 'User') -> bool:
        """
        Verifica se o usuário pode rebaixar outro usuário.
        
        Args:
            target_user: Usuário que será rebaixado
            
        Returns:
            True se pode rebaixar, False caso contrário
        """
        # Apenas administradores podem rebaixar usuários
        if not self.is_admin():
            return False
        
        # Não pode rebaixar outro administrador
        if target_user.is_admin():
            return False
        
        # Não pode rebaixar a si mesmo
        if self.id == target_user.id:
            return False
        
        return True

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
        institution_id (int): ID da instituição/campus (chave estrangeira).
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
    institution_id = Column(Integer, ForeignKey('institutions.id'), nullable=True, index=True, comment="ID da instituição/campus ao qual o dispositivo pertence")
    is_blocked = Column(Boolean, default=False, nullable=False)
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relacionamento com servidor DHCP
    server = relationship("DhcpServer", back_populates="static_mappings")
    
    # Relacionamento com instituição
    institution = relationship("Institution", foreign_keys=[institution_id])
    
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
    pf_id = Column(Integer, index=True, comment="ID do alias no pfSense")
    name = Column(String(255), index=True, nullable=False, comment="Nome do alias")
    alias_type = Column(String(50), nullable=False, comment="Tipo do alias (host, network, port, url, urltable)")
    descr = Column(Text, comment="Descrição do alias")
    institution_id = Column(Integer, ForeignKey('institutions.id'), nullable=True, index=True, comment="ID da instituição/campus ao qual o alias pertence")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamento com instituição
    institution = relationship("Institution", foreign_keys=[institution_id])
    
    # Índice único composto para permitir mesmo nome em instituições diferentes
    __table_args__ = (
        Index('idx_alias_name_institution_unique', 'name', 'institution_id', unique=True),
    )

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
    pf_id = Column(Integer, index=True, nullable=False)
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
    institution_id = Column(Integer, ForeignKey('institutions.id'), nullable=True, index=True, comment="ID da instituição/campus ao qual a regra pertence")
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Índice único composto: pf_id + institution_id (permite mesmo pf_id em diferentes instituições)
    __table_args__ = (
        Index('idx_pf_id_institution_unique', 'pf_id', 'institution_id', unique=True),
    )
    
    # Relacionamento
    institution = relationship("Institution", foreign_keys=[institution_id])

class Incident(Base):
    """
    Modelo SQLAlchemy para incidentes de segurança.
    Armazena informações sobre incidentes capturados (ex.: origem Zeek, workflow de resolução).
    
    Campos:
        id (int): Chave primária.
        device_ip (str): IP do dispositivo envolvido no incidente.
        device_name (str): Nome do dispositivo (opcional).
        incident_type (str): Tipo de incidente detectado.
        severity (IncidentSeverity): Nível de severidade do incidente.
        status (IncidentStatus): Status atual do incidente.
        description (str): Descrição detalhada do incidente.
        detected_at (datetime): Quando o incidente foi detectado.
        zeek_log_type (ZeekLogType): Tipo de log que gerou o incidente.
        raw_log_data (str): Dados brutos do log em JSON.
        action_taken (str): Ação tomada em resposta ao incidente.
        assigned_to (int): ID do usuário responsável pela investigação.
        notes (str): Observações adicionais sobre o incidente.
        created_at (datetime): Data/hora de criação do registro.
        updated_at (datetime): Data/hora da última atualização.
    """
    __tablename__ = 'incidents'

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
    processed_at = Column(DateTime, nullable=True, comment="Data/hora quando foi processado para bloqueio automático")
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
        Index('idx_incident_processed_at', 'processed_at'),
    )
    
    def __repr__(self):
        return f"<Incident(id={self.id}, type='{self.incident_type}', severity='{self.severity}', device_ip='{self.device_ip}')>"

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
            'processed_at': self.processed_at.isoformat() if self.processed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


# Alias para compatibilidade com código legado
ZeekIncident = Incident


class SuricataAlert(Base):
    """
    Modelo SQLAlchemy para alertas do Suricata IDS/IPS.
    Armazena os logs/alertas recebidos via SSE do Suricata por instituição.
    """
    __tablename__ = 'suricata_alerts'

    id = Column(Integer, primary_key=True, index=True)
    institution_id = Column(Integer, ForeignKey('institutions.id'), nullable=False, index=True, comment="ID da instituição à qual o alerta pertence")
    detected_at = Column(DateTime, nullable=False, comment="Data/hora da detecção (timestamp do Suricata)")
    signature = Column(String(500), nullable=False, comment="Assinatura/mensagem do alerta")
    signature_id = Column(String(50), nullable=True, comment="SID da regra Suricata")
    severity = Column(Enum(IncidentSeverity), nullable=False, default=IncidentSeverity.MEDIUM, comment="Severidade do alerta")
    src_ip = Column(String(45), nullable=True, comment="IP de origem")
    dest_ip = Column(String(45), nullable=True, comment="IP de destino")
    src_port = Column(String(20), nullable=True, comment="Porta de origem")
    dest_port = Column(String(20), nullable=True, comment="Porta de destino")
    protocol = Column(String(20), nullable=True, comment="Protocolo (TCP, UDP, etc.)")
    category = Column(String(255), nullable=True, comment="Categoria do alerta")
    raw_log_data = Column(Text, nullable=True, comment="Dados brutos do alerta em JSON")
    processed_at = Column(DateTime, nullable=True, comment="Data/hora em que foi processado para bloqueio automático")
    created_at = Column(DateTime, default=func.now(), comment="Data/hora de inserção no banco")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="Data/hora da última atualização")

    institution = relationship("Institution", foreign_keys=[institution_id])

    __table_args__ = (
        Index('idx_suricata_alerts_institution_id', 'institution_id'),
        Index('idx_suricata_alerts_detected_at', 'detected_at'),
        Index('idx_suricata_alerts_severity', 'severity'),
        Index('idx_suricata_alerts_src_ip', 'src_ip'),
        Index('idx_suricata_alerts_dest_ip', 'dest_ip'),
        Index('idx_suricata_alerts_processed_at', 'processed_at'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'institution_id': self.institution_id,
            'detected_at': self.detected_at.isoformat() if self.detected_at else None,
            'signature': self.signature,
            'signature_id': self.signature_id,
            'severity': self.severity.value if self.severity else None,
            'src_ip': self.src_ip,
            'dest_ip': self.dest_ip,
            'src_port': self.src_port,
            'dest_port': self.dest_port,
            'protocol': self.protocol,
            'category': self.category,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class SnortAlert(Base):
    """
    Modelo SQLAlchemy para alertas do Snort IDS/IPS.
    Armazena os logs/alertas recebidos via SSE do Snort por instituição.
    """
    __tablename__ = 'snort_alerts'

    id = Column(Integer, primary_key=True, index=True)
    institution_id = Column(Integer, ForeignKey('institutions.id'), nullable=False, index=True, comment="ID da instituição à qual o alerta pertence")
    detected_at = Column(DateTime, nullable=False, comment="Data/hora da detecção (timestamp do Snort)")
    signature = Column(String(500), nullable=False, comment="Assinatura/mensagem do alerta")
    signature_id = Column(String(50), nullable=True, comment="SID da regra Snort")
    severity = Column(Enum(IncidentSeverity), nullable=False, default=IncidentSeverity.MEDIUM, comment="Severidade do alerta")
    src_ip = Column(String(45), nullable=True, comment="IP de origem")
    dest_ip = Column(String(45), nullable=True, comment="IP de destino")
    src_port = Column(String(20), nullable=True, comment="Porta de origem")
    dest_port = Column(String(20), nullable=True, comment="Porta de destino")
    protocol = Column(String(20), nullable=True, comment="Protocolo (TCP, UDP, etc.)")
    category = Column(String(255), nullable=True, comment="Categoria do alerta")
    raw_log_data = Column(Text, nullable=True, comment="Dados brutos do alerta em JSON")
    processed_at = Column(DateTime, nullable=True, comment="Data/hora em que foi processado para bloqueio automático")
    created_at = Column(DateTime, default=func.now(), comment="Data/hora de inserção no banco")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="Data/hora da última atualização")

    institution = relationship("Institution", foreign_keys=[institution_id])

    __table_args__ = (
        Index('idx_snort_alerts_institution_id', 'institution_id'),
        Index('idx_snort_alerts_detected_at', 'detected_at'),
        Index('idx_snort_alerts_severity', 'severity'),
        Index('idx_snort_alerts_src_ip', 'src_ip'),
        Index('idx_snort_alerts_dest_ip', 'dest_ip'),
        Index('idx_snort_alerts_processed_at', 'processed_at'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'institution_id': self.institution_id,
            'detected_at': self.detected_at.isoformat() if self.detected_at else None,
            'signature': self.signature,
            'signature_id': self.signature_id,
            'severity': self.severity.value if self.severity else None,
            'src_ip': self.src_ip,
            'dest_ip': self.dest_ip,
            'src_port': self.src_port,
            'dest_port': self.dest_port,
            'protocol': self.protocol,
            'category': self.category,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class ZeekAlert(Base):
    """
    Modelo SQLAlchemy para alertas do Zeek NSM.
    Mesma estrutura que SuricataAlert/SnortAlert: institution_id, signature, src_ip, etc.
    """
    __tablename__ = 'zeek_alerts'

    id = Column(Integer, primary_key=True, index=True)
    institution_id = Column(Integer, ForeignKey('institutions.id'), nullable=False, index=True, comment="ID da instituição")
    detected_at = Column(DateTime, nullable=False, comment="Data/hora da detecção")
    signature = Column(String(500), nullable=False, comment="Assinatura/mensagem do alerta")
    signature_id = Column(String(50), nullable=True, comment="ID da assinatura/regra")
    severity = Column(Enum(IncidentSeverity), nullable=False, default=IncidentSeverity.MEDIUM, comment="Severidade")
    src_ip = Column(String(45), nullable=True, comment="IP de origem")
    dest_ip = Column(String(45), nullable=True, comment="IP de destino")
    src_port = Column(String(20), nullable=True, comment="Porta de origem")
    dest_port = Column(String(20), nullable=True, comment="Porta de destino")
    protocol = Column(String(20), nullable=True, comment="Protocolo")
    category = Column(String(255), nullable=True, comment="Categoria")
    raw_log_data = Column(Text, nullable=True, comment="Dados brutos em JSON")
    processed_at = Column(DateTime, nullable=True, comment="Processado para bloqueio automático")
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    institution = relationship("Institution", foreign_keys=[institution_id])

    __table_args__ = (
        Index('idx_zeek_alerts_institution_id', 'institution_id'),
        Index('idx_zeek_alerts_detected_at', 'detected_at'),
        Index('idx_zeek_alerts_severity', 'severity'),
        Index('idx_zeek_alerts_src_ip', 'src_ip'),
        Index('idx_zeek_alerts_dest_ip', 'dest_ip'),
        Index('idx_zeek_alerts_processed_at', 'processed_at'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'institution_id': self.institution_id,
            'detected_at': self.detected_at.isoformat() if self.detected_at else None,
            'signature': self.signature,
            'signature_id': self.signature_id,
            'severity': self.severity.value if self.severity else None,
            'src_ip': self.src_ip,
            'dest_ip': self.dest_ip,
            'src_port': self.src_port,
            'dest_port': self.dest_port,
            'protocol': self.protocol,
            'category': self.category,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class Institution(Base):
    """
    Modelo SQLAlchemy para instituições.
    Armazena informações sobre instituições educacionais e suas configurações de rede.
    
    Campos:
        id (int): Chave primária.
        nome (str): Nome da instituição.
        cidade (str): Cidade onde está localizada.
        pfsense_base_url (str): URL base para conectar no pfSense.
        pfsense_key (str): Chave de acesso ao pfSense.
        zeek_base_url (str): URL base para conectar no Zeek.
        zeek_key (str): Chave de acesso ao Zeek.
        ip_range_start (str): IP inicial do range da instituição.
        ip_range_end (str): IP final do range da instituição.
        is_active (bool): Se a instituição está ativa.
        created_at (datetime): Data/hora de criação.
        updated_at (datetime): Data/hora da última atualização.
    """
    __tablename__ = 'institutions'
    
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(255), index=True, nullable=False, comment="Nome da instituição")
    cidade = Column(String(255), nullable=False, comment="Cidade onde está localizada")
    pfsense_base_url = Column(String(500), nullable=False, comment="URL base para conectar no pfSense")
    pfsense_key = Column(String(500), nullable=False, comment="Chave de acesso ao pfSense")
    zeek_base_url = Column(String(500), nullable=False, comment="URL base para conectar no Zeek")
    zeek_key = Column(String(500), nullable=False, comment="Chave de acesso ao Zeek")
    suricata_base_url = Column(String(500), nullable=True, comment="URL base para conectar no Suricata")
    suricata_key = Column(String(500), nullable=True, comment="Chave de acesso ao Suricata")
    snort_base_url = Column(String(500), nullable=True, comment="URL base para conectar no Snort")
    snort_key = Column(String(500), nullable=True, comment="Chave de acesso ao Snort")
    ip_range_start = Column(String(15), nullable=False, comment="IP inicial do range")
    ip_range_end = Column(String(15), nullable=False, comment="IP final do range")
    is_active = Column(Boolean, default=True, nullable=False, comment="Se a instituição está ativa")
    created_at = Column(DateTime, default=func.now(), comment="Data/hora de criação")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="Data/hora da última atualização")
    
    # Índice único composto: nome + cidade (permite mesmo nome em cidades diferentes)
    __table_args__ = (
        Index('idx_institution_nome_cidade_unique', 'nome', 'cidade', unique=True),
    )
    
    # Relacionamento com gestores (usuários com permission MANAGER)
    managers = relationship("User", back_populates="institution", foreign_keys="[User.institution_id]")
    
    def __repr__(self):
        return f"<Institution(id={self.id}, nome='{self.nome}', cidade='{self.cidade}')>"
    
    def get_managers(self):
        """Retorna lista de gestores ativos desta instituição."""
        return [manager for manager in self.managers if manager.is_manager() and manager.is_active_user()]
    
    def add_manager(self, user):
        """Adiciona um usuário como gestor desta instituição."""
        if user.is_manager():
            user.institution_id = self.id
            return True
        return False
    
    def remove_manager(self, user):
        """Remove um usuário como gestor desta instituição."""
        if user.institution_id == self.id:
            user.institution_id = None
            return True
        return False
    
    def has_manager(self, user):
        """Verifica se um usuário é gestor desta instituição."""
        return user.institution_id == self.id and user.is_manager()
    
    def to_dict(self):
        """Converte a instituição para dicionário."""
        managers_data = [manager.to_dict() for manager in self.get_managers()]
        return {
            'id': self.id,
            'nome': self.nome,
            'cidade': self.cidade,
            'pfsense_base_url': self.pfsense_base_url,
            'pfsense_key': self.pfsense_key,
            'zeek_base_url': self.zeek_base_url,
            'zeek_key': self.zeek_key,
            'suricata_base_url': self.suricata_base_url,
            'suricata_key': self.suricata_key,
            'snort_base_url': self.snort_base_url,
            'snort_key': self.snort_key,
            'ip_range_start': self.ip_range_start,
            'ip_range_end': self.ip_range_end,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'managers': managers_data,
            'managers_count': len(managers_data)
        }
    
    def activate(self) -> None:
        """Ativa a instituição."""
        self.is_active = True
    
    def deactivate(self) -> None:
        """Desativa a instituição."""
        self.is_active = False
    
    def toggle_active_status(self) -> bool:
        """Alterna o status de ativação da instituição."""
        self.is_active = not self.is_active
        return self.is_active

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