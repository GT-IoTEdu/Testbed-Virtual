#!/usr/bin/env python3
"""
Script para testar todos os endpoints do FastAPI localmente
"""

import requests
import json
import sys
import time

# Configurações
BASE_URL = "http://127.0.0.1:8000"
API_BASE_URL = f"{BASE_URL}/api"
AUTH_BASE_URL = f"{BASE_URL}/auth"

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

def test_endpoint(url, name, method="GET", data=None):
    """Testa um endpoint específico"""
    try:
        log(f"🔍 Testando: {name}")
        
        if method.upper() == "GET":
            response = requests.get(url, timeout=10)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, timeout=10)
        else:
            log(f"❌ Método {method} não suportado", Colors.RED)
            return False
        
        if response.status_code == 200:
            log(f"✅ {name}: OK (Status: {response.status_code})", Colors.GREEN)
            
            # Mostrar resposta se for JSON
            try:
                json_response = response.json()
                log(f"📄 Resposta: {json.dumps(json_response, indent=2)}", Colors.YELLOW)
            except:
                log(f"📄 Resposta: {response.text[:200]}...", Colors.YELLOW)
            
            return True
        else:
            log(f"❌ {name}: Status {response.status_code}", Colors.RED)
            if response.text:
                log(f"   Erro: {response.text[:200]}...", Colors.YELLOW)
            return False
            
    except Exception as e:
        log(f"❌ {name}: Erro - {e}", Colors.RED)
        return False

def main():
    """Função principal"""
    log("🚀 Testando FastAPI Localmente", Colors.BOLD)
    log(f"🌐 URL Base: {BASE_URL}")
    log(f"⏰ Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    log("="*50, Colors.BOLD)
    
    # Testes essenciais
    tests = [
        (f"{BASE_URL}/", "Página Principal"),
        (f"{BASE_URL}/health", "Health Check"),
        (f"{BASE_URL}/docs", "Documentação"),
        (f"{BASE_URL}/openapi.json", "OpenAPI Schema"),
        (f"{API_BASE_URL}/devices/", "API Dispositivos"),
        (f"{API_BASE_URL}/devices/aliases/", "API Aliases"),
        (f"{API_BASE_URL}/devices/dhcp/servers", "API DHCP Servers"),
        (f"{API_BASE_URL}/devices/dhcp/static_mapping?parent_id=lan&id=6", "API DHCP Static Mapping"),
        (f"{AUTH_BASE_URL}/status", "Status de Autenticação"),
        (f"{AUTH_BASE_URL}/metadata", "Metadados de Autenticação")
    ]
    
    passed = 0
    total = len(tests)
    
    for url, name in tests:
        if test_endpoint(url, name):
            passed += 1
        log("")  # Linha em branco entre testes
    
    # Relatório final
    log("="*50, Colors.BOLD)
    log("📊 RELATÓRIO FINAL", Colors.BOLD)
    log("="*50, Colors.BOLD)
    log(f"✅ Passaram: {passed}/{total}")
    log(f"❌ Falharam: {total - passed}/{total}")
    
    if passed == total:
        log("🎉 TODOS OS ENDPOINTS LOCAIS ESTÃO FUNCIONANDO!", Colors.GREEN)
        log("✅ O problema está na configuração do proxy reverso no Apache", Colors.YELLOW)
    elif passed >= total * 0.7:
        log("⚠️ A maioria dos endpoints está funcionando", Colors.YELLOW)
    else:
        log("❌ Muitos endpoints com problemas", Colors.RED)
    
    # Sugestões baseadas no resultado
    if passed >= total * 0.8:
        log("\n💡 PRÓXIMOS PASSOS:", Colors.BOLD)
        log("1. Verificar se o Apache está configurado para proxy reverso", Colors.BLUE)
        log("2. Verificar se os módulos proxy estão habilitados", Colors.BLUE)
        log("3. Verificar se o VirtualHost está configurado corretamente", Colors.BLUE)
        log("4. Verificar logs do Apache para erros de proxy", Colors.BLUE)
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 