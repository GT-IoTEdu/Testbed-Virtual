"""
Módulo de autenticação SAML CAFe para FastAPI.

Este módulo integra a autenticação SAML do Django com o FastAPI,
permitindo que usuários autenticados via CAFe acessem os endpoints da API.
"""

import os
import sys
import django
from pathlib import Path
from typing import Optional, Dict, Any
from fastapi import HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from datetime import datetime, timedelta

# Adicionar o diretório raiz ao path para importar o Django
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sp_django.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.conf import settings

# Configurações JWT
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

security = HTTPBearer()

class SAMLAuthManager:
    """Gerenciador de autenticação SAML CAFe."""
    
    def __init__(self):
        self.secret_key = JWT_SECRET_KEY
        self.algorithm = JWT_ALGORITHM
        self.expiration_hours = JWT_EXPIRATION_HOURS
    
    def create_jwt_token(self, user_data: Dict[str, Any]) -> str:
        """
        Cria um token JWT para um usuário autenticado via SAML.
        
        Args:
            user_data: Dados do usuário (username, email, etc.)
        
        Returns:
            str: Token JWT
        """
        payload = {
            "sub": user_data.get("username"),
            "email": user_data.get("email"),
            "first_name": user_data.get("first_name", ""),
            "last_name": user_data.get("last_name", ""),
            "exp": datetime.utcnow() + timedelta(hours=self.expiration_hours),
            "iat": datetime.utcnow(),
            "auth_method": "saml_cafe"
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def verify_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verifica e decodifica um token JWT.
        
        Args:
            token: Token JWT
        
        Returns:
            Dict com dados do usuário ou None se inválido
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def get_user_from_token(self, token: str) -> Optional[User]:
        """
        Obtém o usuário Django a partir do token JWT.
        
        Args:
            token: Token JWT
        
        Returns:
            User object ou None se não encontrado
        """
        payload = self.verify_jwt_token(token)
        if not payload:
            return None
        
        username = payload.get("sub")
        if not username:
            return None
        
        try:
            return User.objects.get(username=username)
        except User.DoesNotExist:
            return None

# Instância global do gerenciador
saml_auth_manager = SAMLAuthManager()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """
    Dependency para obter o usuário atual autenticado.
    
    Args:
        credentials: Credenciais HTTP Bearer
    
    Returns:
        User: Usuário autenticado
    
    Raises:
        HTTPException: Se não autenticado
    """
    token = credentials.credentials
    user = saml_auth_manager.get_user_from_token(token)
    
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Token inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user

async def get_current_user_optional(request: Request) -> Optional[User]:
    """
    Dependency opcional para obter o usuário atual.
    
    Args:
        request: Request FastAPI
    
    Returns:
        User ou None se não autenticado
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    
    token = auth_header.split(" ")[1]
    return saml_auth_manager.get_user_from_token(token)

def require_saml_auth(func):
    """
    Decorator para proteger endpoints que requerem autenticação SAML.
    
    Args:
        func: Função a ser decorada
    
    Returns:
        Função decorada
    """
    async def wrapper(*args, **kwargs):
        # Esta função será chamada pelo FastAPI
        return await func(*args, **kwargs)
    
    return wrapper

# Funções auxiliares para integração com Django
def create_user_from_saml_data(saml_data: Dict[str, Any]) -> User:
    """
    Cria ou atualiza um usuário Django a partir dos dados SAML.
    
    Args:
        saml_data: Dados recebidos do SAML
    
    Returns:
        User: Usuário criado/atualizado
    """
    username = saml_data.get("eduPersonPrincipalName", "")
    email = saml_data.get("mail", "")
    first_name = saml_data.get("givenName", "")
    last_name = saml_data.get("sn", "")
    
    if not username:
        raise ValueError("eduPersonPrincipalName é obrigatório")
    
    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
        }
    )
    
    if not created:
        # Atualizar dados existentes
        user.email = email
        user.first_name = first_name
        user.last_name = last_name
        user.save()
    
    return user

def get_saml_login_url() -> str:
    """
    Retorna a URL de login SAML.
    
    Returns:
        str: URL de login
    """
    return "/saml2/login/"

def get_saml_metadata_url() -> str:
    """
    Retorna a URL de metadados SAML.
    
    Returns:
        str: URL de metadados
    """
    return "/saml2/metadata/" 