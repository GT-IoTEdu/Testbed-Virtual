#!/usr/bin/env python3
"""
Script de inicialização: Cria aliases e regras iniciais durante instalação.

Este script:
1. Cria aliases "Autorizados" e "Bloqueados" para cada instituição
2. Cria regras de firewall básicas no pfSense
3. Sincroniza regras com o banco de dados

Uso:
    python scripts/setup_initial_aliases_and_rules.py [--institution-id ID]
    
    Se --institution-id não for fornecido, cria para todas as instituições.
"""

import sys
import os
import logging
import argparse
from pathlib import Path

# Adicionar o diretório backend ao path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from db.session import SessionLocal
from db.models import Institution, User
from services_firewalls.alias_service import AliasService
from services_firewalls.pfsense_client import _get_pfsense_config, aplicar_mudancas_firewall_pfsense
import requests

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def criar_regra_firewall_pfsense(
    rule_data: dict,
    pfsense_url: str = None,
    pfsense_key: str = None,
    user_id: int = None,
    institution_id: int = None
) -> dict:
    """
    Cria uma regra de firewall no pfSense via API v2.
    
    Args:
        rule_data: Dados da regra (type, interface, source, destination, etc.)
        pfsense_url: URL base do pfSense (opcional)
        pfsense_key: Chave API do pfSense (opcional)
        user_id: ID do usuário (opcional)
        institution_id: ID da instituição (opcional)
    
    Returns:
        Resposta da API do pfSense
    """
    base_url, api_key = _get_pfsense_config(pfsense_url, pfsense_key, user_id, institution_id)
    url = f"{base_url}firewall/rule"
    headers = {
        "X-API-Key": api_key,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, headers=headers, json=rule_data, timeout=30, verify=False)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Erro ao criar regra no pfSense: {e}")
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"Resposta: {e.response.text}")
        raise


def criar_aliases_iniciais(institution_id: int) -> dict:
    """
    Cria aliases iniciais para uma instituição.
    
    Returns:
        Dict com status de criação de cada alias
    """
    result = {
        'autorizados': False,
        'bloqueados': False
    }
    
    try:
        # Buscar um usuário ADMIN da instituição para usar como referência
        db = SessionLocal()
        try:
            admin_user = db.query(User).filter(
                User.institution_id == institution_id,
                User.permission == 'ADMIN'
            ).first()
            
            if not admin_user:
                # Se não houver ADMIN, criar com institution_id direto
                user_id = None
            else:
                user_id = admin_user.id
        finally:
            db.close()
        
        with AliasService(user_id=user_id, institution_id=institution_id) as alias_service:
            # Criar alias "Autorizados"
            try:
                alias_service.create_alias({
                    'name': 'Autorizados',
                    'alias_type': 'host',
                    'descr': 'Dispositivos autorizados na rede',
                    'addresses': []
                })
                result['autorizados'] = True
                logger.info(f"✅ Alias 'Autorizados' criado para instituição {institution_id}")
            except ValueError as e:
                if 'já existe' in str(e).lower():
                    logger.info(f"ℹ️  Alias 'Autorizados' já existe para instituição {institution_id}")
                    result['autorizados'] = True
                else:
                    logger.error(f"❌ Erro ao criar alias 'Autorizados': {e}")
            
            # Criar alias "Bloqueados"
            try:
                alias_service.create_alias({
                    'name': 'Bloqueados',
                    'alias_type': 'host',
                    'descr': 'Dispositivos bloqueados',
                    'addresses': []
                })
                result['bloqueados'] = True
                logger.info(f"✅ Alias 'Bloqueados' criado para instituição {institution_id}")
            except ValueError as e:
                if 'já existe' in str(e).lower():
                    logger.info(f"ℹ️  Alias 'Bloqueados' já existe para instituição {institution_id}")
                    result['bloqueados'] = True
                else:
                    logger.error(f"❌ Erro ao criar alias 'Bloqueados': {e}")
    
    except Exception as e:
        logger.error(f"❌ Erro ao criar aliases para instituição {institution_id}: {e}")
    
    return result


def criar_regras_iniciais(institution_id: int) -> dict:
    """
    Cria regras de firewall iniciais no pfSense.
    
    Returns:
        Dict com status de criação de cada regra
    """
    result = {
        'regra_block': False,
        'regra_pass': False
    }
    
    try:
        # Buscar configurações da instituição
        db = SessionLocal()
        try:
            institution = db.query(Institution).filter(Institution.id == institution_id).first()
            if not institution:
                logger.error(f"❌ Instituição {institution_id} não encontrada")
                return result
            
            # Buscar um usuário ADMIN da instituição
            admin_user = db.query(User).filter(
                User.institution_id == institution_id,
                User.permission == 'ADMIN'
            ).first()
            
            user_id = admin_user.id if admin_user else None
        finally:
            db.close()
        
        # Criar regra BLOCK para alias "Bloqueados"
        try:
            regra_block = {
                'type': 'block',
                'interface': ['lan'],  # Ajustar conforme necessário
                'ipprotocol': 'inet',
                # Não incluir 'protocol' para permitir qualquer protocolo
                'source': 'Bloqueados',
                'destination': 'any',
                'descr': 'Bloqueio Total - Dispositivos no alias Bloqueados',
                'disabled': False,
                'log': True,
                'statetype': 'keep state'
            }
            
            criar_regra_firewall_pfsense(
                regra_block,
                user_id=user_id,
                institution_id=institution_id
            )
            result['regra_block'] = True
            logger.info(f"✅ Regra BLOCK criada para instituição {institution_id}")
        except Exception as e:
            logger.warning(f"⚠️  Não foi possível criar regra BLOCK (pode já existir): {e}")
        
        # Criar regra PASS para alias "Autorizados"
        try:
            regra_pass = {
                'type': 'pass',
                'interface': ['lan'],  # Ajustar conforme necessário
                'ipprotocol': 'inet',
                # Não incluir 'protocol' para permitir qualquer protocolo
                'source': 'Autorizados',
                'destination': 'any',
                'descr': 'Liberação Total - Dispositivos no alias Autorizados',
                'disabled': False,
                'log': False,
                'statetype': 'keep state'
            }
            
            criar_regra_firewall_pfsense(
                regra_pass,
                user_id=user_id,
                institution_id=institution_id
            )
            result['regra_pass'] = True
            logger.info(f"✅ Regra PASS criada para instituição {institution_id}")
        except Exception as e:
            logger.warning(f"⚠️  Não foi possível criar regra PASS (pode já existir): {e}")
        
        # Aplicar mudanças no firewall
        try:
            aplicar_mudancas_firewall_pfsense(
                user_id=user_id,
                institution_id=institution_id
            )
            logger.info(f"✅ Mudanças aplicadas no firewall para instituição {institution_id}")
        except Exception as e:
            logger.warning(f"⚠️  Erro ao aplicar mudanças no firewall: {e}")
    
    except Exception as e:
        logger.error(f"❌ Erro ao criar regras para instituição {institution_id}: {e}")
    
    return result


def sincronizar_regras(institution_id: int):
    """
    Sincroniza regras do pfSense com o banco de dados.
    """
    try:
        db = SessionLocal()
        try:
            admin_user = db.query(User).filter(
                User.institution_id == institution_id,
                User.permission == 'ADMIN'
            ).first()
            
            if not admin_user:
                logger.warning(f"⚠️  Nenhum usuário ADMIN encontrado para instituição {institution_id}")
                return
            
            user_id = admin_user.id
        finally:
            db.close()
        
        # Usar a lógica de sincronização diretamente
        from services_firewalls.pfsense_client import listar_regras_firewall_pfsense
        from db.models import PfSenseFirewallRule, User as UserModel
        from datetime import datetime
        
        result = listar_regras_firewall_pfsense(user_id=user_id)
        rules = result.get("data") if isinstance(result, dict) else (result or [])
        
        if not isinstance(rules, list):
            logger.warning(f"⚠️  Formato inesperado de retorno de regras para instituição {institution_id}")
            return
        
        db = SessionLocal()
        try:
            user = db.query(UserModel).filter(UserModel.id == user_id).first()
            institution_id_db = user.institution_id if user else institution_id
            
            saved, updated = 0, 0
            for r in rules:
                pf_id = r.get("id")
                if pf_id is None:
                    continue
                
                existing_query = db.query(PfSenseFirewallRule).filter(
                    PfSenseFirewallRule.pf_id == pf_id
                )
                if institution_id_db:
                    existing_query = existing_query.filter(
                        PfSenseFirewallRule.institution_id == institution_id_db
                    )
                existing = existing_query.first()
                
                payload = {
                    'type': r.get('type'),
                    'interface': ", ".join(r.get('interface') or []) if isinstance(r.get('interface'), list) else (r.get('interface') or None),
                    'ipprotocol': r.get('ipprotocol'),
                    'protocol': r.get('protocol'),
                    'source': r.get('source'),
                    'destination': r.get('destination'),
                    'descr': r.get('descr'),
                    'disabled': r.get('disabled') or False,
                    'log': r.get('log') or False,
                    'statetype': r.get('statetype'),
                    'institution_id': institution_id_db,
                }
                
                if existing:
                    for k, v in payload.items():
                        setattr(existing, k, v)
                    updated += 1
                else:
                    rec = PfSenseFirewallRule(pf_id=pf_id, **payload)
                    db.add(rec)
                    saved += 1
            
            db.commit()
            logger.info(f"✅ Regras sincronizadas: {saved} criadas, {updated} atualizadas para instituição {institution_id}")
        finally:
            db.close()
    
    except Exception as e:
        logger.error(f"❌ Erro ao sincronizar regras para instituição {institution_id}: {e}")


def setup_instituicao(institution_id: int):
    """
    Configura aliases e regras para uma instituição específica.
    """
    logger.info(f"\n{'='*60}")
    logger.info(f"Configurando instituição ID: {institution_id}")
    logger.info(f"{'='*60}")
    
    db = SessionLocal()
    try:
        institution = db.query(Institution).filter(Institution.id == institution_id).first()
        if not institution:
            logger.error(f"❌ Instituição {institution_id} não encontrada")
            return False
        
        logger.info(f"📋 Instituição: {institution.nome} - {institution.cidade}")
    finally:
        db.close()
    
    # 1. Criar aliases
    logger.info("\n📦 Passo 1: Criando aliases iniciais...")
    aliases_result = criar_aliases_iniciais(institution_id)
    
    # 2. Criar regras
    logger.info("\n🛡️  Passo 2: Criando regras de firewall...")
    regras_result = criar_regras_iniciais(institution_id)
    
    # 3. Sincronizar regras
    logger.info("\n🔄 Passo 3: Sincronizando regras com banco de dados...")
    sincronizar_regras(institution_id)
    
    # Resumo
    logger.info(f"\n{'='*60}")
    logger.info(f"✅ Configuração concluída para instituição {institution_id}")
    logger.info(f"{'='*60}")
    logger.info(f"Aliases:")
    logger.info(f"  - Autorizados: {'✅' if aliases_result['autorizados'] else '❌'}")
    logger.info(f"  - Bloqueados: {'✅' if aliases_result['bloqueados'] else '❌'}")
    logger.info(f"Regras:")
    logger.info(f"  - BLOCK: {'✅' if regras_result['regra_block'] else '⚠️'}")
    logger.info(f"  - PASS: {'✅' if regras_result['regra_pass'] else '⚠️'}")
    
    return True


def main():
    """Função principal."""
    parser = argparse.ArgumentParser(
        description='Cria aliases e regras iniciais durante instalação'
    )
    parser.add_argument(
        '--institution-id',
        type=int,
        help='ID da instituição (se não fornecido, configura todas)'
    )
    
    args = parser.parse_args()
    
    logger.info("🚀 Iniciando configuração de aliases e regras iniciais")
    logger.info("="*60)
    
    db = SessionLocal()
    try:
        if args.institution_id:
            # Configurar apenas uma instituição
            institutions = [db.query(Institution).filter(Institution.id == args.institution_id).first()]
            if not institutions[0]:
                logger.error(f"❌ Instituição {args.institution_id} não encontrada")
                sys.exit(1)
        else:
            # Configurar todas as instituições
            institutions = db.query(Institution).filter(Institution.is_active == True).all()
            if not institutions:
                logger.warning("⚠️  Nenhuma instituição ativa encontrada")
                sys.exit(0)
    finally:
        db.close()
    
    logger.info(f"📊 Total de instituições a configurar: {len(institutions)}")
    
    success_count = 0
    for institution in institutions:
        try:
            if setup_instituicao(institution.id):
                success_count += 1
        except Exception as e:
            logger.error(f"❌ Erro ao configurar instituição {institution.id}: {e}")
    
    logger.info(f"\n{'='*60}")
    logger.info(f"✅ Configuração concluída: {success_count}/{len(institutions)} instituições")
    logger.info(f"{'='*60}")
    
    if success_count < len(institutions):
        sys.exit(1)


if __name__ == "__main__":
    main()

