#!/usr/bin/env python3
"""
Script de teste para verificar se setup_initial_aliases_and_rules.py funcionou corretamente.

Este script verifica:
1. Se os aliases "Autorizados" e "Bloqueados" foram criados
2. Se as regras de firewall foram criadas no pfSense
3. Se as regras foram sincronizadas no banco de dados
4. Se tudo está associado à instituição correta

Uso:
    python scripts/test_setup_initial_aliases_and_rules.py [--institution-id ID]
"""

import sys
import os
from pathlib import Path

# Adicionar o diretório backend ao path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

import argparse
from db.session import SessionLocal
from db.models import Institution, PfSenseAlias, PfSenseFirewallRule, User
from services_firewalls.alias_service import AliasService
from services_firewalls.pfsense_client import listar_regras_firewall_pfsense, listar_aliases_pfsense

def test_aliases_in_db(institution_id: int) -> dict:
    """Testa se os aliases foram criados no banco de dados."""
    print(f"\n📦 Testando aliases no banco de dados (instituição {institution_id})...")
    
    db = SessionLocal()
    try:
        aliases = db.query(PfSenseAlias).filter(
            PfSenseAlias.institution_id == institution_id,
            PfSenseAlias.name.in_(['Autorizados', 'Bloqueados'])
        ).all()
        
        result = {
            'autorizados': False,
            'bloqueados': False,
            'total': len(aliases)
        }
        
        for alias in aliases:
            if alias.name == 'Autorizados':
                result['autorizados'] = True
                print(f"  ✅ Alias 'Autorizados' encontrado (ID: {alias.id})")
            elif alias.name == 'Bloqueados':
                result['bloqueados'] = True
                print(f"  ✅ Alias 'Bloqueados' encontrado (ID: {alias.id})")
        
        if not result['autorizados']:
            print(f"  ❌ Alias 'Autorizados' NÃO encontrado")
        if not result['bloqueados']:
            print(f"  ❌ Alias 'Bloqueados' NÃO encontrado")
        
        return result
    finally:
        db.close()


def test_aliases_in_pfsense(institution_id: int, user_id: int = None) -> dict:
    """Testa se os aliases existem no pfSense."""
    print(f"\n🌐 Testando aliases no pfSense (instituição {institution_id})...")
    
    try:
        result_aliases = listar_aliases_pfsense(user_id=user_id, institution_id=institution_id)
        aliases_data = result_aliases.get("data", []) if isinstance(result_aliases, dict) else result_aliases
        
        result = {
            'autorizados': False,
            'bloqueados': False,
            'total': len(aliases_data)
        }
        
        for alias in aliases_data:
            name = alias.get('name', '')
            if name == 'Autorizados':
                result['autorizados'] = True
                print(f"  ✅ Alias 'Autorizados' encontrado no pfSense")
            elif name == 'Bloqueados':
                result['bloqueados'] = True
                print(f"  ✅ Alias 'Bloqueados' encontrado no pfSense")
        
        if not result['autorizados']:
            print(f"  ❌ Alias 'Autorizados' NÃO encontrado no pfSense")
        if not result['bloqueados']:
            print(f"  ❌ Alias 'Bloqueados' NÃO encontrado no pfSense")
        
        return result
    except Exception as e:
        print(f"  ⚠️  Erro ao verificar aliases no pfSense: {e}")
        return {'autorizados': False, 'bloqueados': False, 'total': 0}


def test_rules_in_db(institution_id: int) -> dict:
    """Testa se as regras foram sincronizadas no banco de dados."""
    print(f"\n🛡️  Testando regras no banco de dados (instituição {institution_id})...")
    
    db = SessionLocal()
    try:
        rules = db.query(PfSenseFirewallRule).filter(
            PfSenseFirewallRule.institution_id == institution_id
        ).all()
        
        result = {
            'regra_block': False,
            'regra_pass': False,
            'total': len(rules)
        }
        
        for rule in rules:
            source = rule.source or ''
            rule_type = rule.type or ''
            descr = rule.descr or ''
            
            # Verificar se há regra BLOCK para Bloqueados
            if rule_type.lower() == 'block' and 'Bloqueados' in source:
                result['regra_block'] = True
                print(f"  ✅ Regra BLOCK encontrada (pf_id: {rule.pf_id}, descr: {descr[:50]})")
            
            # Verificar se há regra PASS para Autorizados
            if rule_type.lower() == 'pass' and 'Autorizados' in source:
                result['regra_pass'] = True
                print(f"  ✅ Regra PASS encontrada (pf_id: {rule.pf_id}, descr: {descr[:50]})")
        
        if not result['regra_block']:
            print(f"  ⚠️  Regra BLOCK para 'Bloqueados' não encontrada")
        if not result['regra_pass']:
            print(f"  ⚠️  Regra PASS para 'Autorizados' não encontrada")
        
        print(f"  📊 Total de regras sincronizadas: {result['total']}")
        
        return result
    finally:
        db.close()


def test_rules_in_pfsense(institution_id: int, user_id: int = None) -> dict:
    """Testa se as regras existem no pfSense."""
    print(f"\n🌐 Testando regras no pfSense (instituição {institution_id})...")
    
    try:
        result_rules = listar_regras_firewall_pfsense(user_id=user_id, institution_id=institution_id)
        rules_data = result_rules.get("data", []) if isinstance(result_rules, dict) else result_rules
        
        result = {
            'regra_block': False,
            'regra_pass': False,
            'total': len(rules_data)
        }
        
        for rule in rules_data:
            source = rule.get('source', '')
            rule_type = rule.get('type', '').lower()
            descr = rule.get('descr', '')
            
            # Verificar regra BLOCK
            if rule_type == 'block' and ('Bloqueados' in str(source) or 'bloqueados' in descr.lower()):
                result['regra_block'] = True
                print(f"  ✅ Regra BLOCK encontrada no pfSense (descr: {descr[:50]})")
            
            # Verificar regra PASS
            if rule_type == 'pass' and ('Autorizados' in str(source) or 'autorizados' in descr.lower()):
                result['regra_pass'] = True
                print(f"  ✅ Regra PASS encontrada no pfSense (descr: {descr[:50]})")
        
        if not result['regra_block']:
            print(f"  ⚠️  Regra BLOCK para 'Bloqueados' não encontrada no pfSense")
        if not result['regra_pass']:
            print(f"  ⚠️  Regra PASS para 'Autorizados' não encontrada no pfSense")
        
        print(f"  📊 Total de regras no pfSense: {result['total']}")
        
        return result
    except Exception as e:
        print(f"  ⚠️  Erro ao verificar regras no pfSense: {e}")
        return {'regra_block': False, 'regra_pass': False, 'total': 0}


def test_institution_setup(institution_id: int):
    """Testa a configuração completa de uma instituição."""
    print(f"\n{'='*60}")
    print(f"🧪 Testando configuração da instituição ID: {institution_id}")
    print(f"{'='*60}")
    
    db = SessionLocal()
    try:
        institution = db.query(Institution).filter(Institution.id == institution_id).first()
        if not institution:
            print(f"❌ Instituição {institution_id} não encontrada")
            return False
        
        print(f"📋 Instituição: {institution.nome} - {institution.cidade}")
        
        # Buscar usuário ADMIN
        admin_user = db.query(User).filter(
            User.institution_id == institution_id,
            User.permission == 'ADMIN'
        ).first()
        
        user_id = admin_user.id if admin_user else None
        if not user_id:
            print(f"⚠️  Nenhum usuário ADMIN encontrado para esta instituição")
    finally:
        db.close()
    
    # Testar aliases no banco
    aliases_db = test_aliases_in_db(institution_id)
    
    # Testar aliases no pfSense
    aliases_pfsense = test_aliases_in_pfsense(institution_id, user_id)
    
    # Testar regras no banco
    rules_db = test_rules_in_db(institution_id)
    
    # Testar regras no pfSense
    rules_pfsense = test_rules_in_pfsense(institution_id, user_id)
    
    # Resumo
    print(f"\n{'='*60}")
    print(f"📊 RESUMO DOS TESTES")
    print(f"{'='*60}")
    
    print(f"\n✅ Aliases no Banco de Dados:")
    print(f"   - Autorizados: {'✅' if aliases_db['autorizados'] else '❌'}")
    print(f"   - Bloqueados: {'✅' if aliases_db['bloqueados'] else '❌'}")
    
    print(f"\n✅ Aliases no pfSense:")
    print(f"   - Autorizados: {'✅' if aliases_pfsense['autorizados'] else '❌'}")
    print(f"   - Bloqueados: {'✅' if aliases_pfsense['bloqueados'] else '❌'}")
    
    print(f"\n✅ Regras no Banco de Dados:")
    print(f"   - BLOCK: {'✅' if rules_db['regra_block'] else '⚠️'}")
    print(f"   - PASS: {'✅' if rules_db['regra_pass'] else '⚠️'}")
    
    print(f"\n✅ Regras no pfSense:")
    print(f"   - BLOCK: {'✅' if rules_pfsense['regra_block'] else '⚠️'}")
    print(f"   - PASS: {'✅' if rules_pfsense['regra_pass'] else '⚠️'}")
    
    # Verificar se tudo está OK
    all_ok = (
        aliases_db['autorizados'] and aliases_db['bloqueados'] and
        aliases_pfsense['autorizados'] and aliases_pfsense['bloqueados'] and
        (rules_db['regra_block'] or rules_pfsense['regra_block']) and
        (rules_db['regra_pass'] or rules_pfsense['regra_pass'])
    )
    
    if all_ok:
        print(f"\n🎉 TUDO FUNCIONANDO CORRETAMENTE!")
        return True
    else:
        print(f"\n⚠️  Alguns itens precisam de atenção. Verifique os resultados acima.")
        return False


def main():
    """Função principal."""
    parser = argparse.ArgumentParser(
        description='Testa se setup_initial_aliases_and_rules.py funcionou corretamente'
    )
    parser.add_argument(
        '--institution-id',
        type=int,
        help='ID da instituição (se não fornecido, testa todas)'
    )
    
    args = parser.parse_args()
    
    print("🧪 Iniciando testes de configuração inicial")
    print("="*60)
    
    db = SessionLocal()
    try:
        if args.institution_id:
            institutions = [db.query(Institution).filter(Institution.id == args.institution_id).first()]
            if not institutions[0]:
                print(f"❌ Instituição {args.institution_id} não encontrada")
                sys.exit(1)
        else:
            institutions = db.query(Institution).filter(Institution.is_active == True).all()
            if not institutions:
                print("⚠️  Nenhuma instituição ativa encontrada")
                sys.exit(0)
    finally:
        db.close()
    
    print(f"📊 Total de instituições a testar: {len(institutions)}")
    
    success_count = 0
    for institution in institutions:
        if test_institution_setup(institution.id):
            success_count += 1
    
    print(f"\n{'='*60}")
    print(f"✅ Testes concluídos: {success_count}/{len(institutions)} instituições OK")
    print(f"{'='*60}")
    
    if success_count < len(institutions):
        sys.exit(1)


if __name__ == "__main__":
    main()

