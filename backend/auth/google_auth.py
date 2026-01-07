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

router = APIRouter()

config = Config(".env")
GOOGLE_CLIENT_ID = config("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = config("GOOGLE_CLIENT_SECRET")
SECRET_KEY = config("SECRET_KEY", cast=str, default="supersecret")

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"  # Para testes locais
#ip_b=os.getenv("NEXT_PUBLIC_IP_B")
#port_b=os.getenv("NEXT_PUBLIC_PORT_B")
#url="http://"+ip_b+port_b
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

        # Criar/atualizar usuário no banco
        with SessionLocal() as db:
            user = db.query(User).filter(User.email == email).first()
            if user is None:
                user = User(
                    email=email,
                    nome=name,
                    instituicao=None,
                    permission=UserPermission.USER,
                    google_sub=sub,
                    picture=picture,
                )
            else:
                if name:
                    user.nome = name
                if sub and not user.google_sub:
                    user.google_sub = sub
                if picture:
                    user.picture = picture
            user.ultimo_login = datetime.utcnow()
            db.add(user)
            db.commit()
            db.refresh(user)

        # Persistir identificação mínima na sessão (para /api/auth/me)
        try:
            request.session["email"] = email
        except Exception:
            pass

        return HTMLResponse(f"""
        <script>
          window.opener.postMessage({{
            provider: "google",
            id: {userinfo.get('id') if userinfo.get('id') else 'null'},
            user_id: {user.id if 'user' in locals() and user else 'null'},
            name: "{userinfo.get('name')}",
            email: "{userinfo.get('email')}",
            picture: "{userinfo.get('picture')}",
            permission: "{user.permission.value if 'user' in locals() and user and getattr(user, 'permission', None) else 'USER'}"
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
    Retorna dados do usuário autenticado.
    - Tenta pegar o email da sessão se não vier por query.
    - Em ambiente dev, aceita ?email= para facilitar testes.
    """
    user_email = email or request.session.get("email")
    if not user_email:
        raise HTTPException(status_code=401, detail="Não autenticado")
    with SessionLocal() as db:
        user = db.query(User).filter(User.email == user_email).first()
        if not user:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")
        return {
            "id": user.id,
            "email": user.email,
            "nome": user.nome,
            "instituicao": user.instituicao,
            "permission": user.permission.value if getattr(user, "permission", None) else "USER",
            "picture": user.picture,
            "google_sub": user.google_sub,
            "ultimo_login": user.ultimo_login.isoformat() if user.ultimo_login else None,
        }
