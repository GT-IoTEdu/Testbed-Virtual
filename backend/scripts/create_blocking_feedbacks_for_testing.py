"""
Script para criar feedbacks de bloqueio automatico em incidentes processados para testes.
"""
import sys
from pathlib import Path

# Adicionar o diretorio backend ao path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from db.models import ZeekIncident, DhcpStaticMapping, BlockingFeedbackHistory
from db.session import get_db_session
from services_firewalls.blocking_feedback_service import BlockingFeedbackService
from datetime import datetime, timedelta

def create_feedback_for_incident(incident_id, db):
    """Cria feedback de bloqueio para um incidente."""
    try:
        # Buscar o incidente
        incident = db.query(ZeekIncident).filter(ZeekIncident.id == incident_id).first()
        if not incident:
            print(f"  Incidente {incident_id} nao encontrado")
            return False
        
        # Verificar se ja tem feedback
        device = db.query(DhcpStaticMapping).filter(
            DhcpStaticMapping.ipaddr == incident.device_ip
        ).first()
        
        if device:
            existing = db.query(BlockingFeedbackHistory).filter(
                BlockingFeedbackHistory.dhcp_mapping_id == device.id,
                BlockingFeedbackHistory.feedback_by == "Sistema Automático"
            ).first()
            
            if existing:
                print(f"  Incidente {incident_id} ja tem feedback (ID: {existing.id})")
                return True
        
        # Criar feedback
        feedback_service = BlockingFeedbackService()
        
        if device:
            feedback = feedback_service.create_admin_blocking_feedback(
                dhcp_mapping_id=device.id,
                admin_reason=f"Bloqueio automatico por incidente de seguranca - Incidente {incident.id}: {incident.incident_type}",
                admin_name="Sistema Automatico",
                problem_resolved=None
            )
            
            if feedback:
                # Ajustar timestamp do feedback para ser proximo ao processed_at do incidente
                if incident.processed_at:
                    db.query(BlockingFeedbackHistory).filter(
                        BlockingFeedbackHistory.id == feedback.id
                    ).update({
                        'created_at': incident.processed_at + timedelta(seconds=2),
                        'admin_review_date': incident.processed_at + timedelta(seconds=2)
                    })
                    db.commit()
                
                print(f"  OK: Feedback criado para incidente {incident_id} (Feedback ID: {feedback.id})")
                return True
            else:
                print(f"  ERRO: Falha ao criar feedback para incidente {incident_id}")
                return False
        else:
            print(f"  AVISO: Dispositivo {incident.device_ip} nao encontrado no DHCP")
            return False
            
    except Exception as e:
        print(f"  ERRO ao criar feedback para incidente {incident_id}: {e}")
        return False

def main():
    """Cria feedbacks de bloqueio para incidentes processados."""
    print("=" * 80)
    print("CRIACAO DE FEEDBACKS DE BLOQUEIO PARA TESTES")
    print("=" * 80)
    
    try:
        with get_db_session() as db:
            # Buscar incidentes de atacante processados sem feedback
            attacker_incidents = db.query(ZeekIncident).filter(
                ZeekIncident.incident_type.like('%Atacante%'),
                ZeekIncident.processed_at.isnot(None)
            ).all()
            
            print(f"\nEncontrados {len(attacker_incidents)} incidentes de atacante processados")
            
            if not attacker_incidents:
                print("\nNenhum incidente encontrado para processar")
                return
            
            # Contar quantos ja tem feedback
            with_feedback = 0
            without_feedback = 0
            
            for incident in attacker_incidents:
                device = db.query(DhcpStaticMapping).filter(
                    DhcpStaticMapping.ipaddr == incident.device_ip
                ).first()
                
                if device:
                    feedback = db.query(BlockingFeedbackHistory).filter(
                        BlockingFeedbackHistory.dhcp_mapping_id == device.id,
                        BlockingFeedbackHistory.feedback_by == "Sistema Automatico"
                    ).first()
                    
                    if feedback:
                        with_feedback += 1
                    else:
                        without_feedback += 1
            
            print(f"  - Com feedback: {with_feedback}")
            print(f"  - Sem feedback: {without_feedback}")
            
            if without_feedback == 0:
                print("\nTodos os incidentes ja tem feedback!")
                return
            
            # Criar feedbacks para os que nao tem
            print(f"\nCriando feedbacks para {without_feedback} incidentes...")
            success_count = 0
            error_count = 0
            
            for incident in attacker_incidents:
                device = db.query(DhcpStaticMapping).filter(
                    DhcpStaticMapping.ipaddr == incident.device_ip
                ).first()
                
                if device:
                    feedback = db.query(BlockingFeedbackHistory).filter(
                        BlockingFeedbackHistory.dhcp_mapping_id == device.id,
                        BlockingFeedbackHistory.feedback_by == "Sistema Automatico"
                    ).first()
                    
                    if not feedback:
                        if create_feedback_for_incident(incident.id, db):
                            success_count += 1
                        else:
                            error_count += 1
            
            print("\n" + "=" * 80)
            print("RESUMO:")
            print(f"  Feedback criados com sucesso: {success_count}")
            print(f"  Erros: {error_count}")
            print("=" * 80)
            
    except Exception as e:
        print(f"\nERRO: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

