#!/usr/bin/env python3
"""
Script para verificar se o dispositivo foi salvo no pfSense.
"""

from services_firewalls.pfsense_client import listar_clientes_dhcp_pfsense
import json

def check_pfsense_device():
    """Verifica se o dispositivo foi salvo no pfSense."""
    print("🔍 VERIFICANDO DISPOSITIVO NO PFSENSE")
    print("="*50)
    
    try:
        # Buscar dados do pfSense
        data = listar_clientes_dhcp_pfsense()
        
        if data and data.get('status') == 'ok':
            servers = data.get('result', {}).get('data', [])
            
            print(f"📊 Servidores DHCP encontrados: {len(servers)}")
            
            target_mac = "aa:bb:cc:dd:ee:ff"
            target_ip = "10.30.30.50"
            
            found_device = None
            
            for server in servers:
                staticmaps = server.get('staticmap', [])
                print(f"🔧 Servidor {server.get('id')}: {len(staticmaps)} mapeamentos")
                
                for mapping in staticmaps:
                    mac = mapping.get('mac')
                    ipaddr = mapping.get('ipaddr')
                    
                    if mac == target_mac or ipaddr == target_ip:
                        found_device = mapping
                        print(f"🎯 DISPOSITIVO ENCONTRADO NO PFSENSE!")
                        print(f"   MAC: {mapping.get('mac')}")
                        print(f"   IP: {mapping.get('ipaddr')}")
                        print(f"   CID: {mapping.get('cid')}")
                        print(f"   Hostname: {mapping.get('hostname')}")
                        print(f"   Descrição: {mapping.get('descr')}")
                        print(f"   Parent ID: {mapping.get('parent_id')}")
                        print(f"   ID: {mapping.get('id')}")
                        break
                
                if found_device:
                    break
            
            if not found_device:
                print(f"❌ Dispositivo não encontrado no pfSense")
                print(f"   MAC procurado: {target_mac}")
                print(f"   IP procurado: {target_ip}")
                
                # Listar todos os dispositivos para debug
                print("\n📋 Todos os dispositivos no pfSense:")
                for server in servers:
                    for mapping in server.get('staticmap', []):
                        print(f"   MAC: {mapping.get('mac')}, IP: {mapping.get('ipaddr')}, CID: {mapping.get('cid')}")
        else:
            print("❌ Erro ao buscar dados do pfSense")
            print(f"Resposta: {json.dumps(data, indent=2)}")
            
    except Exception as e:
        print(f"💥 Erro: {e}")

if __name__ == "__main__":
    check_pfsense_device()
