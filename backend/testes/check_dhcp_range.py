#!/usr/bin/env python3
"""
Script para verificar o range DHCP atual.
"""

from services_firewalls.pfsense_client import listar_clientes_dhcp_pfsense
import json

def check_dhcp_range():
    """Verifica o range DHCP atual."""
    print("📊 RANGE DHCP ATUAL")
    print("="*50)
    
    try:
        data = listar_clientes_dhcp_pfsense()
        
        for server in data.get('data', []):
            server_id = server.get('id')
            range_from = server.get('range_from')
            range_to = server.get('range_to')
            enable = server.get('enable')
            
            print(f"🔧 Servidor {server_id}:")
            print(f"   - Habilitado: {enable}")
            print(f"   - Range: {range_from} - {range_to}")
            print(f"   - Interface: {server.get('interface')}")
            print()
            
    except Exception as e:
        print(f"💥 Erro: {e}")

if __name__ == "__main__":
    check_dhcp_range()
