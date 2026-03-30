"""
Script para diagnosticar e corrigir relacionamentos incorretos entre 
pfsense_aliases e pfsense_alias_addresses.

PROBLEMA IDENTIFICADO:
- pfsense_aliases.id = ID primário do banco (único em todo o banco)
- pfsense_aliases.pf_id = ID do alias no pfSense (pode ser o mesmo em diferentes pfSenses)
- pfsense_alias_addresses.alias_id = DEVE referenciar pfsense_aliases.id (ID do banco)

O problema ocorre quando:
1. alias_id em pfsense_alias_addresses aponta para o alias errado
2. IPs de uma instituição estão associados ao alias de outra instituição
3. alias_id não corresponde ao alias correto baseado em name + institution_id
"""

import sys
import os
from pathlib import Path
import logging
import ipaddress
from datetime import datetime

# Adicionar o diretório backend ao path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from db.session import SessionLocal
from db.models import Institution, PfSenseAlias, PfSenseAliasAddress, DhcpStaticMapping
from typing import Optional
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from services_firewalls.alias_helper import get_correct_alias_for_ip, get_institution_by_ip

logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)


def get_ip_institution(ip_str: str, db) -> Optional[int]:
    """Identifica a instituição de um IP baseado no range."""
    try:
        ip_obj = ipaddress.ip_address(ip_str)
        institutions = db.query(Institution).filter(Institution.is_active == True).all()
        
        for inst in institutions:
            if inst.ip_range_start and inst.ip_range_end:
                try:
                    range_start = ipaddress.ip_address(inst.ip_range_start)
                    range_end = ipaddress.ip_address(inst.ip_range_end)
                    if range_start <= ip_obj <= range_end:
                        return inst.id
                except (ValueError, AttributeError):
                    continue
    except ValueError:
        pass
    return None


def diagnose_alias_relationships():
    """Diagnostica problemas nos relacionamentos entre aliases e endereços."""
    db = SessionLocal()
    try:
        logger.info("🔍 DIAGNÓSTICO: Verificando relacionamentos entre pfsense_aliases e pfsense_alias_addresses\n")
        
        # 1. Verificar todos os aliases
        all_aliases = db.query(PfSenseAlias).all()
        logger.info(f"📊 Total de aliases no banco: {len(all_aliases)}")
        
        for alias in all_aliases:
            logger.info(f"\n  Alias ID={alias.id}, name='{alias.name}', institution_id={alias.institution_id}, pf_id={alias.pf_id}")
        
        # 2. Verificar todos os endereços
        all_addresses = db.query(PfSenseAliasAddress).all()
        logger.info(f"\n📊 Total de endereços no banco: {len(all_addresses)}")
        
        # 3. Verificar problemas
        problems = []
        
        for addr in all_addresses:
            alias = db.query(PfSenseAlias).filter(PfSenseAlias.id == addr.alias_id).first()
            
            if not alias:
                # Verificar se podemos encontrar o alias correto baseado no IP
                correct_alias = get_correct_alias_for_ip(addr.address, "Autorizados", create_if_not_exists=False)
                if not correct_alias:
                    correct_alias = get_correct_alias_for_ip(addr.address, "Bloqueados", create_if_not_exists=False)
                
                if correct_alias:
                    problems.append({
                        'type': 'ORPHAN_ADDRESS',
                        'address_id': addr.id,
                        'address': addr.address,
                        'alias_id': addr.alias_id,
                        'correct_alias_id': correct_alias.id,
                        'message': f"Endereço {addr.address} (ID: {addr.id}) referencia alias_id {addr.alias_id} que não existe. Alias correto seria ID {correct_alias.id}"
                    })
                else:
                    problems.append({
                        'type': 'ORPHAN_ADDRESS',
                        'address_id': addr.id,
                        'address': addr.address,
                        'alias_id': addr.alias_id,
                        'message': f"Endereço {addr.address} (ID: {addr.id}) referencia alias_id {addr.alias_id} que não existe e não foi possível identificar alias correto"
                    })
                continue
            
            # Verificar se o IP pertence à instituição do alias
            ip_institution = get_ip_institution(addr.address, db)
            
            if ip_institution and alias.institution_id:
                if ip_institution != alias.institution_id:
                    problems.append({
                        'type': 'WRONG_INSTITUTION',
                        'address_id': addr.id,
                        'address': addr.address,
                        'alias_id': addr.alias_id,
                        'alias_name': alias.name,
                        'alias_institution_id': alias.institution_id,
                        'ip_institution_id': ip_institution,
                        'message': f"IP {addr.address} pertence à instituição {ip_institution} mas está no alias '{alias.name}' (ID: {alias.id}) da instituição {alias.institution_id}"
                    })
        
        # 4. Verificar aliases duplicados (mesmo name + institution_id)
        logger.info("\n🔍 Verificando aliases duplicados...")
        institutions = db.query(Institution).filter(Institution.is_active == True).all()
        
        for inst in institutions:
            aliases = db.query(PfSenseAlias).filter(
                PfSenseAlias.institution_id == inst.id
            ).all()
            
            alias_names = {}
            for alias in aliases:
                if alias.name not in alias_names:
                    alias_names[alias.name] = []
                alias_names[alias.name].append(alias)
            
            for name, alias_list in alias_names.items():
                if len(alias_list) > 1:
                    problems.append({
                        'type': 'DUPLICATE_ALIAS',
                        'institution_id': inst.id,
                        'alias_name': name,
                        'alias_ids': [a.id for a in alias_list],
                        'message': f"Alias '{name}' duplicado na instituição {inst.id}: IDs {[a.id for a in alias_list]}"
                    })
        
        # 5. Relatório
        logger.info(f"\n{'='*80}")
        logger.info(f"📋 RELATÓRIO DE PROBLEMAS ENCONTRADOS: {len(problems)}")
        logger.info(f"{'='*80}\n")
        
        if not problems:
            logger.info("✅ Nenhum problema encontrado!")
            return []
        
        for i, problem in enumerate(problems, 1):
            logger.info(f"{i}. [{problem['type']}] {problem['message']}")
        
        return problems
        
    except Exception as e:
        logger.error(f"❌ Erro durante diagnóstico: {e}", exc_info=True)
        raise
    finally:
        db.close()


def fix_alias_relationships(dry_run: bool = True):
    """Corrige os relacionamentos incorretos."""
    db = SessionLocal()
    try:
        logger.info(f"\n{'='*80}")
        logger.info(f"🔧 {'[DRY RUN] ' if dry_run else ''}CORREÇÃO DE RELACIONAMENTOS")
        logger.info(f"{'='*80}\n")
        
        problems = diagnose_alias_relationships()
        
        if not problems:
            logger.info("✅ Nenhuma correção necessária!")
            return
        
        if dry_run:
            logger.info("\n⚠️  MODO DRY RUN - Nenhuma alteração será feita")
            logger.info("Execute com dry_run=False para aplicar as correções\n")
            return
        
        logger.info("\n🔧 Aplicando correções...\n")
        
        fixes_applied = 0
        
        for problem in problems:
            if problem['type'] == 'ORPHAN_ADDRESS':
                # Tentar corrigir endereços órfãos encontrando o alias correto
                addr = db.query(PfSenseAliasAddress).filter(
                    PfSenseAliasAddress.id == problem['address_id']
                ).first()
                if addr:
                    # Tentar encontrar o alias correto baseado no IP
                    # Assumir que é "Autorizados" por padrão (pode ser ajustado)
                    correct_alias = get_correct_alias_for_ip(
                        ip_str=addr.address,
                        alias_name="Autorizados",  # Tentar primeiro com "Autorizados"
                        create_if_not_exists=True
                    )
                    
                    if not correct_alias:
                        # Tentar com "Bloqueados"
                        correct_alias = get_correct_alias_for_ip(
                            ip_str=addr.address,
                            alias_name="Bloqueados",
                            create_if_not_exists=True
                        )
                    
                    if correct_alias:
                        logger.info(f"✅ Corrigindo endereço órfão: IP {addr.address} -> Alias ID {correct_alias.id}")
                        addr.alias_id = correct_alias.id
                        fixes_applied += 1
                    else:
                        logger.warning(f"⚠️ Não foi possível encontrar alias para IP {addr.address}, removendo...")
                        db.delete(addr)
                        fixes_applied += 1
            
            elif problem['type'] == 'WRONG_INSTITUTION':
                # Mover endereço para o alias correto usando a função helper
                addr = db.query(PfSenseAliasAddress).filter(
                    PfSenseAliasAddress.id == problem['address_id']
                ).first()
                
                if addr:
                    # Usar a função helper para encontrar o alias correto baseado no IP
                    correct_alias = get_correct_alias_for_ip(
                        ip_str=addr.address,
                        alias_name=problem['alias_name'],
                        create_if_not_exists=True
                    )
                    
                    if correct_alias:
                        logger.info(f"🔄 Movendo IP {addr.address} do alias ID {problem['alias_id']} para alias ID {correct_alias.id} (instituição {correct_alias.institution_id})")
                        addr.alias_id = correct_alias.id
                        fixes_applied += 1
                    else:
                        logger.error(f"❌ Não foi possível encontrar/criar alias '{problem['alias_name']}' para IP {addr.address}")
            
            elif problem['type'] == 'DUPLICATE_ALIAS':
                # Manter apenas o alias mais recente, mover endereços para ele
                alias_list = [db.query(PfSenseAlias).filter(PfSenseAlias.id == aid).first() 
                             for aid in problem['alias_ids']]
                alias_list = [a for a in alias_list if a]  # Remover None
                
                if len(alias_list) > 1:
                    # Ordenar por updated_at (mais recente primeiro)
                    alias_list.sort(key=lambda x: x.updated_at or datetime.min, reverse=True)
                    keep_alias = alias_list[0]
                    remove_aliases = alias_list[1:]
                    
                    logger.info(f"🔄 Mantendo alias ID {keep_alias.id}, removendo duplicados: {[a.id for a in remove_aliases]}")
                    
                    for remove_alias in remove_aliases:
                        # Mover endereços para o alias mantido
                        addresses_to_move = db.query(PfSenseAliasAddress).filter(
                            PfSenseAliasAddress.alias_id == remove_alias.id
                        ).all()
                        
                        for addr in addresses_to_move:
                            # Verificar se já existe no alias mantido
                            existing = db.query(PfSenseAliasAddress).filter(
                                PfSenseAliasAddress.alias_id == keep_alias.id,
                                PfSenseAliasAddress.address == addr.address
                            ).first()
                            
                            if existing:
                                logger.info(f"  🗑️  Removendo endereço duplicado: {addr.address}")
                                db.delete(addr)
                            else:
                                logger.info(f"  🔄 Movendo endereço {addr.address} para alias ID {keep_alias.id}")
                                addr.alias_id = keep_alias.id
                        
                        # Remover alias duplicado
                        logger.info(f"🗑️  Removendo alias duplicado ID {remove_alias.id}")
                        db.delete(remove_alias)
                        fixes_applied += 1
        
        db.commit()
        logger.info(f"\n✅ Correções aplicadas: {fixes_applied}")
        logger.info("\n🔍 Executando diagnóstico pós-correção...\n")
        diagnose_alias_relationships()
        
    except Exception as e:
        logger.error(f"❌ Erro durante correção: {e}", exc_info=True)
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Diagnosticar e corrigir relacionamentos entre aliases e endereços')
    parser.add_argument('--fix', action='store_true', help='Aplicar correções (sem isso, apenas diagnostica)')
    parser.add_argument('--apply', action='store_true', help='Aplicar correções (equivalente a --fix sem dry-run)')
    
    args = parser.parse_args()
    
    if args.fix or args.apply:
        fix_alias_relationships(dry_run=not args.apply)
    else:
        diagnose_alias_relationships()

