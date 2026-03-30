"""
Cria feedback de bloqueio para o dispositivo 192.168.100.3.
"""
import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from db.models import ZeekIncident, DhcpStaticMapping, BlockingFeedbackHistory
from db.session import get_db_session
from services_firewalls.blocking_feedback_service import BlockingFeedbackService
from datetime import timedelta

def main():
    target_ip = "192.168.100.3"
    
    with get_db_session() as db:
        device = db.query(DhcpStaticMapping).filter(
            DhcpStaticMapping.ipaddr == target_ip
        ).first()
        
        if not device:
            print(f"Dispositivo {target_ip} nao encontrado")
            return
        
        print(f"Dispositivo encontrado: ID {device.id}, IP {device.ipaddr}")
        
        # Verificar se ja tem feedback
        existing = db.query(BlockingFeedbackHistory).filter(
            BlockingFeedbackHistory.dhcp_mapping_id == device.id,
            BlockingFeedbackHistory.feedback_by == "Sistema Automatico"
        ).all()
        
        print(f"Feedbacks existentes: {len(existing)}")
        
        # Buscar incidentes de atacante para este dispositivo
        incidents = db.query(ZeekIncident).filter(
            ZeekIncident.device_ip == target_ip,
            ZeekIncident.incident_type.like('%Atacante%'),
            ZeekIncident.processed_at.isnot(None)
        ).order_by(ZeekIncident.detected_at.desc()).limit(3).all()
        
        print(f"Incidentes de atacante processados para {target_ip}: {len(incidents)}")
        
        if not incidents:
            print("Nenhum incidente encontrado para criar feedback")
            return
        
        for idx, incident in enumerate(incidents, 1):
            print(f"\nIncidente {idx}:")
            print(f"  ID: {incident.id}")
            print(f"  Tipo: {incident.incident_type}")
            print(f"  Detectado: {incident.detected_at}")
            print(f"  Processado: {incident.processed_at}")
        
        # Criar feedback para cada incidente
        feedback_service = BlockingFeedbackService()
        
        for incident in incidents:
            # Verificar se ja tem feedback para este incidente especifico
            has_feedback = False
            for feedback in existing:
                if str(incident.id) in feedback.user_feedback:
                    has_feedback = True
                    break
            
            if has_feedback:
                print(f"\nIncidente {incident.id} ja tem feedback, pulando...")
                continue
            
            feedback = feedback_service.create_admin_blocking_feedback(
                dhcp_mapping_id=device.id,
                admin_reason=f"Bloqueio automatico por incidente de seguranca - Incidente {incident.id}: {incident.incident_type}",
                admin_name="Sistema Automatico",
                problem_resolved=None
            )
            
            if feedback:
                # Ajustar timestamp
                if incident.processed_at:
                    db.query(BlockingFeedbackHistory).filter(
                        BlockingFeedbackHistory.id == feedback.id
                    ).update({
                        'created_at': incident.processed_at + timedelta(seconds=2),
                        'admin_review_date': incident.processed_at + timedelta(seconds=2)
                    })
                    db.commit()
                
                print(f"\nOK: Feedback criado para incidente {incident.id} (Feedback ID: {feedback.id})")
            else:
                print(f"\nERRO: Falha ao criar feedback para incidente {incident.id}")

if __name__ == "__main__":
    main()

