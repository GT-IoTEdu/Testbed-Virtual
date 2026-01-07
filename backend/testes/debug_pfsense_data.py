#!/usr/bin/env python3
"""
Script para debugar os dados do pfSense.
"""

from services_firewalls.pfsense_client import listar_clientes_dhcp_pfsense
import json

def debug_pfsense_data():
    """Debuga os dados do pfSense."""
    print("🔍 DEBUG: Dados do pfSense")
    print("="*50)
    
    try:
        # Buscar dados do pfSense
        data = listar_clientes_dhcp_pfsense()
        
        print(f"📊 Resposta completa:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        
        if data and isinstance(data, dict):
            print(f"\n📈 Estrutura da resposta:")
            print(f"   - Status: {data.get('status')}")
            print(f"   - Code: {data.get('code')}")
            print(f"   - Response ID: {data.get('response_id')}")
            print(f"   - Message: {data.get('message')}")
            
            result = data.get('result', {})
            print(f"\n📋 Result:")
            print(f"   - Code: {result.get('code')}")
            print(f"   - Status: {result.get('status')}")
            print(f"   - Response ID: {result.get('response_id')}")
            print(f"   - Message: {result.get('message')}")
            
            data_list = result.get('data', [])
            print(f"\n📊 Data (servidores): {len(data_list)}")
            
            for i, server in enumerate(data_list):
                print(f"\n🔧 Servidor {i+1}:")
                print(f"   - ID: {server.get('id')}")
                print(f"   - Interface: {server.get('interface')}")
                print(f"   - Enable: {server.get('enable')}")
                
                staticmap = server.get('staticmap', [])
                print(f"   - Static mappings: {len(staticmap)}")
                
                for j, mapping in enumerate(staticmap):
                    print(f"     Mapeamento {j+1}:")
                    print(f"       - ID: {mapping.get('id')}")
                    print(f"       - MAC: {mapping.get('mac')}")
                    print(f"       - IP: {mapping.get('ipaddr')}")
                    print(f"       - CID: {mapping.get('cid')}")
                    print(f"       - Hostname: {mapping.get('hostname')}")
                    print(f"       - Descrição: {mapping.get('descr')}")
        else:
            print("❌ Resposta não é um dicionário válido")
            
    except Exception as e:
        print(f"💥 Erro: {e}")

if __name__ == "__main__":
    debug_pfsense_data()
