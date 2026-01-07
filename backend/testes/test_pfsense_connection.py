#!/usr/bin/env python3
"""
Script para testar a conexão com o pfSense e verificar erros.
"""

import requests
import json
import config

def test_pfsense_connection():
    """Testa a conexão com o pfSense."""
    print("🔍 TESTANDO CONEXÃO COM PFSENSE")
    print("="*50)
    
    print(f"📡 URL Base: {config.PFSENSE_API_URL}")
    print(f"🔑 API Key: {config.PFSENSE_API_KEY[:10]}..." if config.PFSENSE_API_KEY else "None")
    
    # Teste 1: Listar servidores DHCP
    print("\n🧪 TESTE 1: Listar servidores DHCP")
    print("-" * 30)
    
    url = f"{config.PFSENSE_API_URL}services/dhcp_servers"
    headers = {"X-API-Key": config.PFSENSE_API_KEY}
    
    try:
        print(f"📡 Fazendo requisição para: {url}")
        response = requests.get(url, headers=headers, timeout=10, verify=False)
        
        print(f"📊 Status Code: {response.status_code}")
        print(f"📋 Headers de resposta: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Resposta de sucesso:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
            if data and isinstance(data, dict):
                if data.get('status') == 'ok':
                    servers = data.get('result', {}).get('data', [])
                    print(f"📊 Servidores encontrados: {len(servers)}")
                    
                    for server in servers:
                        staticmaps = server.get('staticmap', [])
                        print(f"   Servidor {server.get('id')}: {len(staticmaps)} mapeamentos")
                else:
                    print(f"⚠️  Status não OK: {data.get('status')}")
            else:
                print("⚠️  Resposta não é um dicionário válido")
        else:
            print("❌ Erro na requisição:")
            print(f"Resposta: {response.text}")
            
    except requests.exceptions.Timeout:
        print("⏰ Timeout: A requisição demorou muito para responder")
    except requests.exceptions.ConnectionError as e:
        print(f"🔌 Erro de conexão: {e}")
    except Exception as e:
        print(f"💥 Erro inesperado: {e}")
    
    # Teste 2: Tentar cadastrar um mapeamento
    print("\n🧪 TESTE 2: Tentar cadastrar mapeamento")
    print("-" * 30)
    
    url = f"{config.PFSENSE_API_URL}services/dhcp_server/static_mapping"
    headers = {
        "X-API-Key": config.PFSENSE_API_KEY,
        "Content-Type": "application/json"
    }
    
    test_data = {
        "parent_id": "lan",
        "mac": "aa:bb:cc:dd:ee:ff",
        "ipaddr": "10.30.30.50",
        "cid": "test-device",
        "hostname": "test-device",
        "descr": "Dispositivo de teste"
    }
    
    try:
        print(f"📡 Fazendo requisição POST para: {url}")
        print(f"📝 Dados enviados: {json.dumps(test_data, indent=2)}")
        
        response = requests.post(url, json=test_data, headers=headers, timeout=10, verify=False)
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Cadastro bem-sucedido:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            print("❌ Erro no cadastro:")
            print(f"Resposta: {response.text}")
            
    except requests.exceptions.Timeout:
        print("⏰ Timeout: A requisição demorou muito para responder")
    except requests.exceptions.ConnectionError as e:
        print(f"🔌 Erro de conexão: {e}")
    except Exception as e:
        print(f"💥 Erro inesperado: {e}")

if __name__ == "__main__":
    test_pfsense_connection()
