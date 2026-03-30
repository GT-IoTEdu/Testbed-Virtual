"""
Script para verificar e processar incidentes pendentes de bloqueio automático.

Este script pode ser executado manualmente ou agendado para verificar periodicamente
se há incidentes não processados e aplicar bloqueios automáticos.
"""
import sys
import os
from pathlib import Path

# Adicionar o diretório backend ao path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from services_scanners.incident_service import IncidentService

def main():
    """Função principal"""
    print("\n" + "=" * 80)
    print("VERIFICAÇÃO E PROCESSAMENTO DE INCIDENTES PENDENTES")
    print("=" * 80)
    
    service = IncidentService()
    
    # Verificar incidentes não processados
    print("\n📋 Verificando incidentes não processados...")
    unprocessed = service.get_unprocessed_incidents(limit=100)
    
    if not unprocessed:
        print("✅ Nenhum incidente não processado encontrado.")
        return
    
    print(f"\n⚠️  Encontrados {len(unprocessed)} incidente(s) não processado(s):")
    for inc in unprocessed:
        print(f"  - ID: {inc.id}, IP: {inc.device_ip}, Tipo: {inc.incident_type}, Detectado: {inc.detected_at}")
    
    # Processar incidentes
    print(f"\n🚀 Processando incidentes...")
    result = service.process_incidents_for_auto_blocking(limit=100)
    
    print("\n" + "=" * 80)
    print("RESULTADO DO PROCESSAMENTO")
    print("=" * 80)
    print(f"\n📊 Estatísticas:")
    print(f"  - Processados: {result.get('processed_count', 0)}")
    print(f"  - Bloqueados: {result.get('blocked_count', 0)}")
    print(f"  - Ignorados: {result.get('skipped_count', 0)}")
    print(f"  - Erros: {result.get('error_count', 0)}")
    
    if result.get('processed_incidents'):
        print(f"\n📝 Incidentes processados:")
        for inc_info in result['processed_incidents']:
            print(f"  - ID: {inc_info['id']}, IP: {inc_info['device_ip']}, Ação: {inc_info['action']}")
    
    print("\n" + "=" * 80)
    
    if result.get('success'):
        print("✅ Processamento concluído com sucesso!")
    else:
        print(f"❌ Erro no processamento: {result.get('error', 'Erro desconhecido')}")
        sys.exit(1)

if __name__ == "__main__":
    main()

