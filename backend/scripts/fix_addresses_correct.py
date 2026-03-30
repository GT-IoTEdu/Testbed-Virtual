"""
Script CORRETO para corrigir endereços IP baseado na instituição do IP.
A lógica correta é:
1. Identificar a instituição do IP pelo range
2. Buscar o alias correto (Autorizados/Bloqueados) daquela instituição
3. Atualizar alias_id para o ID correto do alias
"""

import sys
from pathlib import Path
import logging
import ipaddress

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from db.session import SessionLocal
from db.models import Institution, PfSenseAlias, PfSenseAliasAddress

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def get_institution_by_ip(ip_str: str, db) -> dict:
    """Identifica a instituição de um IP pelo range."""
    try:
        ip_obj = ipaddress.ip_address(ip_str)
        institutions = db.query(Institution).filter(Institution.is_active == True).all()
        
        for inst in institutions:
            if inst.ip_range_start and inst.ip_range_end:
                try:
                    range_start = ipaddress.ip_address(inst.ip_range_start)
                    range_end = ipaddress.ip_address(inst.ip_range_end)
                    if range_start <= ip_obj <= range_end:
                        return {
                            'id': inst.id,
                            'nome': inst.nome,
                            'cidade': inst.cidade
                        }
                except (ValueError, AttributeError):
                    continue
    except ValueError:
        pass
    return None


def get_alias_by_institution_and_name(db, institution_id: int, alias_name: str) -> PfSenseAlias:
    """Busca alias por instituição e nome."""
    alias = db.query(PfSenseAlias).filter(
        PfSenseAlias.institution_id == institution_id,
        PfSenseAlias.name == alias_name
    ).first()
    
    if not alias:
        # Criar se não existir
        alias = PfSenseAlias(
            name=alias_name,
            alias_type='host',
            descr=f'Alias {alias_name} para a instituição',
            institution_id=institution_id,
            pf_id=None
        )
        db.add(alias)
        db.flush()
        logger.info(f"  ➕ Criado alias '{alias_name}' (ID: {alias.id}) para instituição {institution_id}")
    
    return alias


def fix_all_addresses():
    """Corrige todos os endereços baseado na instituição do IP."""
    db = SessionLocal()
    try:
        logger.info("🔧 CORREÇÃO: Ajustando alias_id de todos os endereços IP\n")
        
        all_addresses = db.query(PfSenseAliasAddress).all()
        logger.info(f"📊 Total de endereços: {len(all_addresses)}\n")
        
        fixed = 0
        
        for addr in all_addresses:
            logger.info(f"🔍 IP: {addr.address} (ID: {addr.id}, alias_id atual: {addr.alias_id})")
            
            # 1. Identificar instituição do IP
            institution = get_institution_by_ip(addr.address, db)
            if not institution:
                logger.warning(f"  ⚠️ Não foi possível identificar instituição para IP {addr.address}")
                continue
            
            logger.info(f"  📍 Instituição: {institution['nome']} - {institution['cidade']} (ID: {institution['id']})")
            
            # 2. Verificar alias atual
            current_alias = db.query(PfSenseAlias).filter(PfSenseAlias.id == addr.alias_id).first()
            alias_name = "Autorizados"  # Padrão
            if current_alias:
                alias_name = current_alias.name
                logger.info(f"  📋 Alias atual: ID={current_alias.id}, name='{current_alias.name}', institution_id={current_alias.institution_id}")
            
            # 3. Buscar alias correto da instituição do IP
            correct_alias = get_alias_by_institution_and_name(db, institution['id'], alias_name)
            logger.info(f"  ✅ Alias correto: ID={correct_alias.id}, name='{correct_alias.name}', institution_id={correct_alias.institution_id}")
            
            # 4. Corrigir se necessário
            if addr.alias_id != correct_alias.id:
                old_id = addr.alias_id
                addr.alias_id = correct_alias.id
                logger.info(f"  🔄 CORRIGIDO: alias_id {old_id} -> {correct_alias.id}")
                fixed += 1
            else:
                logger.info(f"  ✅ Já está correto")
            
            logger.info("")
        
        db.commit()
        logger.info(f"{'='*60}")
        logger.info(f"✅ Correção concluída: {fixed} endereços corrigidos")
        logger.info(f"{'='*60}")
        
    except Exception as e:
        logger.error(f"❌ Erro: {e}", exc_info=True)
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply', action='store_true', help='Aplicar correções')
    args = parser.parse_args()
    
    if args.apply:
        fix_all_addresses()
    else:
        logger.info("⚠️ MODO DRY RUN - Use --apply para aplicar correções")
        fix_all_addresses()

