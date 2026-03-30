#!/usr/bin/env python3
"""
Script para limpeza automática de incidentes antigos já processados.

Este script remove incidentes que já foram processados para bloqueio automático
e são mais antigos que um período especificado, mantendo o banco de dados limpo.
"""

import sys
import os
import logging
from datetime import datetime, timedelta

# Adicionar o diretório backend ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.session import SessionLocal
from sqlalchemy import text

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def cleanup_old_processed_incidents(days_old: int = 30, dry_run: bool = True):
    """
    Remove incidentes processados mais antigos que o período especificado.
    
    Args:
        days_old: Número de dias para considerar incidente como antigo
        dry_run: Se True, apenas mostra o que seria removido sem executar
        
    Returns:
        Dicionário com estatísticas da limpeza
    """
    db = SessionLocal()
    try:
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        logger.info(f"🧹 Iniciando limpeza de incidentes processados mais antigos que {days_old} dias")
        logger.info(f"📅 Data limite: {cutoff_date.strftime('%Y-%m-%d %H:%M:%S')}")
        
        if dry_run:
            logger.info("🔍 Modo DRY RUN - apenas mostrando o que seria removido")
        
        # Contar incidentes que serão removidos
        count_result = db.execute(text("""
            SELECT COUNT(*) as total,
                   COUNT(CASE WHEN incident_type LIKE '%Atacante%' THEN 1 END) as attacker_incidents,
                   COUNT(CASE WHEN incident_type NOT LIKE '%Atacante%' THEN 1 END) as non_attacker_incidents
            FROM zeek_incidents 
            WHERE processed_at IS NOT NULL 
            AND processed_at < :cutoff_date
        """), {'cutoff_date': cutoff_date})
        
        stats = count_result.fetchone()
        total_to_remove = stats[0]
        attacker_to_remove = stats[1]
        non_attacker_to_remove = stats[2]
        
        logger.info(f"📊 Incidentes que seriam removidos:")
        logger.info(f"  - Total: {total_to_remove}")
        logger.info(f"  - Incidentes de atacante: {attacker_to_remove}")
        logger.info(f"  - Outros incidentes: {non_attacker_to_remove}")
        
        if total_to_remove == 0:
            logger.info("✅ Nenhum incidente antigo processado encontrado para remoção")
            return {
                'success': True,
                'removed_count': 0,
                'attacker_removed': 0,
                'non_attacker_removed': 0,
                'dry_run': dry_run,
                'days_old': days_old
            }
        
        if dry_run:
            # Mostrar alguns exemplos do que seria removido
            examples_result = db.execute(text("""
                SELECT id, device_ip, incident_type, processed_at, detected_at
                FROM zeek_incidents 
                WHERE processed_at IS NOT NULL 
                AND processed_at < :cutoff_date
                ORDER BY processed_at ASC
                LIMIT 5
            """), {'cutoff_date': cutoff_date})
            
            examples = examples_result.fetchall()
            logger.info(f"🔍 Exemplos de incidentes que seriam removidos:")
            for incident in examples:
                logger.info(f"  - ID: {incident[0]}, IP: {incident[1]}, Tipo: {incident[2]}, Processado: {incident[3]}")
            
            return {
                'success': True,
                'removed_count': total_to_remove,
                'attacker_removed': attacker_to_remove,
                'non_attacker_removed': non_attacker_to_remove,
                'dry_run': True,
                'days_old': days_old,
                'message': f'DRY RUN: {total_to_remove} incidentes seriam removidos'
            }
        
        # Executar remoção real
        logger.info("🗑️ Executando remoção de incidentes antigos...")
        
        # Remover incidentes processados antigos
        result = db.execute(text("""
            DELETE FROM zeek_incidents 
            WHERE processed_at IS NOT NULL 
            AND processed_at < :cutoff_date
        """), {'cutoff_date': cutoff_date})
        
        removed_count = result.rowcount
        db.commit()
        
        logger.info(f"✅ Remoção concluída: {removed_count} incidentes removidos")
        
        # Verificar se a remoção foi bem-sucedida
        remaining_result = db.execute(text("""
            SELECT COUNT(*) as total,
                   COUNT(CASE WHEN processed_at IS NOT NULL THEN 1 END) as processed,
                   COUNT(CASE WHEN processed_at IS NULL THEN 1 END) as unprocessed
            FROM zeek_incidents
        """))
        
        remaining_stats = remaining_result.fetchone()
        
        logger.info(f"📊 Estado atual da tabela zeek_incidents:")
        logger.info(f"  - Total restante: {remaining_stats[0]}")
        logger.info(f"  - Processados: {remaining_stats[1]}")
        logger.info(f"  - Não processados: {remaining_stats[2]}")
        
        return {
            'success': True,
            'removed_count': removed_count,
            'attacker_removed': attacker_to_remove,
            'non_attacker_removed': non_attacker_to_remove,
            'dry_run': False,
            'days_old': days_old,
            'remaining_total': remaining_stats[0],
            'remaining_processed': remaining_stats[1],
            'remaining_unprocessed': remaining_stats[2],
            'message': f'Limpeza concluída: {removed_count} incidentes removidos'
        }
        
    except Exception as e:
        logger.error(f"❌ Erro na limpeza: {e}")
        db.rollback()
        return {
            'success': False,
            'error': str(e),
            'removed_count': 0,
            'dry_run': dry_run
        }
        
    finally:
        db.close()

def show_current_stats():
    """
    Mostra estatísticas atuais da tabela zeek_incidents.
    """
    db = SessionLocal()
    try:
        # Estatísticas gerais
        result = db.execute(text("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN processed_at IS NOT NULL THEN 1 END) as processed,
                COUNT(CASE WHEN processed_at IS NULL THEN 1 END) as unprocessed,
                COUNT(CASE WHEN incident_type LIKE '%Atacante%' THEN 1 END) as attacker_total,
                COUNT(CASE WHEN incident_type LIKE '%Atacante%' AND processed_at IS NOT NULL THEN 1 END) as attacker_processed,
                COUNT(CASE WHEN incident_type LIKE '%Atacante%' AND processed_at IS NULL THEN 1 END) as attacker_unprocessed
            FROM zeek_incidents
        """))
        
        stats = result.fetchone()
        
        logger.info(f"📊 Estatísticas atuais da tabela zeek_incidents:")
        logger.info(f"  - Total de incidentes: {stats[0]}")
        logger.info(f"  - Processados: {stats[1]}")
        logger.info(f"  - Não processados: {stats[2]}")
        logger.info(f"  - Incidentes de atacante (total): {stats[3]}")
        logger.info(f"  - Incidentes de atacante (processados): {stats[4]}")
        logger.info(f"  - Incidentes de atacante (não processados): {stats[5]}")
        
        # Incidentes processados por idade
        result = db.execute(text("""
            SELECT 
                CASE 
                    WHEN processed_at >= DATE_SUB(NOW(), INTERVAL 1 DAY) THEN 'Últimas 24h'
                    WHEN processed_at >= DATE_SUB(NOW(), INTERVAL 7 DAY) THEN 'Últimos 7 dias'
                    WHEN processed_at >= DATE_SUB(NOW(), INTERVAL 30 DAY) THEN 'Últimos 30 dias'
                    ELSE 'Mais de 30 dias'
                END as age_group,
                COUNT(*) as count
            FROM zeek_incidents 
            WHERE processed_at IS NOT NULL
            GROUP BY age_group
            ORDER BY 
                CASE 
                    WHEN age_group = 'Últimas 24h' THEN 1
                    WHEN age_group = 'Últimos 7 dias' THEN 2
                    WHEN age_group = 'Últimos 30 dias' THEN 3
                    ELSE 4
                END
        """))
        
        age_groups = result.fetchall()
        
        logger.info(f"📅 Incidentes processados por idade:")
        for age_group in age_groups:
            logger.info(f"  - {age_group[0]}: {age_group[1]}")
        
    except Exception as e:
        logger.error(f"❌ Erro ao mostrar estatísticas: {e}")
    finally:
        db.close()

def main():
    """
    Função principal do script.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Limpeza de incidentes processados antigos')
    parser.add_argument('--days', type=int, default=30, 
                       help='Número de dias para considerar incidente como antigo (padrão: 30)')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Apenas mostra o que seria removido sem executar')
    parser.add_argument('--stats', action='store_true', 
                       help='Apenas mostra estatísticas atuais')
    
    args = parser.parse_args()
    
    if args.stats:
        logger.info("📊 Mostrando estatísticas atuais...")
        show_current_stats()
        return
    
    logger.info(f"🚀 Iniciando script de limpeza de incidentes")
    logger.info(f"📅 Parâmetros: {args.days} dias, dry_run={args.dry_run}")
    
    # Mostrar estatísticas antes
    logger.info("📊 Estatísticas ANTES da limpeza:")
    show_current_stats()
    
    # Executar limpeza
    result = cleanup_old_processed_incidents(args.days, args.dry_run)
    
    if result['success']:
        logger.info(f"✅ {result['message']}")
        
        if not args.dry_run:
            logger.info("📊 Estatísticas APÓS a limpeza:")
            show_current_stats()
    else:
        logger.error(f"❌ Erro na limpeza: {result.get('error', 'Erro desconhecido')}")
        sys.exit(1)

if __name__ == "__main__":
    main()
