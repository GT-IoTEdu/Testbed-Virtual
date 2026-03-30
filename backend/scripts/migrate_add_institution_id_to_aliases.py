#!/usr/bin/env python3
"""
Script de migração para adicionar coluna institution_id na tabela pfsense_aliases.
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
                AND TABLE_NAME = 'pfsense_aliases' 
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
                AND TABLE_NAME = 'pfsense_aliases'
            """, (MYSQL_DB,))
            
            table_exists = cursor.fetchone()
            
            if not table_exists:
                print("[ERRO] Tabela pfsense_aliases nao encontrada!")
                return False
            
            print("[OK] Tabela encontrada. Executando migracao...\n")
            
            # 1. Remover índices únicos antigos se existirem
            print("[*] Removendo indices unicos antigos...")
            try:
                cursor.execute("SHOW INDEX FROM `pfsense_aliases` WHERE Key_name = 'name'")
                if cursor.fetchone():
                    cursor.execute("ALTER TABLE `pfsense_aliases` DROP INDEX `name`")
                    print("   [OK] Indice 'name' removido")
            except Exception as e:
                if "Unknown key" not in str(e):
                    print(f"   [AVISO] Erro ao remover indice 'name': {e}")
            
            try:
                cursor.execute("SHOW INDEX FROM `pfsense_aliases` WHERE Key_name = 'pf_id'")
                if cursor.fetchone():
                    cursor.execute("ALTER TABLE `pfsense_aliases` DROP INDEX `pf_id`")
                    print("   [OK] Indice unico 'pf_id' removido")
            except Exception as e:
                if "Unknown key" not in str(e):
                    print(f"   [AVISO] Erro ao remover indice 'pf_id': {e}")
            
            # 2. Adicionar coluna institution_id
            print("\n[*] Adicionando coluna institution_id...")
            cursor.execute("""
                ALTER TABLE `pfsense_aliases` 
                ADD COLUMN `institution_id` INT(11) NULL DEFAULT NULL 
                COMMENT 'ID da instituição/campus ao qual o alias pertence' 
                AFTER `descr`
            """)
            print("   [OK] Coluna institution_id adicionada com sucesso!")
            
            # 3. Adicionar índice simples
            print("\n[*] Adicionando indice idx_institution_id...")
            try:
                cursor.execute("""
                    ALTER TABLE `pfsense_aliases` 
                    ADD INDEX `idx_institution_id` (`institution_id`)
                """)
                print("   [OK] Indice idx_institution_id criado com sucesso!")
            except pymysql.Error as e:
                if "Duplicate key name" in str(e):
                    print("   [AVISO] Indice ja existe. Continuando...")
                else:
                    raise
            
            # 4. Criar índice único composto (name, institution_id)
            print("\n[*] Criando indice unico composto (name, institution_id)...")
            try:
                cursor.execute("""
                    ALTER TABLE `pfsense_aliases` 
                    ADD UNIQUE INDEX `idx_alias_name_institution_unique` (`name`, `institution_id`)
                """)
                print("   [OK] Indice unico composto criado com sucesso!")
            except pymysql.Error as e:
                if "Duplicate key name" in str(e):
                    print("   [AVISO] Indice composto ja existe. Continuando...")
                else:
                    raise
            
            # 5. Adicionar índice para pf_id (não mais único)
            print("\n[*] Adicionando indice idx_pf_id (nao unico)...")
            try:
                cursor.execute("""
                    ALTER TABLE `pfsense_aliases` 
                    ADD INDEX `idx_pf_id` (`pf_id`)
                """)
                print("   [OK] Indice idx_pf_id criado com sucesso!")
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
            cursor.execute("SHOW COLUMNS FROM `pfsense_aliases` LIKE 'institution_id'")
            column_info = cursor.fetchone()
            
            if column_info:
                print(f"   - Coluna: {column_info['Field']}")
                print(f"   - Tipo: {column_info['Type']}")
                print(f"   - Null: {column_info['Null']}")
                print(f"   - Default: {column_info['Default']}")
            
            # Verificar índices
            cursor.execute("SHOW INDEX FROM `pfsense_aliases` WHERE Key_name IN ('idx_institution_id', 'idx_alias_name_institution_unique', 'idx_pf_id')")
            indexes = cursor.fetchall()
            
            if indexes:
                print("\n   - Indices criados:")
                for idx in indexes:
                    print(f"     * {idx['Key_name']} ({idx['Column_name']})")
            
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
    print("Migracao: Adicionar institution_id em pfsense_aliases")
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

