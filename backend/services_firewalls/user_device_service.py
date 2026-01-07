"""
Serviço para gerenciamento de atribuições entre usuários e dispositivos DHCP.

Este módulo fornece funcionalidades para:
- Atribuir usuários a dispositivos DHCP
- Remover atribuições de usuários
- Consultar dispositivos por usuário
- Consultar usuários por dispositivo
- Estatísticas de atribuições
"""
from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from db.session import SessionLocal
from db.models import User, DhcpStaticMapping, UserDeviceAssignment
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class UserDeviceService:
    """Serviço para gerenciamento de atribuições usuário-dispositivo."""
    
    def __init__(self):
        self.db: Session = SessionLocal()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.db.close()
    
    def assign_device_to_user(self, user_id: int, device_id: int, notes: str = None, assigned_by: int = None) -> UserDeviceAssignment:
        """
        Atribui um dispositivo a um usuário.
        
        Args:
            user_id: ID do usuário
            device_id: ID do dispositivo
            notes: Observações sobre a atribuição
            assigned_by: ID do usuário que está fazendo a atribuição
            
        Returns:
            UserDeviceAssignment criada
            
        Raises:
            ValueError: Se usuário ou dispositivo não existirem
            ValueError: Se atribuição já existir
        """
        try:
            # Verificar se usuário existe
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError(f"Usuário com ID {user_id} não encontrado")
            
            # Verificar se dispositivo existe
            device = self.db.query(DhcpStaticMapping).filter(DhcpStaticMapping.id == device_id).first()
            if not device:
                raise ValueError(f"Dispositivo com ID {device_id} não encontrado")
            
            # Verificar se atribuição já existe
            existing_assignment = self.db.query(UserDeviceAssignment).filter(
                and_(
                    UserDeviceAssignment.user_id == user_id,
                    UserDeviceAssignment.device_id == device_id
                )
            ).first()
            
            if existing_assignment:
                if existing_assignment.is_active:
                    raise ValueError(f"Atribuição já existe e está ativa")
                else:
                    # Reativar atribuição existente
                    existing_assignment.is_active = True
                    existing_assignment.assigned_at = datetime.now()
                    existing_assignment.notes = notes
                    existing_assignment.assigned_by = assigned_by
                    self.db.commit()
                    return existing_assignment
            
            # Criar nova atribuição
            assignment = UserDeviceAssignment(
                user_id=user_id,
                device_id=device_id,
                notes=notes,
                assigned_by=assigned_by,
                is_active=True
            )
            
            self.db.add(assignment)
            self.db.commit()
            self.db.refresh(assignment)
            
            return assignment
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erro ao atribuir dispositivo ao usuário: {e}")
            raise
    
    def remove_device_from_user(self, user_id: int, device_id: int) -> bool:
        """
        Remove (exclui definitivamente) a(s) atribuição(ões) de um dispositivo de um usuário.

        Args:
            user_id: ID do usuário
            device_id: ID do dispositivo

        Returns:
            True se ao menos um registro foi excluído

        Raises:
            ValueError: Se nenhuma atribuição existir
        """
        try:
            # Buscar TODAS as atribuições (ativas ou não) para garantir remoção total
            assignments_q = self.db.query(UserDeviceAssignment).filter(
                and_(
                    UserDeviceAssignment.user_id == user_id,
                    UserDeviceAssignment.device_id == device_id,
                )
            )

            # Verificar existência
            count_existing = assignments_q.count()
            if count_existing == 0:
                raise ValueError(f"Atribuição não encontrada para usuário {user_id} e dispositivo {device_id}")

            # Excluir definitivamente
            assignments_q.delete(synchronize_session=False)
            self.db.commit()

            return True

        except Exception as e:
            self.db.rollback()
            logger.error(f"Erro ao remover (excluir) atribuição: {e}")
            raise
    
    def get_user_devices(self, user_id: int, include_inactive: bool = False) -> List[DhcpStaticMapping]:
        """
        Retorna dispositivos atribuídos a um usuário.
        
        Args:
            user_id: ID do usuário
            include_inactive: Se deve incluir atribuições inativas
            
        Returns:
            Lista de dispositivos
        """
        query = self.db.query(DhcpStaticMapping).join(UserDeviceAssignment).filter(
            UserDeviceAssignment.user_id == user_id
        )
        
        if not include_inactive:
            query = query.filter(UserDeviceAssignment.is_active == True)
        
        return query.all()
    
    def get_device_users(self, device_id: int, include_inactive: bool = False) -> List[User]:
        """
        Retorna usuários atribuídos a um dispositivo.
        
        Args:
            device_id: ID do dispositivo
            include_inactive: Se deve incluir atribuições inativas
            
        Returns:
            Lista de usuários
        """
        query = self.db.query(User).join(
            UserDeviceAssignment, 
            User.id == UserDeviceAssignment.user_id
        ).filter(
            UserDeviceAssignment.device_id == device_id
        )
        
        if not include_inactive:
            query = query.filter(UserDeviceAssignment.is_active == True)
        
        return query.all()
    
    def get_user_assignments(self, user_id: int) -> List[UserDeviceAssignment]:
        """
        Retorna todas as atribuições de um usuário.
        
        Args:
            user_id: ID do usuário
            
        Returns:
            Lista de atribuições
        """
        return self.db.query(UserDeviceAssignment).filter(
            UserDeviceAssignment.user_id == user_id
        ).all()
    
    def get_device_assignments(self, device_id: int) -> List[UserDeviceAssignment]:
        """
        Retorna todas as atribuições de um dispositivo.
        
        Args:
            device_id: ID do dispositivo
            
        Returns:
            Lista de atribuições
        """
        return self.db.query(UserDeviceAssignment).filter(
            UserDeviceAssignment.device_id == device_id
        ).all()
    
    def get_assignment_statistics(self) -> Dict[str, Any]:
        """
        Retorna estatísticas das atribuições.
        
        Returns:
            Dicionário com estatísticas
        """
        total_assignments = self.db.query(UserDeviceAssignment).count()
        active_assignments = self.db.query(UserDeviceAssignment).filter(
            UserDeviceAssignment.is_active == True
        ).count()
        inactive_assignments = total_assignments - active_assignments
        
        # Usuários com dispositivos
        users_with_devices = self.db.query(User).join(
            UserDeviceAssignment, User.id == UserDeviceAssignment.user_id
        ).filter(
            UserDeviceAssignment.is_active == True
        ).distinct().count()
        
        # Dispositivos com usuários
        devices_with_users = self.db.query(DhcpStaticMapping).join(
            UserDeviceAssignment, DhcpStaticMapping.id == UserDeviceAssignment.device_id
        ).filter(
            UserDeviceAssignment.is_active == True
        ).distinct().count()
        
        # Atribuições por instituição
        assignments_by_institution = {}
        institution_stats = self.db.query(
            User.instituicao,
            func.count(UserDeviceAssignment.id).label('count')
        ).join(
            UserDeviceAssignment, User.id == UserDeviceAssignment.user_id
        ).filter(
            UserDeviceAssignment.is_active == True
        ).group_by(User.instituicao).all()
        
        for instituicao, count in institution_stats:
            assignments_by_institution[instituicao or 'Não informado'] = count
        
        return {
            'total_assignments': total_assignments,
            'active_assignments': active_assignments,
            'inactive_assignments': inactive_assignments,
            'users_with_devices': users_with_devices,
            'devices_with_users': devices_with_users,
            'assignments_by_institution': assignments_by_institution
        }
    
    def search_assignments(self, query: str) -> List[UserDeviceAssignment]:
        """
        Busca atribuições por termo (nome do usuário, email, descrição do dispositivo, IP, MAC).
        
        Args:
            query: Termo de busca
            
        Returns:
            Lista de atribuições encontradas
        """
        return self.db.query(UserDeviceAssignment).join(
            User, User.id == UserDeviceAssignment.user_id
        ).join(
            DhcpStaticMapping, DhcpStaticMapping.id == UserDeviceAssignment.device_id
        ).filter(
            or_(
                User.nome.contains(query),
                User.email.contains(query),
                DhcpStaticMapping.descr.contains(query),
                DhcpStaticMapping.ipaddr.contains(query),
                DhcpStaticMapping.mac.contains(query),
                DhcpStaticMapping.hostname.contains(query)
            )
        ).filter(UserDeviceAssignment.is_active == True).all()
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Busca usuário por email."""
        return self.db.query(User).filter(User.email == email).first()
    
    def get_device_by_ip(self, ipaddr: str) -> Optional[DhcpStaticMapping]:
        """Busca dispositivo por IP."""
        return self.db.query(DhcpStaticMapping).filter(DhcpStaticMapping.ipaddr == ipaddr).first()
    
    def get_device_by_mac(self, mac: str) -> Optional[DhcpStaticMapping]:
        """Busca dispositivo por MAC."""
        return self.db.query(DhcpStaticMapping).filter(DhcpStaticMapping.mac == mac).first()
