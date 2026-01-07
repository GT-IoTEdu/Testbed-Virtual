#!/usr/bin/env python3
"""
Script de migração para adicionar a coluna 'permission' à tabela 'users'.
"""
from sqlalchemy import create_engine, text
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
import config

def migrate_add_permission():
    """Adiciona a coluna permission à tabela users."""
    
    try:
        # Criar engine do banco de dados
        engine = create_engine(f"mysql://{config.MYSQL_USER}:{config.MYSQL_PASSWORD}@{config.MYSQL_HOST}/{config.MYSQL_DB}")
        
        with engine.connect() as connection:
            # Verificar se a coluna já existe
            result = connection.execute(text("""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = :db_name 
                AND TABLE_NAME = 'users' 
                AND COLUMN_NAME = 'permission'
            """), {"db_name": config.MYSQL_DB})
            
            if result.fetchone():
                print("ℹ️ Coluna 'permission' já existe na tabela 'users'")
            else:
                # Adicionar a coluna permission
                connection.execute(text("""
                    ALTER TABLE users 
                    ADD COLUMN permission ENUM('user', 'manager') NOT NULL DEFAULT 'user'
                """))
                print("✅ Coluna 'permission' adicionada à tabela 'users'")
            
            # Atualizar usuários existentes para ter permissão 'user' por padrão
            result = connection.execute(text("""
                UPDATE users 
                SET permission = 'user' 
                WHERE permission IS NULL OR permission = ''
            """))
            
            affected_rows = result.rowcount
            if affected_rows > 0:
                print(f"✅ {affected_rows} usuário(s) atualizado(s) com permissão padrão 'user'")
            
            # Commit das alterações
            connection.commit()
            
            # Verificar a estrutura da tabela
            result = connection.execute(text("DESCRIBE users"))
            columns = result.fetchall()
            
            print("\n📋 Estrutura atual da tabela 'users':")
            for column in columns:
                print(f"   - {column[0]}: {column[1]} {column[2] if column[2] else ''}")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        raise

if __name__ == "__main__":
    print("🚀 Executando migração para adicionar coluna 'permission'...")
    print("=" * 60)
    migrate_add_permission()
    print("\n✅ Migração concluída!")
