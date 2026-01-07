"""
Router FastAPI para autenticação SAML CAFe.

Este módulo fornece endpoints para:
- Login SAML
- Callback SAML
- Verificação de token
- Logout SAML
"""

from fastapi import APIRouter, HTTPException, Request, Response, Depends
from fastapi.responses import RedirectResponse, JSONResponse
from typing import Optional, Dict, Any
import os
import sys
import django
from pathlib import Path

# Adicionar o diretório raiz ao path para importar o Django
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'auth.sp_django.settings')
django.setup()

from django.http import HttpRequest, HttpResponse
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.shortcuts import redirect
from django.conf import settings

from .saml_auth import saml_auth_manager, get_current_user, create_user_from_saml_data

router = APIRouter(prefix="/auth", tags=["Autenticação SAML CAFe"])

@router.get("/login", summary="Iniciar login SAML CAFe")
async def saml_login(request: Request):
    """
    Inicia o processo de autenticação SAML CAFe.
    
    Returns:
        RedirectResponse: Redireciona para o login SAML
    """
    try:
        # URL de login SAML do Django
        saml_login_url = "/saml2/login/"
        
        # Construir URL completa
        base_url = str(request.base_url).rstrip('/')
        full_login_url = f"{base_url}{saml_login_url}"
        
        return RedirectResponse(url=full_login_url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao iniciar login SAML: {str(e)}")

@router.get("/callback", summary="Callback SAML CAFe")
async def saml_callback(request: Request):
    """
    Callback após autenticação SAML bem-sucedida.
    
    Returns:
        JSONResponse: Token JWT e informações do usuário
    """
    try:
        # Simular dados SAML (em produção, isso viria do Django SAML)
        # Aqui você precisaria integrar com o callback real do Django SAML
        
        # Dados de exemplo do usuário autenticado
        saml_data = {
            "eduPersonPrincipalName": "user@institution.edu.br",
            "mail": "user@institution.edu.br",
            "givenName": "Nome",
            "sn": "Sobrenome"
        }
        
        # Criar ou atualizar usuário
        user = create_user_from_saml_data(saml_data)
        
        # Criar token JWT
        user_data = {
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name
        }
        
        token = saml_auth_manager.create_jwt_token(user_data)
        
        return JSONResponse({
            "status": "success",
            "message": "Autenticação SAML bem-sucedida",
            "token": token,
            "user": {
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name
            }
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no callback SAML: {str(e)}")

@router.get("/logout", summary="Logout SAML CAFe")
async def saml_logout(request: Request):
    """
    Realiza logout do usuário.
    
    Returns:
        JSONResponse: Confirmação de logout
    """
    try:
        # URL de logout SAML do Django
        saml_logout_url = "/saml2/logout/"
        
        # Construir URL completa
        base_url = str(request.base_url).rstrip('/')
        full_logout_url = f"{base_url}{saml_logout_url}"
        
        return JSONResponse({
            "status": "success",
            "message": "Logout realizado com sucesso",
            "logout_url": full_logout_url
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no logout SAML: {str(e)}")

@router.get("/verify", summary="Verificar token JWT")
async def verify_token(user: User = Depends(get_current_user)):
    """
    Verifica se o token JWT é válido e retorna informações do usuário.
    
    Args:
        user: Usuário autenticado (dependency)
    
    Returns:
        JSONResponse: Informações do usuário
    """
    return JSONResponse({
        "status": "success",
        "message": "Token válido",
        "user": {
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "is_authenticated": user.is_authenticated
        }
    })

@router.get("/metadata", summary="Metadados SAML")
async def saml_metadata(request: Request):
    """
    Retorna a URL dos metadados SAML.
    
    Returns:
        JSONResponse: URL dos metadados
    """
    try:
        # URL de metadados SAML do Django
        saml_metadata_url = "/saml2/metadata/"
        
        # Construir URL completa
        base_url = str(request.base_url).rstrip('/')
        full_metadata_url = f"{base_url}{saml_metadata_url}"
        
        return JSONResponse({
            "status": "success",
            "metadata_url": full_metadata_url,
            "description": "Metadados SAML para configuração do CAFe"
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter metadados: {str(e)}")

@router.get("/status", summary="Status da autenticação")
async def auth_status(request: Request):
    """
    Verifica o status atual da autenticação.
    
    Returns:
        JSONResponse: Status da autenticação
    """
    try:
        # Verificar se há token no header
        auth_header = request.headers.get("Authorization")
        
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse({
                "status": "unauthenticated",
                "message": "Usuário não autenticado",
                "login_url": "/auth/login"
            })
        
        token = auth_header.split(" ")[1]
        payload = saml_auth_manager.verify_jwt_token(token)
        
        if not payload:
            return JSONResponse({
                "status": "invalid_token",
                "message": "Token inválido ou expirado",
                "login_url": "/auth/login"
            })
        
        return JSONResponse({
            "status": "authenticated",
            "message": "Usuário autenticado",
            "user": {
                "username": payload.get("sub"),
                "email": payload.get("email"),
                "auth_method": payload.get("auth_method")
            }
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao verificar status: {str(e)}") 