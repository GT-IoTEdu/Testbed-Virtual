#!/usr/bin/env python3
"""
Script para iniciar o servidor FastAPI
"""

import uvicorn
import os
import sys

# Adicionar o diretório pai ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Carregar variáveis de ambiente
from dotenv import load_dotenv
load_dotenv()

mysql_user = os.getenv("MYSQL_USER")
mysql_password = os.getenv("MYSQL_PASSWORD")
ip_b=os.getenv("NEXT_PUBLIC_IP_B")
port_b=os.getenv("NEXT_PUBLIC_PORT_B")

if not mysql_user or not mysql_password:
    print("❌ ERRO: MYSQL_USER e MYSQL_PASSWORD devem estar definidos no arquivo .env")
    sys.exit(1)

print("✅ Configurações OK! Iniciando servidor...")
print("=" * 50)

if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app",
        host=ip_b,
        port=int(port_b),
        reload=True,
        log_level="info"
    )
