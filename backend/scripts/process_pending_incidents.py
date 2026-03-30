"""
Script para processar incidentes pendentes que não foram bloqueados automaticamente.
Verifica e processa todos os incidentes de atacante que ainda não foram processados.
"""
import sys
import os

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services_scanners.incident_service import IncidentService
from db.session import SessionLocal
from db.models import ZeekIncident
from sqlalchemy import desc, or_
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def main():
    """Processa incidentes pendentes manualmente."""
    incident_service = IncidentService()
    
    # Buscar incidentes não processados do tipo "Atacante"
    with SessionLocal() as db:
        unprocessed = db.query(ZeekIncident).filter(
            ZeekIncident.processed_at.is_(None),
            or_(
                ZeekIncident.incident_type.like('%Atacante%'),
                ZeekIncident.incident_type.like('%Attacker%')
            )
        ).order_by(desc(ZeekIncident.detected_at)).all()
        
        if not unprocessed:
            logger.info("✅ Nenhum incidente pendente encontrado")
            return
        
        logger.info(f"📋 Encontrados {len(unprocessed)} incidente(s) pendente(s) do tipo 'Atacante'")
        
        for incident in unprocessed:
            logger.info(f"\n{'='*60}")
            logger.info(f"🔍 Processando incidente ID: {incident.id}")
            logger.info(f"   Tipo: {incident.incident_type}")
            logger.info(f"   IP: {incident.device_ip}")
            logger.info(f"   Detectado em: {incident.detected_at}")
            logger.info(f"   Status: {incident.status}")
            logger.info(f"   Processado: {incident.processed_at}")
            
            # Verificar se é atacante
            is_attacker = "Atacante" in incident.incident_type or "Attacker" in incident.incident_type
            logger.info(f"   É atacante: {is_attacker}")
            
            if is_attacker:
                logger.info(f"🔒 Aplicando bloqueio automático...")
                try:
                    blocking_success = incident_service._apply_auto_block(incident)
                    
                    if blocking_success:
                        logger.info(f"✅ Bloqueio aplicado com sucesso!")
                        # Marcar como processado
                        incident_service._mark_incident_as_processed(incident.id)
                        logger.info(f"✅ Incidente {incident.id} marcado como processado")
                    else:
                        logger.error(f"❌ Falha ao aplicar bloqueio")
                except Exception as e:
                    logger.error(f"❌ Erro ao processar incidente {incident.id}: {e}", exc_info=True)
            else:
                logger.info(f"⏭️ Incidente não é de atacante, pulando...")
    
    # Processar via batch também para garantir
    logger.info(f"\n{'='*60}")
    logger.info(f"🔄 Processando via batch (método oficial)...")
    result = incident_service.process_incidents_for_auto_blocking(limit=50)
    
    logger.info(f"\n📊 Resultado do processamento em batch:")
    logger.info(f"   Sucesso: {result.get('success', False)}")
    logger.info(f"   Processados: {result.get('processed_count', 0)}")
    logger.info(f"   Bloqueados: {result.get('blocked_count', 0)}")
    logger.info(f"   Erros: {result.get('error_count', 0)}")
    logger.info(f"   Pulados: {result.get('skipped_count', 0)}")
    logger.info(f"   Mensagem: {result.get('message', 'N/A')}")
    
    # Verificar se ainda há incidentes pendentes
    with SessionLocal() as db:
        remaining = db.query(ZeekIncident).filter(
            ZeekIncident.processed_at.is_(None),
            or_(
                ZeekIncident.incident_type.like('%Atacante%'),
                ZeekIncident.incident_type.like('%Attacker%')
            )
        ).count()
        
        if remaining > 0:
            logger.warning(f"⚠️ Ainda há {remaining} incidente(s) pendente(s)")
        else:
            logger.info(f"✅ Todos os incidentes foram processados!")

if __name__ == "__main__":
    main()

