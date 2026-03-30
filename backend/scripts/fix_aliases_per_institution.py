#!/usr/bin/env python3
"""
Script para corrigir aliases por instituição.
Garante que cada instituição tenha seus próprios aliases "Autorizados" e "Bloqueados",
e move os IPs para os aliases corretos baseado no institution_id dos dispositivos.

Uso:
    python -m backend.scripts.fix_aliases_per_institution
    ou
    cd backend && python scripts/fix_aliases_per_institution.py
"""

import sys
import os
from pathlib import Path

# Adicionar o diretório backend ao path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from db.session import SessionLocal
from db.models import Institution, PfSenseAlias, PfSenseAliasAddress, DhcpStaticMapping
import logging
import ipaddress

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_institution_for_ip(ip_address: str, db) -> int:
    """Retorna o institution_id baseado no IP do dispositivo."""
    try:
        device = db.query(DhcpStaticMapping).filter(DhcpStaticMapping.ipaddr == ip_address).first()
        if device and device.institution_id:
            return device.institution_id
        
        # Se não encontrou pelo dispositivo, buscar pela instituição pelo range
        institutions = db.query(Institution).filter(Institution.is_active == True).all()
        ip = ipaddress.ip_address(ip_address)
        
        for institution in institutions:
            try:
                range_start = ipaddress.ip_address(institution.ip_range_start)
                range_end = ipaddress.ip_address(institution.ip_range_end)
                if range_start <= ip <= range_end:
                    return institution.id
            except (ValueError, AttributeError):
                continue
        
        return None
    except Exception as e:
        logger.error(f"Erro ao identificar instituição para IP {ip_address}: {e}")
        return None

def fix_aliases_per_institution():
    """Corrige aliases para garantir que cada instituição tenha seus próprios aliases."""
    db = SessionLocal()
    try:
        logger.info("🔄 Iniciando correção de aliases por instituição...")
        
        # Buscar todas as instituições ativas
        institutions = db.query(Institution).filter(Institution.is_active == True).all()
        logger.info(f"📋 Encontradas {len(institutions)} instituições ativas")
        
        # Aliases padrão que cada instituição deve ter
        required_aliases = [
            {'name': 'Autorizados', 'alias_type': 'host', 'descr': 'Dispositivos Com acesso liberado'},
            {'name': 'Bloqueados', 'alias_type': 'host', 'descr': 'Dispositivos com acesso Bloqueado'}
        ]
        
        for institution in institutions:
            logger.info(f"\n🏫 Processando instituição: {institution.nome} - {institution.cidade} (ID: {institution.id})")
            
            for alias_data in required_aliases:
                alias_name = alias_data['name']
                
                # Verificar se o alias já existe para esta instituição
                existing_alias = db.query(PfSenseAlias).filter(
                    PfSenseAlias.name == alias_name,
                    PfSenseAlias.institution_id == institution.id
                ).first()
                
                if not existing_alias:
                    logger.info(f"  ➕ Criando alias '{alias_name}' para instituição {institution.id}")
                    new_alias = PfSenseAlias(
                        pf_id=None,  # Será atualizado quando sincronizar com pfSense
                        name=alias_name,
                        alias_type=alias_data['alias_type'],
                        descr=alias_data['descr'],
                        institution_id=institution.id
                    )
                    db.add(new_alias)
                    db.flush()
                    logger.info(f"  ✅ Alias '{alias_name}' criado (ID: {new_alias.id})")
                else:
                    logger.info(f"  ✅ Alias '{alias_name}' já existe (ID: {existing_alias.id})")
        
        db.commit()
        logger.info("\n✅ Aliases criados/verificados para todas as instituições")
        
        # Agora corrigir os endereços IP nos aliases
        logger.info("\n🔄 Corrigindo endereços IP nos aliases...")
        
        # Buscar todos os endereços de aliases
        all_addresses = db.query(PfSenseAliasAddress).all()
        logger.info(f"📋 Encontrados {len(all_addresses)} endereços em aliases")
        
        moved_count = 0
        removed_count = 0
        
        for address in all_addresses:
            alias = db.query(PfSenseAlias).filter(PfSenseAlias.id == address.alias_id).first()
            if not alias:
                continue
            
            # Identificar a instituição do IP
            ip_institution_id = get_institution_for_ip(address.address, db)
            
            if not ip_institution_id:
                logger.warning(f"  ⚠️ Não foi possível identificar instituição para IP {address.address}, mantendo no alias atual")
                continue
            
            # Se o IP pertence a outra instituição, mover para o alias correto
            if alias.institution_id != ip_institution_id:
                logger.info(f"  🔄 Movendo IP {address.address} do alias '{alias.name}' (instituição {alias.institution_id}) para instituição {ip_institution_id}")
                
                # Buscar o alias correto da instituição do IP
                correct_alias = db.query(PfSenseAlias).filter(
                    PfSenseAlias.name == alias.name,
                    PfSenseAlias.institution_id == ip_institution_id
                ).first()
                
                if correct_alias:
                    # Verificar se o IP já não está no alias correto
                    existing = db.query(PfSenseAliasAddress).filter(
                        PfSenseAliasAddress.alias_id == correct_alias.id,
                        PfSenseAliasAddress.address == address.address
                    ).first()
                    
                    if not existing:
                        # Mover o endereço para o alias correto
                        address.alias_id = correct_alias.id
                        moved_count += 1
                        logger.info(f"    ✅ IP {address.address} movido para alias '{correct_alias.name}' (ID: {correct_alias.id})")
                    else:
                        # IP já está no alias correto, remover duplicata
                        db.delete(address)
                        removed_count += 1
                        logger.info(f"    🗑️ IP {address.address} removido (já existe no alias correto)")
                else:
                    logger.warning(f"    ⚠️ Alias '{alias.name}' não encontrado para instituição {ip_institution_id}")
            else:
                logger.debug(f"  ✅ IP {address.address} já está no alias correto (instituição {alias.institution_id})")
        
        db.commit()
        logger.info(f"\n✅ Correção concluída:")
        logger.info(f"   - {moved_count} IPs movidos")
        logger.info(f"   - {removed_count} IPs duplicados removidos")
        
        # Mostrar resumo final
        logger.info("\n📊 Resumo final dos aliases por instituição:")
        for institution in institutions:
            logger.info(f"\n🏫 {institution.nome} - {institution.cidade} (ID: {institution.id}):")
            aliases = db.query(PfSenseAlias).filter(PfSenseAlias.institution_id == institution.id).all()
            for alias in aliases:
                addresses = db.query(PfSenseAliasAddress).filter(PfSenseAliasAddress.alias_id == alias.id).all()
                logger.info(f"   - {alias.name}: {len(addresses)} endereços")
                for addr in addresses:
                    logger.info(f"     • {addr.address}")
        
    except Exception as e:
        logger.error(f"❌ Erro durante a correção: {e}", exc_info=True)
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    try:
        fix_aliases_per_institution()
        logger.info("\n✅ Script executado com sucesso!")
    except Exception as e:
        logger.error(f"❌ Falha na execução: {e}")
        sys.exit(1)

