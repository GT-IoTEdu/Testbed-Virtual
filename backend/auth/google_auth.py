import os
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse, HTMLResponse
from starlette.middleware.sessions import SessionMiddleware
from google_auth_oauthlib.flow import Flow
from starlette.config import Config
import httpx
from datetime import datetime
from db.session import SessionLocal
from db.models import User
from db.enums import UserPermission
from typing import Optional
from pydantic import BaseModel
import config as app_config

router = APIRouter()

config = Config(".env")
GOOGLE_CLIENT_ID = config("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = config("GOOGLE_CLIENT_SECRET")
SECRET_KEY = config("SECRET_KEY", cast=str, default="supersecret")

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"  # Para testes locais

REDIRECT_URI = "http://localhost:8000/api/auth/google/callback"

def get_flow():
    return Flow.from_client_config(
        {
            "web": {
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [REDIRECT_URI],
            }
        },
        scopes=[
            "openid",
            "https://www.googleapis.com/auth/userinfo.email",
            "https://www.googleapis.com/auth/userinfo.profile"
        ],
        redirect_uri=REDIRECT_URI,
    )

@router.get("/google/login")
async def google_login(request: Request):
    flow = get_flow()
    authorization_url, state = flow.authorization_url()
    request.session["state"] = state
    return RedirectResponse(authorization_url)

@router.get("/google/callback")
async def google_callback(request: Request):
    try:
        state = request.session.get("state")
        if not state:
            raise HTTPException(status_code=400, detail="State not found in session")

        flow = get_flow()
        flow.fetch_token(authorization_response=str(request.url))
        credentials = flow.credentials

        if not credentials or not credentials.id_token:
            raise HTTPException(status_code=400, detail="Invalid credentials")

        # Buscar dados do usuário
        async with httpx.AsyncClient() as client:
            userinfo_response = await client.get(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                headers={"Authorization": f"Bearer {credentials.token}"},
            )
            userinfo = userinfo_response.json()

        email = userinfo.get("email")
        name = userinfo.get("name")
        sub = userinfo.get("sub") or userinfo.get("id")
        picture = userinfo.get("picture")
        if not email:
            raise HTTPException(status_code=400, detail="Email não encontrado no perfil do Google")

        # Verificar se o email corresponde ao admin configurado
        admin_email = app_config.SUPERUSER_ACCESS
        is_admin_email = email.lower() == admin_email.lower() if admin_email else False

        # Criar/atualizar usuário no banco
        with SessionLocal() as db:
            user = db.query(User).filter(User.email == email).first()
            
            # Determinar permissão inicial
            initial_permission = UserPermission.SUPERUSER if is_admin_email else UserPermission.USER
            
            if user is None:
                # Criar novo usuário
                user = User(
                    email=email,
                    nome=name,
                    instituicao="IoT-EDU" if is_admin_email else None,
                    permission=initial_permission,
                    google_sub=sub,
                    picture=picture,
                    is_active=True
                )
            else:
                # Verificar se o usuário está ativo antes de permitir login
                if not user.is_active:
                    import logging
                    logger_auth = logging.getLogger(__name__)
                    logger_auth.warning(f"🚫 Tentativa de login com usuário inativo: {email}")
                    raise HTTPException(
                        status_code=403,
                        detail="Sua conta está desativada. Entre em contato com o administrador do sistema."
                    )
                
                # Atualizar usuário existente
                if name:
                    user.nome = name
                if sub and not user.google_sub:
                    user.google_sub = sub
                if picture:
                    user.picture = picture
                
                # Se é o email do admin, garantir permissão SUPERUSER (sempre verificar e atualizar se necessário)
                if is_admin_email:
                    if user.permission != UserPermission.SUPERUSER:
                        user.permission = UserPermission.SUPERUSER
                    if not user.instituicao:
                        user.instituicao = "IoT-EDU"
            
            user.ultimo_login = datetime.utcnow()
            db.add(user)
            db.commit()
            db.refresh(user)
            
            # Garantir que a permissão está correta após refresh (para caso de usuário já existente)
            if is_admin_email and user.permission != UserPermission.SUPERUSER:
                user.permission = UserPermission.SUPERUSER
                db.commit()
                db.refresh(user)
            
            # Se o usuário não tem institution_id e não é admin, tentar detectar automaticamente pelo IP
            if not user.institution_id and not is_admin_email:
                try:
                    from services_firewalls.request_utils import get_client_ip
                    from services_firewalls.institution_config_service import InstitutionConfigService
                    import logging
                    logger_auth = logging.getLogger(__name__)
                    
                    client_ip = get_client_ip(request)
                    if client_ip:
                        logger_auth.info(f"🔍 Novo login: usuário {user.email} (ID: {user.id}) não possui instituição. Tentando detectar pelo IP: {client_ip}")
                        detected_institution_id = InstitutionConfigService.get_institution_by_ip(client_ip)
                        if detected_institution_id:
                            logger_auth.info(f"✅ Instituição detectada no login para {user.email}: ID {detected_institution_id} (IP: {client_ip})")
                            user.institution_id = detected_institution_id
                            db.commit()
                            db.refresh(user)
                        else:
                            logger_auth.warning(f"⚠️ Não foi possível detectar instituição para {user.email} pelo IP {client_ip} durante o login")
                    else:
                        logger_auth.warning(f"⚠️ Não foi possível capturar IP de origem durante login para {user.email}")
                except Exception as e:
                    import logging
                    logger_auth = logging.getLogger(__name__)
                    logger_auth.warning(f"⚠️ Erro ao detectar instituição durante login: {e}")
                    # Não falhar o login se a detecção der erro

        # Persistir identificação mínima na sessão (para /api/auth/me)
        try:
            request.session["email"] = email
        except Exception:
            pass

        # Obter permissão final do usuário (garantir que está correta)
        # Se for email do admin, sempre retornar SUPERUSER
        if is_admin_email:
            final_permission = 'SUPERUSER'
        else:
            final_permission = user.permission.value if user and getattr(user, 'permission', None) else 'USER'
        
        return HTMLResponse(f"""
        <script>
          window.opener.postMessage({{
            provider: "google",
            id: {userinfo.get('id') if userinfo.get('id') else 'null'},
            user_id: {user.id if user else 'null'},
            name: "{userinfo.get('name') or ''}",
            email: "{userinfo.get('email') or ''}",
            picture: "{userinfo.get('picture') or ''}",
            permission: "{final_permission}"
          }}, "*");
          window.close();
        </script>
        """)
    except Exception as e:
        import traceback
        print("Erro no callback do Google:", e)
        traceback.print_exc()
        return HTMLResponse(f"<h1>Erro interno</h1><pre>{e}</pre>", status_code=500)

@router.api_route("/health", methods=["GET", "HEAD"])
async def health_check():
    return {"status": "ok"}

@router.post("/logout")
async def logout(request: Request):
    """Finaliza sessão do usuário no backend (limpa dados básicos da sessão)."""
    try:
        if hasattr(request, "session"):
            request.session.clear()
    except Exception:
        pass
    return {"ok": True}

@router.get("/me")
async def get_me(request: Request, email: Optional[str] = None):
    """
    Retorna informações do usuário autenticado.
    - Tenta pegar o email da sessão se não vier por query.
    - Em ambiente dev, aceita ?email= para facilitar testes.
    - Se o usuário não tiver institution_id, tenta detectar automaticamente pelo IP de origem.
    """
    user_email = email or request.session.get("email")
    if not user_email:
        raise HTTPException(status_code=401, detail="Não autenticado")
    with SessionLocal() as db:
        from db.models import Institution
        from services_firewalls.request_utils import get_client_ip
        from services_firewalls.institution_config_service import InstitutionConfigService
        import logging
        
        logger = logging.getLogger(__name__)
        
        user = db.query(User).filter(User.email == user_email).first()
        if not user:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")
        
        # Verificar se o usuário está ativo
        if not user.is_active:
            logger.warning(f"🚫 Tentativa de acesso com usuário inativo: {user_email}")
            raise HTTPException(
                status_code=403,
                detail="Sua conta está desativada. Entre em contato com o administrador do sistema."
            )
        
        # Se o usuário não tem institution_id, tentar detectar automaticamente pelo IP
        if not user.institution_id:
            client_ip = get_client_ip(request)
            if client_ip:
                logger.info(f"🔍 Usuário {user.email} (ID: {user.id}) não possui instituição. Tentando detectar pelo IP: {client_ip}")
                logger.info(f"📋 Headers da requisição: X-Forwarded-For={request.headers.get('X-Forwarded-For')}, X-Real-IP={request.headers.get('X-Real-IP')}, client.host={request.client.host if request.client else None}")
                
                detected_institution_id = InstitutionConfigService.get_institution_by_ip(client_ip)
                if detected_institution_id:
                    logger.info(f"✅ Instituição detectada automaticamente para {user.email}: ID {detected_institution_id} (IP: {client_ip})")
                    user.institution_id = detected_institution_id
                    db.commit()
                    db.refresh(user)
                    logger.info(f"✅ Instituição {detected_institution_id} associada ao usuário {user.email} (ID: {user.id})")
                else:
                    logger.warning(f"⚠️ Não foi possível detectar instituição para {user.email} pelo IP {client_ip}. Verifique se o IP está dentro de algum range configurado.")
            else:
                logger.warning(f"⚠️ Não foi possível capturar IP de origem para usuário {user.email} (ID: {user.id})")
        
        # Buscar informações da instituição se o usuário tiver institution_id
        institution_name = None
        institution_city = None
        if user.institution_id:
            institution = db.query(Institution).filter(Institution.id == user.institution_id).first()
            if institution:
                institution_name = institution.nome
                institution_city = institution.cidade
        
        return {
            "id": user.id,
            "email": user.email,
            "nome": user.nome,
            "instituicao": user.instituicao,
            "institution_id": user.institution_id,
            "institution_name": institution_name,
            "institution_city": institution_city,
            "permission": user.permission.value if getattr(user, "permission", None) else "USER",
            "picture": user.picture,
            "google_sub": user.google_sub,
            "ultimo_login": user.ultimo_login.isoformat() if user.ultimo_login else None,
        }

@router.get("/institutions")
async def list_available_institutions(request: Request, email: Optional[str] = None):
    """
    Lista todas as instituições disponíveis para seleção.
    Apenas usuários autenticados podem acessar este endpoint.
    """
    user_email = email or request.session.get("email")
    if not user_email:
        raise HTTPException(status_code=401, detail="Não autenticado")
    
    with SessionLocal() as db:
        from db.models import Institution
        import logging
        
        logger = logging.getLogger(__name__)
        
        # Verificar se o usuário está ativo
        user = db.query(User).filter(User.email == user_email).first()
        if not user:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")
        
        if not user.is_active:
            logger.warning(f"🚫 Tentativa de acesso com usuário inativo: {user_email}")
            raise HTTPException(
                status_code=403,
                detail="Sua conta está desativada. Entre em contato com o administrador do sistema."
            )
        
        institutions = db.query(Institution).filter(Institution.is_active == True).all()
        
        institutions_data = [
            {
                "id": inst.id,
                "nome": inst.nome,
                "cidade": inst.cidade,
            }
            for inst in institutions
        ]
        
        return {
            "success": True,
            "institutions": institutions_data,
            "count": len(institutions_data)
        }

class UpdateInstitutionRequest(BaseModel):
    institution_id: int

@router.put("/me/institution")
async def update_user_institution(
    request: Request,
    body: UpdateInstitutionRequest,
    email: Optional[str] = None
):
    """
    Atualiza a instituição do usuário autenticado.
    """
    user_email = email or request.session.get("email")
    if not user_email:
        raise HTTPException(status_code=401, detail="Não autenticado")
    
    with SessionLocal() as db:
        from db.models import Institution
        import logging
        
        logger = logging.getLogger(__name__)
        
        user = db.query(User).filter(User.email == user_email).first()
        if not user:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")
        
        # Verificar se o usuário está ativo
        if not user.is_active:
            logger.warning(f"🚫 Tentativa de acesso com usuário inativo: {user_email}")
            raise HTTPException(
                status_code=403,
                detail="Sua conta está desativada. Entre em contato com o administrador do sistema."
            )
        
        # Verificar se a instituição existe e está ativa
        institution = db.query(Institution).filter(
            Institution.id == body.institution_id,
            Institution.is_active == True
        ).first()
        
        if not institution:
            raise HTTPException(
                status_code=404,
                detail=f"Instituição com ID {body.institution_id} não encontrada ou inativa"
            )
        
        # Atualizar instituição do usuário
        old_institution_id = user.institution_id
        user.institution_id = body.institution_id
        if not user.instituicao:
            user.instituicao = institution.nome
        
        db.commit()
        db.refresh(user)
        
        logger.info(f"✅ Instituição atualizada para {user.email}: {old_institution_id} → {body.institution_id} ({institution.nome})")
        
        return {
            "success": True,
            "message": "Instituição atualizada com sucesso",
            "user_id": user.id,
            "user_email": user.email,
            "institution_id": body.institution_id,
            "institution_name": institution.nome,
            "institution_city": institution.cidade
        }

@router.post("/detect-institution")
async def detect_institution_for_user(request: Request, email: Optional[str] = None):
    """
    Endpoint para forçar detecção de instituição para um usuário.
    Útil para testar ou corrigir usuários que não foram associados automaticamente.
    """
    user_email = email or request.session.get("email")
    if not user_email:
        raise HTTPException(status_code=401, detail="Não autenticado")
    
    with SessionLocal() as db:
        from db.models import Institution
        from services_firewalls.request_utils import get_client_ip
        from services_firewalls.institution_config_service import InstitutionConfigService
        import logging
        
        logger = logging.getLogger(__name__)
        
        user = db.query(User).filter(User.email == user_email).first()
        if not user:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")
        
        client_ip = get_client_ip(request)
        if not client_ip:
            raise HTTPException(
                status_code=400,
                detail="Não foi possível capturar IP de origem. Verifique se está conectado à rede."
            )
        
        logger.info(f"🔍 Forçando detecção de instituição para {user.email} (ID: {user.id}) pelo IP: {client_ip}")
        logger.info(f"📋 Headers: X-Forwarded-For={request.headers.get('X-Forwarded-For')}, X-Real-IP={request.headers.get('X-Real-IP')}, client.host={request.client.host if request.client else None}")
        
        # Listar todas as instituições e seus ranges para debug
        institutions = db.query(Institution).filter(Institution.is_active == True).all()
        logger.info(f"📊 Instituições ativas encontradas: {len(institutions)}")
        for inst in institutions:
            logger.info(f"   - {inst.nome} (ID: {inst.id}): {inst.ip_range_start} a {inst.ip_range_end}")
        
        detected_institution_id = InstitutionConfigService.get_institution_by_ip(client_ip)
        
        if detected_institution_id:
            user.institution_id = detected_institution_id
            db.commit()
            db.refresh(user)
            
            institution = db.query(Institution).filter(Institution.id == detected_institution_id).first()
            return {
                "success": True,
                "message": f"Instituição detectada e associada com sucesso",
                "user_id": user.id,
                "user_email": user.email,
                "client_ip": client_ip,
                "institution_id": detected_institution_id,
                "institution_name": institution.nome if institution else None,
                "institution_city": institution.cidade if institution else None
            }
        else:
            return {
                "success": False,
                "message": f"IP {client_ip} não pertence a nenhuma instituição configurada",
                "user_id": user.id,
                "user_email": user.email,
                "client_ip": client_ip,
                "available_ranges": [
                    {
                        "id": inst.id,
                        "nome": inst.nome,
                        "range": f"{inst.ip_range_start} - {inst.ip_range_end}"
                    }
                    for inst in institutions
                ]
            }