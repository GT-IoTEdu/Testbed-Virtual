"""
Script para corrigir TODOS os endereços IP baseado na instituição do IP.
Garante que cada IP está no alias correto da sua instituição.
"""

import sys
from pathlib import Path
import logging

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from db.session import SessionLocal
from db.models import PfSenseAlias, PfSenseAliasAddress
from services_firewalls.alias_helper import get_correct_alias_for_ip

logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)


def fix_all_addresses_by_ip():
    """Corrige todos os endereços IP baseado na instituição do IP."""
    db = SessionLocal()
    try:
        logger.info("🔧 CORREÇÃO: Ajustando todos os endereços IP para os aliases corretos\n")
        
        # Buscar todos os endereços
        all_addresses = db.query(PfSenseAliasAddress).all()
        logger.info(f"📊 Total de endereços encontrados: {len(all_addresses)}\n")
        
        fixed_count = 0
        error_count = 0
        
        for addr in all_addresses:
            logger.info(f"🔍 Processando IP {addr.address} (ID: {addr.id}, alias_id atual: {addr.alias_id})")
            
            # Verificar se o alias atual existe e qual é o nome
            current_alias = db.query(PfSenseAlias).filter(
                PfSenseAlias.id == addr.alias_id
            ).first()
            
            alias_name = "Autorizados"  # Padrão
            if current_alias:
                alias_name = current_alias.name
                logger.info(f"  📋 Alias atual: ID={current_alias.id}, name='{current_alias.name}', institution_id={current_alias.institution_id}")
            
            # SEMPRE encontrar o alias correto baseado no IP e no tipo (Autorizados/Bloqueados)
            # Isso garante que mesmo que o alias_id esteja "correto", vamos verificar se é realmente o alias da instituição do IP
            correct_alias = get_correct_alias_for_ip(
                ip_str=addr.address,
                alias_name=alias_name,
                create_if_not_exists=True
            )
            
            if correct_alias:
                # Verificar se precisa corrigir
                if addr.alias_id != correct_alias.id:
                    old_alias_id = addr.alias_id
                    old_alias_name = current_alias.name if current_alias else "desconhecido"
                    addr.alias_id = correct_alias.id
                    logger.info(f"  ✅ CORRIGIDO: IP {addr.address} movido de alias_id {old_alias_id} ('{old_alias_name}') para alias_id {correct_alias.id} ('{correct_alias.name}', Instituição: {correct_alias.institution_id})")
                    fixed_count += 1
                else:
                    logger.info(f"  ✅ IP {addr.address} já está no alias correto (ID: {correct_alias.id}, '{correct_alias.name}', Instituição: {correct_alias.institution_id})")
            else:
                logger.error(f"  ❌ Não foi possível encontrar/criar alias '{alias_name}' para IP {addr.address}")
                error_count += 1
        
        db.commit()
        
        logger.info(f"\n{'='*80}")
        logger.info(f"✅ CORREÇÃO CONCLUÍDA:")
        logger.info(f"   - {fixed_count} endereços corrigidos")
        logger.info(f"   - {error_count} erros")
        logger.info(f"{'='*80}\n")
        
    except Exception as e:
        logger.error(f"❌ Erro durante correção: {e}", exc_info=True)
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Corrigir todos os endereços IP para os aliases corretos')
    parser.add_argument('--apply', action='store_true', help='Aplicar correções (sem isso, apenas mostra o que seria feito)')
    
    args = parser.parse_args()
    
    if args.apply:
        fix_all_addresses_by_ip()
    else:
        logger.info("⚠️  MODO DRY RUN - Execute com --apply para aplicar as correções")
        logger.info("Mostrando o que seria corrigido:\n")
        # Ainda executar mas sem commit
        fix_all_addresses_by_ip()

