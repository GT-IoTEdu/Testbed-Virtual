#!/usr/bin/env python3
"""
Script de verificação rápida da instalação.

Verifica se todos os componentes estão configurados corretamente.

Uso:
    python scripts/verify_installation.py
"""

import sys
import os
from pathlib import Path

# Adicionar o diretório backend ao path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from db.session import SessionLocal
from db.models import Institution, User, PfSenseAlias, PfSenseFirewallRule
import config

def check_database():
    """Verifica se o banco de dados está acessível."""
    print("\n📊 Verificando banco de dados...")
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        print("  ✅ Conexão com banco de dados OK")
        return True
    except Exception as e:
        print(f"  ❌ Erro ao conectar no banco: {e}")
        return False


def check_tables():
    """Verifica se as tabelas principais existem."""
    print("\n📋 Verificando tabelas...")
    required_tables = [
        'users', 'institutions', 'dhcp_static_mappings',
        'pfsense_aliases', 'pfsense_firewall_rules'
    ]
    
    db = SessionLocal()
    try:
        for table in required_tables:
            result = db.execute(f"SHOW TABLES LIKE '{table}'")
            if result.fetchone():
                print(f"  ✅ Tabela '{table}' existe")
            else:
                print(f"  ❌ Tabela '{table}' NÃO encontrada")
                return False
        return True
    finally:
        db.close()


def check_institutions():
    """Verifica se há instituições cadastradas."""
    print("\n🏛️  Verificando instituições...")
    db = SessionLocal()
    try:
        institutions = db.query(Institution).filter(Institution.is_active == True).all()
        if institutions:
            print(f"  ✅ {len(institutions)} instituição(ões) encontrada(s):")
            for inst in institutions:
                print(f"     - {inst.nome} ({inst.cidade}) - ID: {inst.id}")
                # Verificar configurações do pfSense
                if inst.pfsense_base_url and inst.pfsense_key:
                    print(f"       ✅ pfSense configurado")
                else:
                    print(f"       ⚠️  pfSense não configurado")
            return True
        else:
            print("  ⚠️  Nenhuma instituição encontrada")
            return False
    finally:
        db.close()


def check_users():
    """Verifica se há usuários cadastrados."""
    print("\n👤 Verificando usuários...")
    db = SessionLocal()
    try:
        users = db.query(User).all()
        if users:
            print(f"  ✅ {len(users)} usuário(s) encontrado(s):")
            admins = [u for u in users if u.permission == 'ADMIN']
            superusers = [u for u in users if u.permission == 'SUPERUSER']
            regular = [u for u in users if u.permission == 'USER']
            
            if admins:
                print(f"     - {len(admins)} ADMIN(s)")
            if superusers:
                print(f"     - {len(superusers)} SUPERUSER(s)")
            if regular:
                print(f"     - {len(regular)} USER(s)")
            
            # Verificar se há ADMIN com institution_id
            admins_with_inst = [u for u in admins if u.institution_id]
            if admins_with_inst:
                print(f"     ✅ {len(admins_with_inst)} ADMIN(s) com instituição associada")
            else:
                print(f"     ⚠️  Nenhum ADMIN com instituição associada")
            
            return True
        else:
            print("  ⚠️  Nenhum usuário encontrado")
            return False
    finally:
        db.close()


def check_aliases():
    """Verifica se os aliases iniciais foram criados."""
    print("\n📦 Verificando aliases iniciais...")
    db = SessionLocal()
    try:
        aliases = db.query(PfSenseAlias).filter(
            PfSenseAlias.name.in_(['Autorizados', 'Bloqueados'])
        ).all()
        
        if aliases:
            print(f"  ✅ {len(aliases)} alias(es) encontrado(s):")
            for alias in aliases:
                inst_name = "Sem instituição"
                if alias.institution_id:
                    inst = db.query(Institution).filter(Institution.id == alias.institution_id).first()
                    if inst:
                        inst_name = f"{inst.nome} ({inst.cidade})"
                print(f"     - {alias.name} - Instituição: {inst_name}")
            return True
        else:
            print("  ⚠️  Nenhum alias inicial encontrado")
            print("     Execute: python scripts/setup_initial_aliases_and_rules.py")
            return False
    finally:
        db.close()


def check_rules():
    """Verifica se as regras foram sincronizadas."""
    print("\n🛡️  Verificando regras de firewall...")
    db = SessionLocal()
    try:
        rules = db.query(PfSenseFirewallRule).all()
        if rules:
            print(f"  ✅ {len(rules)} regra(s) encontrada(s) no banco")
            
            # Verificar regras por instituição
            institutions = db.query(Institution).all()
            for inst in institutions:
                inst_rules = [r for r in rules if r.institution_id == inst.id]
                if inst_rules:
                    block_rules = [r for r in inst_rules if r.type == 'block']
                    pass_rules = [r for r in inst_rules if r.type == 'pass']
                    print(f"     - {inst.nome}: {len(inst_rules)} regras ({len(block_rules)} BLOCK, {len(pass_rules)} PASS)")
            return True
        else:
            print("  ⚠️  Nenhuma regra encontrada")
            print("     Execute: python scripts/setup_initial_aliases_and_rules.py")
            return False
    finally:
        db.close()


def check_config():
    """Verifica configurações do .env."""
    print("\n⚙️  Verificando configurações...")
    issues = []
    
    # Verificar variáveis críticas
    if not hasattr(config, 'MYSQL_USER') or not config.MYSQL_USER:
        issues.append("MYSQL_USER não configurado")
    else:
        print(f"  ✅ MYSQL_USER: {config.MYSQL_USER}")
    
    if not hasattr(config, 'MYSQL_DB') or not config.MYSQL_DB:
        issues.append("MYSQL_DB não configurado")
    else:
        print(f"  ✅ MYSQL_DB: {config.MYSQL_DB}")
    
    if issues:
        print(f"  ⚠️  Problemas encontrados:")
        for issue in issues:
            print(f"     - {issue}")
        return False
    
    return True


def main():
    """Função principal."""
    print("="*60)
    print("🔍 VERIFICAÇÃO DE INSTALAÇÃO")
    print("="*60)
    
    results = []
    
    # Executar verificações
    results.append(("Banco de Dados", check_database()))
    results.append(("Tabelas", check_tables()))
    results.append(("Configurações", check_config()))
    results.append(("Instituições", check_institutions()))
    results.append(("Usuários", check_users()))
    results.append(("Aliases", check_aliases()))
    results.append(("Regras", check_rules()))
    
    # Resumo
    print("\n" + "="*60)
    print("📊 RESUMO")
    print("="*60)
    
    all_ok = True
    for name, result in results:
        status = "✅" if result else "❌"
        print(f"{status} {name}")
        if not result:
            all_ok = False
    
    print("="*60)
    
    if all_ok:
        print("🎉 TODAS AS VERIFICAÇÕES PASSARAM!")
        print("\n✅ Sistema pronto para uso!")
        print("\nPróximos passos:")
        print("  1. Iniciar servidor: python start_server.py")
        print("  2. Testar endpoints: python scripts/test_setup_initial_aliases_and_rules.py")
        return 0
    else:
        print("⚠️  ALGUMAS VERIFICAÇÕES FALHARAM")
        print("\nConsulte o guia de instalação:")
        print("  backend/docs/GUIA_INSTALACAO_COMPLETA.md")
        return 1


if __name__ == "__main__":
    sys.exit(main())

