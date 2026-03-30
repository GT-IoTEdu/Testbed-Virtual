"""
Script para testar bloqueio automático manualmente.
Processa incidentes pendentes que não foram bloqueados automaticamente.
"""
import sys
import os

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services_scanners.incident_service import IncidentService
from db.session import SessionLocal
from db.models import ZeekIncident
from sqlalchemy import desc
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def main():
    """Processa incidentes pendentes manualmente."""
    incident_service = IncidentService()
    
    # Buscar incidentes não processados do tipo "SQL Injection - Atacante"
    with SessionLocal() as db:
        unprocessed = db.query(ZeekIncident).filter(
            ZeekIncident.processed_at.is_(None),
            ZeekIncident.incident_type.like('%Atacante%')
        ).order_by(desc(ZeekIncident.detected_at)).limit(10).all()
        
        if not unprocessed:
            logger.info("✅ Nenhum incidente pendente encontrado")
            return
        
        logger.info(f"📋 Encontrados {len(unprocessed)} incidente(s) pendente(s)")
        
        for incident in unprocessed:
            logger.info(f"\n{'='*60}")
            logger.info(f"🔍 Processando incidente ID: {incident.id}")
            logger.info(f"   Tipo: {incident.incident_type}")
            logger.info(f"   IP: {incident.device_ip}")
            logger.info(f"   Detectado em: {incident.detected_at}")
            logger.info(f"   Status: {incident.status}")
            
            # Verificar se é atacante
            is_attacker = "Atacante" in incident.incident_type or "Attacker" in incident.incident_type
            logger.info(f"   É atacante: {is_attacker}")
            
            if is_attacker:
                logger.info(f"🔒 Aplicando bloqueio automático...")
                blocking_success = incident_service._apply_auto_block(incident)
                
                if blocking_success:
                    logger.info(f"✅ Bloqueio aplicado com sucesso!")
                else:
                    logger.error(f"❌ Falha ao aplicar bloqueio")
            else:
                logger.info(f"⏭️ Incidente não é de atacante, pulando...")
    
    # Processar via batch também
    logger.info(f"\n{'='*60}")
    logger.info(f"🔄 Processando via batch...")
    result = incident_service.process_incidents_for_auto_blocking(limit=10)
    
    logger.info(f"\n📊 Resultado do processamento em batch:")
    logger.info(f"   Processados: {result.get('processed_count', 0)}")
    logger.info(f"   Bloqueados: {result.get('blocked_count', 0)}")
    logger.info(f"   Erros: {result.get('error_count', 0)}")
    logger.info(f"   Pulados: {result.get('skipped_count', 0)}")

if __name__ == "__main__":
    main()

