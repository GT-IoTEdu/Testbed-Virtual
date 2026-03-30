#!/usr/bin/env python3
"""
Script unificado para configurar o banco de dados.

Este script:
- Detecta se é instalação do zero (banco vazio)
- Se for instalação do zero: cria todas as tabelas com estrutura completa
- Se for atualização: executa apenas migrações necessárias

Uso:
    python -m db.setup_database
    # ou
    python db/setup_database.py
"""

import sys
import os
from pathlib import Path

# Adicionar o diretório backend ao path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from db.models import Base
from db.session import engine, SessionLocal
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def is_database_empty() -> bool:
    """Verifica se o banco de dados está vazio (instalação do zero)."""
    try:
        db = SessionLocal()
        try:
            # Tentar listar tabelas
            result = db.execute(text("SHOW TABLES"))
            tables = result.fetchall()
            
            # Se não há tabelas, é instalação do zero
            if not tables:
                logger.info("📊 Banco de dados vazio detectado - instalação do zero")
                return True
            
            # Verificar se as tabelas principais existem
            table_names = [table[0] for table in tables]
            required_tables = ['users', 'institutions', 'dhcp_static_mappings']
            
            missing_tables = [t for t in required_tables if t not in table_names]
            if missing_tables:
                logger.info(f"📊 Algumas tabelas não existem: {missing_tables}")
                return True
            
            logger.info(f"📊 Banco de dados já possui {len(tables)} tabela(s)")
            return False
            
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"⚠️  Erro ao verificar banco: {e}")
        # Em caso de erro, assumir que é instalação do zero
        return True


def check_migration_needed() -> dict:
    """Verifica quais migrações são necessárias."""
    needed = {
        'institution_id_dhcp': False,
        'institution_id_aliases': False,
        'institution_id_rules': False,
        'fix_pf_id_constraint': False
    }
    
    try:
        db = SessionLocal()
        try:
            # Verificar se dhcp_static_mappings tem institution_id
            result = db.execute(text("""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = 'dhcp_static_mappings' 
                AND COLUMN_NAME = 'institution_id'
            """))
            if not result.fetchone():
                needed['institution_id_dhcp'] = True
            
            # Verificar se pfsense_aliases tem institution_id
            result = db.execute(text("""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = 'pfsense_aliases' 
                AND COLUMN_NAME = 'institution_id'
            """))
            if not result.fetchone():
                needed['institution_id_aliases'] = True
            
            # Verificar se pfsense_firewall_rules tem institution_id
            result = db.execute(text("""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = 'pfsense_firewall_rules' 
                AND COLUMN_NAME = 'institution_id'
            """))
            if not result.fetchone():
                needed['institution_id_rules'] = True
            
            # Verificar índice único composto em pfsense_firewall_rules
            result = db.execute(text("""
                SELECT INDEX_NAME 
                FROM INFORMATION_SCHEMA.STATISTICS 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = 'pfsense_firewall_rules' 
                AND INDEX_NAME = 'idx_pf_id_institution_unique'
            """))
            if not result.fetchone():
                needed['fix_pf_id_constraint'] = True
            
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"⚠️  Erro ao verificar migrações: {e}")
    
    return needed


def create_all_tables():
    """Cria todas as tabelas com estrutura completa."""
    logger.info("🔨 Criando todas as tabelas...")
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Tabelas criadas com sucesso!")
        
        # Listar tabelas criadas
        db = SessionLocal()
        try:
            result = db.execute(text("SHOW TABLES"))
            tables = result.fetchall()
            logger.info(f"📋 Total de tabelas criadas: {len(tables)}")
            for table in tables:
                logger.info(f"   - {table[0]}")
        finally:
            db.close()
        
        return True
    except Exception as e:
        logger.error(f"❌ Erro ao criar tabelas: {e}")
        return False


def run_migrations():
    """Executa migrações necessárias."""
    logger.info("🔄 Verificando migrações necessárias...")
    
    needed = check_migration_needed()
    
    if not any(needed.values()):
        logger.info("✅ Nenhuma migração necessária - banco já está atualizado")
        return True
    
    logger.info("📦 Executando migrações necessárias...")
    
    # Executar migrações via SQL direto (mais confiável)
    db = SessionLocal()
    try:
        if needed['institution_id_dhcp']:
            logger.info("📝 Adicionando institution_id a dhcp_static_mappings...")
            try:
                db.execute(text("""
                    ALTER TABLE `dhcp_static_mappings` 
                    ADD COLUMN `institution_id` INT(11) NULL DEFAULT NULL 
                    COMMENT 'ID da instituição/campus ao qual o dispositivo pertence' 
                    AFTER `descr`
                """))
                db.execute(text("ALTER TABLE `dhcp_static_mappings` ADD INDEX `idx_institution_id` (`institution_id`)"))
                db.commit()
                logger.info("   ✅ institution_id adicionado a dhcp_static_mappings")
            except Exception as e:
                if 'Duplicate column name' not in str(e):
                    logger.error(f"   ❌ Erro: {e}")
                    db.rollback()
                    return False
                db.rollback()
        
        if needed['institution_id_aliases']:
            logger.info("📝 Adicionando institution_id a pfsense_aliases...")
            try:
                db.execute(text("""
                    ALTER TABLE `pfsense_aliases` 
                    ADD COLUMN `institution_id` INT(11) NULL DEFAULT NULL 
                    COMMENT 'ID da instituição/campus ao qual o alias pertence' 
                    AFTER `descr`
                """))
                db.execute(text("ALTER TABLE `pfsense_aliases` ADD INDEX `idx_institution_id` (`institution_id`)"))
                db.execute(text("""
                    ALTER TABLE `pfsense_aliases` 
                    ADD UNIQUE INDEX `idx_alias_name_institution_unique` (`name`, `institution_id`)
                """))
                db.commit()
                logger.info("   ✅ institution_id adicionado a pfsense_aliases")
            except Exception as e:
                if 'Duplicate column name' not in str(e) and 'Duplicate key name' not in str(e):
                    logger.error(f"   ❌ Erro: {e}")
                    db.rollback()
                    return False
                else:
                    logger.info("   ℹ️  Coluna ou índice já existe (ignorando)")
                    db.rollback()
        
        if needed['institution_id_rules']:
            logger.info("📝 Adicionando institution_id a pfsense_firewall_rules...")
            try:
                db.execute(text("""
                    ALTER TABLE `pfsense_firewall_rules` 
                    ADD COLUMN `institution_id` INT(11) NULL DEFAULT NULL 
                    COMMENT 'ID da instituição/campus ao qual a regra pertence' 
                    AFTER `updated_by`
                """))
                db.execute(text("ALTER TABLE `pfsense_firewall_rules` ADD INDEX `idx_institution_id` (`institution_id`)"))
                db.commit()
                logger.info("   ✅ institution_id adicionado a pfsense_firewall_rules")
            except Exception as e:
                if 'Duplicate column name' not in str(e):
                    logger.error(f"   ❌ Erro: {e}")
                    db.rollback()
                    return False
                else:
                    logger.info("   ℹ️  Coluna já existe (ignorando)")
                    db.rollback()
        
        if needed['fix_pf_id_constraint']:
            logger.info("📝 Corrigindo constraint de pf_id em pfsense_firewall_rules...")
            try:
                # Tentar remover índice único antigo (pode não existir)
                try:
                    db.execute(text("ALTER TABLE `pfsense_firewall_rules` DROP INDEX `ix_pfsense_firewall_rules_pf_id`"))
                    db.commit()
                except:
                    db.rollback()  # Pode não existir, continuar
                
                # Criar índice único composto
                db.execute(text("""
                    ALTER TABLE `pfsense_firewall_rules` 
                    ADD UNIQUE INDEX `idx_pf_id_institution_unique` (`pf_id`, `institution_id`)
                """))
                db.execute(text("ALTER TABLE `pfsense_firewall_rules` ADD INDEX `idx_pf_id` (`pf_id`)"))
                db.commit()
                logger.info("   ✅ Constraint de pf_id corrigida")
            except Exception as e:
                if 'Duplicate key name' not in str(e):
                    logger.error(f"   ❌ Erro: {e}")
                    db.rollback()
                    return False
                else:
                    logger.info("   ℹ️  Índice já existe (ignorando)")
                    db.rollback()
        
    finally:
        db.close()
    
    logger.info("✅ Migrações concluídas")
    return True


def main():
    """Função principal."""
    logger.info("="*60)
    logger.info("🚀 CONFIGURAÇÃO DO BANCO DE DADOS")
    logger.info("="*60)
    
    # Verificar se é instalação do zero
    is_empty = is_database_empty()
    
    if is_empty:
        logger.info("\n📦 Modo: INSTALAÇÃO DO ZERO")
        logger.info("   Criando todas as tabelas com estrutura completa...")
        
        if create_all_tables():
            logger.info("\n✅ Instalação do zero concluída com sucesso!")
            logger.info("\n📋 Próximos passos:")
            logger.info("   1. Criar instituição: python scripts/create_institutions_simple.py")
            logger.info("   2. Criar usuário ADMIN: python scripts/create_initial_admin.py")
            logger.info("   3. Criar aliases e regras: python scripts/setup_initial_aliases_and_rules.py")
            return 0
        else:
            logger.error("\n❌ Falha na instalação do zero")
            return 1
    else:
        logger.info("\n🔄 Modo: ATUALIZAÇÃO")
        logger.info("   Verificando e executando migrações necessárias...")
        
        if run_migrations():
            logger.info("\n✅ Atualização concluída com sucesso!")
            return 0
        else:
            logger.error("\n❌ Falha na atualização")
            return 1


if __name__ == "__main__":
    sys.exit(main())

