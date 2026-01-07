#!/usr/bin/env python3
"""
Script de diagnóstico detalhado para identificar problemas específicos
nos endpoints que falharam durante os testes
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

def test_endpoint_detailed(url, method="GET", data=None, headers=None):
    """Testa um endpoint com informações detalhadas"""
    try:
        log(f"\n🔍 Testando: {method} {url}")
        
        if method.upper() == "GET":
            response = requests.get(url, headers=headers, timeout=15, verify=False)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, headers=headers, timeout=15, verify=False)
        else:
            log(f"❌ Método {method} não suportado", Colors.RED)
            return False
        
        log(f"📊 Status Code: {response.status_code}")
        log(f"📋 Headers de Resposta:")
        for key, value in response.headers.items():
            log(f"   {key}: {value}", Colors.YELLOW)
        
        if response.text:
            try:
                json_response = response.json()
                log(f"📄 Resposta JSON:")
                log(f"   {json.dumps(json_response, indent=2)}", Colors.YELLOW)
            except:
                log(f"📄 Resposta (não JSON):")
                log(f"   {response.text[:500]}...", Colors.YELLOW)
        
        if response.status_code == 200:
            log("✅ Endpoint funcionando corretamente", Colors.GREEN)
            return True
        else:
            log(f"❌ Endpoint com problema (Status: {response.status_code})", Colors.RED)
            return False
            
    except requests.exceptions.RequestException as e:
        log(f"❌ Erro de conexão: {e}", Colors.RED)
        return False
    except Exception as e:
        log(f"❌ Erro inesperado: {e}", Colors.RED)
        return False

def diagnose_health_check():
    """Diagnóstico detalhado do health check"""
    log("\n🏥 DIAGNÓSTICO: Health Check", Colors.BOLD)
    log("="*50, Colors.BOLD)
    
    endpoints = [
        f"{BASE_URL}/health",
        f"{BASE_URL}/",
        f"{BASE_URL}/docs",
        f"{BASE_URL}/openapi.json"
    ]
    
    for endpoint in endpoints:
        test_endpoint_detailed(endpoint)

def diagnose_saml_endpoints():
    """Diagnóstico detalhado dos endpoints SAML"""
    log("\n🔐 DIAGNÓSTICO: Endpoints SAML", Colors.BOLD)
    log("="*50, Colors.BOLD)
    
    endpoints = [
        f"{SAML_BASE_URL}/metadata/",
        f"{SAML_BASE_URL}/login/",
        f"{AUTH_BASE_URL}/status",
        f"{AUTH_BASE_URL}/metadata"
    ]
    
    for endpoint in endpoints:
        test_endpoint_detailed(endpoint)

def diagnose_api_endpoints():
    """Diagnóstico detalhado dos endpoints da API"""
    log("\n🌐 DIAGNÓSTICO: Endpoints da API", Colors.BOLD)
    log("="*50, Colors.BOLD)
    
    endpoints = [
        f"{API_BASE_URL}/devices/",
        f"{API_BASE_URL}/devices/aliases/",
        f"{API_BASE_URL}/devices/dhcp/servers",
        f"{API_BASE_URL}/devices/dhcp/static_mapping?parent_id=lan&id=6"
    ]
    
    for endpoint in endpoints:
        test_endpoint_detailed(endpoint)

def test_ssl_connection():
    """Teste detalhado de SSL"""
    log("\n🔒 DIAGNÓSTICO: Certificado SSL", Colors.BOLD)
    log("="*50, Colors.BOLD)
    
    try:
        # Teste sem verificação SSL
        log("🔍 Testando sem verificação SSL...")
        response = requests.get(BASE_URL, timeout=10, verify=False)
        log(f"✅ Conectividade OK (Status: {response.status_code})", Colors.GREEN)
        
        # Teste com verificação SSL
        log("🔍 Testando com verificação SSL...")
        response = requests.get(BASE_URL, timeout=10, verify=True)
        log(f"✅ SSL válido (Status: {response.status_code})", Colors.GREEN)
        
        return True
    except requests.exceptions.SSLError as e:
        log(f"❌ Problema SSL: {e}", Colors.RED)
        return False
    except Exception as e:
        log(f"❌ Erro de conexão: {e}", Colors.RED)
        return False

def test_network_connectivity():
    """Teste de conectividade de rede"""
    log("\n🌐 DIAGNÓSTICO: Conectividade de Rede", Colors.BOLD)
    log("="*50, Colors.BOLD)
    
    try:
        # Teste DNS
        import socket
        log("🔍 Testando resolução DNS...")
        ip = socket.gethostbyname("sp-python.cafeexpresso.rnp.br")
        log(f"✅ DNS OK: {ip}", Colors.GREEN)
        
        # Teste de conectividade básica
        log("🔍 Testando conectividade básica...")
        response = requests.get(f"http://{ip}", timeout=5, verify=False)
        log(f"✅ Conectividade básica OK", Colors.GREEN)
        
        return True
    except Exception as e:
        log(f"❌ Problema de conectividade: {e}", Colors.RED)
        return False

def test_headers_and_security():
    """Teste de headers de segurança"""
    log("\n🛡️ DIAGNÓSTICO: Headers de Segurança", Colors.BOLD)
    log("="*50, Colors.BOLD)
    
    try:
        response = requests.get(BASE_URL, timeout=10, verify=False)
        
        security_headers = [
            'X-Content-Type-Options',
            'X-Frame-Options', 
            'X-XSS-Protection',
            'Strict-Transport-Security',
            'Content-Security-Policy'
        ]
        
        log("📋 Headers de segurança encontrados:")
        for header in security_headers:
            value = response.headers.get(header)
            if value:
                log(f"   ✅ {header}: {value}", Colors.GREEN)
            else:
                log(f"   ❌ {header}: Não encontrado", Colors.RED)
        
        return True
    except Exception as e:
        log(f"❌ Erro ao verificar headers: {e}", Colors.RED)
        return False

def test_error_handling():
    """Teste de tratamento de erros"""
    log("\n🚨 DIAGNÓSTICO: Tratamento de Erros", Colors.BOLD)
    log("="*50, Colors.BOLD)
    
    error_endpoints = [
        f"{BASE_URL}/api/endpoint-inexistente",
        f"{BASE_URL}/api/devices/aliases/endpoint-inexistente",
        f"{BASE_URL}/auth/endpoint-inexistente"
    ]
    
    for endpoint in error_endpoints:
        test_endpoint_detailed(endpoint)

def generate_diagnostic_report():
    """Gera relatório de diagnóstico"""
    log("\n" + "="*60, Colors.BOLD)
    log("📋 RELATÓRIO DE DIAGNÓSTICO", Colors.BOLD)
    log("="*60, Colors.BOLD)
    
    log("🔍 Problemas identificados:")
    log("1. Health check falhando - possível problema no servidor")
    log("2. Documentação não carregando - possível problema no FastAPI")
    log("3. Endpoints da API falhando - possível problema na aplicação")
    log("4. Status de autenticação falhando - possível problema no SAML")
    
    log("\n💡 Possíveis soluções:")
    log("1. Verificar se o servidor está rodando: sudo systemctl status apache2")
    log("2. Verificar logs do Apache: sudo tail -f /var/log/apache2/iot_edu_ssl_error.log")
    log("3. Verificar se o FastAPI está rodando: sudo systemctl status fastapi.service")
    log("4. Verificar logs do FastAPI: sudo journalctl -u fastapi.service -f")
    log("5. Verificar conectividade: ping sp-python.cafeexpresso.rnp.br")

def main():
    """Função principal"""
    log("🔍 Iniciando diagnóstico detalhado da aplicação IoT-EDU", Colors.BOLD)
    log(f"🌐 URL Base: {BASE_URL}")
    log(f"⏰ Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Desabilitar warnings de SSL para testes
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    # Executar diagnósticos
    test_network_connectivity()
    test_ssl_connection()
    test_headers_and_security()
    diagnose_health_check()
    diagnose_saml_endpoints()
    diagnose_api_endpoints()
    test_error_handling()
    
    # Gerar relatório
    generate_diagnostic_report()
    
    log("\n🎯 Diagnóstico concluído!", Colors.GREEN)
    log("Consulte o relatório acima para identificar os problemas específicos.", Colors.YELLOW)

if __name__ == "__main__":
    main() 