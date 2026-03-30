"""
Script para verificar dispositivos no DHCP.
"""
import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from db.models import DhcpStaticMapping
from db.session import get_db_session

def main():
    with get_db_session() as db:
        devices = db.query(DhcpStaticMapping).all()
        
        print(f"Total de dispositivos: {len(devices)}")
        
        if devices:
            print("\nPrimeiros 20 dispositivos:")
            for dev in devices[:20]:
                print(f"  ID {dev.id}: {dev.ipaddr} - {dev.hostname or 'Sem hostname'}")
        
        # Verificar IPs de incidentes
        from db.models import ZeekIncident
        incidents = db.query(ZeekIncident).filter(
            ZeekIncident.incident_type.like('%Atacante%')
        ).all()
        
        incident_ips = set([inc.device_ip for inc in incidents])
        device_ips = set([dev.ipaddr for dev in devices])
        
        print(f"\nIPs unicos de incidentes de atacante: {len(incident_ips)}")
        print(f"IPs unicos de dispositivos: {len(device_ips)}")
        
        matching = incident_ips.intersection(device_ips)
        print(f"IPs coincidentes: {len(matching)}")
        
        if matching:
            print("\nIPs coincidentes:")
            for ip in sorted(matching):
                print(f"  {ip}")
        else:
            print("\nNenhum IP de incidente corresponde a um dispositivo no DHCP")
            print("\nExemplos de IPs de incidentes:")
            for ip in sorted(list(incident_ips))[:10]:
                print(f"  {ip}")

if __name__ == "__main__":
    main()

