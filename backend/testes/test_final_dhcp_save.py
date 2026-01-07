#!/usr/bin/env python3
"""
Teste final para confirmar que o endpoint /dhcp/save está funcionando perfeitamente.
"""

import requests
import json
import time

# Configuração
BASE_URL = "http://127.0.0.1:8000/api/devices"
TIMEOUT = 30

def test_final_dhcp_save():
    """Teste final com dispositivo completamente novo."""
    print("🎯 TESTE FINAL - Endpoint DHCP Save")
    print("="*60)
    
    url = f"{BASE_URL}/dhcp/save"
    
    # Dados de teste com dispositivo completamente novo
    test_data = {
        "mac": "11:22:33:44:55:66",
        "ipaddr": "10.30.30.60",
        "cid": "final-test",
        "descr": "Teste final - dispositivo novo"
    }
    
    print(f"📡 URL: {url}")
    print(f"📝 Dados enviados: {json.dumps(test_data, indent=2)}")
    print("⏳ Fazendo requisição...")
    
    try:
        start_time = time.time()
        response = requests.post(url, json=test_data, timeout=TIMEOUT)
        end_time = time.time()
        
        print(f"⏱️  Tempo de resposta: {end_time - start_time:.2f} segundos")
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Resposta de sucesso:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
            # Verificar se há dados salvos
            servers_saved = data.get('servers_saved', 0)
            mappings_saved = data.get('mappings_saved', 0)
            mappings_updated = data.get('mappings_updated', 0)
            pfsense_saved = data.get('pfsense_saved', False)
            pfsense_message = data.get('pfsense_message', '')
            
            print(f"\n📊 Estatísticas:")
            print(f"   - Servidores salvos: {servers_saved}")
            print(f"   - Mapeamentos salvos: {mappings_saved}")
            print(f"   - Mapeamentos atualizados: {mappings_updated}")
            print(f"   - pfSense salvo: {pfsense_saved}")
            print(f"   - Mensagem pfSense: {pfsense_message}")
            
            if mappings_saved > 0:
                print("🎉 SUCCESS: Dados foram salvos corretamente no banco!")
            elif mappings_updated > 0:
                print("🔄 SUCCESS: Dados foram atualizados corretamente no banco!")
            else:
                print("⚠️  WARNING: Nenhum mapeamento foi salvo ou atualizado no banco")
                
            if pfsense_saved:
                print("🎉 SUCCESS: Dados foram salvos no pfSense!")
            else:
                print("⚠️  WARNING: Dados não foram salvos no pfSense")
                
        else:
            print("❌ Erro na requisição:")
            print(f"Status: {response.status_code}")
            print(f"Resposta: {response.text}")
            
    except requests.exceptions.Timeout:
        print("⏰ Timeout: A requisição demorou muito para responder")
    except requests.exceptions.ConnectionError:
        print("🔌 Erro de conexão: Verifique se o servidor está rodando")
    except Exception as e:
        print(f"💥 Erro inesperado: {e}")

def verify_in_database():
    """Verifica se o dispositivo foi salvo no banco."""
    print("\n" + "="*60)
    print("🧪 VERIFICANDO NO BANCO DE DADOS")
    print("="*60)
    
    url = f"{BASE_URL}/dhcp/devices/ip/10.30.30.60"
    
    try:
        response = requests.get(url, timeout=TIMEOUT)
        
        if response.status_code == 200:
            data = response.json()
            device = data.get('device', {})
            
            print("✅ Dispositivo encontrado no banco:")
            print(f"   ID: {device.get('id')}")
            print(f"   pf_id: {device.get('pf_id')}")
            print(f"   IP: {device.get('ipaddr')}")
            print(f"   MAC: {device.get('mac')}")
            print(f"   CID: {device.get('cid')}")
            print(f"   Hostname: {device.get('hostname')}")
            print(f"   Descrição: {device.get('descr')}")
        else:
            print("❌ Dispositivo não encontrado no banco")
            
    except Exception as e:
        print(f"💥 Erro ao verificar no banco: {e}")

def verify_in_pfsense():
    """Verifica se o dispositivo foi salvo no pfSense."""
    print("\n" + "="*60)
    print("🧪 VERIFICANDO NO PFSENSE")
    print("="*60)
    
    try:
        from services_firewalls.pfsense_client import listar_clientes_dhcp_pfsense
        
        data = listar_clientes_dhcp_pfsense()
        
        if data and data.get('status') == 'ok':
            servers = data.get('result', {}).get('data', [])
            
            target_mac = "11:22:33:44:55:66"
            target_ip = "10.30.30.60"
            
            found_device = None
            
            for server in servers:
                for mapping in server.get('staticmap', []):
                    if mapping.get('mac') == target_mac or mapping.get('ipaddr') == target_ip:
                        found_device = mapping
                        break
                if found_device:
                    break
            
            if found_device:
                print("✅ Dispositivo encontrado no pfSense:")
                print(f"   ID: {found_device.get('id')}")
                print(f"   MAC: {found_device.get('mac')}")
                print(f"   IP: {found_device.get('ipaddr')}")
                print(f"   CID: {found_device.get('cid')}")
                print(f"   Hostname: {found_device.get('hostname')}")
                print(f"   Descrição: {found_device.get('descr')}")
            else:
                print("❌ Dispositivo não encontrado no pfSense")
        else:
            print("❌ Erro ao buscar dados do pfSense")
            
    except Exception as e:
        print(f"💥 Erro ao verificar no pfSense: {e}")

if __name__ == "__main__":
    test_final_dhcp_save()
    time.sleep(2)
    verify_in_database()
    time.sleep(1)
    verify_in_pfsense()
    
    print("\n" + "="*60)
    print("🎯 TESTE FINAL CONCLUÍDO!")
    print("="*60)
