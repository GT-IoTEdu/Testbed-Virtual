#!/usr/bin/env python3
"""
Script de verificação rápida dos endpoints essenciais
"""

import requests
import json
import sys
import time

# Configurações
BASE_URL = "https://sp-python.cafeexpresso.rnp.br"

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

def quick_test(url, name):
    """Teste rápido de um endpoint"""
    try:
        response = requests.get(url, timeout=10, verify=False)
        if response.status_code == 200:
            log(f"✅ {name}: OK", Colors.GREEN)
            return True
        else:
            log(f"❌ {name}: Status {response.status_code}", Colors.RED)
            return False
    except Exception as e:
        log(f"❌ {name}: Erro - {e}", Colors.RED)
        return False

def main():
    """Função principal"""
    log("🚀 Verificação Rápida - Endpoints Essenciais", Colors.BOLD)
    log(f"🌐 URL Base: {BASE_URL}")
    log(f"⏰ Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    log("="*50, Colors.BOLD)
    
    # Desabilitar warnings de SSL
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    # Testes essenciais
    tests = [
        (f"{BASE_URL}/", "Página Principal"),
        (f"{BASE_URL}/health", "Health Check"),
        (f"{BASE_URL}/docs", "Documentação"),
        (f"{BASE_URL}/saml2/metadata/", "Metadados SAML"),
        (f"{BASE_URL}/api/devices/", "API Dispositivos"),
        (f"{BASE_URL}/api/devices/aliases/", "API Aliases"),
        (f"{BASE_URL}/api/devices/dhcp/servers", "API DHCP Servers")
    ]
    
    passed = 0
    total = len(tests)
    
    for url, name in tests:
        if quick_test(url, name):
            passed += 1
    
    # Relatório final
    log("\n" + "="*50, Colors.BOLD)
    log("📊 RESUMO", Colors.BOLD)
    log("="*50, Colors.BOLD)
    log(f"✅ Passaram: {passed}/{total}")
    log(f"❌ Falharam: {total - passed}/{total}")
    
    if passed == total:
        log("🎉 TODOS OS ENDPOINTS ESSENCIAIS ESTÃO FUNCIONANDO!", Colors.GREEN)
    elif passed >= total * 0.7:
        log("⚠️ A maioria dos endpoints está funcionando", Colors.YELLOW)
    else:
        log("❌ Muitos endpoints com problemas", Colors.RED)
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 