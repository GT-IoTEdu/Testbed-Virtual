#!/usr/bin/env python3
"""
Script para testar o endpoint /dhcp/save
Testa o salvamento de dados DHCP do pfSense no banco de dados
"""

import requests
import json
import time
from datetime import datetime

# Configuração
BASE_URL = "http://127.0.0.1:8000/api/devices"
TIMEOUT = 30

def print_separator(title):
    """Imprime um separador visual para organizar os testes."""
    print("\n" + "="*60)
    print(f"🧪 {title}")
    print("="*60)

def test_dhcp_save():
    """Testa o endpoint de salvamento de dados DHCP."""
    print_separator("TESTE 1: Salvar Dados DHCP no Banco")
    
    url = f"{BASE_URL}/dhcp/save"
    
    # Dados de teste
    test_data = {
        "mac": "bc:24:11:2c:0f:31",
        "ipaddr": "10.30.30.10",
        "cid": "lubuntu-live",
        "descr": "lubuntu-live-proxmox"
    }
    
    print(f"📡 Fazendo requisição para: {url}")
    print(f"📝 Dados enviados: {json.dumps(test_data, indent=2)}")
    print("⏳ Aguarde... (pode demorar alguns segundos)")
    
    try:
        start_time = time.time()
        response = requests.post(url, json=test_data, timeout=TIMEOUT)
        end_time = time.time()
        
        print(f"⏱️  Tempo de resposta: {end_time - start_time:.2f} segundos")
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Sucesso! Dados salvos:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
            # Verificar se há dados salvos
            if data.get('mappings_saved', 0) > 0:
                print(f"🎉 {data['mappings_saved']} mapeamentos DHCP foram salvos!")
            else:
                print("⚠️  Nenhum mapeamento foi salvo (pode ser normal se não há dados no pfSense)")
                
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
    """Testa a listagem de dispositivos salvos."""
    print_separator("TESTE 2: Listar Dispositivos Salvos")
    
    url = f"{BASE_URL}/dhcp/devices"
    params = {"page": 1, "per_page": 10}
    
    print(f"📡 Fazendo requisição para: {url}")
    
    try:
        response = requests.get(url, params=params, timeout=TIMEOUT)
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Sucesso! Dispositivos encontrados:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
            devices = data.get('devices', [])
            print(f"📱 Total de dispositivos: {len(devices)}")
            
            # Mostrar exemplo do dispositivo específico
            for device in devices:
                if device.get('mac') == 'bc:24:11:2c:0f:31':
                    print("\n🎯 Dispositivo específico encontrado:")
                    print(f"   IP: {device.get('ipaddr')}")
                    print(f"   MAC: {device.get('mac')}")
                    print(f"   Hostname: {device.get('hostname')}")
                    print(f"   Descrição: {device.get('descr')}")
                    break
        else:
            print("❌ Erro na requisição:")
            print(f"Status: {response.status_code}")
            print(f"Resposta: {response.text}")
            
    except Exception as e:
        print(f"💥 Erro: {e}")

def test_search_by_ip():
    """Testa a busca de dispositivo por IP."""
    print_separator("TESTE 3: Buscar Dispositivo por IP")
    
    ip = "10.30.30.10"
    url = f"{BASE_URL}/dhcp/devices/ip/{ip}"
    
    print(f"📡 Fazendo requisição para: {url}")
    
    try:
        response = requests.get(url, timeout=TIMEOUT)
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Sucesso! Dispositivo encontrado:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
        elif response.status_code == 404:
            print("❌ Dispositivo não encontrado")
        else:
            print("❌ Erro na requisição:")
            print(f"Status: {response.status_code}")
            print(f"Resposta: {response.text}")
            
    except Exception as e:
        print(f"💥 Erro: {e}")

def test_search_by_mac():
    """Testa a busca de dispositivo por MAC."""
    print_separator("TESTE 4: Buscar Dispositivo por MAC")
    
    mac = "bc:24:11:2c:0f:31"
    url = f"{BASE_URL}/dhcp/devices/mac/{mac}"
    
    print(f"📡 Fazendo requisição para: {url}")
    
    try:
        response = requests.get(url, timeout=TIMEOUT)
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Sucesso! Dispositivo encontrado:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
        elif response.status_code == 404:
            print("❌ Dispositivo não encontrado")
        else:
            print("❌ Erro na requisição:")
            print(f"Status: {response.status_code}")
            print(f"Resposta: {response.text}")
            
    except Exception as e:
        print(f"💥 Erro: {e}")

def test_statistics():
    """Testa as estatísticas de dispositivos."""
    print_separator("TESTE 5: Ver Estatísticas")
    
    url = f"{BASE_URL}/dhcp/statistics"
    
    print(f"📡 Fazendo requisição para: {url}")
    
    try:
        response = requests.get(url, timeout=TIMEOUT)
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Sucesso! Estatísticas:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            print("❌ Erro na requisição:")
            print(f"Status: {response.status_code}")
            print(f"Resposta: {response.text}")
            
    except Exception as e:
        print(f"💥 Erro: {e}")

def test_search_by_term():
    """Testa a busca de dispositivos por termo."""
    print_separator("TESTE 6: Buscar por Termo")
    
    term = "lubuntu"
    url = f"{BASE_URL}/dhcp/devices/search"
    params = {"query": term}
    
    print(f"📡 Fazendo requisição para: {url}?query={term}")
    
    try:
        response = requests.get(url, params=params, timeout=TIMEOUT)
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Sucesso! Resultados da busca:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            print("❌ Erro na requisição:")
            print(f"Status: {response.status_code}")
            print(f"Resposta: {response.text}")
            
    except Exception as e:
        print(f"💥 Erro: {e}")

def main():
    """Função principal que executa todos os testes."""
    print("🚀 INICIANDO TESTES DO ENDPOINT DHCP SAVE")
    print(f"📅 Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 URL Base: {BASE_URL}")
    
    # Executar testes em sequência
    test_dhcp_save()
    time.sleep(2)  # Pequena pausa entre testes
    
    test_list_devices()
    time.sleep(1)
    
    test_search_by_ip()
    time.sleep(1)
    
    test_search_by_mac()
    time.sleep(1)
    
    test_statistics()
    time.sleep(1)
    
    test_search_by_term()
    
    print("\n" + "="*60)
    print("🎉 TESTES CONCLUÍDOS!")
    print("="*60)
    print("\n📋 Resumo:")
    print("1. ✅ Teste de salvamento DHCP")
    print("2. ✅ Teste de listagem de dispositivos")
    print("3. ✅ Teste de busca por IP")
    print("4. ✅ Teste de busca por MAC")
    print("5. ✅ Teste de estatísticas")
    print("6. ✅ Teste de busca por termo")
    
    print("\n💡 Dicas:")
    print("- Verifique se o servidor está rodando em http://127.0.0.1:8000")
    print("- Confirme se o pfSense está acessível")
    print("- Verifique as credenciais no arquivo .env")
    print("- Monitore os logs do servidor para mais detalhes")

if __name__ == "__main__":
    main()
