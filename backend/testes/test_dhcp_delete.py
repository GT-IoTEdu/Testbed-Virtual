#!/usr/bin/env python3
"""
Teste para o endpoint de exclusão de mapeamento estático DHCP.

Este script testa:
1. Exclusão de mapeamento DHCP sem aplicar (apply=False)
2. Exclusão de mapeamento DHCP aplicando imediatamente (apply=True)
3. Tratamento de erros para mapeamentos inexistentes

Uso:
    python testes/test_dhcp_delete.py
"""
import requests
import json
import time
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000/api/devices"
TIMEOUT = 30

def test_dhcp_delete_without_apply():
    """Testa exclusão de mapeamento DHCP sem aplicar."""
    print("🧪 Testando exclusão de mapeamento DHCP sem aplicar...")
    
    # Parâmetros de teste (ajuste conforme necessário)
    parent_id = 1  # ID do servidor DHCP pai (lan)
    mapping_id = 5  # ID do mapeamento a ser excluído
    
    url = f"{BASE_URL}/dhcp/static_mapping"
    params = {
        "parent_id": parent_id,
        "mapping_id": mapping_id,
        "apply": False
    }
    
    try:
        response = requests.delete(url, params=params, timeout=TIMEOUT)
        
        print(f"📡 Status Code: {response.status_code}")
        print(f"📡 URL: {response.url}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Exclusão sem aplicar foi bem-sucedida!")
            print(f"📋 Resposta: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            # Verificar campos obrigatórios
            required_fields = ["success", "message", "parent_id", "mapping_id", "applied"]
            for field in required_fields:
                if field in data:
                    print(f"✅ Campo '{field}' presente: {data[field]}")
                else:
                    print(f"❌ Campo '{field}' ausente")
            
            # Verificar se applied é False
            if data.get("applied") == False:
                print("✅ Parâmetro apply=False funcionando corretamente")
            else:
                print("⚠️ Parâmetro apply=False não está sendo respeitado")
                
        else:
            print(f"❌ Erro na requisição: {response.status_code}")
            print(f"📋 Resposta: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro de conexão: {e}")

def test_dhcp_delete_with_apply():
    """Testa exclusão de mapeamento DHCP aplicando imediatamente."""
    print("\n🧪 Testando exclusão de mapeamento DHCP aplicando imediatamente...")
    
    # Parâmetros de teste (ajuste conforme necessário)
    parent_id = 1  # ID do servidor DHCP pai (lan)
    mapping_id = 6  # ID do mapeamento a ser excluído
    
    url = f"{BASE_URL}/dhcp/static_mapping"
    params = {
        "parent_id": parent_id,
        "mapping_id": mapping_id,
        "apply": True
    }
    
    try:
        response = requests.delete(url, params=params, timeout=TIMEOUT)
        
        print(f"📡 Status Code: {response.status_code}")
        print(f"📡 URL: {response.url}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Exclusão com aplicação foi bem-sucedida!")
            print(f"📋 Resposta: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            # Verificar se applied é True
            if data.get("applied") == True:
                print("✅ Parâmetro apply=True funcionando corretamente")
            else:
                print("⚠️ Parâmetro apply=True não está sendo respeitado")
                
        else:
            print(f"❌ Erro na requisição: {response.status_code}")
            print(f"📋 Resposta: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro de conexão: {e}")

def test_dhcp_delete_nonexistent_mapping():
    """Testa exclusão de mapeamento DHCP inexistente."""
    print("\n🧪 Testando exclusão de mapeamento DHCP inexistente...")
    
    # Parâmetros de teste com ID inexistente
    parent_id = 1  # ID do servidor DHCP pai (lan)
    mapping_id = 99999  # ID de mapeamento inexistente
    
    url = f"{BASE_URL}/dhcp/static_mapping"
    params = {
        "parent_id": parent_id,
        "mapping_id": mapping_id,
        "apply": False
    }
    
    try:
        response = requests.delete(url, params=params, timeout=TIMEOUT)
        
        print(f"📡 Status Code: {response.status_code}")
        print(f"📡 URL: {response.url}")
        
        if response.status_code == 404:
            print("✅ Erro 404 retornado corretamente para mapeamento inexistente")
            print(f"📋 Resposta: {response.text}")
        elif response.status_code == 500:
            print("✅ Erro 500 retornado (esperado para mapeamento inexistente)")
            print(f"📋 Resposta: {response.text}")
        else:
            print(f"⚠️ Status code inesperado: {response.status_code}")
            print(f"📋 Resposta: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro de conexão: {e}")

def test_dhcp_delete_invalid_parent_id():
    """Testa exclusão com parent_id inválido."""
    print("\n🧪 Testando exclusão com parent_id inválido...")
    
    # Parâmetros de teste com parent_id inválido
    parent_id = 99999  # ID de servidor DHCP inexistente
    mapping_id = 5  # ID do mapeamento
    
    url = f"{BASE_URL}/dhcp/static_mapping"
    params = {
        "parent_id": parent_id,
        "mapping_id": mapping_id,
        "apply": False
    }
    
    try:
        response = requests.delete(url, params=params, timeout=TIMEOUT)
        
        print(f"📡 Status Code: {response.status_code}")
        print(f"📡 URL: {response.url}")
        
        if response.status_code in [404, 500]:
            print("✅ Erro retornado corretamente para parent_id inválido")
            print(f"📋 Resposta: {response.text}")
        else:
            print(f"⚠️ Status code inesperado: {response.status_code}")
            print(f"📋 Resposta: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro de conexão: {e}")

def main():
    """Função principal para executar todos os testes."""
    print("🚀 Iniciando testes do endpoint de exclusão DHCP")
    print("=" * 60)
    print(f"⏰ Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 Base URL: {BASE_URL}")
    print("=" * 60)
    
    # Executar testes
    test_dhcp_delete_without_apply()
    time.sleep(1)  # Pausa entre testes
    
    test_dhcp_delete_with_apply()
    time.sleep(1)  # Pausa entre testes
    
    test_dhcp_delete_nonexistent_mapping()
    time.sleep(1)  # Pausa entre testes
    
    test_dhcp_delete_invalid_parent_id()
    
    print("\n" + "=" * 60)
    print("🏁 Testes concluídos!")
    print("=" * 60)

if __name__ == "__main__":
    main()
