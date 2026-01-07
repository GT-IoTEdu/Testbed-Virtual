"""
Serviço para verificação de permissões de usuários.

Este módulo implementa as regras de negócio para:
- Verificar se um usuário pode gerenciar dispositivos
- Validar permissões de acesso
- Controlar operações baseadas no nível de permissão
"""
from typing import Optional, List
from sqlalchemy.orm import Session
from db.session import SessionLocal
from db.models import User, DhcpStaticMapping, UserDeviceAssignment
from db.enums import UserPermission
from fastapi import HTTPException, status
import logging

logger = logging.getLogger(__name__)

class PermissionService:
    """Serviço para verificação de permissões."""
    
    def __init__(self):
        self.db: Session = SessionLocal()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.db.close()
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Busca usuário por ID."""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def verify_user_exists(self, user_id: int) -> User:
        """
        Verifica se o usuário existe e retorna o objeto.
        
        Args:
            user_id: ID do usuário
            
        Returns:
            Objeto User
            
        Raises:
            HTTPException: Se usuário não existir
        """
        user = self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Usuário com ID {user_id} não encontrado"
            )
        return user
    
    def verify_device_exists(self, device_id: int) -> DhcpStaticMapping:
        """
        Verifica se o dispositivo existe e retorna o objeto.
        
        Args:
            device_id: ID do dispositivo
            
        Returns:
            Objeto DhcpStaticMapping
            
        Raises:
            HTTPException: Se dispositivo não existir
        """
        device = self.db.query(DhcpStaticMapping).filter(DhcpStaticMapping.id == device_id).first()
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Dispositivo com ID {device_id} não encontrado"
            )
        return device
    
    def can_assign_device(self, user_id: int, device_id: int, target_user_id: int) -> bool:
        """
        Verifica se um usuário pode atribuir um dispositivo a outro usuário.
        
        Args:
            user_id: ID do usuário que está fazendo a atribuição
            device_id: ID do dispositivo
            target_user_id: ID do usuário que receberá o dispositivo
            
        Returns:
            True se pode atribuir, False caso contrário
        """
        # Buscar usuário que está fazendo a atribuição
        user = self.verify_user_exists(user_id)
        
        # Verificar se o dispositivo existe
        device = self.verify_device_exists(device_id)
        
        # Verificar se o usuário alvo existe
        target_user = self.verify_user_exists(target_user_id)
        
        # Gestores podem atribuir dispositivos a qualquer usuário
        if user.is_manager():
            return True
        
        # Usuários comuns só podem atribuir dispositivos a si mesmos
        return user_id == target_user_id
    
    def can_remove_device_assignment(self, user_id: int, device_id: int, target_user_id: int) -> bool:
        """
        Verifica se um usuário pode remover uma atribuição de dispositivo.
        
        Args:
            user_id: ID do usuário que está fazendo a remoção
            device_id: ID do dispositivo
            target_user_id: ID do usuário que tem o dispositivo
            
        Returns:
            True se pode remover, False caso contrário
        """
        # Buscar usuário que está fazendo a remoção
        user = self.verify_user_exists(user_id)
        
        # Verificar se o dispositivo existe
        device = self.verify_device_exists(device_id)
        
        # Verificar se o usuário alvo existe
        target_user = self.verify_user_exists(target_user_id)
        
        # Gestores podem remover atribuições de qualquer usuário
        if user.is_manager():
            return True
        
        # Usuários comuns só podem remover suas próprias atribuições
        return user_id == target_user_id
    
    def can_view_user_devices(self, user_id: int, target_user_id: int) -> bool:
        """
        Verifica se um usuário pode visualizar os dispositivos de outro usuário.
        
        Args:
            user_id: ID do usuário que está fazendo a consulta
            target_user_id: ID do usuário cujos dispositivos serão visualizados
            
        Returns:
            True se pode visualizar, False caso contrário
        """
        # Buscar usuário que está fazendo a consulta
        user = self.verify_user_exists(user_id)
        
        # Verificar se o usuário alvo existe
        target_user = self.verify_user_exists(target_user_id)
        
        # Gestores podem visualizar dispositivos de qualquer usuário
        if user.is_manager():
            return True
        
        # Usuários comuns só podem visualizar seus próprios dispositivos
        return user_id == target_user_id
    
    def can_view_device_users(self, user_id: int, device_id: int) -> bool:
        """
        Verifica se um usuário pode visualizar os usuários de um dispositivo.
        
        Args:
            user_id: ID do usuário que está fazendo a consulta
            device_id: ID do dispositivo
            
        Returns:
            True se pode visualizar, False caso contrário
        """
        # Buscar usuário que está fazendo a consulta
        user = self.verify_user_exists(user_id)
        
        # Verificar se o dispositivo existe
        device = self.verify_device_exists(device_id)
        
        # Gestores podem visualizar usuários de qualquer dispositivo
        if user.is_manager():
            return True
        
        # Usuários comuns só podem visualizar usuários de dispositivos que possuem
        user_assignments = self.db.query(UserDeviceAssignment).filter(
            UserDeviceAssignment.user_id == user_id,
            UserDeviceAssignment.device_id == device_id,
            UserDeviceAssignment.is_active == True
        ).first()
        
        return user_assignments is not None
    
    def get_user_devices_with_permission(self, user_id: int, target_user_id: int) -> List[DhcpStaticMapping]:
        """
        Retorna dispositivos de um usuário considerando permissões.
        
        Args:
            user_id: ID do usuário que está fazendo a consulta
            target_user_id: ID do usuário cujos dispositivos serão retornados
            
        Returns:
            Lista de dispositivos
        """
        # Verificar permissão
        if not self.can_view_user_devices(user_id, target_user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Você não tem permissão para visualizar os dispositivos deste usuário"
            )
        
        # Buscar dispositivos
        devices = self.db.query(DhcpStaticMapping).join(UserDeviceAssignment).filter(
            UserDeviceAssignment.user_id == target_user_id,
            UserDeviceAssignment.is_active == True
        ).all()
        
        return devices
    
    def get_device_users_with_permission(self, user_id: int, device_id: int) -> List[User]:
        """
        Retorna usuários de um dispositivo considerando permissões.
        
        Args:
            user_id: ID do usuário que está fazendo a consulta
            device_id: ID do dispositivo
            
        Returns:
            Lista de usuários
        """
        # Verificar permissão
        if not self.can_view_device_users(user_id, device_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Você não tem permissão para visualizar os usuários deste dispositivo"
            )
        
        # Buscar usuários
        users = self.db.query(User).join(UserDeviceAssignment).filter(
            UserDeviceAssignment.device_id == device_id,
            UserDeviceAssignment.is_active == True
        ).all()
        
        return users
    
    def get_user_permission_level(self, user_id: int) -> UserPermission:
        """
        Retorna o nível de permissão de um usuário.
        
        Args:
            user_id: ID do usuário
            
        Returns:
            Nível de permissão
        """
        user = self.verify_user_exists(user_id)
        return user.permission
    
    def is_manager(self, user_id: int) -> bool:
        """
        Verifica se um usuário é gestor.
        
        Args:
            user_id: ID do usuário
            
        Returns:
            True se é gestor, False caso contrário
        """
        user = self.verify_user_exists(user_id)
        return user.is_manager()
