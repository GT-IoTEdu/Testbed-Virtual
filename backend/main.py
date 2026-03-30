from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from services_firewalls.router import router as devices_router
from services_firewalls.blocking_feedback_router import router as feedback_router
from services_scanners.zeek_router import router as zeek_router
from services_scanners.incident_router import router as incident_router
from services_scanners.suricata_router import router as suricata_router
from services_scanners.snort_router import router as snort_router
from auth.cafe_auth import router as cafe_auth_router
from auth.google_auth import router as google_auth_router
from auth.saml_router import router as saml_router
from auth.admin_router import router as admin_router
from dotenv import load_dotenv
import os
import config
import logging

logger = logging.getLogger(__name__)

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
    allow_origins=["localhost","127.0.0.1","iot-edu.cafeexpresso.rnp.br","172.20.0.20","172.20.0.30","172.20.0.40","http://localhost:3000"],  # Em produção, especifique os domínios permitidos
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
# Router adicional para compatibilidade com rotas /api/firewalls
app.include_router(devices_router, prefix="/api/firewalls", tags=["Firewalls (Compatibilidade)"])
app.include_router(feedback_router, prefix="/api", tags=["Feedback de Bloqueio"])
app.include_router(zeek_router, prefix="/api", tags=["Zeek Network Monitor"])
app.include_router(incident_router, prefix="/api", tags=["Incidentes de Segurança"])
app.include_router(suricata_router, prefix="/api", tags=["Suricata IDS/IPS"])
app.include_router(snort_router, prefix="/api", tags=["Snort IDS/IPS"])
app.include_router(cafe_auth_router, prefix="/api/auth/cafe", tags=["Autenticação CAFe"])
app.include_router(google_auth_router, prefix="/api/auth", tags=["Autenticação Google OAuth2"])
app.include_router(saml_router, tags=["Autenticação SAML CAFe"])
app.include_router(admin_router, prefix="/api", tags=["Autenticação Administrativa"])


@app.on_event("startup")
def startup_zeek_collectors():
    """Inicia coletores em background para persistir alertas Zeek em zeek_alerts (mesmo sem dashboard aberto)."""
    try:
        from services_scanners.zeek_router import start_zeek_background_collectors
        start_zeek_background_collectors()
    except Exception as e:
        logger.warning("Startup Zeek collectors: %s", e)


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
            "saml_cafe": {
                "endpoint": "/auth/login",
                "description": "Inicia autenticação SAML CAFe (recomendado para instituições)",
                "method": "GET",
                "example": "GET /auth/login"
            },
            "cafe_oauth": {
                "endpoint": "/api/auth/cafe/login",
                "description": "Inicia autenticação OAuth2 CAFe (legacy)",
                "method": "GET",
                "example": "GET /api/auth/cafe/login"
            },
            "google_oauth": {
                "endpoint": "/api/auth/login",
                "description": "Inicia autenticação Google OAuth2",
                "method": "GET",
                "example": "GET /api/auth/login"
            },
            "admin_login": {
                "endpoint": "/api/admin/login",
                "description": "Login administrativo via Google OAuth",
                "method": "GET",
                "example": "GET /api/admin/login"
            }
        },
        "endpoints": {
            "devices": {
                "list": {
                    "endpoint": "/api/devices/dhcp/devices",
                    "description": "Lista todos os dispositivos cadastrados no banco de dados com paginação",
                    "method": "GET",
                    "query_params": {
                        "page": "Número da página (padrão: 1)",
                        "per_page": "Itens por página (padrão: 20, máximo: 100)"
                    },
                    "example": "GET /api/devices/dhcp/devices?page=1&per_page=20"
                },
                "search": {
                    "endpoint": "/api/devices/dhcp/devices/search",
                    "description": "Busca dispositivos por termo (nome, IP, MAC, descrição)",
                    "method": "GET",
                    "query_params": {
                        "query": "Termo de busca"
                    },
                    "example": "GET /api/devices/dhcp/devices/search?query=192.168.1.100"
                },
                "by_ip": {
                    "endpoint": "/api/devices/dhcp/devices/ip/{ipaddr}",
                    "description": "Busca dispositivo específico por endereço IP",
                    "method": "GET",
                    "example": "GET /api/devices/dhcp/devices/ip/192.168.1.100"
                },
                "by_mac": {
                    "endpoint": "/api/devices/dhcp/devices/mac/{mac}",
                    "description": "Busca dispositivo específico por endereço MAC",
                    "method": "GET",
                    "example": "GET /api/devices/dhcp/devices/mac/00:11:22:33:44:55"
                },
                "statistics": {
                    "endpoint": "/api/devices/dhcp/statistics",
                    "description": "Retorna estatísticas gerais dos dispositivos cadastrados",
                    "method": "GET",
                    "example": "GET /api/devices/dhcp/statistics"
                }
            },
            "aliases": {
                "list": {
                    "endpoint": "/api/devices/aliases",
                    "description": "Lista todos os aliases do pfSense ou busca por nome",
                    "method": "GET",
                    "query_params": {
                        "name": "Nome do alias (opcional, para busca)"
                    },
                    "example": "GET /api/devices/aliases?name=Bloqueados"
                },
                "get": {
                    "endpoint": "/api/devices/aliases/{name}",
                    "description": "Obtém informações detalhadas de um alias específico",
                    "method": "GET",
                    "example": "GET /api/devices/aliases/Bloqueados"
                },
                "create": {
                    "endpoint": "/api/devices/alias",
                    "description": "Cria um novo alias no pfSense",
                    "method": "POST",
                    "body": {
                        "name": "Nome do alias",
                        "type": "Tipo (host, network, port, url)",
                        "address": "Endereço ou lista de endereços",
                        "descr": "Descrição (opcional)"
                    },
                    "example": "POST /api/devices/alias"
                }
            },
            "dhcp": {
                "servers": {
                    "endpoint": "/api/devices/dhcp/servers",
                    "description": "Lista todos os servidores DHCP configurados no pfSense",
                    "method": "GET",
                    "example": "GET /api/devices/dhcp/servers"
                },
                "static_mapping": {
                    "endpoint": "/api/devices/dhcp/static_mapping",
                    "description": "Lista mapeamentos estáticos DHCP do pfSense",
                    "method": "GET",
                    "query_params": {
                        "parent_id": "ID do servidor DHCP (ex: lan)",
                        "id": "ID do mapeamento (opcional)"
                    },
                    "example": "GET /api/devices/dhcp/static_mapping?parent_id=lan"
                },
                "save": {
                    "endpoint": "/api/devices/dhcp/save",
                    "description": "Sincroniza dados DHCP do pfSense com o banco de dados",
                    "method": "POST",
                    "example": "POST /api/devices/dhcp/save"
                },
                "ip_addresses": {
                    "endpoint": "/api/devices/dhcp/ip-addresses",
                    "description": "Lista endereços IP usados e disponíveis na faixa configurada",
                    "method": "GET",
                    "example": "GET /api/devices/dhcp/ip-addresses"
                }
            },
            "firewall": {
                "rules": {
                    "endpoint": "/api/devices/firewall/rules",
                    "description": "Lista regras de firewall do pfSense",
                    "method": "GET",
                    "example": "GET /api/devices/firewall/rules"
                },
                "apply": {
                    "endpoint": "/api/devices/firewall/apply",
                    "description": "Aplica mudanças pendentes no firewall do pfSense",
                    "method": "POST",
                    "example": "POST /api/devices/firewall/apply"
                }
            },
            "pfsense": {
                "health": {
                    "endpoint": "/api/firewalls/pfsense/health",
                    "description": "Verifica se o pfSense está online e acessível",
                    "method": "GET",
                    "query_params": {
                        "current_user_id": "ID do usuário logado"
                    },
                    "example": "GET /api/firewalls/pfsense/health?current_user_id=1",
                    "response": {
                        "status": "online|offline",
                        "message": "Mensagem descritiva",
                        "online": "true|false"
                    }
                }
            },
            "feedback": {
                "create": {
                    "endpoint": "/api/feedback/",
                    "description": "Cria feedback sobre bloqueio/liberação de dispositivo",
                    "method": "POST",
                    "body": {
                        "dhcp_mapping_id": "ID do mapeamento DHCP",
                        "status": "blocked|unblocked",
                        "reason": "Motivo do bloqueio/liberação",
                        "feedback_by": "ID do usuário que criou o feedback"
                    },
                    "example": "POST /api/feedback/"
                },
                "list": {
                    "endpoint": "/api/feedback/dhcp/{dhcp_mapping_id}",
                    "description": "Lista histórico de feedbacks de um dispositivo específico",
                    "method": "GET",
                    "example": "GET /api/feedback/dhcp/123"
                },
                "stats": {
                    "endpoint": "/api/feedback/stats",
                    "description": "Retorna estatísticas de feedbacks (total, bloqueados, liberados)",
                    "method": "GET",
                    "example": "GET /api/feedback/stats"
                },
                "recent": {
                    "endpoint": "/api/feedback/recent",
                    "description": "Lista feedbacks recentes",
                    "method": "GET",
                    "query_params": {
                        "limit": "Número de resultados (padrão: 10)"
                    },
                    "example": "GET /api/feedback/recent?limit=20"
                }
            },
            "zeek": {
                "alerts": {
                    "endpoint": "/api/scanners/zeek/alerts",
                    "description": "Lista alertas do Zeek salvos no banco (paginado)",
                    "method": "GET",
                    "query_params": {
                        "user_id": "ID do usuário (opcional)",
                        "institution_id": "ID da instituição (opcional)",
                        "limit": "Itens por página",
                        "offset": "Offset para paginação"
                    },
                    "example": "GET /api/scanners/zeek/alerts?institution_id=1&limit=10"
                },
                "health": {
                    "endpoint": "/api/scanners/zeek/health",
                    "description": "Verifica se a integração com Zeek está funcionando",
                    "method": "GET",
                    "query_params": {
                        "user_id": "ID do usuário (current_user_id)",
                        "institution_id": "ID da instituição"
                    },
                    "example": "GET /api/scanners/zeek/health?current_user_id=1",
                    "response": {
                        "success": "true|false",
                        "status": "healthy|unhealthy",
                        "message": "Mensagem descritiva",
                        "configured": "true|false"
                    }
                },
                "sse_alerts": {
                    "endpoint": "/api/scanners/zeek/sse/alerts",
                    "description": "Stream SSE de alertas do Zeek em tempo real",
                    "method": "GET",
                    "query_params": {
                        "user_id": "ID do usuário",
                        "institution_id": "ID da instituição"
                    },
                    "example": "GET /api/scanners/zeek/sse/alerts?institution_id=1"
                }
            },
            "incidents": {
                "list": {
                    "endpoint": "/api/incidents/",
                    "description": "Lista incidentes de segurança detectados pelo Zeek",
                    "method": "GET",
                    "query_params": {
                        "status": "Filtrar por status (pending, processed, etc.)",
                        "severity": "Filtrar por severidade (low, medium, high, critical)",
                        "limit": "Número máximo de resultados",
                        "offset": "Offset para paginação"
                    },
                    "example": "GET /api/incidents/?status=pending&severity=high&limit=50"
                },
                "stream": {
                    "endpoint": "/api/incidents/stream",
                    "description": "Stream Server-Sent Events (SSE) de novos incidentes em tempo real",
                    "method": "GET",
                    "example": "GET /api/incidents/stream",
                    "note": "Retorna eventos SSE contínuos quando novos incidentes são detectados"
                },
                "stats": {
                    "endpoint": "/api/incidents/stats/summary",
                    "description": "Retorna estatísticas resumidas dos incidentes",
                    "method": "GET",
                    "example": "GET /api/incidents/stats/summary"
                },
                "unprocessed": {
                    "endpoint": "/api/incidents/unprocessed",
                    "description": "Lista incidentes não processados (pendentes de análise)",
                    "method": "GET",
                    "example": "GET /api/incidents/unprocessed"
                }
            },
            "admin": {
                "users": {
                    "endpoint": "/api/users",
                    "description": "Lista todos os usuários do sistema (requer permissão ADMIN ou SUPERUSER)",
                    "method": "GET",
                    "example": "GET /api/users"
                },
                "users_stats": {
                    "endpoint": "/api/users/stats",
                    "description": "Retorna estatísticas de usuários (total, por permissão, ativos/inativos)",
                    "method": "GET",
                    "example": "GET /api/users/stats"
                },
                "institutions": {
                    "endpoint": "/api/institutions",
                    "description": "Lista todas as instituições cadastradas (requer permissão SUPERUSER)",
                    "method": "GET",
                    "example": "GET /api/institutions"
                },
                "admin_info": {
                    "endpoint": "/api/info",
                    "description": "Retorna informações do administrador logado (email, permissão, instituição)",
                    "method": "GET",
                    "example": "GET /api/info"
                }
            },
            "auth_status": {
                "endpoint": "/auth/status",
                "description": "Verifica status da autenticação atual do usuário",
                "method": "GET",
                "example": "GET /auth/status"
            }
        },
        "documentation": "/docs"
    }
@app.get("/api/scanners/zeek/debug/count")
async def debug_zeek_count(user_id: int = None):
    """Debug endpoint to check Zeek alerts in database"""
    import mysql.connector
    import os
    import json
    from datetime import datetime

    try:
        # Connect directly to MySQL (same as your wait_for_db function)
        connection = mysql.connector.connect(
            host=os.getenv('MYSQL_HOST', 'mysql'),
            database=os.getenv('MYSQL_DB', 'iot_edu'),
            user=os.getenv('MYSQL_USER', 'IoT_EDU'),
            password=os.getenv('MYSQL_PASSWORD', 'sua_senha_mysql_aqui'),
            port=3306
        )

        cursor = connection.cursor(dictionary=True)

        # Get total count
        cursor.execute("SELECT COUNT(*) as total FROM zeek_alerts")
        total = cursor.fetchone()['total']

        # Get sample of recent alerts
        cursor.execute("""
            SELECT id, detected_at, signature, severity, src_ip, dest_ip, protocol
            FROM zeek_alerts
            ORDER BY detected_at DESC
            LIMIT 5
        """)
        sample = cursor.fetchall()

        # Format datetime objects for JSON serialization
        for alert in sample:
            if alert.get('detected_at'):
                alert['detected_at'] = alert['detected_at'].isoformat() if isinstance(alert['detected_at'], datetime) else str(alert['detected_at'])

        cursor.close()
        connection.close()

        return {
            "success": True,
            "total_alerts": total,
            "sample": sample,
            "table_exists": True
        }

    except mysql.connector.Error as e:
        # Check if table doesn't exist
        if e.errno == 1146:  # ER_NO_SUCH_TABLE
            return {
                "success": False,
                "error": "Table 'zeek_alerts' does not exist yet",
                "total_alerts": 0,
                "sample": [],
                "table_exists": False
            }
        else:
            return {
                "success": False,
                "error": str(e),
                "total_alerts": 0,
                "sample": []
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "total_alerts": 0,
            "sample": []
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
