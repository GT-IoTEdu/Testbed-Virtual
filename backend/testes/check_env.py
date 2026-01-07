#!/usr/bin/env python3
"""
Script para verificar se as configurações do .env estão funcionando
"""

import os
import sys
from dotenv import load_dotenv

# Cores para output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def log(message, color=Colors.GREEN):
    """Função para log colorido"""
    print(f"{color}{message}{Colors.END}")

def check_env_variable(name, required=True, show_value=False):
    """Verifica se uma variável de ambiente está configurada"""
    value = os.getenv(name)
    
    if value:
        if show_value:
            # Mostrar apenas os primeiros caracteres para segurança
            display_value = value[:10] + "..." if len(value) > 10 else value
            log(f"✅ {name}: {display_value}")
        else:
            log(f"✅ {name}: Configurado")
        return True
    else:
        if required:
            log(f"❌ {name}: NÃO CONFIGURADO", Colors.RED)
        else:
            log(f"⚠️ {name}: Não configurado (opcional)", Colors.YELLOW)
        return False

def main():
    """Função principal"""
    log("🔍 Verificando configurações do .env", Colors.BOLD)
    log("="*50, Colors.BOLD)
    
    # Carregar variáveis de ambiente
    load_dotenv()
    
    # Verificar variáveis essenciais
    log("\n📋 Variáveis Essenciais:", Colors.BLUE)
    essential_vars = [
        "PFSENSE_API_URL",
        "PFSENSE_API_KEY",
        "MYSQL_USER",
        "MYSQL_HOST",
        "JWT_SECRET_KEY"
    ]
    
    essential_count = 0
    for var in essential_vars:
        if check_env_variable(var, required=True, show_value=True):
            essential_count += 1
    
    # Verificar variáveis opcionais
    log("\n📋 Variáveis Opcionais:", Colors.BLUE)
    optional_vars = [
        "MYSQL_PASSWORD",
        "MYSQL_DB",
        "CAFE_REDIRECT_URI",
        "DEBUG",
        "SECRET_KEY",
        "ALLOWED_HOSTS"
    ]
    
    optional_count = 0
    for var in optional_vars:
        if check_env_variable(var, required=False, show_value=False):
            optional_count += 1
    
    # Relatório final
    log("\n" + "="*50, Colors.BOLD)
    log("📊 RELATÓRIO", Colors.BOLD)
    log("="*50, Colors.BOLD)
    log(f"✅ Variáveis essenciais: {essential_count}/{len(essential_vars)}")
    log(f"⚠️ Variáveis opcionais: {optional_count}/{len(optional_vars)}")
    
    if essential_count == len(essential_vars):
        log("\n🎉 Todas as variáveis essenciais estão configuradas!", Colors.GREEN)
        log("✅ O arquivo .env está pronto para uso", Colors.GREEN)
    else:
        log("\n❌ Algumas variáveis essenciais estão faltando", Colors.RED)
        log("🔧 Configure as variáveis faltantes no arquivo .env", Colors.YELLOW)
    
    # Verificar configurações específicas
    log("\n🔍 Verificações Específicas:", Colors.BLUE)
    
    # Verificar URL do pfSense
    pfsense_url = os.getenv("PFSENSE_API_URL")
    if pfsense_url and pfsense_url.endswith("/"):
        log("✅ PFSENSE_API_URL termina com / (correto)")
    elif pfsense_url:
        log("⚠️ PFSENSE_API_URL não termina com / (pode causar problemas)")
    else:
        log("❌ PFSENSE_API_URL não configurada")
    
    # Verificar chave da API
    pfsense_key = os.getenv("PFSENSE_API_KEY")
    if pfsense_key and len(pfsense_key) > 50:
        log("✅ PFSENSE_API_KEY parece válida (longa o suficiente)")
    elif pfsense_key:
        log("⚠️ PFSENSE_API_KEY parece muito curta")
    else:
        log("❌ PFSENSE_API_KEY não configurada")
    
    # Verificar configurações de desenvolvimento
    debug = os.getenv("DEBUG", "False").lower()
    if debug == "true":
        log("✅ DEBUG=True (modo desenvolvimento)")
    else:
        log("⚠️ DEBUG=False (modo produção)")
    
    return essential_count == len(essential_vars)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 