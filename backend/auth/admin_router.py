"""
Router FastAPI para autenticação administrativa.

Este router fornece endpoints para:
- Verificação de acesso administrativo (login via Google OAuth)
- Gerenciamento de permissões de usuários
- Informações do administrador

IMPORTANTE: O login administrativo é feito via Google OAuth.
O email do superusuário deve estar configurado em SUPERUSER_ACCESS.
"""

import logging
from typing import Dict, Any, List
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Query, Request
from starlette.requests import Request
from typing import Optional
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr

from .admin_auth import admin_auth_service
from db.models import User, Institution
from db.enums import UserPermission
from db.session import get_db_session

logger = logging.getLogger(__name__)

# Cria o roteador
router = APIRouter(prefix="/admin", tags=["Autenticação Administrativa"])

# Modelos Pydantic para validação
class AdminVerifyRequest(BaseModel):
    email: EmailStr

class AdminVerifyResponse(BaseModel):
    success: bool
    message: str
    is_admin: bool
    user: Dict[str, Any] = None

class UserPermissionUpdate(BaseModel):
    user_id: int
    new_permission: str

class UserPermissionResponse(BaseModel):
    success: bool
    message: str
    user: Dict[str, Any]

class UserStatusUpdate(BaseModel):
    user_id: int
    is_active: bool

class UserStatusResponse(BaseModel):
    success: bool
    message: str
    user: Dict[str, Any]

# Modelos para instituições
class InstitutionCreateRequest(BaseModel):
    nome: str
    cidade: str
    pfsense_base_url: str
    pfsense_key: str
    zeek_base_url: str
    zeek_key: str
    suricata_base_url: Optional[str] = None
    suricata_key: Optional[str] = None
    ip_range_start: str
    ip_range_end: str

class InstitutionUpdateRequest(BaseModel):
    nome: str = None
    cidade: str = None
    pfsense_base_url: str = None
    pfsense_key: str = None
    zeek_base_url: str = None
    zeek_key: str = None
    suricata_base_url: Optional[str] = None
    suricata_key: Optional[str] = None
    ip_range_start: str = None
    ip_range_end: str = None
    is_active: bool = None

class InstitutionResponse(BaseModel):
    success: bool
    message: str
    institution: Dict[str, Any]

class InstitutionListResponse(BaseModel):
    success: bool
    count: int
    institutions: List[Dict[str, Any]]
    message: str

@router.post("/verify", response_model=AdminVerifyResponse, summary="Verificar se email é administrador")
async def verify_admin_email(request: AdminVerifyRequest):
    """
    Verifica se um email corresponde ao administrador configurado.
    
    IMPORTANTE: O login real é feito via Google OAuth.
    Este endpoint apenas verifica se o email autenticado via Google
    corresponde ao SUPERUSER_ACCESS configurado.
    
    O email do superusuário deve estar configurado em SUPERUSER_ACCESS.
    """
    try:
        logger.info(f"Verificação de acesso administrativo: {request.email}")
        
        # Verificar se é email do administrador
        auth_result = admin_auth_service.authenticate_admin(request.email)
        
        if not auth_result:
            return AdminVerifyResponse(
                success=True,
                message="Email não corresponde ao administrador configurado",
                is_admin=False
            )
        
        logger.info(f"Email confirmado como administrador: {request.email}")
        
        return AdminVerifyResponse(
            success=True,
            message="Email corresponde ao administrador configurado",
            is_admin=True,
            user=auth_result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro na verificação administrativa: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno na verificação: {str(e)}"
        )

@router.get("/info", summary="Informações do administrador")
async def get_admin_info(http_request: Request):
    """
    Retorna informações sobre o acesso administrativo configurado.
    
    Mostra:
    - Email do administrador
    - Último login
    - Status da configuração
    - Institution ID (se o usuário for ADMIN com rede atribuída)
    """
    try:
        # Tentar obter informações do usuário logado da sessão
        user_info = None
        if http_request:
            user_email = http_request.session.get("email")
            if user_email:
                with get_db_session() as db:
                    user = db.query(User).filter(User.email == user_email).first()
                    # Aceitar ADMIN, SUPERUSER ou MANAGER (caso ainda exista no banco)
                    # Obter valor da permissão como string para compatibilidade
                    permission_value = user.permission.value if hasattr(user.permission, 'value') else str(user.permission)
                    if user and (permission_value in ["ADMIN", "SUPERUSER", "MANAGER"]):
                        # Buscar informações da instituição se o usuário tiver institution_id
                        institution_name = None
                        institution_city = None
                        if user.institution_id:
                            institution = db.query(Institution).filter(Institution.id == user.institution_id).first()
                            if institution:
                                institution_name = institution.nome
                                institution_city = institution.cidade
                        
                        user_info = {
                            'email': user.email,
                            'nome': user.nome,
                            'instituicao': user.instituicao,
                            'permission': user.permission.value,
                            'ultimo_login': user.ultimo_login.isoformat() if user.ultimo_login else None,
                            'institution_id': user.institution_id,
                            'institution_name': institution_name,
                            'institution_city': institution_city,
                            'created_at': None
                        }
        
        # Se não conseguiu obter da sessão, usar o método padrão
        if not user_info:
            admin_info = admin_auth_service.get_admin_info()
            if not admin_info:
                raise HTTPException(
                    status_code=404,
                    detail="Informações do administrador não encontradas"
                )
            user_info = admin_info
        
        return {
            "success": True,
            "admin_info": user_info,
            "message": "Informações do administrador obtidas com sucesso"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao obter informações do administrador: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno ao obter informações: {str(e)}"
        )


@router.get("/validate-config", summary="Validar configuração administrativa")
async def validate_admin_config():
    """
    Valida se as configurações de acesso administrativo estão corretas.
    
    Verifica:
    - SUPERUSER_ACCESS está definido
    - Email é válido
    
    IMPORTANTE: Não é mais necessário ADMIN_PASSWORD, pois o login é via Google OAuth.
    """
    try:
        is_valid = admin_auth_service.validate_admin_access()
        
        return {
            "success": is_valid,
            "message": "Configuração administrativa validada" if is_valid else "Configuração administrativa inválida (SUPERUSER_ACCESS não definido)",
            "valid": is_valid,
            "note": "Login administrativo é feito via Google OAuth. Configure o email do superusuário em SUPERUSER_ACCESS."
        }
        
    except Exception as e:
        logger.error(f"Erro ao validar configuração administrativa: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno na validação: {str(e)}"
        )

@router.get("/users", summary="Listar todos os usuários")
async def list_all_users(
    permission: str = Query(None, description="Filtrar por permissão"),
    limit: int = Query(100, ge=1, le=500, description="Limite de resultados")
):
    """
    Lista todos os usuários do sistema.
    
    Apenas administradores podem acessar este endpoint.
    """
    try:
        with get_db_session() as db:
            query = db.query(User)
            
            # Filtrar por permissão se especificado
            if permission:
                try:
                    permission_enum = UserPermission(permission.upper())
                    query = query.filter(User.permission == permission_enum)
                except ValueError:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Permissão inválida: {permission}. Valores válidos: USER, ADMIN, SUPERUSER"
                    )
            
            users = query.limit(limit).all()
            
            # Buscar todas as instituições de uma vez para melhor performance
            from db.models import Institution
            institution_ids = [u.institution_id for u in users if u.institution_id]
            institutions_map = {}
            if institution_ids:
                institutions = db.query(Institution).filter(Institution.id.in_(institution_ids)).all()
                institutions_map = {inst.id: inst for inst in institutions}
            
            users_data = []
            for user in users:
                # Buscar dados da instituição do mapa
                institution_name = None
                institution_city = None
                if user.institution_id and user.institution_id in institutions_map:
                    institution = institutions_map[user.institution_id]
                    institution_name = institution.nome
                    institution_city = institution.cidade
                
                users_data.append({
                    'id': user.id,
                    'email': user.email,
                    'nome': user.nome,
                    'instituicao': user.instituicao,
                    'institution_id': user.institution_id,
                    'institution_name': institution_name,
                    'institution_city': institution_city,
                    'permission': user.permission.value,
                    'ultimo_login': user.ultimo_login.isoformat() if user.ultimo_login else None,
                    'is_active': user.is_active,
                    'is_admin': user.is_admin(),
                    'is_manager': user.is_manager(),
                    'is_user': user.permission == UserPermission.USER,
                    'is_active_user': user.is_active_user()
                })
            
            return {
                "success": True,
                "count": len(users_data),
                "users": users_data,
                "message": f"Listados {len(users_data)} usuários"
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao listar usuários: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno ao listar usuários: {str(e)}"
        )

@router.put("/users/{user_id}/permission", response_model=UserPermissionResponse, summary="Alterar permissão de usuário")
async def update_user_permission(user_id: int, request: UserPermissionUpdate):
    """
    Altera a permissão de um usuário.
    
    Apenas administradores podem alterar permissões.
    Administradores não podem alterar suas próprias permissões.
    """
    try:
        with get_db_session() as db:
            # Buscar usuário alvo
            target_user = db.query(User).filter(User.id == user_id).first()
            if not target_user:
                raise HTTPException(
                    status_code=404,
                    detail=f"Usuário {user_id} não encontrado"
                )
            
            # Validar nova permissão
            try:
                new_permission = UserPermission(request.new_permission.upper())
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Permissão inválida: {request.new_permission}. Valores válidos: USER, MANAGER, ADMIN"
                )
            
            # Verificar se a permissão já é a mesma
            if target_user.permission == new_permission:
                return UserPermissionResponse(
                    success=True,
                    message=f"Usuário {target_user.email} já possui a permissão {new_permission.value}",
                    user={
                        'id': target_user.id,
                        'email': target_user.email,
                        'nome': target_user.nome,
                        'permission': target_user.permission.value
                    }
                )
            
            # Alterar permissão
            old_permission = target_user.permission.value
            target_user.permission = new_permission
            
            db.commit()
            db.refresh(target_user)
            
            logger.info(f"Permissão do usuário {target_user.email} alterada de {old_permission} para {new_permission.value}")
            
            return UserPermissionResponse(
                success=True,
                message=f"Permissão alterada de {old_permission} para {new_permission.value}",
                user={
                    'id': target_user.id,
                    'email': target_user.email,
                    'nome': target_user.nome,
                    'permission': target_user.permission.value,
                    'old_permission': old_permission
                }
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao alterar permissão do usuário {user_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno ao alterar permissão: {str(e)}"
        )

@router.put("/users/{user_id}/status", response_model=UserStatusResponse, summary="Alterar status de ativação do usuário")
async def update_user_status(user_id: int, request: UserStatusUpdate):
    """
    Altera o status de ativação de um usuário.
    
    Apenas administradores podem alterar o status de ativação.
    Administradores não podem alterar seu próprio status.
    
    Args:
        user_id: ID do usuário a ser alterado
        request: Dados da alteração (user_id, is_active)
    
    Returns:
        UserStatusResponse: Resposta com sucesso e dados do usuário
    """
    try:
        # Verificar se o usuário existe
        with get_db_session() as db:
            target_user = db.query(User).filter(User.id == user_id).first()
            
            if not target_user:
                raise HTTPException(
                    status_code=404,
                    detail=f"Usuário com ID {user_id} não encontrado"
                )
            
            # Verificar se não está tentando alterar a si mesmo
            if request.user_id != user_id:
                raise HTTPException(
                    status_code=400,
                    detail="ID do usuário na URL deve coincidir com o ID no corpo da requisição"
                )
            
            # Verificar se não está tentando alterar outro administrador
            if target_user.is_admin():
                raise HTTPException(
                    status_code=403,
                    detail="Não é possível alterar o status de outros administradores"
                )
            
            # Alterar status de ativação
            old_status = target_user.is_active
            target_user.is_active = request.is_active
            
            db.commit()
            db.refresh(target_user)
            
            status_text = "ativado" if request.is_active else "desativado"
            logger.info(f"Usuário {target_user.email} {status_text}")
            
            return UserStatusResponse(
                success=True,
                message=f"Usuário {status_text} com sucesso",
                user={
                    'id': target_user.id,
                    'email': target_user.email,
                    'nome': target_user.nome,
                    'is_active': target_user.is_active,
                    'old_status': old_status,
                    'permission': target_user.permission.value
                }
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao alterar status do usuário {user_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno ao alterar status: {str(e)}"
        )

@router.get("/users/stats", summary="Estatísticas de usuários")
async def get_users_stats():
    """
    Retorna estatísticas dos usuários por permissão.
    """
    try:
        with get_db_session() as db:
            # Contar usuários por permissão
            stats = {}
            for permission in UserPermission:
                count = db.query(User).filter(User.permission == permission).count()
                stats[permission.value] = count
            
            # Total de usuários
            total_users = db.query(User).count()
            
            # Usuários ativos e inativos
            active_users = db.query(User).filter(User.is_active == True).count()
            inactive_users = db.query(User).filter(User.is_active == False).count()
            
            # Usuários com login recente (últimos 30 dias)
            from datetime import datetime, timedelta
            thirty_days_ago = datetime.now() - timedelta(days=30)
            recent_logins = db.query(User).filter(User.ultimo_login >= thirty_days_ago).count()
            
            return {
                "success": True,
                "statistics": {
                    "total_users": total_users,
                    "permission_stats": stats,
                    "active_users": active_users,
                    "inactive_users": inactive_users,
                    "recent_logins_30_days": recent_logins,
                    "generated_at": datetime.now().isoformat()
                },
                "message": "Estatísticas de usuários obtidas com sucesso"
            }
            
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas de usuários: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno ao obter estatísticas: {str(e)}"
        )

# ==================== ENDPOINTS DE INSTITUIÇÕES ====================

@router.post("/institutions", response_model=InstitutionResponse, summary="Cadastrar nova instituição")
async def create_institution(request: InstitutionCreateRequest):
    """
    Cadastra uma nova instituição.
    
    Apenas administradores podem cadastrar instituições.
    """
    try:
        with get_db_session() as db:
            # Verificar se já existe uma instituição com o mesmo nome E cidade
            existing_institution = db.query(Institution).filter(
                Institution.nome == request.nome,
                Institution.cidade == request.cidade
            ).first()
            if existing_institution:
                raise HTTPException(
                    status_code=400,
                    detail=f"Já existe uma instituição com o nome '{request.nome}' na cidade '{request.cidade}'"
                )
            
            # Criar nova instituição
            new_institution = Institution(
                nome=request.nome,
                cidade=request.cidade,
                pfsense_base_url=request.pfsense_base_url,
                pfsense_key=request.pfsense_key,
                zeek_base_url=request.zeek_base_url,
                zeek_key=request.zeek_key,
                suricata_base_url=request.suricata_base_url,
                suricata_key=request.suricata_key,
                ip_range_start=request.ip_range_start,
                ip_range_end=request.ip_range_end,
                is_active=True
            )
            
            db.add(new_institution)
            db.commit()
            db.refresh(new_institution)
            
            logger.info(f"Nova instituição cadastrada: {new_institution.nome} em {new_institution.cidade}")
            
            return InstitutionResponse(
                success=True,
                message=f"Instituição '{new_institution.nome}' cadastrada com sucesso",
                institution=new_institution.to_dict()
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao cadastrar instituição: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno ao cadastrar instituição: {str(e)}"
        )

@router.get("/institutions", response_model=InstitutionListResponse, summary="Listar instituições")
async def list_institutions(
    is_active: bool = Query(None, description="Filtrar por status ativo/inativo"),
    limit: int = Query(100, ge=1, le=500, description="Limite de resultados")
):
    """
    Lista todas as instituições cadastradas.
    
    Apenas administradores podem acessar este endpoint.
    """
    try:
        with get_db_session() as db:
            query = db.query(Institution)
            
            # Filtrar por status se especificado
            if is_active is not None:
                query = query.filter(Institution.is_active == is_active)
            
            institutions = query.limit(limit).all()
            
            institutions_data = [institution.to_dict() for institution in institutions]
            
            return InstitutionListResponse(
                success=True,
                count=len(institutions_data),
                institutions=institutions_data,
                message=f"Listadas {len(institutions_data)} instituições"
            )
            
    except Exception as e:
        logger.error(f"Erro ao listar instituições: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno ao listar instituições: {str(e)}"
        )

@router.get("/institutions/{institution_id}", response_model=InstitutionResponse, summary="Obter instituição por ID")
async def get_institution(institution_id: int):
    """
    Obtém uma instituição específica por ID.
    
    Apenas administradores podem acessar este endpoint.
    """
    try:
        with get_db_session() as db:
            institution = db.query(Institution).filter(Institution.id == institution_id).first()
            
            if not institution:
                raise HTTPException(
                    status_code=404,
                    detail=f"Instituição com ID {institution_id} não encontrada"
                )
            
            return InstitutionResponse(
                success=True,
                message=f"Instituição '{institution.nome}' obtida com sucesso",
                institution=institution.to_dict()
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao obter instituição {institution_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno ao obter instituição: {str(e)}"
        )

@router.put("/institutions/{institution_id}", response_model=InstitutionResponse, summary="Atualizar instituição")
async def update_institution(institution_id: int, request: InstitutionUpdateRequest, http_request: Request):
    """
    Atualiza uma instituição existente.
    
    Apenas administradores podem atualizar instituições.
    Se o usuário for ADMIN (não SUPERUSER), só pode editar sua própria rede (institution_id).
    """
    try:
        with get_db_session() as db:
            institution = db.query(Institution).filter(Institution.id == institution_id).first()
            
            if not institution:
                raise HTTPException(
                    status_code=404,
                    detail=f"Instituição com ID {institution_id} não encontrada"
                )
            
            # Verificar se o usuário atual é ADMIN (não SUPERUSER) e se está tentando editar outra rede
            if http_request:
                user_email = http_request.session.get("email")
                if user_email:
                    current_user = db.query(User).filter(User.email == user_email).first()
                    if current_user:
                        # Se for ADMIN ou MANAGER (não SUPERUSER) e tiver institution_id, só pode editar sua própria rede
                        current_permission = current_user.permission.value if hasattr(current_user.permission, 'value') else str(current_user.permission)
                        if current_permission in ["ADMIN", "MANAGER"] and current_user.institution_id:
                            if current_user.institution_id != institution_id:
                                raise HTTPException(
                                    status_code=403,
                                    detail="Você só pode editar a rede atribuída a você"
                                )
            
            # Verificar se o nome e cidade já existem em outra instituição
            if request.nome and request.cidade:
                existing_institution = db.query(Institution).filter(
                    Institution.nome == request.nome,
                    Institution.cidade == request.cidade,
                    Institution.id != institution_id
                ).first()
                if existing_institution:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Já existe uma instituição com o nome '{request.nome}' na cidade '{request.cidade}'"
                    )
            
            # Atualizar campos fornecidos
            update_data = request.dict(exclude_unset=True)
            for field, value in update_data.items():
                if hasattr(institution, field):
                    setattr(institution, field, value)
            
            db.commit()
            db.refresh(institution)
            
            logger.info(f"Instituição atualizada: {institution.nome}")
            
            return InstitutionResponse(
                success=True,
                message=f"Instituição '{institution.nome}' atualizada com sucesso",
                institution=institution.to_dict()
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao atualizar instituição {institution_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno ao atualizar instituição: {str(e)}"
        )

@router.delete("/institutions/{institution_id}", summary="Excluir instituição")
async def delete_institution(institution_id: int):
    """
    Exclui uma instituição.
    
    Apenas administradores podem excluir instituições.
    ATENÇÃO: Esta ação é irreversível!
    """
    try:
        with get_db_session() as db:
            institution = db.query(Institution).filter(Institution.id == institution_id).first()
            
            if not institution:
                raise HTTPException(
                    status_code=404,
                    detail=f"Instituição com ID {institution_id} não encontrada"
                )
            
            institution_name = institution.nome
            
            # Verificar se há usuários associados à instituição
            users_count = db.query(User).filter(User.instituicao == institution_name).count()
            if users_count > 0:
                raise HTTPException(
                    status_code=400,
                    detail=f"Não é possível excluir a instituição '{institution_name}' pois há {users_count} usuário(s) associado(s) a ela"
                )
            
            db.delete(institution)
            db.commit()
            
            logger.info(f"Instituição excluída: {institution_name}")
            
            return {
                "success": True,
                "message": f"Instituição '{institution_name}' excluída com sucesso"
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao excluir instituição {institution_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno ao excluir instituição: {str(e)}"
        )

@router.put("/institutions/{institution_id}/toggle-status", response_model=InstitutionResponse, summary="Alternar status da instituição")
async def toggle_institution_status(institution_id: int):
    """
    Alterna o status de ativação de uma instituição.
    
    Apenas administradores podem alterar o status de instituições.
    """
    try:
        with get_db_session() as db:
            institution = db.query(Institution).filter(Institution.id == institution_id).first()
            
            if not institution:
                raise HTTPException(
                    status_code=404,
                    detail=f"Instituição com ID {institution_id} não encontrada"
                )
            
            old_status = institution.is_active
            new_status = institution.toggle_active_status()
            
            db.commit()
            db.refresh(institution)
            
            status_text = "ativada" if new_status else "desativada"
            logger.info(f"Instituição {institution.nome} {status_text}")
            
            return InstitutionResponse(
                success=True,
                message=f"Instituição '{institution.nome}' {status_text} com sucesso",
                institution=institution.to_dict()
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao alternar status da instituição {institution_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno ao alternar status: {str(e)}"
        )

# Modelos Pydantic para gestores
class ManagerAssignmentRequest(BaseModel):
    user_id: int

class ManagerAssignmentResponse(BaseModel):
    success: bool
    message: str
    institution: Dict[str, Any]
    manager: Dict[str, Any]

class ManagerRemovalResponse(BaseModel):
    success: bool
    message: str
    institution: Dict[str, Any]

class InstitutionManagersResponse(BaseModel):
    success: bool
    institution: Dict[str, Any]
    managers: List[Dict[str, Any]]

# Endpoints para gerenciar gestores
@router.post("/institutions/{institution_id}/managers", response_model=ManagerAssignmentResponse, summary="Adicionar administrador ao campus")
async def add_manager_to_institution(institution_id: int, request: ManagerAssignmentRequest):
    """
    Adiciona um usuário como administrador de um campus específico.
    
    O usuário deve ter permissão ADMIN para ser atribuído.
    """
    try:
        with get_db_session() as db:
            # Verificar se a instituição existe
            institution = db.query(Institution).filter(Institution.id == institution_id).first()
            if not institution:
                raise HTTPException(
                    status_code=404,
                    detail=f"Instituição com ID {institution_id} não encontrada"
                )
            
            # Verificar se o usuário existe
            user = db.query(User).filter(User.id == request.user_id).first()
            if not user:
                raise HTTPException(
                    status_code=404,
                    detail=f"Usuário com ID {request.user_id} não encontrado"
                )
            
            # Verificar se o usuário é ADMIN
            if user.permission != UserPermission.ADMIN:
                raise HTTPException(
                    status_code=400,
                    detail=f"Usuário '{user.nome}' não possui permissão ADMIN"
                )
            
            # Verificar se já é administrador de outro campus
            if user.institution_id and user.institution_id != institution_id:
                other_institution = db.query(Institution).filter(Institution.id == user.institution_id).first()
                raise HTTPException(
                    status_code=400,
                    detail=f"Usuário '{user.nome}' já é administrador do campus '{other_institution.nome} - {other_institution.cidade}'"
                )
            
            # Atribuir administrador ao campus
            user.institution_id = institution_id
            db.commit()
            db.refresh(user)
            db.refresh(institution)
            
            logger.info(f"Administrador '{user.nome}' adicionado ao campus '{institution.nome} - {institution.cidade}'")
            
            return ManagerAssignmentResponse(
                success=True,
                message=f"Administrador '{user.nome}' adicionado ao campus '{institution.nome} - {institution.cidade}' com sucesso",
                institution=institution.to_dict(),
                manager=user.to_dict()
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao adicionar administrador {request.user_id} à instituição {institution_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno ao adicionar administrador: {str(e)}"
        )

@router.delete("/institutions/{institution_id}/managers/{user_id}", response_model=ManagerRemovalResponse, summary="Remover administrador do campus")
async def remove_manager_from_institution(institution_id: int, user_id: int):
    """
    Remove um usuário como administrador de um campus específico.
    """
    try:
        with get_db_session() as db:
            # Verificar se a instituição existe
            institution = db.query(Institution).filter(Institution.id == institution_id).first()
            if not institution:
                raise HTTPException(
                    status_code=404,
                    detail=f"Instituição com ID {institution_id} não encontrada"
                )
            
            # Verificar se o usuário existe
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise HTTPException(
                    status_code=404,
                    detail=f"Usuário com ID {user_id} não encontrado"
                )
            
            # Verificar se é administrador deste campus
            if user.institution_id != institution_id:
                raise HTTPException(
                    status_code=400,
                    detail=f"Usuário '{user.nome}' não é administrador deste campus"
                )
            
            # Remover administrador do campus
            user.institution_id = None
            db.commit()
            db.refresh(institution)
            
            logger.info(f"Administrador '{user.nome}' removido do campus '{institution.nome} - {institution.cidade}'")
            
            return ManagerRemovalResponse(
                success=True,
                message=f"Administrador '{user.nome}' removido do campus '{institution.nome} - {institution.cidade}' com sucesso",
                institution=institution.to_dict()
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao remover administrador {user_id} da instituição {institution_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno ao remover administrador: {str(e)}"
        )

@router.get("/institutions/{institution_id}/managers", response_model=InstitutionManagersResponse, summary="Listar administradores do campus")
async def get_institution_managers(institution_id: int):
    """
    Lista todos os administradores de um campus específico.
    """
    try:
        with get_db_session() as db:
            # Verificar se a instituição existe
            institution = db.query(Institution).filter(Institution.id == institution_id).first()
            if not institution:
                raise HTTPException(
                    status_code=404,
                    detail=f"Instituição com ID {institution_id} não encontrada"
                )
            
            # Buscar administradores do campus (permissão ADMIN)
            managers = db.query(User).filter(
                User.institution_id == institution_id,
                User.permission == UserPermission.ADMIN,
                User.is_active == True
            ).all()
            
            managers_data = [manager.to_dict() for manager in managers]
            
            return InstitutionManagersResponse(
                success=True,
                institution=institution.to_dict(),
                managers=managers_data
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao listar administradores da instituição {institution_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno ao listar administradores: {str(e)}"
        )

@router.get("/users/managers/available", summary="Listar administradores disponíveis")
async def get_available_managers():
    """
    Lista todos os usuários com permissão ADMIN que não estão atribuídos a nenhum campus.
    """
    try:
        with get_db_session() as db:
            # Buscar administradores não atribuídos (permissão ADMIN)
            available_managers = db.query(User).filter(
                User.permission == UserPermission.ADMIN,
                User.institution_id.is_(None),
                User.is_active == True
            ).all()
            
            managers_data = [manager.to_dict() for manager in available_managers]
            
            return {
                "success": True,
                "available_managers": managers_data,
                "count": len(managers_data)
            }
            
    except Exception as e:
        logger.error(f"Erro ao listar administradores disponíveis: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno ao listar administradores disponíveis: {str(e)}"
        )
