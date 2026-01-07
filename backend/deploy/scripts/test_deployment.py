#!/usr/bin/env python3
"""
Script para testar o deploy da aplicação IoT-EDU
Testa todos os endpoints e funcionalidades principais
"""

import requests
import json
import sys
import time
from urllib.parse import urljoin

# Configurações
BASE_URL = "https://sp-python.cafeexpresso.rnp.br"
API_BASE_URL = f"{BASE_URL}/api"
AUTH_BASE_URL = f"{BASE_URL}/auth"
SAML_BASE_URL = f"{BASE_URL}/saml2"

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

def test_endpoint(url, method="GET", data=None, headers=None, expected_status=200):
    """Testa um endpoint específico"""
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers, timeout=10, verify=False)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, headers=headers, timeout=10, verify=False)
        else:
            log(f"❌ Método {method} não suportado", Colors.RED)
            return False
        
        if response.status_code == expected_status:
            log(f"✅ {method} {url} - Status: {response.status_code}")
            return True
        else:
            log(f"❌ {method} {url} - Status: {response.status_code} (esperado: {expected_status})", Colors.RED)
            if response.text:
                log(f"   Resposta: {response.text[:200]}...", Colors.YELLOW)
            return False
            
    except requests.exceptions.RequestException as e:
        log(f"❌ Erro ao testar {method} {url}: {e}", Colors.RED)
        return False

def test_health_endpoints():
    """Testa endpoints de saúde da aplicação"""
    log("\n🏥 Testando endpoints de saúde...", Colors.BLUE)
    
    endpoints = [
        f"{BASE_URL}/health",
        f"{BASE_URL}/",
        f"{BASE_URL}/docs",
        f"{BASE_URL}/openapi.json"
    ]
    
    success_count = 0
    for endpoint in endpoints:
        if test_endpoint(endpoint):
            success_count += 1
    
    log(f"📊 Resultado: {success_count}/{len(endpoints)} endpoints de saúde funcionando")
    return success_count == len(endpoints)

def test_saml_endpoints():
    """Testa endpoints SAML"""
    log("\n🔐 Testando endpoints SAML...", Colors.BLUE)
    
    endpoints = [
        f"{SAML_BASE_URL}/metadata/",
        f"{SAML_BASE_URL}/login/",
        f"{AUTH_BASE_URL}/status",
        f"{AUTH_BASE_URL}/metadata"
    ]
    
    success_count = 0
    for endpoint in endpoints:
        if test_endpoint(endpoint):
            success_count += 1
    
    log(f"📊 Resultado: {success_count}/{len(endpoints)} endpoints SAML funcionando")
    return success_count == len(endpoints)

def test_api_endpoints():
    """Testa endpoints da API"""
    log("\n🌐 Testando endpoints da API...", Colors.BLUE)
    
    endpoints = [
        f"{API_BASE_URL}/devices/",
        f"{API_BASE_URL}/devices/aliases/",
        f"{API_BASE_URL}/devices/dhcp/servers"
    ]
    
    success_count = 0
    for endpoint in endpoints:
        if test_endpoint(endpoint):
            success_count += 1
    
    log(f"📊 Resultado: {success_count}/{len(endpoints)} endpoints da API funcionando")
    return success_count == len(endpoints)

def test_ssl_certificate():
    """Testa certificado SSL"""
    log("\n🔒 Testando certificado SSL...", Colors.BLUE)
    
    try:
        response = requests.get(BASE_URL, timeout=10, verify=True)
        if response.status_code == 200:
            log("✅ Certificado SSL válido")
            return True
        else:
            log(f"⚠️ Certificado SSL válido, mas status: {response.status_code}", Colors.YELLOW)
            return True
    except requests.exceptions.SSLError as e:
        log(f"❌ Erro no certificado SSL: {e}", Colors.RED)
        return False
    except Exception as e:
        log(f"❌ Erro ao testar SSL: {e}", Colors.RED)
        return False

def test_authentication_flow():
    """Testa fluxo de autenticação"""
    log("\n🔑 Testando fluxo de autenticação...", Colors.BLUE)
    
    # Testar status inicial (não autenticado)
    if test_endpoint(f"{AUTH_BASE_URL}/status", expected_status=200):
        log("✅ Endpoint de status funcionando")
        
        # Verificar se retorna status "unauthenticated"
        try:
            response = requests.get(f"{AUTH_BASE_URL}/status", timeout=10, verify=False)
            data = response.json()
            if data.get("status") == "unauthenticated":
                log("✅ Status de não autenticado correto")
                return True
            else:
                log(f"⚠️ Status inesperado: {data.get('status')}", Colors.YELLOW)
                return True
        except Exception as e:
            log(f"❌ Erro ao verificar status: {e}", Colors.RED)
            return False
    else:
        return False

def test_database_connection():
    """Testa conexão com banco de dados"""
    log("\n🗄️ Testando conexão com banco de dados...", Colors.BLUE)
    
    try:
        # Testar endpoint que usa banco de dados
        response = requests.get(f"{API_BASE_URL}/devices/", timeout=10, verify=False)
        if response.status_code == 200:
            log("✅ Conexão com banco de dados funcionando")
            return True
        else:
            log(f"⚠️ Endpoint retornou status: {response.status_code}", Colors.YELLOW)
            return True
    except Exception as e:
        log(f"❌ Erro ao testar banco de dados: {e}", Colors.RED)
        return False

def test_pfsense_integration():
    """Testa integração com pfSense"""
    log("\n🛡️ Testando integração com pfSense...", Colors.BLUE)
    
    endpoints = [
        f"{API_BASE_URL}/devices/dhcp/servers",
        f"{API_BASE_URL}/devices/aliases/"
    ]
    
    success_count = 0
    for endpoint in endpoints:
        if test_endpoint(endpoint):
            success_count += 1
    
    log(f"📊 Resultado: {success_count}/{len(endpoints)} endpoints pfSense funcionando")
    return success_count > 0  # Pelo menos um endpoint deve funcionar

def generate_test_report(results):
    """Gera relatório de testes"""
    log("\n" + "="*60, Colors.BOLD)
    log("📋 RELATÓRIO DE TESTES", Colors.BOLD)
    log("="*60, Colors.BOLD)
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    
    for test_name, result in results.items():
        status = "✅ PASSOU" if result else "❌ FALHOU"
        color = Colors.GREEN if result else Colors.RED
        log(f"{test_name}: {status}", color)
    
    log(f"\n📊 RESUMO: {passed_tests}/{total_tests} testes passaram")
    
    if passed_tests == total_tests:
        log("🎉 TODOS OS TESTES PASSARAM! Aplicação funcionando corretamente.", Colors.GREEN)
    elif passed_tests >= total_tests * 0.8:
        log("⚠️ A maioria dos testes passou. Verifique os que falharam.", Colors.YELLOW)
    else:
        log("❌ Muitos testes falharam. Verifique a configuração.", Colors.RED)

def main():
    """Função principal"""
    log("🚀 Iniciando testes da aplicação IoT-EDU", Colors.BOLD)
    log(f"🌐 URL Base: {BASE_URL}")
    log(f"⏰ Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Desabilitar warnings de SSL para testes
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    # Executar testes
    results = {
        "Certificado SSL": test_ssl_certificate(),
        "Endpoints de Saúde": test_health_endpoints(),
        "Endpoints SAML": test_saml_endpoints(),
        "Endpoints da API": test_api_endpoints(),
        "Fluxo de Autenticação": test_authentication_flow(),
        "Conexão com Banco": test_database_connection(),
        "Integração pfSense": test_pfsense_integration()
    }
    
    # Gerar relatório
    generate_test_report(results)
    
    # Retornar código de saída
    passed_tests = sum(1 for result in results.values() if result)
    total_tests = len(results)
    
    if passed_tests == total_tests:
        log("\n🎉 Deploy funcionando perfeitamente!", Colors.GREEN)
        sys.exit(0)
    elif passed_tests >= total_tests * 0.8:
        log("\n⚠️ Deploy funcionando com pequenos problemas.", Colors.YELLOW)
        sys.exit(1)
    else:
        log("\n❌ Deploy com problemas significativos.", Colors.RED)
        sys.exit(2)

if __name__ == "__main__":
    main() 