#!/usr/bin/env python3
"""
Demonstração do gerenciamento de endereços IP DHCP.
"""

import requests
import json

def demo_ip_management():
    """Demonstra o gerenciamento de endereços IP."""
    print("🎯 DEMONSTRAÇÃO: GERENCIAMENTO DE ENDEREÇOS IP")
    print("="*60)
    
    base_url = "http://127.0.0.1:8000/api/devices"
    
    # 1. Verificar estatísticas gerais
    print("\n📊 1. ESTATÍSTICAS GERAIS")
    print("-" * 30)
    
    try:
        response = requests.get(f"{base_url}/dhcp/ip-addresses")
        if response.status_code == 200:
            data = response.json()
            summary = data.get('summary', {})
            range_info = data.get('range_info', {})
            
            print(f"📈 Range: {range_info.get('range_from')} - {range_info.get('range_to')}")
            print(f"📊 Total de IPs: {summary.get('total')}")
            print(f"✅ Usados: {summary.get('used')}")
            print(f"🆓 Livres: {summary.get('free')}")
            print(f"🔒 Reservados: {summary.get('reserved')}")
        else:
            print(f"❌ Erro: {response.status_code}")
    except Exception as e:
        print(f"💥 Erro: {e}")
    
    # 2. Encontrar IP livre para novo dispositivo
    print("\n🔍 2. ENCONTRAR IP LIVRE")
    print("-" * 30)
    
    try:
        response = requests.get(f"{base_url}/dhcp/ip-addresses?status_filter=free")
        if response.status_code == 200:
            data = response.json()
            free_ips = data.get('ip_addresses', [])
            
            if free_ips:
                first_free_ip = free_ips[0]['ip']
                print(f"✅ IP livre encontrado: {first_free_ip}")
                print(f"📊 Total de IPs livres: {len(free_ips)}")
                
                # Mostrar próximos 5 IPs livres
                print(f"📱 Próximos IPs livres:")
                for ip_info in free_ips[1:6]:
                    print(f"   - {ip_info['ip']}")
            else:
                print("❌ Nenhum IP livre encontrado!")
        else:
            print(f"❌ Erro: {response.status_code}")
    except Exception as e:
        print(f"💥 Erro: {e}")
    
    # 3. Verificar IP específico
    print("\n🔍 3. VERIFICAR IP ESPECÍFICO")
    print("-" * 30)
    
    target_ip = "10.30.30.15"
    try:
        response = requests.get(f"{base_url}/dhcp/ip-addresses")
        if response.status_code == 200:
            data = response.json()
            ip_addresses = data.get('ip_addresses', [])
            
            # Encontrar IP específico
            target_ip_info = None
            for ip_info in ip_addresses:
                if ip_info['ip'] == target_ip:
                    target_ip_info = ip_info
                    break
            
            if target_ip_info:
                if target_ip_info['status'] == 'free':
                    print(f"✅ IP {target_ip} está livre")
                else:
                    print(f"❌ IP {target_ip} está usado")
                    print(f"   MAC: {target_ip_info['mac']}")
                    print(f"   Hostname: {target_ip_info['hostname']}")
                    print(f"   Descrição: {target_ip_info['description']}")
            else:
                print(f"❌ IP {target_ip} não encontrado no range")
        else:
            print(f"❌ Erro: {response.status_code}")
    except Exception as e:
        print(f"💥 Erro: {e}")
    
    # 4. Listar dispositivos ativos
    print("\n📱 4. DISPOSITIVOS ATIVOS")
    print("-" * 30)
    
    try:
        response = requests.get(f"{base_url}/dhcp/ip-addresses?status_filter=used")
        if response.status_code == 200:
            data = response.json()
            used_ips = data.get('ip_addresses', [])
            
            print(f"📊 Total de dispositivos ativos: {len(used_ips)}")
            
            for ip_info in used_ips:
                print(f"   - {ip_info['ip']}: {ip_info['mac']} ({ip_info['description']})")
        else:
            print(f"❌ Erro: {response.status_code}")
    except Exception as e:
        print(f"💥 Erro: {e}")
    
    # 5. Simular cadastro de novo dispositivo
    print("\n🆕 5. SIMULAR CADASTRO DE NOVO DISPOSITIVO")
    print("-" * 30)
    
    try:
        # Buscar IP livre
        response = requests.get(f"{base_url}/dhcp/ip-addresses?status_filter=free")
        if response.status_code == 200:
            data = response.json()
            free_ips = data.get('ip_addresses', [])
            
            if free_ips:
                new_ip = free_ips[0]['ip']
                print(f"🎯 IP selecionado para novo dispositivo: {new_ip}")
                
                # Simular dados do novo dispositivo
                new_device_data = {
                    "mac": "aa:bb:cc:dd:ee:ff",
                    "ipaddr": new_ip,
                    "cid": "novo-dispositivo",
                    "descr": "Dispositivo de demonstração"
                }
                
                print(f"📝 Dados do dispositivo:")
                print(f"   MAC: {new_device_data['mac']}")
                print(f"   IP: {new_device_data['ipaddr']}")
                print(f"   CID: {new_device_data['cid']}")
                print(f"   Descrição: {new_device_data['descr']}")
                
                print(f"\n💡 Para cadastrar, use:")
                print(f"POST {base_url}/dhcp/save")
                print(f"Body: {json.dumps(new_device_data, indent=2)}")
            else:
                print("❌ Nenhum IP livre disponível!")
        else:
            print(f"❌ Erro: {response.status_code}")
    except Exception as e:
        print(f"💥 Erro: {e}")

def show_usage_examples():
    """Mostra exemplos de uso."""
    print("\n" + "="*60)
    print("📚 EXEMPLOS DE USO")
    print("="*60)
    
    print("\n🔗 Endpoints disponíveis:")
    print("   GET /api/devices/dhcp/ip-addresses")
    print("   GET /api/devices/dhcp/ip-addresses?status_filter=free")
    print("   GET /api/devices/dhcp/ip-addresses?status_filter=used")
    print("   GET /api/devices/dhcp/ip-addresses?range_from=10.30.30.1&range_to=10.30.30.50")
    
    print("\n🎯 Casos de uso comuns:")
    print("   1. Encontrar IP livre para novo dispositivo")
    print("   2. Verificar se IP específico está disponível")
    print("   3. Listar todos os dispositivos ativos")
    print("   4. Obter estatísticas do range DHCP")
    print("   5. Filtrar IPs por status (livre/usado)")
    
    print("\n📖 Para mais detalhes, consulte o arquivo GUIA_ENDERECOS_IP.md")

if __name__ == "__main__":
    demo_ip_management()
    show_usage_examples()
    
    print("\n" + "="*60)
    print("🎯 DEMONSTRAÇÃO CONCLUÍDA!")
    print("="*60)
