#!/usr/bin/env python3
"""
Script de teste rápido para verificar se o endpoint /dhcp/save está funcionando
após a correção da estrutura de dados.
"""

import requests
import json
import time

# Configuração
BASE_URL = "http://127.0.0.1:8000/api/devices"
TIMEOUT = 30

def test_dhcp_save_fix():
    """Testa o endpoint de salvamento de dados DHCP após a correção."""
    print("🧪 TESTE RÁPIDO - Endpoint DHCP Save (Após Correção)")
    print("="*60)
    
    url = f"{BASE_URL}/dhcp/save"
    
    # Dados de teste com novo dispositivo
    test_data = {
        "mac": "aa:bb:cc:dd:ee:ff",
        "ipaddr": "10.30.30.50",
        "cid": "test-device",
        "descr": "Dispositivo de teste corrigido"
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

def test_list_devices():
    """Testa a listagem de dispositivos para verificar se foram salvos."""
    print("\n" + "="*60)
    print("🧪 VERIFICANDO SE OS DADOS FORAM SALVOS")
    print("="*60)
    
    url = f"{BASE_URL}/dhcp/devices"
    params = {"page": 1, "per_page": 10}
    
    print(f"📡 URL: {url}")
    print("⏳ Fazendo requisição...")
    
    try:
        response = requests.get(url, params=params, timeout=TIMEOUT)
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            devices = data.get('devices', [])
            total = data.get('total', 0)
            
            print(f"✅ Dispositivos encontrados: {total}")
            
            if devices:
                print("📱 Lista de dispositivos:")
                for i, device in enumerate(devices, 1):
                    print(f"   {i}. ID:{device.get('id')} | pf_id:{device.get('pf_id')} | IP: {device.get('ipaddr')} | MAC: {device.get('mac')} | Descrição: {device.get('descr')}")
                    
                # Verificar se o dispositivo específico foi salvo
                target_mac = "aa:bb:cc:dd:ee:ff"
                target_ip = "10.30.30.50"
                
                found_device = None
                for device in devices:
                    if device.get('mac') == target_mac or device.get('ipaddr') == target_ip:
                        found_device = device
                        break
                
                if found_device:
                    print(f"\n🎯 Dispositivo específico encontrado:")
                    print(f"   ID: {found_device.get('id')}")
                    print(f"   pf_id: {found_device.get('pf_id')}")
                    print(f"   IP: {found_device.get('ipaddr')}")
                    print(f"   MAC: {found_device.get('mac')}")
                    print(f"   CID: {found_device.get('cid')}")
                    print(f"   Hostname: {found_device.get('hostname')}")
                    print(f"   Descrição: {found_device.get('descr')}")
                else:
                    print(f"\n❌ Dispositivo específico não encontrado (MAC: {target_mac}, IP: {target_ip})")
            else:
                print("⚠️  Nenhum dispositivo encontrado")
                
        else:
            print("❌ Erro na requisição:")
            print(f"Status: {response.status_code}")
            print(f"Resposta: {response.text}")
            
    except Exception as e:
        print(f"💥 Erro: {e}")

def test_search_specific_device():
    """Testa a busca do dispositivo específico por IP e MAC."""
    print("\n" + "="*60)
    print("🧪 BUSCANDO DISPOSITIVO ESPECÍFICO")
    print("="*60)
    
    # Buscar por IP
    ip_url = f"{BASE_URL}/dhcp/devices/ip/10.30.30.50"
    print(f"📡 Buscando por IP: {ip_url}")
    
    try:
        response = requests.get(ip_url, timeout=TIMEOUT)
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Dispositivo encontrado por IP:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
        elif response.status_code == 404:
            print("❌ Dispositivo não encontrado por IP")
        else:
            print(f"❌ Erro na busca por IP: {response.text}")
    except Exception as e:
        print(f"💥 Erro na busca por IP: {e}")
    
    print()
    
    # Buscar por MAC
    mac_url = f"{BASE_URL}/dhcp/devices/mac/aa:bb:cc:dd:ee:ff"
    print(f"📡 Buscando por MAC: {mac_url}")
    
    try:
        response = requests.get(mac_url, timeout=TIMEOUT)
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Dispositivo encontrado por MAC:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
        elif response.status_code == 404:
            print("❌ Dispositivo não encontrado por MAC")
        else:
            print(f"❌ Erro na busca por MAC: {response.text}")
    except Exception as e:
        print(f"💥 Erro na busca por MAC: {e}")

if __name__ == "__main__":
    test_dhcp_save_fix()
    time.sleep(2)
    test_list_devices()
    time.sleep(1)
    test_search_specific_device()
    
    print("\n" + "="*60)
    print("🎯 TESTE CONCLUÍDO!")
    print("="*60)
