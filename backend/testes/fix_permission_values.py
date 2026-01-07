#!/usr/bin/env python3
"""
Script para corrigir os valores de permissão no banco de dados.
"""
from sqlalchemy import create_engine, text
import config

def fix_permission_values():
    """Corrige os valores de permissão para maiúsculas."""
    
    try:
        # Criar engine do banco de dados
        engine = create_engine(f"mysql://{config.MYSQL_USER}:{config.MYSQL_PASSWORD}@{config.MYSQL_HOST}/{config.MYSQL_DB}")
        
        with engine.connect() as connection:
            # Atualizar valores de permissão para maiúsculas
            result1 = connection.execute(text("UPDATE users SET permission = 'USER' WHERE permission = 'user'"))
            result2 = connection.execute(text("UPDATE users SET permission = 'MANAGER' WHERE permission = 'manager'"))
            
            print(f"✅ {result1.rowcount} usuário(s) atualizado(s) para 'USER'")
            print(f"✅ {result2.rowcount} usuário(s) atualizado(s) para 'MANAGER'")
            
            # Commit das alterações
            connection.commit()
            
            # Verificar os valores atuais
            result = connection.execute(text("SELECT id, email, permission FROM users"))
            users = result.fetchall()
            
            print("\n📋 Usuários no banco de dados:")
            for user in users:
                print(f"   - ID: {user[0]}, Email: {user[1]}, Permissão: {user[2]}")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        raise

if __name__ == "__main__":
    print("🚀 Corrigindo valores de permissão...")
    print("=" * 50)
    fix_permission_values()
    print("\n✅ Correção concluída!")
