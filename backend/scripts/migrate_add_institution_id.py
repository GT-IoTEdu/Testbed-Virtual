#!/usr/bin/env python3
"""
Script de migração para adicionar coluna institution_id na tabela dhcp_static_mappings.
"""

import sys
import os
from pathlib import Path

# Adicionar o diretório backend ao path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

try:
    import pymysql
except ImportError:
    print("[ERRO] pymysql nao esta instalado. Execute: pip install pymysql")
    sys.exit(1)

from config import MYSQL_USER, MYSQL_PASSWORD, MYSQL_HOST, MYSQL_DB

def execute_migration():
    """Executa a migração para adicionar institution_id."""
    
    try:
        # Conectar ao MySQL
        print(f"[*] Conectando ao banco de dados: {MYSQL_HOST}/{MYSQL_DB}...")
        connection = pymysql.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DB,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        print("[OK] Conectado com sucesso!")
        
        with connection.cursor() as cursor:
            # Verificar se a coluna já existe
            print("\n[*] Verificando se a coluna institution_id ja existe...")
            cursor.execute("""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = %s 
                AND TABLE_NAME = 'dhcp_static_mappings' 
                AND COLUMN_NAME = 'institution_id'
            """, (MYSQL_DB,))
            
            column_exists = cursor.fetchone()
            
            if column_exists:
                print("[AVISO] A coluna institution_id ja existe. Pulando migracao.")
                return True
            
            # Verificar se a tabela existe
            cursor.execute("""
                SELECT TABLE_NAME 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_SCHEMA = %s 
                AND TABLE_NAME = 'dhcp_static_mappings'
            """, (MYSQL_DB,))
            
            table_exists = cursor.fetchone()
            
            if not table_exists:
                print("[ERRO] Tabela dhcp_static_mappings nao encontrada!")
                return False
            
            print("[OK] Tabela encontrada. Executando migracao...\n")
            
            # 1. Adicionar coluna institution_id
            print("[*] Adicionando coluna institution_id...")
            cursor.execute("""
                ALTER TABLE `dhcp_static_mappings` 
                ADD COLUMN `institution_id` INT(11) NULL DEFAULT NULL 
                COMMENT 'ID da instituição/campus ao qual o dispositivo pertence' 
                AFTER `descr`
            """)
            print("   [OK] Coluna institution_id adicionada com sucesso!")
            
            # 2. Adicionar índice
            print("\n[*] Adicionando indice idx_institution_id...")
            try:
                cursor.execute("""
                    ALTER TABLE `dhcp_static_mappings` 
                    ADD INDEX `idx_institution_id` (`institution_id`)
                """)
                print("   [OK] Indice idx_institution_id criado com sucesso!")
            except pymysql.Error as e:
                if "Duplicate key name" in str(e):
                    print("   [AVISO] Indice ja existe. Continuando...")
                else:
                    raise
            
            # Commit das alterações
            connection.commit()
            
            print("\n[OK] Migracao concluida com sucesso!")
            print("\n[*] Verificando estrutura da tabela...")
            
            # Verificar estrutura final
            cursor.execute("SHOW COLUMNS FROM `dhcp_static_mappings` LIKE 'institution_id'")
            column_info = cursor.fetchone()
            
            if column_info:
                print(f"   - Coluna: {column_info['Field']}")
                print(f"   - Tipo: {column_info['Type']}")
                print(f"   - Null: {column_info['Null']}")
                print(f"   - Default: {column_info['Default']}")
                print(f"   - Comentário: {column_info.get('Comment', 'N/A')}")
            
            # Verificar índice
            cursor.execute("""
                SHOW INDEX FROM `dhcp_static_mappings` 
                WHERE Key_name = 'idx_institution_id'
            """)
            index_info = cursor.fetchone()
            
            if index_info:
                print(f"\n   - Índice: {index_info['Key_name']}")
                print(f"   - Coluna: {index_info['Column_name']}")
            
            return True
            
    except pymysql.Error as e:
        print(f"\n[ERRO] Erro ao executar migracao: {e}")
        if connection:
            connection.rollback()
        return False
    except Exception as e:
        print(f"\n[ERRO] Erro inesperado: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if connection:
            connection.close()
            print("\n[*] Conexao fechada.")

if __name__ == "__main__":
    print("=" * 60)
    print("Migracao: Adicionar institution_id em dhcp_static_mappings")
    print("=" * 60)
    
    success = execute_migration()
    
    if success:
        print("\n" + "=" * 60)
        print("[OK] Migracao executada com sucesso!")
        print("=" * 60)
        sys.exit(0)
    else:
        print("\n" + "=" * 60)
        print("[ERRO] Migracao falhou!")
        print("=" * 60)
        sys.exit(1)

