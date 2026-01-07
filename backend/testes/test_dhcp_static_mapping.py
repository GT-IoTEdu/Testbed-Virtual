#!/usr/bin/env python3
"""
Script para testar o endpoint de cadastro de mapeamentos estáticos DHCP no pfSense.
"""
import requests
import json

def test_create_dhcp_static_mapping():
    """Testa o endpoint de criação de mapeamento estático DHCP."""
    
    # URL do endpoint
    url = "http://127.0.0.1:8000/api/devices/dhcp/static_mapping"
    
    # Dados de teste
    test_data = {
        "mac": "00:11:22:33:44:55",
        "ipaddr": "192.168.1.100",
        "cid": "test_device_001",
        "hostname": "test-device",
        "domain": "",
        "domainsearchlist": [],
        "defaultleasetime": 7200,
        "maxleasetime": 86400,
        "gateway": "",
        "dnsserver": [],
        "winsserver": [],
        "ntpserver": [],
        "arp_table_static_entry": True,
        "descr": "Dispositivo de teste IoT-EDU"
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    print("🚀 Testando endpoint de cadastro de mapeamento estático DHCP...")
    print("=" * 80)
    print(f"URL: {url}")
    print(f"Dados: {json.dumps(test_data, indent=2)}")
    print()
    
    try:
        # Fazer a requisição
        response = requests.post(url, json=test_data, headers=headers, timeout=30)
        
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        print()
        
        if response.status_code == 200:
            result = response.json()
            print("✅ SUCESSO!")
            print(f"Resposta: {json.dumps(result, indent=2)}")
        else:
            print("❌ ERRO!")
            print(f"Resposta: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Erro de conexão - servidor não está rodando")
        print("Execute 'python main.py' primeiro")
    except Exception as e:
        print(f"❌ Erro: {e}")

def test_create_dhcp_static_mapping_minimal():
    """Testa o endpoint com dados mínimos obrigatórios."""
    
    url = "http://127.0.0.1:8000/api/devices/dhcp/static_mapping"
    
    # Dados mínimos (apenas campos obrigatórios)
    minimal_data = {
        "mac": "AA:BB:CC:DD:EE:FF",
        "ipaddr": "192.168.1.101",
        "cid": "minimal_test"
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    print("\n🧪 Testando com dados mínimos...")
    print("=" * 80)
    print(f"Dados mínimos: {json.dumps(minimal_data, indent=2)}")
    print()
    
    try:
        response = requests.post(url, json=minimal_data, headers=headers, timeout=30)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ SUCESSO com dados mínimos!")
            print(f"Resposta: {json.dumps(result, indent=2)}")
        else:
            print("❌ ERRO com dados mínimos!")
            print(f"Resposta: {response.text}")
            
    except Exception as e:
        print(f"❌ Erro: {e}")

def test_create_dhcp_static_mapping_invalid():
    """Testa o endpoint com dados inválidos."""
    
    url = "http://127.0.0.1:8000/api/devices/dhcp/static_mapping"
    
    # Dados inválidos (faltando campos obrigatórios)
    invalid_data = {
        "mac": "invalid-mac-address",
        "ipaddr": "invalid-ip-address",
        # Faltando cid (campo obrigatório)
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    print("\n⚠️ Testando com dados inválidos...")
    print("=" * 80)
    print(f"Dados inválidos: {json.dumps(invalid_data, indent=2)}")
    print()
    
    try:
        response = requests.post(url, json=invalid_data, headers=headers, timeout=30)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 422:
            print("✅ Validação funcionando corretamente!")
            print(f"Resposta: {response.text}")
        else:
            print("❌ Validação não funcionou como esperado!")
            print(f"Resposta: {response.text}")
            
    except Exception as e:
        print(f"❌ Erro: {e}")

def test_check_existing_mappings():
    """Testa o endpoint de verificação de mapeamentos existentes."""
    
    base_url = "http://127.0.0.1:8000/api/devices/dhcp/static_mapping/check"
    
    print("\n🔍 Testando verificação de mapeamentos existentes...")
    print("=" * 80)
    
    # Teste 1: Verificar por IP
    print("1. Verificando por IP...")
    try:
        response = requests.get(f"{base_url}?ipaddr=10.30.30.3", timeout=30)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print("✅ Verificação por IP funcionando!")
            print(f"Existe: {result.get('exists')}")
            print(f"Total encontrado: {result.get('total_found')}")
        else:
            print(f"❌ Erro na verificação por IP: {response.text}")
    except Exception as e:
        print(f"❌ Erro: {e}")
    
    # Teste 2: Verificar por MAC
    print("\n2. Verificando por MAC...")
    try:
        response = requests.get(f"{base_url}?mac=bc:24:11:68:fb:77", timeout=30)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print("✅ Verificação por MAC funcionando!")
            print(f"Existe: {result.get('exists')}")
            print(f"Total encontrado: {result.get('total_found')}")
        else:
            print(f"❌ Erro na verificação por MAC: {response.text}")
    except Exception as e:
        print(f"❌ Erro: {e}")
    
    # Teste 3: Verificar sem parâmetros (deve dar erro)
    print("\n3. Testando sem parâmetros (deve dar erro)...")
    try:
        response = requests.get(f"{base_url}", timeout=30)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 400:
            print("✅ Validação funcionando corretamente!")
            print(f"Resposta: {response.text}")
        else:
            print("❌ Validação não funcionou como esperado!")
            print(f"Resposta: {response.text}")
    except Exception as e:
        print(f"❌ Erro: {e}")

def test_duplicate_mapping():
    """Testa a tentativa de cadastrar um mapeamento duplicado."""
    
    url = "http://127.0.0.1:8000/api/devices/dhcp/static_mapping"
    
    # Dados que provavelmente já existem no pfSense
    duplicate_data = {
        "parent_id": "lan",
        "mac": "bc:24:11:68:fb:77",  # MAC que já existe
        "ipaddr": "10.30.30.3",      # IP que já existe
        "cid": "test_duplicate"
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    print("\n🔄 Testando cadastro de mapeamento duplicado...")
    print("=" * 80)
    print(f"Dados duplicados: {json.dumps(duplicate_data, indent=2)}")
    print()
    
    try:
        response = requests.post(url, json=duplicate_data, headers=headers, timeout=30)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 409:
            print("✅ Proteção contra duplicatas funcionando!")
            print(f"Resposta: {response.text}")
        else:
            print("❌ Proteção contra duplicatas não funcionou como esperado!")
            print(f"Resposta: {response.text}")
            
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    print("🔐 Testador do Endpoint de Mapeamento Estático DHCP")
    print("=" * 80)
    
    # Teste 1: Dados completos
    test_create_dhcp_static_mapping()
    
    # Teste 2: Dados mínimos
    test_create_dhcp_static_mapping_minimal()
    
    # Teste 3: Dados inválidos
    test_create_dhcp_static_mapping_invalid()
    
    # Teste 4: Verificação de mapeamentos existentes
    test_check_existing_mappings()
    
    # Teste 5: Tentativa de cadastro duplicado
    test_duplicate_mapping()
    
    print("\n🎉 Testes concluídos!")
