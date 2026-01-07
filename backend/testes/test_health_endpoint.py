#!/usr/bin/env python3
"""
Script para testar o endpoint de saúde da API IoT-EDU.

Este script verifica:
- Conectividade com a API
- Resposta do endpoint /health
- Validação dos campos retornados
- Tempo de resposta
- Status da API

Uso:
    python test_health_endpoint.py
"""

import requests
import json
import time
from datetime import datetime
import sys

# Configurações
BASE_URL = "http://127.0.0.1:8000"
HEALTH_ENDPOINT = f"{BASE_URL}/health"
TIMEOUT = 10  # segundos

def test_health_endpoint():
    """Testa o endpoint de saúde da API."""
    print("🏥 Testando Endpoint de Saúde da API IoT-EDU")
    print("=" * 50)
    
    try:
        # Fazer requisição
        print(f"📍 URL: {HEALTH_ENDPOINT}")
        print(f"⏱️  Timeout: {TIMEOUT}s")
        print()
        
        start_time = time.time()
        response = requests.get(
            HEALTH_ENDPOINT,
            headers={"Content-Type": "application/json"},
            timeout=TIMEOUT
        )
        response_time = time.time() - start_time
        
        # Exibir resultados básicos
        print(f"📊 Status Code: {response.status_code}")
        print(f"⏱️  Response Time: {response_time:.3f}s")
        print(f"📏 Content Length: {len(response.text)} bytes")
        print()
        
        # Verificar status code
        if response.status_code == 200:
            print("✅ Status Code: OK (200)")
        else:
            print(f"❌ Status Code: ERRO ({response.status_code})")
            print(f"📄 Response: {response.text}")
            return False
        
        # Verificar tempo de resposta
        if response_time < 1.0:
            print("✅ Response Time: OK (< 1s)")
        else:
            print(f"⚠️  Response Time: LENTO ({response_time:.3f}s)")
        
        # Parsear JSON
        try:
            data = response.json()
            print("✅ JSON Parse: OK")
        except json.JSONDecodeError as e:
            print(f"❌ JSON Parse: ERRO - {e}")
            print(f"📄 Response: {response.text}")
            return False
        
        # Validar campos obrigatórios
        print("\n🔍 Validando Campos:")
        
        required_fields = ['status', 'timestamp', 'version']
        for field in required_fields:
            if field in data:
                print(f"✅ {field}: {data[field]}")
            else:
                print(f"❌ {field}: CAMPO AUSENTE")
                return False
        
        # Validações específicas
        print("\n🔍 Validações Específicas:")
        
        # Status deve ser 'healthy'
        if data['status'] == 'healthy':
            print("✅ Status: 'healthy'")
        else:
            print(f"❌ Status: '{data['status']}' (deveria ser 'healthy')")
            return False
        
        # Versão deve ter formato válido
        if '.' in data['version']:
            print(f"✅ Version: {data['version']}")
        else:
            print(f"❌ Version: formato inválido - {data['version']}")
            return False
        
        # Timestamp deve ter formato ISO
        try:
            datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
            print(f"✅ Timestamp: {data['timestamp']}")
        except ValueError:
            print(f"❌ Timestamp: formato inválido - {data['timestamp']}")
            return False
        
        # Resumo final
        print("\n" + "=" * 50)
        print("🎉 TESTE CONCLUÍDO COM SUCESSO!")
        print(f"📊 API Status: {data['status']}")
        print(f"🔢 Versão: {data['version']}")
        print(f"⏰ Timestamp: {data['timestamp']}")
        print(f"⚡ Performance: {response_time:.3f}s")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ ERRO DE CONEXÃO")
        print("💡 Verifique se o servidor está rodando:")
        print("   python start_server.py")
        return False
        
    except requests.exceptions.Timeout:
        print("❌ TIMEOUT")
        print(f"💡 A requisição demorou mais que {TIMEOUT}s")
        return False
        
    except requests.exceptions.RequestException as e:
        print(f"❌ ERRO DE REQUISIÇÃO: {e}")
        return False
        
    except Exception as e:
        print(f"❌ ERRO INESPERADO: {e}")
        return False

def test_additional_endpoints():
    """Testa endpoints adicionais relacionados."""
    print("\n🔗 Testando Endpoints Adicionais")
    print("=" * 40)
    
    endpoints = [
        ("API Root", f"{BASE_URL}/"),
        ("Documentation", f"{BASE_URL}/docs"),
        ("Auth Status", f"{BASE_URL}/auth/status"),
    ]
    
    for name, url in endpoints:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ {name}: OK ({response.status_code})")
            else:
                print(f"⚠️  {name}: {response.status_code}")
        except Exception as e:
            print(f"❌ {name}: ERRO - {e}")

def main():
    """Função principal."""
    print("🚀 Iniciando Testes de Saúde da API IoT-EDU")
    print(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Teste principal
    success = test_health_endpoint()
    
    # Testes adicionais
    if success:
        test_additional_endpoints()
    
    # Resultado final
    print("\n" + "=" * 50)
    if success:
        print("🎉 TODOS OS TESTES PASSARAM!")
        sys.exit(0)
    else:
        print("❌ ALGUNS TESTES FALHARAM!")
        sys.exit(1)

if __name__ == "__main__":
    main()
