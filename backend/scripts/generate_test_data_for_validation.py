"""
Gera dados de teste simulados para validar o calculo de tempos de bloqueio.
"""
import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from db.models import DhcpStaticMapping, ZeekIncident, BlockingFeedbackHistory
from db.session import get_db_session
from db.enums import IncidentSeverity, IncidentStatus, ZeekLogType, FeedbackStatus
from services_firewalls.blocking_feedback_service import BlockingFeedbackService
from datetime import datetime, timedelta
import random

def create_test_data():
    """Cria dados de teste simulados."""
    print("=" * 80)
    print("GERACAO DE DADOS DE TESTE PARA VALIDACAO")
    print("=" * 80)
    
    try:
        with get_db_session() as db:
            # Criar 10 dispositivos de teste
            test_ips = [f"192.168.100.{10+i}" for i in range(10)]
            
            print(f"\nCriando {len(test_ips)} dispositivos de teste...")
            devices_created = 0
            
            for ip in test_ips:
                # Verificar se ja existe
                existing = db.query(DhcpStaticMapping).filter(
                    DhcpStaticMapping.ipaddr == ip
                ).first()
                
                if not existing:
                    device = DhcpStaticMapping(
                        server_id=1,
                        pf_id=0,
                        ipaddr=ip,
                        mac='00:00:00:00:00:00',  # MAC ficticio
                        hostname=f'TestDevice-{ip.split(".")[-1]}',
                        descr=f'Dispositivo de teste {ip}',
                        cid=None
                    )
                    db.add(device)
                    devices_created += 1
            
            db.commit()
            print(f"  Dispositivos criados: {devices_created}")
            
            # Criar incidentes de teste
            print(f"\nCriando 20 incidentes de teste...")
            incidents_created = 0
            
            for i in range(20):
                ip = random.choice(test_ips)
                
                # Timestamp base
                base_time = datetime.now() - timedelta(days=random.randint(1, 7))
                detected_time = base_time
                processed_time = base_time + timedelta(seconds=random.randint(1, 10))
                
                incident = ZeekIncident(
                    device_ip=ip,
                    device_name=f'TestDevice-{ip.split(".")[-1]}',
                    incident_type=random.choice(['SQL Injection - Atacante', 'DDoS Attack - Atacante', 'Malware - Atacante']),
                    severity=random.choice(list(IncidentSeverity)),
                    status=IncidentStatus.RESOLVED,
                    description=f'Incidente de teste #{i+1}',
                    detected_at=detected_time,
                    zeek_log_type=ZeekLogType.NOTICE,
                    raw_log_data='{}',
                    action_taken='Bloqueado automaticamente',
                    processed_at=processed_time
                )
                
                db.add(incident)
                incidents_created += 1
            
            db.commit()
            print(f"  Incidentes criados: {incidents_created}")
            
            # Criar feedbacks de bloqueio
            print(f"\nCriando feedbacks de bloqueio...")
            
            feedback_service = BlockingFeedbackService()
            feedbacks_created = 0
            
            # Buscar incidentes criados
            test_incidents = db.query(ZeekIncident).filter(
                ZeekIncident.device_ip.in_(test_ips),
                ZeekIncident.incident_type.like('%Atacante%'),
                ZeekIncident.processed_at.isnot(None)
            ).all()
            
            for incident in test_incidents:
                # Buscar dispositivo
                device = db.query(DhcpStaticMapping).filter(
                    DhcpStaticMapping.ipaddr == incident.device_ip
                ).first()
                
                if device:
                    # Verificar se ja tem feedback
                    existing = db.query(BlockingFeedbackHistory).filter(
                        BlockingFeedbackHistory.dhcp_mapping_id == device.id,
                        BlockingFeedbackHistory.feedback_by == "Sistema Automatico"
                    ).first()
                    
                    if not existing:
                        feedback = feedback_service.create_admin_blocking_feedback(
                            dhcp_mapping_id=device.id,
                            admin_reason=f'Bloqueio automatico por incidente de seguranca - Incidente {incident.id}: {incident.incident_type}',
                            admin_name="Sistema Automatico",
                            problem_resolved=None
                        )
                        
                        if feedback:
                            # Ajustar timestamp para ser proximo ao processamento
                            if incident.processed_at:
                                db.query(BlockingFeedbackHistory).filter(
                                    BlockingFeedbackHistory.id == feedback.id
                                ).update({
                                    'created_at': incident.processed_at + timedelta(seconds=random.randint(1, 5)),
                                    'admin_review_date': incident.processed_at + timedelta(seconds=random.randint(1, 5))
                                })
                                db.commit()
                            
                            feedbacks_created += 1
            
            print(f"  Feedbacks criados: {feedbacks_created}")
            
            print("\n" + "=" * 80)
            print("DADOS DE TESTE CRIADOS COM SUCESSO!")
            print("=" * 80)
            
            # Mostrar resumo
            print("\nResumo:")
            devices_count = db.query(DhcpStaticMapping).filter(
                DhcpStaticMapping.ipaddr.in_(test_ips)
            ).count()
            
            incidents_count = db.query(ZeekIncident).filter(
                ZeekIncident.device_ip.in_(test_ips),
                ZeekIncident.incident_type.like('%Atacante%'),
                ZeekIncident.processed_at.isnot(None)
            ).count()
            
            feedbacks_count = 0
            for ip in test_ips:
                device = db.query(DhcpStaticMapping).filter(DhcpStaticMapping.ipaddr == ip).first()
                if device:
                    feedbacks_count += db.query(BlockingFeedbackHistory).filter(
                        BlockingFeedbackHistory.dhcp_mapping_id == device.id,
                        BlockingFeedbackHistory.feedback_by == "Sistema Automatico"
                    ).count()
            
            print(f"  Dispositivos de teste: {devices_count}")
            print(f"  Incidentes processados: {incidents_count}")
            print(f"  Feedbacks de bloqueio: {feedbacks_count}")
            
    except Exception as e:
        print(f"\nERRO: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_test_data()

