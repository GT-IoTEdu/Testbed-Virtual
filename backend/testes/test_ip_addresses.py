#!/usr/bin/env python3
"""
Script para testar o endpoint de listagem de endereços IP.
"""

import requests
import json

def test_ip_addresses():
    """Testa o endpoint de listagem de endereços IP."""
    print("🔍 TESTANDO ENDPOINT DE ENDEREÇOS IP")
    print("="*60)
    
    base_url = "http://127.0.0.1:8000/api/devices"
    
    # Teste 1: Listar todos os IPs
    print("\n🧪 TESTE 1: Listar todos os IPs")
    print("-" * 30)
    
    try:
        response = requests.get(f"{base_url}/dhcp/ip-addresses")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Resposta de sucesso!")
            
            range_info = data.get('range_info', {})
            summary = data.get('summary', {})
            
            print(f"📊 Informações do Range:")
            print(f"   - Servidor: {range_info.get('server_id')}")
            print(f"   - Interface: {range_info.get('interface')}")
            print(f"   - Range: {range_info.get('range_from')} - {range_info.get('range_to')}")
            print(f"   - Total de IPs: {range_info.get('total_ips')}")
            
            print(f"\n📈 Resumo:")
            print(f"   - Usados: {summary.get('used')}")
            print(f"   - Livres: {summary.get('free')}")
            print(f"   - Reservados: {summary.get('reserved')}")
            
            # Mostrar alguns IPs usados
            ip_addresses = data.get('ip_addresses', [])
            used_ips = [ip for ip in ip_addresses if ip['status'] == 'used']
            
            if used_ips:
                print(f"\n📱 IPs Usados (primeiros 5):")
                for ip in used_ips[:5]:
                    print(f"   - {ip['ip']}: {ip['mac']} ({ip['description']})")
            
            # Mostrar alguns IPs livres
            free_ips = [ip for ip in ip_addresses if ip['status'] == 'free']
            if free_ips:
                print(f"\n🆓 IPs Livres (primeiros 5):")
                for ip in free_ips[:5]:
                    print(f"   - {ip['ip']}")
        else:
            print(f"❌ Erro: {response.status_code}")
            print(f"Resposta: {response.text}")
            
    except Exception as e:
        print(f"💥 Erro: {e}")
    
    # Teste 2: Filtrar apenas IPs livres
    print("\n🧪 TESTE 2: Filtrar apenas IPs livres")
    print("-" * 30)
    
    try:
        response = requests.get(f"{base_url}/dhcp/ip-addresses?status_filter=free")
        
        if response.status_code == 200:
            data = response.json()
            summary = data.get('summary', {})
            
            print(f"✅ IPs Livres encontrados: {summary.get('free')}")
            
            # Mostrar alguns IPs livres
            ip_addresses = data.get('ip_addresses', [])
            if ip_addresses:
                print(f"📱 Primeiros 10 IPs livres:")
                for ip in ip_addresses[:10]:
                    print(f"   - {ip['ip']}")
        else:
            print(f"❌ Erro: {response.status_code}")
            
    except Exception as e:
        print(f"💥 Erro: {e}")
    
    # Teste 3: Filtrar apenas IPs usados
    print("\n🧪 TESTE 3: Filtrar apenas IPs usados")
    print("-" * 30)
    
    try:
        response = requests.get(f"{base_url}/dhcp/ip-addresses?status_filter=used")
        
        if response.status_code == 200:
            data = response.json()
            summary = data.get('summary', {})
            
            print(f"✅ IPs Usados encontrados: {summary.get('used')}")
            
            # Mostrar IPs usados
            ip_addresses = data.get('ip_addresses', [])
            if ip_addresses:
                print(f"📱 IPs usados:")
                for ip in ip_addresses:
                    print(f"   - {ip['ip']}: {ip['mac']} ({ip['description']})")
        else:
            print(f"❌ Erro: {response.status_code}")
            
    except Exception as e:
        print(f"💥 Erro: {e}")

if __name__ == "__main__":
    test_ip_addresses()
