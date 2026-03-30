"""
Encontra incidentes de atacante processados.
"""
import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from db.models import ZeekIncident
from db.session import get_db_session

def main():
    with get_db_session() as db:
        incidents = db.query(ZeekIncident).filter(
            ZeekIncident.incident_type.like('%Atacante%'),
            ZeekIncident.processed_at.isnot(None)
        ).order_by(ZeekIncident.detected_at.desc()).all()
        
        print(f"Total de incidentes de atacante processados: {len(incidents)}")
        
        if incidents:
            print("\nPrimeiros 10:")
            for inc in incidents[:10]:
                print(f"  ID {inc.id}: {inc.device_ip} - {inc.incident_type} - "
                      f"Detectado: {inc.detected_at} - "
                      f"Processado: {inc.processed_at}")

if __name__ == "__main__":
    main()

