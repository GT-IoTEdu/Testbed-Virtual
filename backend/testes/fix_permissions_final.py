#!/usr/bin/env python3
"""
Script para corrigir definitivamente os valores de permissão no banco de dados.
"""
from sqlalchemy import create_engine, text
import config

def fix_permissions_final():
    """Corrige os valores de permissão para maiúsculas."""
    
    try:
        # Criar engine do banco de dados
        engine = create_engine(f"mysql://{config.MYSQL_USER}:{config.MYSQL_PASSWORD}@{config.MYSQL_HOST}/{config.MYSQL_DB}")
        
        with engine.connect() as connection:
            # Primeiro, vamos ver o que está no banco
            print("🔍 Verificando valores atuais...")
            result = connection.execute(text("SELECT id, email, permission FROM users"))
            users = result.fetchall()
            
            print("📋 Usuários antes da correção:")
            for user in users:
                print(f"   - ID: {user[0]}, Email: {user[1]}, Permission: '{user[2]}'")
            
            # Atualizar valores de permissão para maiúsculas
            print("\n🔧 Corrigindo valores...")
            
            # Atualizar 'user' para 'USER'
            result1 = connection.execute(text("UPDATE users SET permission = 'USER' WHERE permission = 'user'"))
            print(f"✅ {result1.rowcount} usuário(s) atualizado(s) para 'USER'")
            
            # Atualizar 'manager' para 'MANAGER'
            result2 = connection.execute(text("UPDATE users SET permission = 'MANAGER' WHERE permission = 'manager'"))
            print(f"✅ {result2.rowcount} usuário(s) atualizado(s) para 'MANAGER'")
            
            # Commit das alterações
            connection.commit()
            
            # Verificar os valores após a correção
            print("\n📋 Usuários após a correção:")
            result = connection.execute(text("SELECT id, email, permission FROM users"))
            users = result.fetchall()
            
            for user in users:
                print(f"   - ID: {user[0]}, Email: {user[1]}, Permission: '{user[2]}'")
            
            # Verificar se ainda há valores em minúsculas
            result = connection.execute(text("SELECT COUNT(*) FROM users WHERE permission IN ('user', 'manager')"))
            lowercase_count = result.fetchone()[0]
            
            if lowercase_count == 0:
                print("\n🎉 Todos os valores foram corrigidos com sucesso!")
            else:
                print(f"\n⚠️ Ainda há {lowercase_count} usuário(s) com valores em minúsculas")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        raise

if __name__ == "__main__":
    print("🚀 Corrigindo valores de permissão definitivamente...")
    print("=" * 60)
    fix_permissions_final()
    print("\n✅ Correção finalizada!")
