#!/usr/bin/env python3
"""
Script para criar a tabela blocking_feedback_history no banco de dados.
"""
import sys
import os

# Adicionar o diretório raiz do projeto ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from db.models import Base, BlockingFeedbackHistory
from db.session import DATABASE_URL
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_feedback_table():
    """Cria a tabela blocking_feedback_history no banco de dados."""
    try:
        # Criar engine
        engine = create_engine(DATABASE_URL)
        
        logger.info("Conectando ao banco de dados...")
        
        # Verificar se a tabela já existe
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT TABLE_NAME FROM information_schema.TABLES 
                WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'blocking_feedback_history'
            """))
            
            if result.fetchone():
                logger.warning("Tabela 'blocking_feedback_history' já existe!")
                return False
        
        # Criar a tabela
        logger.info("Criando tabela 'blocking_feedback_history'...")
        BlockingFeedbackHistory.__table__.create(engine, checkfirst=True)
        
        logger.info("✅ Tabela 'blocking_feedback_history' criada com sucesso!")
        
        # Verificar se a tabela foi criada corretamente
        with engine.connect() as conn:
            result = conn.execute(text("""
                SHOW CREATE TABLE blocking_feedback_history
            """))
            
            schema = result.fetchone()
            if schema:
                logger.info("📋 Schema da tabela criada:")
                logger.info(schema[1])
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro ao criar tabela: {e}")
        return False

def verify_table_structure():
    """Verifica a estrutura da tabela criada."""
    try:
        engine = create_engine(DATABASE_URL)
        
        with engine.connect() as conn:
            # Verificar colunas da tabela
            result = conn.execute(text("DESCRIBE blocking_feedback_history"))
            columns = result.fetchall()
            
            logger.info("📊 Estrutura da tabela 'blocking_feedback_history':")
            for column in columns:
                logger.info(f"  - {column[0]} ({column[1]}) {'NOT NULL' if column[2] == 'NO' else 'NULL'}")
            
            # Verificar índices
            result = conn.execute(text("SHOW INDEX FROM blocking_feedback_history"))
            indexes = result.fetchall()
            
            if indexes:
                logger.info("🔍 Índices criados:")
                unique_indexes = {}
                for index in indexes:
                    idx_name = index[2]
                    if idx_name not in unique_indexes:
                        unique_indexes[idx_name] = index[1] == 0  # Non_unique = 0 means unique
                        logger.info(f"  - {idx_name} ({'UNIQUE' if unique_indexes[idx_name] else 'NON-UNIQUE'})")
            
            # Verificar foreign keys
            result = conn.execute(text("""
                SELECT 
                    CONSTRAINT_NAME, 
                    COLUMN_NAME, 
                    REFERENCED_TABLE_NAME, 
                    REFERENCED_COLUMN_NAME
                FROM information_schema.KEY_COLUMN_USAGE 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = 'blocking_feedback_history' 
                AND REFERENCED_TABLE_NAME IS NOT NULL
            """))
            foreign_keys = result.fetchall()
            
            if foreign_keys:
                logger.info("🔗 Foreign Keys:")
                for fk in foreign_keys:
                    logger.info(f"  - {fk[1]} -> {fk[2]}.{fk[3]}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro ao verificar estrutura da tabela: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Script de criação da tabela blocking_feedback_history")
    print("=" * 60)
    
    # Criar tabela
    if create_feedback_table():
        print("\n🔍 Verificando estrutura da tabela...")
        verify_table_structure()
        
        print("\n✅ Processo concluído com sucesso!")
        print("\n📝 Próximos passos:")
        print("   1. A tabela foi criada no banco de dados")
        print("   2. Os endpoints da API estão disponíveis em /api/feedback/")
        print("   3. Consulte a documentação em /docs para ver todos os endpoints")
        print("   4. Use o frontend para implementar a interface de feedback")
        
    else:
        print("\n❌ Falha na criação da tabela!")
        sys.exit(1)
