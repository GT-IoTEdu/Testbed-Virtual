"""
Módulo de autenticação Google OAuth2 para o backend IoT-EDU.

Este módulo expõe endpoints para:
- Iniciar o fluxo de autenticação Google OAuth2
- Receber o callback do provedor Google
- Salvar/atualizar usuários autenticados no banco de dados

Utiliza Authlib para integração OAuth2/OpenID Connect.
"""
from fastapi import APIRouter, Request, Response
from fastapi.responses import RedirectResponse, JSONResponse
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config
from starlette.requests import Request as StarletteRequest
import config
from db.session import SessionLocal
from db.models import User, Base
from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound

router = APIRouter()

# Configuração OAuth2 para Google
starlette_config = Config(environ={
    'GOOGLE_CLIENT_ID': config.GOOGLE_CLIENT_ID,
    'GOOGLE_CLIENT_SECRET': config.GOOGLE_CLIENT_SECRET,
})
oauth = OAuth(starlette_config)
oauth.register(
    name='google',
    client_id=config.GOOGLE_CLIENT_ID,
    client_secret=config.GOOGLE_CLIENT_SECRET,
    access_token_url='https://accounts.google.com/o/oauth2/token',
    access_token_params=None,
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    authorize_params=None,
    api_base_url='https://www.googleapis.com/oauth2/v1/',
    client_kwargs={'scope': 'openid email profile'},
)

@router.get("/login", summary="Iniciar autenticação federada CAFe")
def cafe_login(request: Request):
    """
    Inicia o fluxo de autenticação federada CAFe.
    Redireciona o usuário para o provedor CAFe (OAuth2/SAML).
    Parâmetros:
        request (Request): Requisição FastAPI.
    Retorna:
        RedirectResponse para o provedor CAFe.
    """
    redirect_uri = config.CAFE_REDIRECT_URI
    return oauth.cafe.authorize_redirect(request, redirect_uri)

@router.get("/callback", summary="Callback OAuth2 CAFe")
async def cafe_callback(request: Request):
    """
    Endpoint de callback para o fluxo OAuth2 CAFe.
    Recebe o código/token do provedor, valida, obtém dados do usuário e salva/atualiza no banco.
    Parâmetros:
        request (Request): Requisição FastAPI.
    Retorna:
        JSON com token, dados do usuário e instituição.
    """
    token = await oauth.cafe.authorize_access_token(request)
    user = await oauth.cafe.parse_id_token(request, token)
    instituicao = user.get('schacHomeOrganization') or user.get('email', '').split('@')[-1]
    user['instituicao'] = instituicao
    nome = user.get('name') or user.get('preferred_username') or user.get('email')
    email = user.get('email')

    # Salvar/atualizar usuário no banco
    db: Session = SessionLocal()
    try:
        db_user = db.query(User).filter(User.email == email).one_or_none()
        if db_user:
            db_user.nome = nome
            db_user.instituicao = instituicao
        else:
            db_user = User(email=email, nome=nome, instituicao=instituicao)
            db.add(db_user)
        db.commit()
    finally:
        db.close()

    return JSONResponse({"token": token, "user": user, "instituicao": instituicao}) 