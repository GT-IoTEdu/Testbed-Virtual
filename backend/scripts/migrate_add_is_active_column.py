#!/usr/bin/env python3
"""
Migração: Adicionar coluna is_active à tabela users
Permite ativar/desativar usuários do sistema
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.session import engine
from sqlalchemy import text
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

def migrate_add_is_active_column():
    logger.info("🚀 Iniciando migração: Adicionar coluna is_active")
    logger.info("")
    logger.info("=" * 60)
    logger.info("PASSO 1: Verificar se coluna já existe")
    logger.info("=" * 60)
    
    try:
        with engine.connect() as conn:
            # Verificar se coluna já existe
            result = conn.execute(text("SHOW COLUMNS FROM users LIKE 'is_active'"))
            existing_column = result.fetchone()
            
            if existing_column:
                logger.info("✅ Coluna 'is_active' já existe!")
                logger.info(f"📋 Detalhes: {existing_column[0]} - {existing_column[1]}")
                return True
            
            logger.info("❌ Coluna 'is_active' não encontrada. Criando...")
            
            logger.info("")
            logger.info("=" * 60)
            logger.info("PASSO 2: Adicionar coluna is_active")
            logger.info("=" * 60)
            
            # Adicionar coluna is_active
            conn.execute(text("""
                ALTER TABLE users 
                ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT TRUE 
                COMMENT 'Indica se o usuário está ativo no sistema'
            """))
            
            logger.info("✅ Coluna 'is_active' adicionada com sucesso!")
            
            logger.info("")
            logger.info("=" * 60)
            logger.info("PASSO 3: Atualizar usuários existentes")
            logger.info("=" * 60)
            
            # Ativar todos os usuários existentes
            result = conn.execute(text("UPDATE users SET is_active = TRUE WHERE is_active IS NULL"))
            logger.info(f"✅ {result.rowcount} usuários existentes ativados")
            
            logger.info("")
            logger.info("=" * 60)
            logger.info("PASSO 4: Verificar estrutura final")
            logger.info("=" * 60)
            
            # Verificar estrutura final
            result = conn.execute(text("DESCRIBE users"))
            logger.info("📋 Estrutura final da tabela users:")
            for row in result:
                logger.info(f"  {row[0]}: {row[1]}")
            
            logger.info("")
            logger.info("=" * 60)
            logger.info("PASSO 5: Estatísticas finais")
            logger.info("=" * 60)
            
            # Estatísticas
            result = conn.execute(text("SELECT COUNT(*) as total FROM users"))
            total_users = result.fetchone()[0]
            logger.info(f"👥 Total de usuários: {total_users}")
            
            result = conn.execute(text("SELECT COUNT(*) as active FROM users WHERE is_active = TRUE"))
            active_users = result.fetchone()[0]
            logger.info(f"✅ Usuários ativos: {active_users}")
            
            result = conn.execute(text("SELECT COUNT(*) as inactive FROM users WHERE is_active = FALSE"))
            inactive_users = result.fetchone()[0]
            logger.info(f"❌ Usuários inativos: {inactive_users}")
            
            logger.info("")
            logger.info("=" * 60)
            logger.info("✅ MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
            logger.info("=" * 60)
            logger.info("📋 Resumo da migração:")
            logger.info("  ✅ Coluna 'is_active' adicionada")
            logger.info("  ✅ Todos os usuários existentes ativados")
            logger.info("  ✅ Sistema pronto para gerenciar status de usuários")
            logger.info("")
            logger.info("🔧 Próximos passos:")
            logger.info("  1. Atualizar modelo User")
            logger.info("  2. Implementar endpoints para ativar/desativar")
            logger.info("  3. Atualizar frontend para mostrar status")
            logger.info("  4. Testar funcionalidades")
            
            return True
            
    except Exception as e:
        logger.error(f"❌ Erro durante migração: {e}")
        return False

if __name__ == "__main__":
    success = migrate_add_is_active_column()
    if success:
        print("\n🎉 Migração executada com sucesso!")
    else:
        print("\n💥 Falha na migração!")
        sys.exit(1)
