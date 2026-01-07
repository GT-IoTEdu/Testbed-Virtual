#!/usr/bin/env python3
"""
Migração para adicionar colunas is_blocked e reason na tabela dhcp_static_mappings
"""

import sqlite3
import os
from datetime import datetime

def migrate_add_blocking_columns():
    """Adiciona colunas is_blocked e reason na tabela dhcp_static_mappings"""
    
    # Caminho para o banco de dados
    db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'db.sqlite3')
    
    if not os.path.exists(db_path):
        print(f"❌ Banco de dados não encontrado: {db_path}")
        return False
    
    print(f"🔧 Executando migração no banco: {db_path}")
    
    try:
        # Conectar ao banco
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar se as colunas já existem
        cursor.execute("PRAGMA table_info(dhcp_static_mappings)")
        columns = [column[1] for column in cursor.fetchall()]
        
        print(f"📋 Colunas existentes: {columns}")
        
        # Adicionar coluna is_blocked se não existir
        if 'is_blocked' not in columns:
            print("➕ Adicionando coluna is_blocked...")
            cursor.execute("ALTER TABLE dhcp_static_mappings ADD COLUMN is_blocked INTEGER DEFAULT 0")
            print("✅ Coluna is_blocked adicionada")
        else:
            print("ℹ️ Coluna is_blocked já existe")
        
        # Adicionar coluna reason se não existir
        if 'reason' not in columns:
            print("➕ Adicionando coluna reason...")
            cursor.execute("ALTER TABLE dhcp_static_mappings ADD COLUMN reason TEXT")
            print("✅ Coluna reason adicionada")
        else:
            print("ℹ️ Coluna reason já existe")
        
        # Verificar se as colunas foram adicionadas
        cursor.execute("PRAGMA table_info(dhcp_static_mappings)")
        columns_after = [column[1] for column in cursor.fetchall()]
        
        print(f"📋 Colunas após migração: {columns_after}")
        
        # Confirmar as mudanças
        conn.commit()
        
        # Testar as novas colunas
        print("\n🧪 Testando as novas colunas...")
        cursor.execute("SELECT COUNT(*) FROM dhcp_static_mappings")
        total_devices = cursor.fetchone()[0]
        print(f"📊 Total de dispositivos: {total_devices}")
        
        if total_devices > 0:
            cursor.execute("SELECT id, mac, ipaddr, is_blocked, reason FROM dhcp_static_mappings LIMIT 3")
            sample_devices = cursor.fetchall()
            print("📋 Amostra de dispositivos:")
            for device in sample_devices:
                print(f"   ID: {device[0]}, MAC: {device[1]}, IP: {device[2]}, Blocked: {device[3]}, Reason: {device[4]}")
        
        print("\n✅ Migração concluída com sucesso!")
        return True
        
    except Exception as e:
        print(f"❌ Erro durante a migração: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def rollback_migration():
    """Remove as colunas is_blocked e reason (rollback)"""
    
    db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'db.sqlite3')
    
    if not os.path.exists(db_path):
        print(f"❌ Banco de dados não encontrado: {db_path}")
        return False
    
    print(f"🔄 Executando rollback no banco: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # SQLite não suporta DROP COLUMN diretamente
        # Precisamos recriar a tabela sem as colunas
        print("⚠️ SQLite não suporta DROP COLUMN. Rollback manual necessário.")
        print("💡 Para fazer rollback, restaure o backup do banco de dados.")
        
        conn.close()
        return False
        
    except Exception as e:
        print(f"❌ Erro durante rollback: {e}")
        return False

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "rollback":
        rollback_migration()
    else:
        migrate_add_blocking_columns()
