#!/usr/bin/env python3
"""
Script para executar migração: adicionar institution_id à tabela pfsense_firewall_rules
"""
import sys
import os

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from config import MYSQL_USER, MYSQL_PASSWORD, MYSQL_HOST, MYSQL_DB
except ImportError:
    # Tentar importar de outra forma
    import config
    MYSQL_USER = getattr(config, 'MYSQL_USER', getattr(config, 'DB_USER', 'root'))
    MYSQL_PASSWORD = getattr(config, 'MYSQL_PASSWORD', getattr(config, 'DB_PASSWORD', ''))
    MYSQL_HOST = getattr(config, 'MYSQL_HOST', getattr(config, 'DB_HOST', 'localhost'))
    MYSQL_DB = getattr(config, 'MYSQL_DB', getattr(config, 'DB_NAME', 'api_iot_edu'))

import pymysql
from pathlib import Path

def execute_migration():
    """Executa a migração SQL para adicionar institution_id à tabela pfsense_firewall_rules"""
    
    # Caminho do arquivo SQL
    migration_file = Path(__file__).parent.parent / "db" / "migrations" / "add_institution_id_to_pfsense_firewall_rules.sql"
    
    if not migration_file.exists():
        print(f"ERRO: Arquivo de migracao nao encontrado: {migration_file}")
        return False
    
    # Ler o conteúdo do arquivo SQL
    with open(migration_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    # Conectar ao banco de dados
    try:
        connection = pymysql.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DB,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        print(f"OK: Conectado ao banco de dados: {MYSQL_DB}")
        
        try:
            with connection.cursor() as cursor:
                # Executar cada comando SQL separadamente
                statements = [s.strip() for s in sql_content.split(';') if s.strip() and not s.strip().startswith('--')]
                
                for statement in statements:
                    if statement:
                        print(f"Executando: {statement[:80]}...")
                        cursor.execute(statement)
                        connection.commit()
                        print("   OK: Comando executado com sucesso")
                
                print("\nOK: Migracao concluida com sucesso!")
                return True
                
        except Exception as e:
            connection.rollback()
            print(f"ERRO ao executar migracao: {e}")
            return False
        finally:
            connection.close()
            
    except Exception as e:
        print(f"ERRO ao conectar ao banco de dados: {e}")
        return False

if __name__ == "__main__":
    print("Iniciando migracao: adicionar institution_id a tabela pfsense_firewall_rules\n")
    success = execute_migration()
    sys.exit(0 if success else 1)

