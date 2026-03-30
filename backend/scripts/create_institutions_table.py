#!/usr/bin/env python3
"""
Script para criar a tabela institutions no banco de dados.
Execute este script após atualizar o modelo Institution.
"""

import sys
import os
from pathlib import Path

# Adicionar o diretório backend ao path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine, text
from db.models import Institution, Base
from config import MYSQL_USER, MYSQL_PASSWORD, MYSQL_HOST, MYSQL_DB

def create_institutions_table():
    """Cria a tabela institutions no banco de dados."""
    
    # String de conexão MySQL
    connection_string = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DB}"
    
    try:
        # Criar engine
        engine = create_engine(connection_string)
        
        print(f"Conectando ao banco de dados: {MYSQL_HOST}/{MYSQL_DB}")
        
        # Verificar se a tabela já existe
        with engine.connect() as conn:
            result = conn.execute(text("SHOW TABLES LIKE 'institutions'"))
            if result.fetchone():
                print("ERRO: Tabela 'institutions' já existe!")
                return False
        
        # Criar a tabela
        print("Criando tabela 'institutions'...")
        Institution.__table__.create(engine, checkfirst=True)
        
        print("SUCESSO: Tabela 'institutions' criada com sucesso!")
        
        # Verificar se foi criada corretamente
        with engine.connect() as conn:
            result = conn.execute(text("DESCRIBE institutions"))
            columns = result.fetchall()
            
            print("\nEstrutura da tabela 'institutions':")
            print("-" * 50)
            for column in columns:
                print(f"  {column[0]:<20} {column[1]:<15} {column[2]:<10} {column[3] or ''}")
        
        return True
        
    except Exception as e:
        print(f"ERRO ao criar tabela 'institutions': {e}")
        return False

def insert_sample_institution():
    """Insere uma instituição de exemplo."""
    
    connection_string = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DB}"
    
    try:
        engine = create_engine(connection_string)
        
        with engine.connect() as conn:
            # Verificar se já existe uma instituição de exemplo
            result = conn.execute(text("SELECT COUNT(*) FROM institutions WHERE nome = 'Unipampa'"))
            count = result.scalar()
            
            if count > 0:
                print("INFO: Instituição de exemplo 'Unipampa' já existe!")
                return True
            
            # Inserir instituição de exemplo
            insert_sql = text("""
                INSERT INTO institutions (
                    nome, cidade, pfsense_base_url, pfsense_key,
                    zeek_base_url, zeek_key, ip_range_start, ip_range_end,
                    is_active, created_at, updated_at
                ) VALUES (
                    'Unipampa', 'Alegrete', 'http://192.168.1.1', 'pfsense_key_example',
                    'http://192.168.1.2', 'zeek_key_example', '192.168.1.1', '192.168.1.200',
                    1, NOW(), NOW()
                )
            """)
            
            conn.execute(insert_sql)
            conn.commit()
            
            print("SUCESSO: Instituição de exemplo 'Unipampa' inserida com sucesso!")
            return True
            
    except Exception as e:
        print(f"ERRO ao inserir instituição de exemplo: {e}")
        return False

def main():
    """Função principal."""
    print("Criando tabela 'institutions' no banco de dados...")
    print("=" * 60)
    
    # Criar tabela
    if create_institutions_table():
        print("\n" + "=" * 60)
        
        # Inserir exemplo
        print("Inserindo instituição de exemplo...")
        insert_sample_institution()
        
        print("\n" + "=" * 60)
        print("SUCESSO: Processo concluído com sucesso!")
        print("\nPróximos passos:")
        print("   1. Reinicie o servidor backend")
        print("   2. Acesse o dashboard administrativo")
        print("   3. Teste o cadastro de instituições")
        print("   4. Verifique os endpoints em /docs")
    else:
        print("\nERRO: Falha ao criar tabela. Verifique os logs acima.")
        sys.exit(1)

if __name__ == "__main__":
    main()
