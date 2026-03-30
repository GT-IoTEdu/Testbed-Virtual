#!/usr/bin/env python3
"""Script para corrigir constraint único em pf_id da tabela pfsense_firewall_rules"""
import sys
import os
from pathlib import Path

# Adicionar o diretório backend ao path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from config import MYSQL_USER, MYSQL_PASSWORD, MYSQL_HOST, MYSQL_DB
import pymysql

sql_statements = [
    # Verificar e remover índice único antigo
    "SET @index_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.STATISTICS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'pfsense_firewall_rules' AND INDEX_NAME = 'ix_pfsense_firewall_rules_pf_id' AND NON_UNIQUE = 0)",
    # Remover índice único se existir
    "SET @sql = IF(@index_exists > 0, 'ALTER TABLE `pfsense_firewall_rules` DROP INDEX `ix_pfsense_firewall_rules_pf_id`', 'SELECT 1')",
    "PREPARE stmt FROM @sql",
    "EXECUTE stmt",
    "DEALLOCATE PREPARE stmt",
    # Verificar se índice composto já existe
    "SET @comp_index_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.STATISTICS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'pfsense_firewall_rules' AND INDEX_NAME = 'idx_pf_id_institution_unique')",
    # Criar índice único composto se não existir
    "SET @sql2 = IF(@comp_index_exists = 0, 'ALTER TABLE `pfsense_firewall_rules` ADD UNIQUE INDEX `idx_pf_id_institution_unique` (`pf_id`, `institution_id`)', 'SELECT 1')",
    "PREPARE stmt2 FROM @sql2",
    "EXECUTE stmt2",
    "DEALLOCATE PREPARE stmt2",
    # Verificar se índice simples em pf_id existe
    "SET @simple_index_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.STATISTICS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'pfsense_firewall_rules' AND INDEX_NAME = 'idx_pf_id')",
    # Criar índice simples em pf_id se não existir
    "SET @sql3 = IF(@simple_index_exists = 0, 'ALTER TABLE `pfsense_firewall_rules` ADD INDEX `idx_pf_id` (`pf_id`)', 'SELECT 1')",
    "PREPARE stmt3 FROM @sql3",
    "EXECUTE stmt3",
    "DEALLOCATE PREPARE stmt3",
]

# Abordagem mais simples: tentar executar comandos e ignorar erros de "já existe"
simple_sql = [
    # Tentar remover índice único antigo (pode não existir)
    "ALTER TABLE `pfsense_firewall_rules` DROP INDEX `ix_pfsense_firewall_rules_pf_id`",
    # Criar índice único composto (pode já existir)
    "ALTER TABLE `pfsense_firewall_rules` ADD UNIQUE INDEX `idx_pf_id_institution_unique` (`pf_id`, `institution_id`)",
    # Criar índice simples em pf_id (pode já existir)
    "ALTER TABLE `pfsense_firewall_rules` ADD INDEX `idx_pf_id` (`pf_id`)",
]

try:
    print(f"Conectando ao banco {MYSQL_DB}...")
    connection = pymysql.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DB,
        charset='utf8mb4'
    )
    
    with connection.cursor() as cursor:
        for sql in simple_sql:
            try:
                print(f"Executando: {sql[:60]}...")
                cursor.execute(sql)
                connection.commit()
                print("OK")
            except Exception as e:
                error_msg = str(e)
                if "Duplicate key name" in error_msg or "already exists" in error_msg.lower() or "Unknown key" in error_msg:
                    print(f"Ja existe ou nao encontrado (ignorando): {error_msg[:60]}")
                else:
                    print(f"ERRO: {e}")
                    # Não fazer raise, continuar com os próximos comandos
    
    connection.close()
    print("\nMigracao concluida!")
except Exception as e:
    print(f"ERRO: {e}")
    sys.exit(1)

