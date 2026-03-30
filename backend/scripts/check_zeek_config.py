"""
Script para verificar e configurar as configurações do Zeek de uma instituição.

Uso:
    python backend/scripts/check_zeek_config.py [user_id]
    
    Se user_id não for fornecido, lista todas as instituições e suas configurações do Zeek.
"""

import sys
import os

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.session import SessionLocal
from db.models import User, Institution
from services_firewalls.institution_config_service import InstitutionConfigService

def check_user_config(user_id: int):
    """Verifica as configurações do Zeek para um usuário específico."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            print(f"❌ Usuário com ID {user_id} não encontrado")
            return
        
        print(f"\n👤 Usuário: {user.email} (ID: {user.id})")
        print(f"   Nome: {user.nome}")
        print(f"   Instituição ID: {user.institution_id or 'NÃO ASSOCIADO'}")
        
        if user.institution_id:
            config = InstitutionConfigService.get_user_institution_config(user_id=user_id)
            if config:
                print(f"\n✅ Configurações encontradas:")
                print(f"   Instituição: {config.get('nome')} (ID: {config.get('institution_id')})")
                print(f"   Zeek URL: {config.get('zeek_base_url') or '❌ NÃO CONFIGURADO'}")
                print(f"   Zeek Key: {'✅ Configurado' if config.get('zeek_key') else '❌ NÃO CONFIGURADO'}")
            else:
                institution = db.query(Institution).filter(Institution.id == user.institution_id).first()
                if institution:
                    print(f"\n⚠️ Instituição encontrada mas sem configurações do Zeek:")
                    print(f"   Instituição: {institution.nome} (ID: {institution.id})")
                    print(f"   Zeek URL: {institution.zeek_base_url or '❌ NÃO CONFIGURADO'}")
                    print(f"   Zeek Key: {'✅ Configurado' if institution.zeek_key else '❌ NÃO CONFIGURADO'}")
                    print(f"\n💡 Para configurar, execute:")
                    print(f"   python backend/scripts/update_zeek_config.py {institution.id} \"http://192.168.59.2/zeek-api\" \"SEU_TOKEN\"")
        else:
            print(f"\n⚠️ Usuário não possui instituição associada")
            print(f"   Para usar o Zeek, o usuário precisa ter uma instituição associada")
    finally:
        db.close()

def list_all_institutions():
    """Lista todas as instituições e suas configurações do Zeek."""
    db = SessionLocal()
    try:
        institutions = db.query(Institution).filter(Institution.is_active == True).all()
        
        if not institutions:
            print("❌ Nenhuma instituição ativa encontrada")
            return
        
        print(f"\n📋 Instituições ativas ({len(institutions)}):\n")
        
        for inst in institutions:
            print(f"🏛️  {inst.nome} (ID: {inst.id})")
            print(f"   Cidade: {inst.cidade}")
            print(f"   Zeek URL: {inst.zeek_base_url or '❌ NÃO CONFIGURADO'}")
            print(f"   Zeek Key: {'✅ Configurado' if inst.zeek_key else '❌ NÃO CONFIGURADO'}")
            
            if not inst.zeek_base_url or not inst.zeek_key:
                print(f"   💡 Para configurar:")
                print(f"      python backend/scripts/update_zeek_config.py {inst.id} \"http://192.168.59.2/zeek-api\" \"SEU_TOKEN\"")
            print()
    finally:
        db.close()

def main():
    if len(sys.argv) > 1:
        try:
            user_id = int(sys.argv[1])
            check_user_config(user_id)
        except ValueError:
            print(f"❌ Erro: {sys.argv[1]} não é um ID de usuário válido")
            sys.exit(1)
    else:
        list_all_institutions()

if __name__ == "__main__":
    main()

