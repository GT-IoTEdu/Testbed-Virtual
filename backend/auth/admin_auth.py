"""
Serviço de autenticação administrativa para o sistema IoT-EDU.

Este serviço permite que superusuários façam login via Google OAuth.
O email do superusuário deve estar configurado na variável de ambiente SUPERUSER_ACCESS.
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from db.models import User
from db.enums import UserPermission
from db.session import get_db_session
import config

logger = logging.getLogger(__name__)

class AdminAuthService:
    """Serviço de autenticação administrativa."""
    
    def __init__(self):
        """Inicializa o serviço de autenticação administrativa."""
        self.admin_email = config.SUPERUSER_ACCESS
    
    def is_admin_email(self, email: str) -> bool:
        """
        Verifica se o email corresponde ao administrador configurado.
        
        Args:
            email: Email a verificar
            
        Returns:
            True se for o email do administrador, False caso contrário
        """
        if not self.admin_email:
            return False
        return email.lower() == self.admin_email.lower()
    
    def authenticate_admin(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Verifica se um email corresponde ao administrador configurado.
        
        IMPORTANTE: A autenticação real é feita via Google OAuth.
        Este método apenas verifica se o email corresponde ao SUPERUSER_ACCESS.
        
        Args:
            email: Email a verificar
            
        Returns:
            Dicionário com dados do administrador se o email corresponder, None caso contrário
        """
        try:
            # Verificar se o email corresponde ao configurado
            if not self.is_admin_email(email):
                logger.warning(f"Email não corresponde ao administrador configurado: {email}")
                return None
            
            # Buscar usuário administrador
            admin_user = self._get_or_create_admin_user(email)
            
            if not admin_user:
                logger.error(f"Falha ao obter/criar usuário administrador: {email}")
                return None
            
            # Verificar se o usuário está ativo
            if not admin_user.is_active:
                logger.warning(f"Tentativa de acesso administrativo com usuário inativo: {email}")
                return None
            
            # Atualizar último login
            self._update_last_login(admin_user.id)
            
            logger.info(f"Verificação administrativa bem-sucedida: {email}")
            
            return {
                'user_id': admin_user.id,
                'email': admin_user.email,
                'nome': admin_user.nome,
                'instituicao': admin_user.instituicao,
                'permission': admin_user.permission.value,
                'is_admin': True,
                'is_manager': False,
                'is_user': False,
                'login_type': 'admin',
                'authenticated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erro na verificação administrativa: {e}")
            return None
    
    def _get_or_create_admin_user(self, email: str) -> Optional[User]:
        """
        Busca ou cria o usuário administrador.
        
        Args:
            email: Email do administrador
            
        Returns:
            Usuário administrador ou None
        """
        try:
            with get_db_session() as db:
                # Buscar usuário existente
                user = db.query(User).filter(User.email == email).first()
                
                if user:
                    # Verificar se já é superusuário
                    if user.permission == UserPermission.SUPERUSER:
                        logger.info(f"Usuário superusuário encontrado: {email}")
                        return user
                    else:
                        # Promover para superusuário
                        logger.info(f"Promovendo usuário para superusuário: {email}")
                        user.permission = UserPermission.SUPERUSER
                        db.commit()
                        db.refresh(user)
                        return user
                
                # Criar novo usuário superusuário
                logger.info(f"Criando novo usuário superusuário: {email}")
                
                admin_user = User(
                    email=email,
                    nome="Superusuário do Sistema",
                    instituicao="IoT-EDU",
                    permission=UserPermission.SUPERUSER,
                    is_active=True
                )
                
                db.add(admin_user)
                db.commit()
                db.refresh(admin_user)
                
                logger.info(f"Usuário administrador criado com ID: {admin_user.id}")
                return admin_user
                
        except Exception as e:
            logger.error(f"Erro ao obter/criar usuário administrador: {e}")
            return None
    
    def _update_last_login(self, user_id: int) -> bool:
        """
        Atualiza o último login do usuário.
        
        Args:
            user_id: ID do usuário
            
        Returns:
            True se atualizado com sucesso, False caso contrário
        """
        try:
            with get_db_session() as db:
                user = db.query(User).filter(User.id == user_id).first()
                if user:
                    user.ultimo_login = datetime.now()
                    db.commit()
                    return True
                return False
                
        except Exception as e:
            logger.error(f"Erro ao atualizar último login: {e}")
            return False
    
    
    def get_admin_info(self) -> Dict[str, Any]:
        """
        Retorna informações sobre o acesso administrativo.
        
        Returns:
            Dicionário com informações do administrador
        """
        try:
            with get_db_session() as db:
                admin_user = db.query(User).filter(
                    User.permission == UserPermission.SUPERUSER
                ).first()
                
                if admin_user:
                    return {
                        'email': admin_user.email,
                        'nome': admin_user.nome,
                        'instituicao': admin_user.instituicao,
                        'permission': admin_user.permission.value,
                        'ultimo_login': admin_user.ultimo_login.isoformat() if admin_user.ultimo_login else None,
                        'created_at': admin_user.created_at.isoformat() if hasattr(admin_user, 'created_at') and admin_user.created_at else None
                    }
                else:
                    return {
                        'email': self.admin_email,
                        'nome': 'Administrador do Sistema',
                        'instituicao': 'IoT-EDU',
                        'permission': 'ADMIN',
                        'ultimo_login': None,
                        'created_at': None,
                        'status': 'not_created'
                    }
                    
        except Exception as e:
            logger.error(f"Erro ao obter informações do administrador: {e}")
            return {}
    
    def validate_admin_access(self) -> bool:
        """
        Valida se o acesso administrativo está configurado corretamente.
        
        Returns:
            True se configurado corretamente, False caso contrário
        """
        try:
            # Verificar se a configuração está definida
            if not self.admin_email:
                logger.error("Configuração de acesso administrativo não definida (SUPERUSER_ACCESS)")
                return False
            
            # Verificar se o email é válido
            if '@' not in self.admin_email:
                logger.error("Email administrativo inválido")
                return False
            
            logger.info("Configuração de acesso administrativo validada")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao validar acesso administrativo: {e}")
            return False

# Instância global do serviço
admin_auth_service = AdminAuthService()
