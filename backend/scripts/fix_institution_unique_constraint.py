#!/usr/bin/env python3
"""
Script para corrigir constraint única do campo nome na tabela institutions.
Permite múltiplas instituições com o mesmo nome em cidades diferentes.

Uso:
    cd backend && python scripts/fix_institution_unique_constraint.py
"""

import sys
import os
from pathlib import Path

# Adicionar o diretório backend ao path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from db.session import SessionLocal
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migration():
    """Executa a migração para corrigir constraint única do campo nome."""
    db = SessionLocal()
    try:
        logger.info("🔄 Iniciando migração: corrigir constraint única do campo nome em institutions...")
        
        # Remover índice único antigo do campo nome
        logger.info("📝 Removendo índice único antigo do campo nome...")
        try:
            db.execute(text("ALTER TABLE `institutions` DROP INDEX IF EXISTS `ix_institutions_nome`"))
            db.commit()
            logger.info("✅ Índice 'ix_institutions_nome' removido (se existia)")
        except Exception as e:
            logger.warning(f"⚠️ Erro ao remover índice 'ix_institutions_nome': {e}")
            db.rollback()
        
        # Remover constraint única se existir (pode ter nomes diferentes)
        logger.info("📝 Removendo constraint única do campo nome...")
        try:
            db.execute(text("ALTER TABLE `institutions` DROP INDEX IF EXISTS `nome`"))
            db.commit()
            logger.info("✅ Índice 'nome' removido (se existia)")
        except Exception as e:
            logger.warning(f"⚠️ Erro ao remover índice 'nome': {e}")
            db.rollback()
        
        # Criar índice único composto (nome, cidade)
        logger.info("📝 Criando índice único composto (nome, cidade)...")
        try:
            db.execute(text("""
                ALTER TABLE `institutions` 
                ADD UNIQUE INDEX `idx_institution_nome_cidade_unique` (`nome`, `cidade`)
            """))
            db.commit()
            logger.info("✅ Índice único composto criado com sucesso")
        except Exception as e:
            logger.error(f"❌ Erro ao criar índice único composto: {e}")
            db.rollback()
            raise
        
        # Adicionar índice simples no campo nome para melhorar performance
        logger.info("📝 Adicionando índice simples no campo nome...")
        try:
            db.execute(text("""
                ALTER TABLE `institutions` 
                ADD INDEX `idx_institution_nome` (`nome`)
            """))
            db.commit()
            logger.info("✅ Índice simples no campo nome criado com sucesso")
        except Exception as e:
            logger.warning(f"⚠️ Erro ao criar índice simples (pode já existir): {e}")
            db.rollback()
        
        logger.info("✅ Migração concluída com sucesso!")
        logger.info("📋 Agora é possível criar múltiplas instituições com o mesmo nome em cidades diferentes")
        
    except Exception as e:
        logger.error(f"❌ Erro durante a migração: {e}", exc_info=True)
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    try:
        run_migration()
    except Exception as e:
        logger.error(f"❌ Falha na migração: {e}")
        sys.exit(1)

