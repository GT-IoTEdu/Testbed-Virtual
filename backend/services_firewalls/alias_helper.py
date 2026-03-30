"""
Helper functions para gerenciar aliases baseado em IP e instituição.
Garante que sempre usamos o alias correto da instituição correta.
"""

import ipaddress
import logging
from typing import Optional, Dict, Any
from db.session import SessionLocal
from db.models import Institution, PfSenseAlias, PfSenseAliasAddress

logger = logging.getLogger(__name__)


def get_institution_by_ip(ip_str: str) -> Optional[Dict[str, Any]]:
    """
    Identifica a instituição de um IP baseado no range de IPs.
    
    Args:
        ip_str: Endereço IP (ex: "192.168.59.4")
        
    Returns:
        Dict com informações da instituição ou None se não encontrado
    """
    try:
        ip_obj = ipaddress.ip_address(ip_str)
        db = SessionLocal()
        try:
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
                                'cidade': inst.cidade,
                                'ip_range_start': inst.ip_range_start,
                                'ip_range_end': inst.ip_range_end
                            }
                    except (ValueError, AttributeError):
                        continue
        finally:
            db.close()
    except ValueError:
        pass
    except Exception as e:
        logger.error(f"Erro ao identificar instituição pelo IP {ip_str}: {e}")
    
    return None


def get_alias_by_institution_and_name(
    institution_id: int, 
    alias_name: str,
    create_if_not_exists: bool = False
) -> Optional[PfSenseAlias]:
    """
    Busca um alias específico de uma instituição.
    
    Args:
        institution_id: ID da instituição
        alias_name: Nome do alias ("Autorizados" ou "Bloqueados")
        create_if_not_exists: Se True, cria o alias se não existir
        
    Returns:
        Objeto PfSenseAlias ou None
    """
    db = SessionLocal()
    try:
        alias = db.query(PfSenseAlias).filter(
            PfSenseAlias.institution_id == institution_id,
            PfSenseAlias.name == alias_name
        ).first()
        
        if not alias and create_if_not_exists:
            # Criar alias se não existir
            alias = PfSenseAlias(
                name=alias_name,
                alias_type='host',
                descr=f'Alias {alias_name} para a instituição',
                institution_id=institution_id,
                pf_id=None  # Será preenchido ao sincronizar com pfSense
            )
            db.add(alias)
            db.flush()  # Importante: flush para obter o ID
            logger.info(f"✅ Alias '{alias_name}' criado para instituição {institution_id} (ID: {alias.id})")
        
        return alias
    finally:
        db.close()


def get_correct_alias_for_ip(
    ip_str: str, 
    alias_name: str,
    create_if_not_exists: bool = False
) -> Optional[PfSenseAlias]:
    """
    Encontra o alias correto para um IP baseado na instituição do IP.
    
    Lógica:
    1. Identifica a instituição do IP pelo range
    2. Busca o alias (Autorizados/Bloqueados) daquela instituição
    3. Retorna o alias correto
    
    Args:
        ip_str: Endereço IP (ex: "192.168.59.4")
        alias_name: Nome do alias ("Autorizados" ou "Bloqueados")
        create_if_not_exists: Se True, cria o alias se não existir
        
    Returns:
        Objeto PfSenseAlias ou None se não conseguir identificar
    """
    # 1. Identificar instituição pelo IP
    institution = get_institution_by_ip(ip_str)
    if not institution:
        logger.warning(f"⚠️ Não foi possível identificar a instituição do IP {ip_str}")
        return None
    
    # 2. Buscar alias da instituição
    alias = get_alias_by_institution_and_name(
        institution_id=institution['id'],
        alias_name=alias_name,
        create_if_not_exists=create_if_not_exists
    )
    
    if alias:
        logger.info(f"✅ Alias '{alias_name}' encontrado para IP {ip_str} (Instituição: {institution['nome']} - {institution['cidade']}, Alias ID: {alias.id})")
    else:
        logger.warning(f"⚠️ Alias '{alias_name}' não encontrado para IP {ip_str} (Instituição: {institution['nome']} - {institution['cidade']})")
    
    return alias


def fix_address_alias_relationship(address_id: Optional[int] = None, address_ip: Optional[str] = None) -> bool:
    """
    Corrige o relacionamento de um endereço IP com o alias correto.
    
    Args:
        address_id: ID do registro em pfsense_alias_addresses (opcional)
        address_ip: IP do endereço (opcional, usado se address_id não fornecido)
        
    Returns:
        True se corrigido com sucesso, False caso contrário
    """
    db = SessionLocal()
    try:
        # Buscar o registro do endereço
        if address_id:
            addr = db.query(PfSenseAliasAddress).filter(
                PfSenseAliasAddress.id == address_id
            ).first()
        elif address_ip:
            addr = db.query(PfSenseAliasAddress).filter(
                PfSenseAliasAddress.address == address_ip
            ).first()
        else:
            logger.error("❌ É necessário fornecer address_id ou address_ip")
            return False
        
        if not addr:
            logger.warning(f"⚠️ Endereço não encontrado (ID: {address_id}, IP: {address_ip})")
            return False
        
        # Verificar se o alias atual existe
        current_alias = db.query(PfSenseAlias).filter(
            PfSenseAlias.id == addr.alias_id
        ).first()
        
        if current_alias:
            # Verificar se o IP pertence à instituição do alias
            institution = get_institution_by_ip(addr.address)
            if institution and current_alias.institution_id == institution['id']:
                logger.info(f"✅ Relacionamento correto: IP {addr.address} -> Alias ID {addr.alias_id} (Instituição {institution['id']})")
                return True
        
        # Precisamos corrigir: encontrar o alias correto
        # Determinar se é "Autorizados" ou "Bloqueados" pelo alias atual (se existir)
        alias_name = "Autorizados"  # Padrão
        if current_alias:
            alias_name = current_alias.name
        
        # Encontrar o alias correto
        correct_alias = get_correct_alias_for_ip(
            ip_str=addr.address,
            alias_name=alias_name,
            create_if_not_exists=True
        )
        
        if correct_alias:
            old_alias_id = addr.alias_id
            addr.alias_id = correct_alias.id
            db.commit()
            logger.info(f"✅ Corrigido: IP {addr.address} movido de alias_id {old_alias_id} para alias_id {correct_alias.id} (Instituição {correct_alias.institution_id})")
            return True
        else:
            logger.error(f"❌ Não foi possível encontrar/criar alias correto para IP {addr.address}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Erro ao corrigir relacionamento: {e}", exc_info=True)
        db.rollback()
        return False
    finally:
        db.close()

