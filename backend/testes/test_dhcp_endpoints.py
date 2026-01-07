#!/usr/bin/env python3
"""
Script de teste para os novos endpoints de DHCP.

Este script testa:
1. Salvamento de dados DHCP no banco
2. Consulta de dispositivos cadastrados
3. Busca por IP, MAC e descrição
4. Estatísticas de dispositivos
"""
import requests
import json
import time

# Configuração
BASE_URL = "http://127.0.0.1:8000/api/devices"

def test_save_dhcp_data():
    """Testa o endpoint de salvamento de dados DHCP."""
    print("🔧 Testando salvamento de dados DHCP...")
    
    try:
        response = requests.post(f"{BASE_URL}/dhcp/save")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Dados salvos com sucesso!")
            print(f"   - Servidores salvos: {data['servers_saved']}")
            print(f"   - Mapeamentos salvos: {data['mappings_saved']}")
            print(f"   - Mapeamentos atualizados: {data['mappings_updated']}")
            print(f"   - Timestamp: {data['timestamp']}")
        else:
            print(f"❌ Erro ao salvar dados: {response.status_code}")
            print(f"   Resposta: {response.text}")
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")

def test_list_devices():
    """Testa o endpoint de listagem de dispositivos."""
    print("\n📋 Testando listagem de dispositivos...")
    
    try:
        response = requests.get(f"{BASE_URL}/dhcp/devices?page=1&per_page=10")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Dispositivos listados com sucesso!")
            print(f"   - Total de dispositivos: {data['total']}")
            print(f"   - Página atual: {data['page']}")
            print(f"   - Itens por página: {data['per_page']}")
            print(f"   - Tem próxima página: {data['has_next']}")
            print(f"   - Tem página anterior: {data['has_prev']}")
            
            if data['devices']:
                print(f"   - Primeiros dispositivos:")
                for i, device in enumerate(data['devices'][:3]):
                    print(f"     {i+1}. {device['descr']} - {device['ipaddr']} ({device['mac']})")
        else:
            print(f"❌ Erro ao listar dispositivos: {response.status_code}")
            print(f"   Resposta: {response.text}")
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")

def test_search_devices():
    """Testa o endpoint de busca de dispositivos."""
    print("\n🔍 Testando busca de dispositivos...")
    
    # Testar busca por descrição
    try:
        response = requests.get(f"{BASE_URL}/dhcp/devices/search?query=ubuntu")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Busca por 'ubuntu' realizada!")
            print(f"   - Total encontrado: {data['total_found']}")
            print(f"   - Query: {data['query']}")
            
            if data['devices']:
                print(f"   - Dispositivos encontrados:")
                for device in data['devices']:
                    print(f"     - {device['descr']} - {device['ipaddr']}")
        else:
            print(f"❌ Erro na busca: {response.status_code}")
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")

def test_device_by_ip():
    """Testa o endpoint de busca por IP."""
    print("\n🌐 Testando busca por IP...")
    
    try:
        # Buscar por um IP específico (ajuste conforme seus dados)
        response = requests.get(f"{BASE_URL}/dhcp/devices/ip/10.30.30.3")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Dispositivo encontrado por IP!")
            print(f"   - Descrição: {data['device']['descr']}")
            print(f"   - MAC: {data['device']['mac']}")
            print(f"   - Servidor: {data['server']['server_id']}")
            print(f"   - Tem duplicatas: {data['is_duplicate']}")
        elif response.status_code == 404:
            print("ℹ️  Dispositivo com IP 10.30.30.3 não encontrado")
        else:
            print(f"❌ Erro na busca por IP: {response.status_code}")
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")

def test_device_by_mac():
    """Testa o endpoint de busca por MAC."""
    print("\n📱 Testando busca por MAC...")
    
    try:
        # Buscar por um MAC específico (ajuste conforme seus dados)
        response = requests.get(f"{BASE_URL}/dhcp/devices/mac/bc:24:11:68:fb:77")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Dispositivo encontrado por MAC!")
            print(f"   - Descrição: {data['device']['descr']}")
            print(f"   - IP: {data['device']['ipaddr']}")
            print(f"   - Servidor: {data['server']['server_id']}")
            print(f"   - Tem duplicatas: {data['is_duplicate']}")
        elif response.status_code == 404:
            print("ℹ️  Dispositivo com MAC bc:24:11:68:fb:77 não encontrado")
        else:
            print(f"❌ Erro na busca por MAC: {response.status_code}")
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")

def test_statistics():
    """Testa o endpoint de estatísticas."""
    print("\n📊 Testando estatísticas...")
    
    try:
        response = requests.get(f"{BASE_URL}/dhcp/statistics")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Estatísticas obtidas!")
            print(f"   - Total de dispositivos: {data['total_devices']}")
            print(f"   - Total de servidores: {data['total_servers']}")
            print(f"   - Dispositivos por servidor: {data['devices_by_server']}")
            print(f"   - Última atualização: {data['last_update']}")
        else:
            print(f"❌ Erro ao obter estatísticas: {response.status_code}")
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")

def main():
    """Executa todos os testes."""
    print("🚀 Iniciando testes dos endpoints de DHCP...")
    print("=" * 50)
    
    # Aguardar um pouco para garantir que o servidor está rodando
    time.sleep(2)
    
    # Executar testes
    test_save_dhcp_data()
    test_list_devices()
    test_search_devices()
    test_device_by_ip()
    test_device_by_mac()
    test_statistics()
    
    print("\n" + "=" * 50)
    print("✅ Testes concluídos!")

if __name__ == "__main__":
    main()
