"""
Script para verificar incidentes no banco de dados e preparar dados de teste se necessario.
"""
import sys
from pathlib import Path

# Adicionar o diretorio backend ao path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from services_scanners.incident_service import IncidentService
from db.models import ZeekIncident
from db.enums import IncidentSeverity, IncidentStatus, ZeekLogType
from db.session import get_db_session
from datetime import datetime

def check_existing_incidents():
    """Verifica incidentes existentes no banco."""
    print("=" * 80)
    print("VERIFICACAO DE INCIDENTES NO BANCO DE DADOS")
    print("=" * 80)
    
    try:
        with get_db_session() as db:
            # Total de incidentes
            total = db.query(ZeekIncident).count()
            print(f"\nTotal de incidentes: {total}")
            
            # Incidentes por tipo
            if total > 0:
                print("\nIncidentes por tipo:")
                incidents = db.query(ZeekIncident).all()
                by_type = {}
                for inc in incidents:
                    inc_type = inc.incident_type
                    by_type[inc_type] = by_type.get(inc_type, 0) + 1
                
                for inc_type, count in sorted(by_type.items(), key=lambda x: -x[1]):
                    print(f"  - {inc_type}: {count}")
                
                # Incidentes de atacante
                attacker_incidents = [inc for inc in incidents if "Atacante" in inc.incident_type]
                print(f"\nIncidentes de atacante: {len(attacker_incidents)}")
                
                # Incidentes processados
                processed = [inc for inc in incidents if inc.processed_at is not None]
                print(f"Incidentes processados: {len(processed)}")
                
                # Incidentes bloqueados (com feedback)
                from db.models import DhcpStaticMapping, BlockingFeedbackHistory
                
                blocked_count = 0
                for inc in attacker_incidents:
                    if inc.processed_at is not None:
                        device = db.query(DhcpStaticMapping).filter(
                            DhcpStaticMapping.ipaddr == inc.device_ip
                        ).first()
                        
                        if device:
                            feedback = db.query(BlockingFeedbackHistory).filter(
                                BlockingFeedbackHistory.dhcp_mapping_id == device.id,
                                BlockingFeedbackHistory.feedback_by == "Sistema Automático"
                            ).first()
                            
                            if feedback:
                                blocked_count += 1
                
                print(f"Incidentes bloqueados: {blocked_count}")
                
                # Mostrar alguns exemplos
                print("\nUltimos 10 incidentes:")
                recent = db.query(ZeekIncident).order_by(ZeekIncident.detected_at.desc()).limit(10).all()
                for inc in recent:
                    print(f"  ID {inc.id}: {inc.incident_type} - "
                          f"IP: {inc.device_ip} - "
                          f"Detectado: {inc.detected_at} - "
                          f"Processado: {inc.processed_at or 'Nao'}")
            
    except Exception as e:
        print(f"\nERRO: {e}")
        import traceback
        traceback.print_exc()

def suggest_test_data():
    """Sugere como criar dados de teste."""
    print("\n" + "=" * 80)
    print("SUGESTAO: Como criar dados de teste")
    print("=" * 80)
    
    print("""
Para testar os tempos de bloqueio, voce precisa:

1. Criar um incidente de atacante
2. Processar o incidente (marcar como processado)
3. Criar feedback de bloqueio automatico

OU

Gerar um ataque real com sqlmap na rede para criar incidentes naturalmente.

Opcoes:

A) Criar dados de teste manualmente via SQL
B) Executar um ataque de teste com sqlmap
C) Verificar se ha logs do Zeek recentes para processar

Deseja ver instrucoes detalhadas? (S/N)
    """)

if __name__ == "__main__":
    try:
        check_existing_incidents()
        suggest_test_data()
        
    except Exception as e:
        print(f"\nERRO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

