#!/usr/bin/env python3
"""
Script para corrigir a estrutura do ENUM no MySQL.
"""
from sqlalchemy import create_engine, text
import config

def fix_enum_structure():
    """Corrige a estrutura do ENUM para aceitar valores em maiúsculas."""
    
    try:
        # Criar engine do banco de dados
        engine = create_engine(f"mysql://{config.MYSQL_USER}:{config.MYSQL_PASSWORD}@{config.MYSQL_HOST}/{config.MYSQL_DB}")
        
        with engine.connect() as connection:
            # Verificar estrutura atual
            print("🔍 Verificando estrutura atual da tabela...")
            result = connection.execute(text("SHOW COLUMNS FROM users WHERE Field = 'permission'"))
            column_info = result.fetchone()
            print(f"Estrutura atual: {column_info}")
            
            # Modificar o ENUM para aceitar valores em maiúsculas
            print("\n🔧 Modificando estrutura do ENUM...")
            connection.execute(text("""
                ALTER TABLE users 
                MODIFY COLUMN permission ENUM('USER', 'MANAGER') NOT NULL DEFAULT 'USER'
            """))
            print("✅ Estrutura do ENUM modificada para aceitar USER/MANAGER")
            
            # Agora atualizar os valores
            print("\n🔧 Atualizando valores...")
            
            # Atualizar 'user' para 'USER'
            result1 = connection.execute(text("UPDATE users SET permission = 'USER' WHERE permission = 'user'"))
            print(f"✅ {result1.rowcount} usuário(s) atualizado(s) para 'USER'")
            
            # Atualizar 'manager' para 'MANAGER'
            result2 = connection.execute(text("UPDATE users SET permission = 'MANAGER' WHERE permission = 'manager'"))
            print(f"✅ {result2.rowcount} usuário(s) atualizado(s) para 'MANAGER'")
            
            # Commit das alterações
            connection.commit()
            
            # Verificar os valores finais
            print("\n📋 Usuários após correção completa:")
            result = connection.execute(text("SELECT id, email, permission FROM users"))
            users = result.fetchall()
            
            for user in users:
                print(f"   - ID: {user[0]}, Email: {user[1]}, Permission: '{user[2]}'")
            
            # Verificar nova estrutura
            print("\n🔍 Nova estrutura da coluna permission:")
            result = connection.execute(text("SHOW COLUMNS FROM users WHERE Field = 'permission'"))
            column_info = result.fetchone()
            print(f"Nova estrutura: {column_info}")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        raise

if __name__ == "__main__":
    print("🚀 Corrigindo estrutura do ENUM e valores...")
    print("=" * 60)
    fix_enum_structure()
    print("\n✅ Correção completa finalizada!")
