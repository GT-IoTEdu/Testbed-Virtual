"""
Script para diagnosticar problemas com configurações do Zeek.

Verifica:
1. Se os dados estão no banco
2. Se os valores estão vazios ou None
3. Compara com o .env
"""

import sys
import os

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.session import SessionLocal
from db.models import User, Institution
import config

def diagnose_zeek_config(user_id: int = None):
    """Diagnostica as configurações do Zeek."""
    db = SessionLocal()
    try:
        print("=" * 60)
        print("DIAGNÓSTICO DE CONFIGURAÇÕES DO ZEEK")
        print("=" * 60)
        
        # Verificar .env
        print("\n📄 CONFIGURAÇÕES DO .ENV:")
        print(f"   ZEEK_API_URL: {config.ZEEK_API_URL or '❌ NÃO DEFINIDO'}")
        print(f"   ZEEK_API_TOKEN: {'✅ Configurado' if config.ZEEK_API_TOKEN else '❌ NÃO DEFINIDO'}")
        if config.ZEEK_API_TOKEN:
            print(f"   ZEEK_API_TOKEN (primeiros 10 chars): {config.ZEEK_API_TOKEN[:10]}...")
        
        # Verificar usuário se fornecido
        if user_id:
            print(f"\n👤 USUÁRIO (ID: {user_id}):")
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                print(f"   Email: {user.email}")
                print(f"   Nome: {user.nome}")
                print(f"   Institution ID: {user.institution_id or '❌ NÃO ASSOCIADO'}")
                
                if user.institution_id:
                    institution = db.query(Institution).filter(Institution.id == user.institution_id).first()
                    if institution:
                        print(f"\n🏛️  INSTITUIÇÃO (ID: {user.institution_id}):")
                        print(f"   Nome: {institution.nome}")
                        print(f"   Cidade: {institution.cidade}")
                        print(f"   Is Active: {institution.is_active}")
                        
                        # Verificar valores brutos do banco
                        print(f"\n   📊 VALORES BRUTOS DO BANCO:")
                        print(f"   zeek_base_url (type: {type(institution.zeek_base_url).__name__}): {repr(institution.zeek_base_url)}")
                        print(f"   zeek_key (type: {type(institution.zeek_key).__name__}): {'***' if institution.zeek_key else 'None/Empty'}")
                        print(f"   zeek_key (length): {len(institution.zeek_key) if institution.zeek_key else 0}")
                        
                        # Verificar valores processados
                        zeek_base_url = institution.zeek_base_url.strip() if institution.zeek_base_url else ''
                        zeek_key = institution.zeek_key.strip() if institution.zeek_key else ''
                        
                        print(f"\n   📊 VALORES PROCESSADOS:")
                        print(f"   zeek_base_url: {repr(zeek_base_url)}")
                        print(f"   zeek_key: {'***' if zeek_key else 'None/Empty'}")
                        print(f"   zeek_key (length): {len(zeek_key) if zeek_key else 0}")
                        
                        # Comparar com .env
                        print(f"\n   🔍 COMPARAÇÃO COM .ENV:")
                        if zeek_base_url and config.ZEEK_API_URL:
                            print(f"   URLs são iguais: {zeek_base_url.rstrip('/') == config.ZEEK_API_URL.rstrip('/')}")
                        if zeek_key and config.ZEEK_API_TOKEN:
                            print(f"   Tokens são iguais: {zeek_key == config.ZEEK_API_TOKEN}")
                            if zeek_key != config.ZEEK_API_TOKEN:
                                print(f"   ⚠️ Tokens diferentes!")
                                print(f"      Banco (primeiros 20): {zeek_key[:20]}...")
                                print(f"      .env (primeiros 20): {config.ZEEK_API_TOKEN[:20]}...")
                    else:
                        print(f"   ❌ Instituição {user.institution_id} não encontrada")
                else:
                    print(f"   ⚠️ Usuário não tem instituição associada")
            else:
                print(f"   ❌ Usuário não encontrado")
        
        # Listar todas as instituições
        print(f"\n📋 TODAS AS INSTITUIÇÕES:")
        institutions = db.query(Institution).filter(Institution.is_active == True).all()
        for inst in institutions:
            print(f"\n   🏛️  {inst.nome} (ID: {inst.id})")
            print(f"      zeek_base_url: {repr(inst.zeek_base_url) if inst.zeek_base_url else 'None/Empty'}")
            print(f"      zeek_key: {'✅ Configurado' if inst.zeek_key else '❌ NÃO CONFIGURADO'}")
            if inst.zeek_key:
                print(f"      zeek_key (length): {len(inst.zeek_key)}")
                print(f"      zeek_key (primeiros 20): {inst.zeek_key[:20]}...")
        
        print("\n" + "=" * 60)
        
    finally:
        db.close()

if __name__ == "__main__":
    user_id = int(sys.argv[1]) if len(sys.argv) > 1 else None
    diagnose_zeek_config(user_id)

