#!/usr/bin/env python3
"""
Script para verificar usuários no banco de dados.
"""
from sqlalchemy import create_engine, text
import config

def check_users():
    """Verifica usuários no banco de dados."""
    
    try:
        # Criar engine do banco de dados
        engine = create_engine(f"mysql://{config.MYSQL_USER}:{config.MYSQL_PASSWORD}@{config.MYSQL_HOST}/{config.MYSQL_DB}")
        
        with engine.connect() as connection:
            # Verificar usuários
            result = connection.execute(text("SELECT id, email, permission FROM users"))
            users = result.fetchall()
            
            print("📋 Usuários no banco de dados:")
            for user in users:
                print(f"   - ID: {user[0]}, Email: {user[1]}, Permission: '{user[2]}'")
            
            # Verificar estrutura da tabela
            result = connection.execute(text("SHOW COLUMNS FROM users"))
            columns = result.fetchall()
            
            print("\n📋 Estrutura da tabela users:")
            for column in columns:
                print(f"   - {column[0]}: {column[1]}")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        raise

if __name__ == "__main__":
    check_users()
