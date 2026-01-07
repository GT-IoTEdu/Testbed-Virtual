#!/usr/bin/env python3
"""
Teste simples para o endpoint de IPs.
"""

import requests

def test_simple():
    """Teste simples."""
    print("🔍 TESTE SIMPLES")
    print("="*30)
    
    try:
        # Testar endpoint existente
        response1 = requests.get('http://127.0.0.1:8000/api/devices/dhcp/devices')
        print(f"✅ /dhcp/devices: {response1.status_code}")
        
        # Testar novo endpoint
        response2 = requests.get('http://127.0.0.1:8000/api/devices/dhcp/ip-addresses')
        print(f"📊 /dhcp/ip-addresses: {response2.status_code}")
        
        if response2.status_code == 200:
            data = response2.json()
            print(f"✅ Dados recebidos: {len(data.get('ip_addresses', []))} IPs")
        else:
            print(f"❌ Erro: {response2.text}")
            
    except Exception as e:
        print(f"💥 Erro: {e}")

if __name__ == "__main__":
    test_simple()
