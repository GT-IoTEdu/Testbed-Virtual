from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from services_firewalls.router import router as devices_router
from services_firewalls.blocking_feedback_router import router as feedback_router
from services_scanners.zeek_router import router as zeek_router
from services_scanners.incident_router import router as incident_router
from auth.cafe_auth import router as cafe_auth_router
from auth.google_auth import router as google_auth_router
from auth.saml_router import router as saml_router
from dotenv import load_dotenv
import os
import config

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

app = FastAPI(
    title="IoT-EDU API", 
    description="Gerenciamento seguro de dispositivos IoT em ambientes acadêmicos com autenticação SAML CAFe",
    version="2.0.0"
)

# Configuração CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especifique os domínios permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Session middleware para OAuth (necessário para request.session)
app.add_middleware(
    SessionMiddleware,
    secret_key=config.JWT_SECRET_KEY,
)

# Incluir routers
app.include_router(devices_router, prefix="/api/devices", tags=["Dispositivos e pfSense"])
app.include_router(feedback_router, prefix="/api", tags=["Feedback de Bloqueio"])
app.include_router(zeek_router, prefix="/api/scanners", tags=["Zeek Network Monitor"])
app.include_router(incident_router, prefix="/api", tags=["Incidentes de Segurança"])
app.include_router(cafe_auth_router, prefix="/api/auth/cafe", tags=["Autenticação CAFe"])
app.include_router(google_auth_router, prefix="/api/auth", tags=["Autenticação Google OAuth2"])
app.include_router(saml_router, tags=["Autenticação SAML CAFe"])

@app.get("/", summary="Página inicial")
async def root():
    """
    Página inicial da API IoT-EDU.
    
    Returns:
        dict: Informações sobre a API
    """
    return {
        "message": "IoT-EDU API - Gerenciamento seguro de dispositivos IoT",
        "version": "2.0.0",
        "authentication": {
            "saml_cafe": "/auth/login",
            "cafe_oauth": "/api/auth/cafe/login",
            "google_oauth": "/api/auth/login"
        },
        "endpoints": {
            "devices": "/api/devices/",
            "aliases": "/api/devices/aliases/",
            "dhcp": "/api/devices/dhcp/",
            "feedback": "/api/feedback/",
            "feedback_stats": "/api/feedback/stats",
            "zeek_logs": "/api/scanners/zeek/logs",
            "zeek_incidents": "/api/scanners/zeek/incidents",
            "incidents_db": "/api/incidents/",
            "auth_status": "/auth/status"
        },
        "documentation": "/docs"
    }

@app.get("/health", summary="Verificação de saúde")
async def health_check():
    """
    Endpoint para verificação de saúde da API.
    
    Returns:
        dict: Status da API
    """
    return {
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00Z",
        "version": "2.0.0"
    } 