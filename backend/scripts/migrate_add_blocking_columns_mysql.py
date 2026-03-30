#!/usr/bin/env python3
"""
Migração para adicionar colunas is_blocked e reason na tabela dhcp_static_mappings (MySQL)
"""

import mysql.connector
import os
from datetime import datetime

def get_db_connection():
    """Cria conexão com o banco MySQL"""
    try:
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            database=os.getenv('DB_NAME', 'iot_edu'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', ''),
            port=int(os.getenv('DB_PORT', 3306))
        )
        return connection
    except mysql.connector.Error as e:
        print(f"❌ Erro ao conectar com MySQL: {e}")
        return None

def migrate_add_blocking_columns():
    """Adiciona colunas is_blocked e reason na tabela dhcp_static_mappings"""
    
    print("🔧 Executando migração MySQL...")
    
    connection = get_db_connection()
    if not connection:
        return False
    
    try:
        cursor = connection.cursor()
        
        # Verificar se a tabela existe
        cursor.execute("SHOW TABLES LIKE 'dhcp_static_mappings'")
        if not cursor.fetchone():
            print("❌ Tabela dhcp_static_mappings não encontrada")
            return False
        
        # Verificar colunas existentes
        cursor.execute("DESCRIBE dhcp_static_mappings")
        columns = [column[0] for column in cursor.fetchall()]
        
        print(f"📋 Colunas existentes: {columns}")
        
        # Adicionar coluna is_blocked se não existir
        if 'is_blocked' not in columns:
            print("➕ Adicionando coluna is_blocked...")
            cursor.execute("ALTER TABLE dhcp_static_mappings ADD COLUMN is_blocked TINYINT(1) DEFAULT 0")
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
        
        # Confirmar as mudanças
        connection.commit()
        
        # Verificar se as colunas foram adicionadas
        cursor.execute("DESCRIBE dhcp_static_mappings")
        columns_after = [column[0] for column in cursor.fetchall()]
        
        print(f"📋 Colunas após migração: {columns_after}")
        
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
        
    except mysql.connector.Error as e:
        print(f"❌ Erro durante a migração: {e}")
        connection.rollback()
        return False
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def rollback_migration():
    """Remove as colunas is_blocked e reason (rollback)"""
    
    print("🔄 Executando rollback MySQL...")
    
    connection = get_db_connection()
    if not connection:
        return False
    
    try:
        cursor = connection.cursor()
        
        # Verificar colunas existentes
        cursor.execute("DESCRIBE dhcp_static_mappings")
        columns = [column[0] for column in cursor.fetchall()]
        
        # Remover coluna is_blocked se existir
        if 'is_blocked' in columns:
            print("➖ Removendo coluna is_blocked...")
            cursor.execute("ALTER TABLE dhcp_static_mappings DROP COLUMN is_blocked")
            print("✅ Coluna is_blocked removida")
        
        # Remover coluna reason se existir
        if 'reason' in columns:
            print("➖ Removendo coluna reason...")
            cursor.execute("ALTER TABLE dhcp_static_mappings DROP COLUMN reason")
            print("✅ Coluna reason removida")
        
        # Confirmar as mudanças
        connection.commit()
        
        print("\n✅ Rollback concluído com sucesso!")
        return True
        
    except mysql.connector.Error as e:
        print(f"❌ Erro durante rollback: {e}")
        connection.rollback()
        return False
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "rollback":
        rollback_migration()
    else:
        migrate_add_blocking_columns()
