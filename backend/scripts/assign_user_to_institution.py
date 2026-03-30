#!/usr/bin/env python3
"""
Script para associar manualmente um usuário a uma instituição.

Uso:
    python scripts/assign_user_to_institution.py <email> <institution_id>
    
Exemplos:
    python scripts/assign_user_to_institution.py vt02joner@gmail.com 1
"""

import sys
import os
from pathlib import Path

# Adicionar o diretório backend ao path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from db.session import SessionLocal
from db.models import User, Institution
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def assign_user_to_institution(user_email: str, institution_id: int):
    """Associa um usuário a uma instituição."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == user_email).first()
        if not user:
            logger.error(f"❌ Usuário {user_email} não encontrado")
            return False
        
        institution = db.query(Institution).filter(Institution.id == institution_id).first()
        if not institution:
            logger.error(f"❌ Instituição ID {institution_id} não encontrada")
            return False
        
        logger.info(f"\n{'='*60}")
        logger.info(f"👤 ASSOCIANDO USUÁRIO A INSTITUIÇÃO")
        logger.info(f"{'='*60}")
        logger.info(f"\n📋 Usuário:")
        logger.info(f"   ID: {user.id}")
        logger.info(f"   Email: {user.email}")
        logger.info(f"   Nome: {user.nome}")
        logger.info(f"   Instituição atual: {user.instituicao}")
        logger.info(f"   institution_id atual: {user.institution_id}")
        
        logger.info(f"\n🏛️  Instituição:")
        logger.info(f"   ID: {institution.id}")
        logger.info(f"   Nome: {institution.nome}")
        logger.info(f"   Cidade: {institution.cidade}")
        
        if user.institution_id == institution_id:
            logger.info(f"\n✅ Usuário já está associado a esta instituição")
            return True
        
        # Associar
        old_institution_id = user.institution_id
        user.institution_id = institution_id
        if not user.instituicao:
            user.instituicao = institution.nome
        
        db.commit()
        db.refresh(user)
        
        logger.info(f"\n✅ Usuário associado com sucesso!")
        logger.info(f"   institution_id alterado: {old_institution_id} → {institution_id}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro ao associar usuário: {e}")
        db.rollback()
        return False
    finally:
        db.close()


def list_institutions():
    """Lista todas as instituições."""
    db = SessionLocal()
    try:
        institutions = db.query(Institution).filter(Institution.is_active == True).all()
        logger.info(f"\n📊 Instituições disponíveis:")
        for inst in institutions:
            logger.info(f"   ID: {inst.id} - {inst.nome} ({inst.cidade})")
        return institutions
    finally:
        db.close()


def main():
    if len(sys.argv) < 3:
        print("Uso: python scripts/assign_user_to_institution.py <email> <institution_id>")
        print("\nExemplo:")
        print("  python scripts/assign_user_to_institution.py vt02joner@gmail.com 1")
        print("\nPara listar instituições disponíveis:")
        print("  python scripts/assign_user_to_institution.py --list")
        sys.exit(1)
    
    if sys.argv[1] == "--list":
        list_institutions()
        sys.exit(0)
    
    user_email = sys.argv[1]
    try:
        institution_id = int(sys.argv[2])
    except ValueError:
        logger.error(f"❌ institution_id deve ser um número. Recebido: {sys.argv[2]}")
        sys.exit(1)
    
    # Listar instituições antes de associar
    list_institutions()
    
    # Associar
    success = assign_user_to_institution(user_email, institution_id)
    
    if success:
        logger.info(f"\n🎉 Operação concluída com sucesso!")
        sys.exit(0)
    else:
        logger.error(f"\n❌ Falha na operação")
        sys.exit(1)


if __name__ == "__main__":
    main()

