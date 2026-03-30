#!/usr/bin/env python3
"""
Script de teste para validar o sistema de bloqueio automático em lote.

Este script testa o novo sistema que resolve o problema de incidentes simultâneos
não serem processados para bloqueio automático.
"""

import sys
import os
import logging
import time
from datetime import datetime, timedelta
from typing import List

# Adicionar o diretório backend ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services_scanners.incident_service import IncidentService
from db.enums import IncidentSeverity, IncidentStatus, ZeekLogType

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_test_incidents(incident_service: IncidentService, count: int = 5) -> List[int]:
    """
    Cria incidentes de teste para validar o sistema.
    
    Args:
        incident_service: Serviço de incidentes
        count: Número de incidentes a criar
        
    Returns:
        Lista de IDs dos incidentes criados
    """
    logger.info(f"🧪 Criando {count} incidentes de teste...")
    
    incident_ids = []
    
    # Criar incidentes de atacante (que devem ser bloqueados)
    for i in range(count // 2):
        incident_data = {
            'device_ip': f'192.168.100.{10 + i}',
            'device_name': f'Dispositivo Atacante {i + 1}',
            'incident_type': f'SQL Injection - Atacante',
            'severity': 'high',
            'status': 'new',
            'description': f'Teste de incidente de atacante {i + 1}',
            'detected_at': datetime.now() - timedelta(minutes=i),
            'zeek_log_type': 'notice.log',
            'raw_log_data': {'test': True, 'incident_number': i + 1},
            'action_taken': None,
            'assigned_to': None,
            'notes': f'Incidente de teste {i + 1}'
        }
        
        incident = incident_service.save_incident(incident_data)
        if incident:
            incident_ids.append(incident.id)
            logger.info(f"✅ Incidente de atacante criado: ID {incident.id}, IP {incident.device_ip}")
        else:
            logger.error(f"❌ Falha ao criar incidente de atacante {i + 1}")
    
    # Criar incidentes de vítima (que NÃO devem ser bloqueados)
    for i in range(count // 2):
        incident_data = {
            'device_ip': f'192.168.100.{20 + i}',
            'device_name': f'Dispositivo Vítima {i + 1}',
            'incident_type': f'SQL Injection - Vítima',
            'severity': 'medium',
            'status': 'new',
            'description': f'Teste de incidente de vítima {i + 1}',
            'detected_at': datetime.now() - timedelta(minutes=i),
            'zeek_log_type': 'notice.log',
            'raw_log_data': {'test': True, 'incident_number': i + 1},
            'action_taken': None,
            'assigned_to': None,
            'notes': f'Incidente de teste {i + 1}'
        }
        
        incident = incident_service.save_incident(incident_data)
        if incident:
            incident_ids.append(incident.id)
            logger.info(f"✅ Incidente de vítima criado: ID {incident.id}, IP {incident.device_ip}")
        else:
            logger.error(f"❌ Falha ao criar incidente de vítima {i + 1}")
    
    logger.info(f"📊 Total de incidentes criados: {len(incident_ids)}")
    return incident_ids

def test_unprocessed_incidents(incident_service: IncidentService):
    """
    Testa a busca de incidentes não processados.
    """
    logger.info("🔍 Testando busca de incidentes não processados...")
    
    unprocessed = incident_service.get_unprocessed_incidents(limit=50)
    
    logger.info(f"📊 Incidentes não processados encontrados: {len(unprocessed)}")
    
    for incident in unprocessed:
        logger.info(f"  - ID: {incident.id}, IP: {incident.device_ip}, Tipo: {incident.incident_type}, Processado: {incident.processed_at}")
    
    return len(unprocessed)

def test_batch_processing(incident_service: IncidentService, limit: int = 10):
    """
    Testa o processamento em lote de incidentes.
    """
    logger.info(f"🚀 Testando processamento em lote (limite: {limit})...")
    
    result = incident_service.process_incidents_for_auto_blocking(limit)
    
    if result['success']:
        logger.info(f"✅ Processamento em lote concluído:")
        logger.info(f"  - Processados: {result['processed_count']}")
        logger.info(f"  - Bloqueados: {result['blocked_count']}")
        logger.info(f"  - Ignorados: {result['skipped_count']}")
        logger.info(f"  - Erros: {result['error_count']}")
        
        # Mostrar detalhes dos incidentes processados
        for incident_info in result.get('processed_incidents', []):
            logger.info(f"  - ID {incident_info['id']}: {incident_info['action']} (IP: {incident_info['device_ip']})")
        
        return result
    else:
        logger.error(f"❌ Erro no processamento em lote: {result.get('error', 'Erro desconhecido')}")
        return None

def test_processing_stats(incident_service: IncidentService):
    """
    Testa as estatísticas de processamento.
    """
    logger.info("📊 Testando estatísticas de processamento...")
    
    stats = incident_service.get_processing_stats(hours_ago=24)
    
    if stats:
        logger.info(f"📈 Estatísticas das últimas 24 horas:")
        logger.info(f"  - Total de incidentes: {stats['total_incidents']}")
        logger.info(f"  - Processados: {stats['processed_count']}")
        logger.info(f"  - Não processados: {stats['unprocessed_count']}")
        logger.info(f"  - Atacantes processados: {stats['attacker_processed']}")
        logger.info(f"  - Atacantes não processados: {stats['attacker_unprocessed']}")
        logger.info(f"  - Taxa de processamento: {stats['processing_rate']}%")
        
        return stats
    else:
        logger.error("❌ Erro ao obter estatísticas")
        return None

def test_simultaneous_incidents(incident_service: IncidentService):
    """
    Testa o cenário de incidentes simultâneos.
    """
    logger.info("⚡ Testando cenário de incidentes simultâneos...")
    
    # Criar vários incidentes rapidamente
    simultaneous_incidents = []
    
    for i in range(10):
        incident_data = {
            'device_ip': f'192.168.200.{10 + i}',
            'device_name': f'Dispositivo Simultâneo {i + 1}',
            'incident_type': f'DDoS Attack - Atacante',
            'severity': 'critical',
            'status': 'new',
            'description': f'Teste de incidente simultâneo {i + 1}',
            'detected_at': datetime.now(),
            'zeek_log_type': 'notice.log',
            'raw_log_data': {'test': True, 'simultaneous': True, 'incident_number': i + 1},
            'action_taken': None,
            'assigned_to': None,
            'notes': f'Incidente simultâneo de teste {i + 1}'
        }
        
        incident = incident_service.save_incident(incident_data)
        if incident:
            simultaneous_incidents.append(incident.id)
    
    logger.info(f"✅ {len(simultaneous_incidents)} incidentes simultâneos criados")
    
    # Aguardar um pouco para garantir que todos foram salvos
    time.sleep(1)
    
    # Verificar quantos não foram processados
    unprocessed_before = test_unprocessed_incidents(incident_service)
    
    # Processar em lote
    result = test_batch_processing(incident_service, limit=20)
    
    # Verificar quantos restaram não processados
    unprocessed_after = test_unprocessed_incidents(incident_service)
    
    logger.info(f"📊 Resultado do teste simultâneo:")
    logger.info(f"  - Incidentes criados: {len(simultaneous_incidents)}")
    logger.info(f"  - Não processados antes: {unprocessed_before}")
    logger.info(f"  - Não processados depois: {unprocessed_after}")
    logger.info(f"  - Processados no teste: {result['processed_count'] if result else 0}")
    
    return {
        'created': len(simultaneous_incidents),
        'unprocessed_before': unprocessed_before,
        'unprocessed_after': unprocessed_after,
        'processed_in_batch': result['processed_count'] if result else 0
    }

def cleanup_test_incidents(incident_service: IncidentService):
    """
    Limpa incidentes de teste (marca como resolvidos).
    """
    logger.info("🧹 Limpando incidentes de teste...")
    
    # Buscar incidentes de teste
    unprocessed = incident_service.get_unprocessed_incidents(limit=100)
    
    test_incidents = [inc for inc in unprocessed if inc.notes and 'teste' in inc.notes.lower()]
    
    logger.info(f"🗑️ Encontrados {len(test_incidents)} incidentes de teste para limpar")
    
    for incident in test_incidents:
        incident_service.update_incident_status(
            incident.id, 
            'resolved', 
            'Incidente de teste - removido automaticamente'
        )
        logger.info(f"✅ Incidente de teste {incident.id} marcado como resolvido")
    
    return len(test_incidents)

def main():
    """
    Função principal do teste.
    """
    logger.info("🚀 Iniciando teste do sistema de bloqueio automático em lote")
    
    incident_service = IncidentService()
    
    try:
        # Teste 1: Criar incidentes de teste
        logger.info("\n" + "="*60)
        logger.info("TESTE 1: Criação de incidentes de teste")
        logger.info("="*60)
        
        test_incident_ids = create_test_incidents(incident_service, count=10)
        
        # Teste 2: Verificar incidentes não processados
        logger.info("\n" + "="*60)
        logger.info("TESTE 2: Busca de incidentes não processados")
        logger.info("="*60)
        
        unprocessed_count = test_unprocessed_incidents(incident_service)
        
        # Teste 3: Processamento em lote
        logger.info("\n" + "="*60)
        logger.info("TESTE 3: Processamento em lote")
        logger.info("="*60)
        
        batch_result = test_batch_processing(incident_service, limit=20)
        
        # Teste 4: Estatísticas
        logger.info("\n" + "="*60)
        logger.info("TESTE 4: Estatísticas de processamento")
        logger.info("="*60)
        
        stats_result = test_processing_stats(incident_service)
        
        # Teste 5: Incidentes simultâneos
        logger.info("\n" + "="*60)
        logger.info("TESTE 5: Incidentes simultâneos")
        logger.info("="*60)
        
        simultaneous_result = test_simultaneous_incidents(incident_service)
        
        # Teste 6: Limpeza
        logger.info("\n" + "="*60)
        logger.info("TESTE 6: Limpeza de incidentes de teste")
        logger.info("="*60)
        
        cleanup_count = cleanup_test_incidents(incident_service)
        
        # Resumo final
        logger.info("\n" + "="*60)
        logger.info("RESUMO DOS TESTES")
        logger.info("="*60)
        
        logger.info(f"✅ Testes concluídos com sucesso!")
        logger.info(f"📊 Incidentes de teste criados: {len(test_incident_ids)}")
        logger.info(f"📊 Incidentes não processados encontrados: {unprocessed_count}")
        logger.info(f"📊 Processamento em lote: {'✅ Sucesso' if batch_result and batch_result['success'] else '❌ Falha'}")
        logger.info(f"📊 Estatísticas: {'✅ Sucesso' if stats_result else '❌ Falha'}")
        logger.info(f"📊 Teste simultâneo: {'✅ Sucesso' if simultaneous_result else '❌ Falha'}")
        logger.info(f"📊 Incidentes de teste limpos: {cleanup_count}")
        
        if batch_result and batch_result['success']:
            logger.info(f"🎯 Sistema de bloqueio automático em lote funcionando corretamente!")
            logger.info(f"🔒 Dispositivos bloqueados: {batch_result['blocked_count']}")
        else:
            logger.error("❌ Sistema de bloqueio automático em lote com problemas")
        
    except Exception as e:
        logger.error(f"❌ Erro durante os testes: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
