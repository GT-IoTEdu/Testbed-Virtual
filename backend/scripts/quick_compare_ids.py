#!/usr/bin/env python3
"""
Script rápido para comparar IDs do pfSense com pf_id do banco de dados.
"""

from db.session import SessionLocal
from db.models import DhcpStaticMapping
from services_firewalls.pfsense_client import listar_clientes_dhcp_pfsense

def quick_compare():
    """Compara IDs do pfSense com pf_id do banco de dados."""
    print("🔍 COMPARAÇÃO RÁPIDA: pfSense vs Banco de Dados")
    print("="*70)
    
    try:
        # Buscar dados do pfSense
        pfsense_data = listar_clientes_dhcp_pfsense()
        if not pfsense_data or pfsense_data.get('status') != 'ok':
            print("❌ Erro ao buscar dados do pfSense")
            return
        
        pfsense_servers = pfsense_data.get('data', [])
        
        # Buscar dados do banco
        db = SessionLocal()
        db_devices = db.query(DhcpStaticMapping).order_by(DhcpStaticMapping.pf_id).all()
        
        print("📊 COMPARAÇÃO:")
        print("pfSense ID | Banco pf_id | MAC | IP | Descrição | Status")
        print("-" * 80)
        
        # Mapear dispositivos do pfSense por MAC
        pfsense_devices = {}
        for server in pfsense_servers:
            for mapping in server.get('staticmap', []):
                mac = mapping.get('mac')
                pfsense_id = mapping.get('id')
                pfsense_devices[mac] = pfsense_id
        
        # Comparar com banco de dados
        mismatches = []
        for device in db_devices:
            mac = device.mac
            pfsense_id = pfsense_devices.get(mac)
            
            if pfsense_id is not None:
                if pfsense_id != device.pf_id:
                    status = f"❌ MISMATCH"
                    mismatches.append({
                        'device_id': device.id,
                        'mac': mac,
                        'pfsense_id': pfsense_id,
                        'db_pf_id': device.pf_id,
                        'ipaddr': device.ipaddr,
                        'descr': device.descr
                    })
                else:
                    status = "✅ OK"
            else:
                status = "⚠️  Não no pfSense"
                pfsense_id = "N/A"
            
            print(f"{str(pfsense_id):>10s} | {device.pf_id:>10d} | {mac:17s} | {device.ipaddr:15s} | {device.descr[:20]:20s} | {status}")
        
        print(f"\n📈 RESUMO:")
        print(f"   - Total de dispositivos no banco: {len(db_devices)}")
        print(f"   - Total de dispositivos no pfSense: {len(pfsense_devices)}")
        print(f"   - Mismatches encontrados: {len(mismatches)}")
        
        if mismatches:
            print(f"\n🔧 DISPOSITIVOS COM MISMATCH:")
            for mismatch in mismatches:
                print(f"   - MAC: {mismatch['mac']}")
                print(f"     pfSense ID: {mismatch['pfsense_id']}")
                print(f"     Banco pf_id: {mismatch['db_pf_id']}")
                print(f"     IP: {mismatch['ipaddr']}")
                print(f"     Descrição: {mismatch['descr']}")
        
        db.close()
        
    except Exception as e:
        print(f"💥 Erro: {e}")

if __name__ == "__main__":
    quick_compare()
