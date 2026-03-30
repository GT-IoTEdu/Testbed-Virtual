#!/usr/bin/env python3
"""
Script para analisar a estrutura da tabela users
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.session import engine
from sqlalchemy import text

def analyze_users_table():
    print("🔍 Analisando estrutura da tabela users...")
    print("=" * 50)
    
    try:
        with engine.connect() as conn:
            # Descrever estrutura da tabela
            result = conn.execute(text("DESCRIBE users"))
            print("📋 Estrutura da tabela users:")
            for row in result:
                print(f"  {row[0]}: {row[1]}")
            
            print("\n" + "=" * 50)
            
            # Verificar dados existentes
            result = conn.execute(text("SELECT COUNT(*) as total FROM users"))
            total_users = result.fetchone()[0]
            print(f"👥 Total de usuários: {total_users}")
            
            # Verificar distribuição de permissões
            result = conn.execute(text("SELECT permission, COUNT(*) as count FROM users GROUP BY permission"))
            print("\n📊 Distribuição de permissões:")
            for row in result:
                print(f"  {row[0]}: {row[1]} usuários")
            
            # Verificar se existe coluna de ativação
            result = conn.execute(text("SHOW COLUMNS FROM users LIKE '%active%'"))
            active_column = result.fetchone()
            if active_column:
                print(f"\n✅ Coluna de ativação encontrada: {active_column[0]}")
            else:
                print("\n❌ Coluna de ativação NÃO encontrada")
            
            # Verificar se existe coluna de ativação com outros nomes
            result = conn.execute(text("SHOW COLUMNS FROM users LIKE '%status%'"))
            status_column = result.fetchone()
            if status_column:
                print(f"✅ Coluna de status encontrada: {status_column[0]}")
            else:
                print("❌ Coluna de status NÃO encontrada")
                
            # Verificar se existe coluna de ativação com outros nomes
            result = conn.execute(text("SHOW COLUMNS FROM users LIKE '%enabled%'"))
            enabled_column = result.fetchone()
            if enabled_column:
                print(f"✅ Coluna de enabled encontrada: {enabled_column[0]}")
            else:
                print("❌ Coluna de enabled NÃO encontrada")
                
    except Exception as e:
        print(f"❌ Erro ao analisar tabela: {e}")

if __name__ == "__main__":
    analyze_users_table()
