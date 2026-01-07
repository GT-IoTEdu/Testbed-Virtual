#!/usr/bin/env python3
"""
Script para debugar o problema da listagem de IPs.
"""

from services_firewalls.dhcp_service import DhcpService
from db.models import DhcpServer, DhcpStaticMapping

def debug_ip_list():
    """Debuga o problema da listagem de IPs."""
    print("🔍 DEBUGANDO LISTAGEM DE IPs")
    print("="*50)
    
    with DhcpService() as service:
        # 1. Verificar servidores DHCP
        print("\n📊 1. SERVIDORES DHCP")
        print("-" * 30)
        
        servers = service.db.query(DhcpServer).all()
        print(f"Total de servidores: {len(servers)}")
        
        for server in servers:
            print(f"  - ID: {server.id}")
            print(f"    Server ID: {server.server_id}")
            print(f"    Interface: {server.interface}")
            print(f"    Range: {server.range_from} - {server.range_to}")
            print(f"    Enable: {server.enable}")
            print()
        
        # 2. Verificar mapeamentos estáticos
        print("\n📱 2. MAPEAMENTOS ESTÁTICOS")
        print("-" * 30)
        
        mappings = service.db.query(DhcpStaticMapping).all()
        print(f"Total de mapeamentos: {len(mappings)}")
        
        for mapping in mappings:
            print(f"  - ID: {mapping.id}")
            print(f"    Server ID: {mapping.server_id}")
            print(f"    PF ID: {mapping.pf_id}")
            print(f"    IP: {mapping.ipaddr}")
            print(f"    MAC: {mapping.mac}")
            print(f"    Hostname: {mapping.hostname}")
            print(f"    Descrição: {mapping.descr}")
            print()
        
        # 3. Verificar IPs usados por servidor
        print("\n🔍 3. IPs USADOS POR SERVIDOR")
        print("-" * 30)
        
        for server in servers:
            server_mappings = service.db.query(DhcpStaticMapping).filter(
                DhcpStaticMapping.server_id == server.id
            ).all()
            
            print(f"Servidor {server.server_id} (ID: {server.id}):")
            print(f"  - Mapeamentos: {len(server_mappings)}")
            
            for mapping in server_mappings:
                print(f"    - {mapping.ipaddr} ({mapping.mac})")
            print()
        
        # 4. Testar método get_ip_address_list
        print("\n🧪 4. TESTE DO MÉTODO get_ip_address_list")
        print("-" * 30)
        
        try:
            result = service.get_ip_address_list("lan", "10.30.30.1", "10.30.30.100")
            
            print(f"Range Info:")
            print(f"  - Server ID: {result['range_info']['server_id']}")
            print(f"  - Interface: {result['range_info']['interface']}")
            print(f"  - Range: {result['range_info']['range_from']} - {result['range_info']['range_to']}")
            print(f"  - Total IPs: {result['range_info']['total_ips']}")
            print(f"  - Used IPs: {result['range_info']['used_ips']}")
            print(f"  - Free IPs: {result['range_info']['free_ips']}")
            
            print(f"\nSummary:")
            print(f"  - Total: {result['summary']['total']}")
            print(f"  - Used: {result['summary']['used']}")
            print(f"  - Free: {result['summary']['free']}")
            
            # Verificar IPs usados na resposta
            used_ips_in_response = [ip for ip in result['ip_addresses'] if ip['status'] == 'used']
            print(f"\nIPs usados na resposta: {len(used_ips_in_response)}")
            
            for ip_info in used_ips_in_response:
                print(f"  - {ip_info['ip']}: {ip_info['mac']} ({ip_info['description']})")
                
        except Exception as e:
            print(f"❌ Erro: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    debug_ip_list()
