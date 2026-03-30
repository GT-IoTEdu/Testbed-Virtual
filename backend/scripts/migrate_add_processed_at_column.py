#!/usr/bin/env python3
"""
Script para adicionar coluna processed_at na tabela zeek_incidents.

Esta coluna rastreará quando um incidente foi processado para bloqueio automático,
permitindo processar apenas incidentes novos e evitar reprocessamento.
"""

import sys
import os
import logging
from datetime import datetime

# Adicionar o diretório backend ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.session import SessionLocal
from sqlalchemy import text

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_processed_at_column():
    """
    Adiciona a coluna processed_at na tabela zeek_incidents.
    """
    db = SessionLocal()
    try:
        # Verificar se a coluna já existe
        result = db.execute(text("""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'zeek_incidents' 
            AND COLUMN_NAME = 'processed_at'
        """))
        
        if result.fetchone():
            logger.info("Coluna 'processed_at' já existe na tabela zeek_incidents")
            return True
        
        # Adicionar a coluna processed_at
        logger.info("Adicionando coluna 'processed_at' na tabela zeek_incidents...")
        
        db.execute(text("""
            ALTER TABLE zeek_incidents 
            ADD COLUMN processed_at DATETIME NULL 
            COMMENT 'Data/hora quando o incidente foi processado para bloqueio automático'
        """))
        
        db.commit()
        logger.info("✅ Coluna 'processed_at' adicionada com sucesso!")
        
        # Adicionar índice para otimizar consultas
        logger.info("Adicionando índice para coluna 'processed_at'...")
        
        db.execute(text("""
            CREATE INDEX idx_incident_processed_at 
            ON zeek_incidents(processed_at)
        """))
        
        db.commit()
        logger.info("✅ Índice adicionado com sucesso!")
        
        # Mostrar estrutura atualizada da tabela
        result = db.execute(text("DESCRIBE zeek_incidents"))
        columns = result.fetchall()
        
        logger.info("📋 Estrutura atualizada da tabela zeek_incidents:")
        for column in columns:
            logger.info(f"  - {column[0]} ({column[1]}) - {column[2] if column[2] else 'NULL'}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro ao adicionar coluna: {e}")
        db.rollback()
        return False
        
    finally:
        db.close()

def show_unprocessed_incidents():
    """
    Mostra incidentes não processados (para teste).
    """
    db = SessionLocal()
    try:
        result = db.execute(text("""
            SELECT COUNT(*) as total,
                   COUNT(CASE WHEN processed_at IS NULL THEN 1 END) as unprocessed,
                   COUNT(CASE WHEN processed_at IS NOT NULL THEN 1 END) as processed
            FROM zeek_incidents
        """))
        
        stats = result.fetchone()
        logger.info(f"📊 Estatísticas dos incidentes:")
        logger.info(f"  - Total: {stats[0]}")
        logger.info(f"  - Não processados: {stats[1]}")
        logger.info(f"  - Processados: {stats[2]}")
        
        # Mostrar alguns incidentes não processados
        if stats[1] > 0:
            result = db.execute(text("""
                SELECT id, device_ip, incident_type, detected_at, processed_at
                FROM zeek_incidents 
                WHERE processed_at IS NULL 
                ORDER BY detected_at DESC 
                LIMIT 5
            """))
            
            unprocessed = result.fetchall()
            logger.info(f"🔍 Últimos 5 incidentes não processados:")
            for incident in unprocessed:
                logger.info(f"  - ID: {incident[0]}, IP: {incident[1]}, Tipo: {incident[2]}, Detectado: {incident[3]}")
        
    except Exception as e:
        logger.error(f"❌ Erro ao mostrar estatísticas: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    logger.info("🚀 Iniciando migração: Adicionar coluna processed_at")
    
    success = add_processed_at_column()
    
    if success:
        logger.info("✅ Migração concluída com sucesso!")
        show_unprocessed_incidents()
    else:
        logger.error("❌ Migração falhou!")
        sys.exit(1)
