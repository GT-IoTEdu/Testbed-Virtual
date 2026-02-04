#!/usr/bin/env python3
"""
Script para iniciar o servidor FastAPI com configurações corretas
"""

import uvicorn
import os
import sys

# Adicionar o diretório pai ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Carregar variáveis de ambiente
from dotenv import load_dotenv
load_dotenv()

# Verificar configurações antes de iniciar
print("🔍 Verificando configurações antes de iniciar o servidor...")
print("=" * 50)

pfsense_url = os.getenv("PFSENSE_API_URL")
pfsense_key = os.getenv("PFSENSE_API_KEY")
ip_b=os.getenv("NEXT_PUBLIC_IP_B")
port_b=os.getenv("NEXT_PUBLIC_PORT_B")

print(f"PFSENSE_API_URL: {pfsense_url}")
print(f"PFSENSE_API_KEY: {'*' * len(pfsense_key) if pfsense_key else 'NÃO DEFINIDO'}")

if not pfsense_url or not pfsense_key:
    print("❌ Configurações incompletas! Verifique o arquivo .env")
    exit(1)

print("✅ Configurações OK! Iniciando servidor...")
print("=" * 50)

# Importar e iniciar o servidor
from main import app

if __name__ == "__main__":
    print(ip_b)
    uvicorn.run(
        "main:app",
        host=ip_b,
        port=int(port_b),
        reload=True,
        log_level="info"
    ) 
