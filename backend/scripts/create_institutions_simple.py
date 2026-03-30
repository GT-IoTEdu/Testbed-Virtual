#!/usr/bin/env python3
"""
Script simples para criar a tabela institutions usando SQL direto.
"""

import sys
import os
from pathlib import Path

# Adicionar o diretório backend ao path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

import pymysql
from config import MYSQL_USER, MYSQL_PASSWORD, MYSQL_HOST, MYSQL_DB

def create_institutions_table():
    """Cria a tabela institutions usando SQL direto."""
    
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
            # Verificar se a tabela já existe
            cursor.execute("SHOW TABLES LIKE 'institutions'")
            if cursor.fetchone():
                print("INFO: Tabela 'institutions' já existe!")
                return True
            
            # SQL para criar a tabela
            create_table_sql = """
            CREATE TABLE `institutions` (
              `id` int(11) NOT NULL AUTO_INCREMENT,
              `nome` varchar(255) NOT NULL COMMENT 'Nome da instituição',
              `cidade` varchar(255) NOT NULL COMMENT 'Cidade onde está localizada',
              `pfsense_base_url` varchar(500) NOT NULL COMMENT 'URL base para conectar no pfSense',
              `pfsense_key` varchar(500) NOT NULL COMMENT 'Chave de acesso ao pfSense',
              `zeek_base_url` varchar(500) NOT NULL COMMENT 'URL base para conectar no Zeek',
              `zeek_key` varchar(500) NOT NULL COMMENT 'Chave de acesso ao Zeek',
              `ip_range_start` varchar(15) NOT NULL COMMENT 'IP inicial do range',
              `ip_range_end` varchar(15) NOT NULL COMMENT 'IP final do range',
              `is_active` tinyint(1) NOT NULL DEFAULT 1 COMMENT 'Se a instituição está ativa',
              `created_at` datetime DEFAULT NULL COMMENT 'Data/hora de criação',
              `updated_at` datetime DEFAULT NULL COMMENT 'Data/hora da última atualização',
              PRIMARY KEY (`id`),
              UNIQUE KEY `ix_institutions_nome` (`nome`),
              KEY `ix_institutions_id` (`id`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """
            
            # Executar SQL
            cursor.execute(create_table_sql)
            connection.commit()
            
            print("SUCESSO: Tabela 'institutions' criada com sucesso!")
            
            # Verificar estrutura
            cursor.execute("DESCRIBE institutions")
            columns = cursor.fetchall()
            
            print("\nEstrutura da tabela 'institutions':")
            print("-" * 60)
            for column in columns:
                print(f"  {column[0]:<20} {column[1]:<15} {column[2]:<10} {column[3] or ''}")
            
            return True
            
    except Exception as e:
        print(f"ERRO ao criar tabela 'institutions': {e}")
        return False
    finally:
        if 'connection' in locals():
            connection.close()

def insert_sample_institution():
    """Insere uma instituição de exemplo."""
    
    try:
        connection = pymysql.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DB,
            charset='utf8mb4'
        )
        
        with connection.cursor() as cursor:
            # Verificar se já existe
            cursor.execute("SELECT COUNT(*) FROM institutions WHERE nome = 'Unipampa'")
            count = cursor.fetchone()[0]
            
            if count > 0:
                print("INFO: Instituição de exemplo 'Unipampa' já existe!")
                return True
            
            # Inserir exemplo
            insert_sql = """
                INSERT INTO institutions (
                    nome, cidade, pfsense_base_url, pfsense_key,
                    zeek_base_url, zeek_key, ip_range_start, ip_range_end,
                    is_active, created_at, updated_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW()
                )
            """
            
            values = (
                'Unipampa', 'Alegrete', 'http://192.168.56.101/api/v2/', '929ca6e1a3ed6ab30f531dc6421dec7a',
                'http://host.docker.internal:8001', 'a8f4c2d9-1c9b-4b6f-9d6e-aaa111bbb222', '172.20.0.10', '172.20.0.254', 1
            )
            cursor.execute(insert_sql, values)
            connection.commit()
            
            print("SUCESSO: Instituição de exemplo 'Unipampa' inserida com sucesso!")
            return True
            
    except Exception as e:
        print(f"ERRO ao inserir instituição de exemplo: {e}")
        return False
    finally:
        if 'connection' in locals():
            connection.close()

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
