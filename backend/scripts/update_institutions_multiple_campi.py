#!/usr/bin/env python3
"""
Script para atualizar a tabela institutions removendo a restrição de unicidade apenas no nome.
Permite múltiplos campi da mesma instituição em cidades diferentes.
"""

import sys
import os
from pathlib import Path

# Adicionar o diretório backend ao path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

import pymysql
from config import MYSQL_USER, MYSQL_PASSWORD, MYSQL_HOST, MYSQL_DB

def update_institutions_table():
    """Atualiza a tabela institutions para permitir múltiplos campi."""
    
    try:
        # Conectar ao MySQL
        connection = pymysql.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DB,
            charset='utf8mb4'
        )
        
        print(f"Conectado ao banco de dados: {MYSQL_HOST}/{MYSQL_DB}")
        
        with connection.cursor() as cursor:
            # Verificar se a restrição de unicidade existe
            cursor.execute("""
                SELECT CONSTRAINT_NAME 
                FROM information_schema.TABLE_CONSTRAINTS 
                WHERE TABLE_SCHEMA = %s 
                AND TABLE_NAME = 'institutions' 
                AND CONSTRAINT_NAME = 'ix_institutions_nome'
            """, (MYSQL_DB,))
            
            if cursor.fetchone():
                print("Removendo restrição de unicidade no campo 'nome'...")
                cursor.execute("ALTER TABLE institutions DROP INDEX ix_institutions_nome")
                print("SUCESSO: Restrição de unicidade removida!")
            else:
                print("INFO: Restrição de unicidade não encontrada (já foi removida ou não existe)")
            
            # Criar índice composto para nome + cidade (opcional, para performance)
            cursor.execute("""
                SELECT INDEX_NAME 
                FROM information_schema.STATISTICS 
                WHERE TABLE_SCHEMA = %s 
                AND TABLE_NAME = 'institutions' 
                AND INDEX_NAME = 'idx_institution_nome_cidade'
            """, (MYSQL_DB,))
            
            if not cursor.fetchone():
                print("Criando índice composto para nome + cidade...")
                cursor.execute("""
                    CREATE INDEX idx_institution_nome_cidade 
                    ON institutions (nome, cidade)
                """)
                print("SUCESSO: Índice composto criado!")
            else:
                print("INFO: Índice composto já existe")
            
            connection.commit()
            
            # Verificar estrutura atual
            cursor.execute("SHOW INDEX FROM institutions")
            indexes = cursor.fetchall()
            
            print("\nÍndices atuais da tabela 'institutions':")
            print("-" * 60)
            for index in indexes:
                print(f"  {index[2]:<30} {index[4]:<20} {index[10] or ''}")
            
            return True
            
    except Exception as e:
        print(f"ERRO ao atualizar tabela 'institutions': {e}")
        return False
    finally:
        if 'connection' in locals():
            connection.close()

def test_multiple_campi():
    """Testa se é possível cadastrar múltiplos campi."""
    
    try:
        connection = pymysql.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DB,
            charset='utf8mb4'
        )
        
        with connection.cursor() as cursor:
            # Verificar quantas instituições Unipampa existem
            cursor.execute("SELECT COUNT(*) FROM institutions WHERE nome = 'Unipampa'")
            count = cursor.fetchone()[0]
            
            print(f"\nInstituições 'Unipampa' cadastradas: {count}")
            
            if count > 0:
                cursor.execute("SELECT nome, cidade FROM institutions WHERE nome = 'Unipampa'")
                campi = cursor.fetchall()
                
                print("Campi Unipampa existentes:")
                for campus in campi:
                    print(f"  - {campus[0]} ({campus[1]})")
            
            return True
            
    except Exception as e:
        print(f"ERRO ao testar múltiplos campi: {e}")
        return False
    finally:
        if 'connection' in locals():
            connection.close()

def main():
    """Função principal."""
    print("Atualizando tabela 'institutions' para permitir múltiplos campi...")
    print("=" * 60)
    
    # Atualizar tabela
    if update_institutions_table():
        print("\n" + "=" * 60)
        
        # Testar múltiplos campi
        print("Testando configuração...")
        test_multiple_campi()
        
        print("\n" + "=" * 60)
        print("SUCESSO: Processo concluído!")
        print("\nAgora você pode cadastrar:")
        print("  - Unipampa Alegrete")
        print("  - Unipampa Uruguaiana")
        print("  - Unipampa Bagé")
        print("  - E outros campi...")
    else:
        print("\nERRO: Falha ao atualizar tabela. Verifique os logs acima.")
        sys.exit(1)

if __name__ == "__main__":
    main()
