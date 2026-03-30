#!/usr/bin/env python3
"""
Script para adicionar campos suricata_base_url e suricata_key na tabela institutions.
Execute este script após atualizar o modelo Institution.
"""

import sys
import os
from pathlib import Path

# Adicionar o diretório backend ao path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine, text, inspect
from config import MYSQL_USER, MYSQL_PASSWORD, MYSQL_HOST, MYSQL_DB

def migrate_add_suricata_fields():
    """Adiciona campos suricata_base_url e suricata_key na tabela institutions."""
    
    # String de conexão MySQL
    connection_string = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DB}"
    
    try:
        # Criar engine
        engine = create_engine(connection_string)
        
        print(f"Conectando ao banco de dados: {MYSQL_HOST}/{MYSQL_DB}")
        
        with engine.connect() as conn:
            # Verificar se a tabela existe
            result = conn.execute(text("SHOW TABLES LIKE 'institutions'"))
            if not result.fetchone():
                print("ERRO: Tabela 'institutions' não existe!")
                return False
            
            # Verificar se os campos já existem
            inspector = inspect(engine)
            columns = [col['name'] for col in inspector.get_columns('institutions')]
            
            if 'suricata_base_url' in columns and 'suricata_key' in columns:
                print("INFO: Campos suricata_base_url e suricata_key já existem na tabela 'institutions'")
                return True
            
            print("Adicionando campos suricata_base_url e suricata_key...")
            
            # Adicionar campo suricata_base_url se não existir
            if 'suricata_base_url' not in columns:
                conn.execute(text("""
                    ALTER TABLE institutions 
                    ADD COLUMN suricata_base_url VARCHAR(500) NULL 
                    COMMENT 'URL base para conectar no Suricata'
                """))
                conn.commit()
                print("✅ Campo 'suricata_base_url' adicionado com sucesso!")
            else:
                print("ℹ️  Campo 'suricata_base_url' já existe")
            
            # Adicionar campo suricata_key se não existir
            if 'suricata_key' not in columns:
                conn.execute(text("""
                    ALTER TABLE institutions 
                    ADD COLUMN suricata_key VARCHAR(500) NULL 
                    COMMENT 'Chave de acesso ao Suricata'
                """))
                conn.commit()
                print("✅ Campo 'suricata_key' adicionado com sucesso!")
            else:
                print("ℹ️  Campo 'suricata_key' já existe")
            
            # Verificar estrutura final
            result = conn.execute(text("DESCRIBE institutions"))
            columns_final = result.fetchall()
            
            print("\n✅ Migração concluída com sucesso!")
            print("\nEstrutura atualizada da tabela 'institutions':")
            print("-" * 80)
            for col in columns_final:
                print(f"  {col[0]:<25} {col[1]:<20} {col[2]:<10} {col[3]:<10} {col[4] or ''}")
            
            return True
            
    except Exception as e:
        print(f"ERRO: Falha ao executar migração: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 80)
    print("MIGRAÇÃO: Adicionar campos Suricata na tabela institutions")
    print("=" * 80)
    print()
    
    success = migrate_add_suricata_fields()
    
    if success:
        print("\n✅ Migração concluída com sucesso!")
        sys.exit(0)
    else:
        print("\n❌ Migração falhou!")
        sys.exit(1)
