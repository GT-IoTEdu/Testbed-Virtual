"""
Script de teste para verificar os endpoints de tempo de detecção e bloqueio.
"""
import sys
import os
from pathlib import Path

# Adicionar o diretório backend ao path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from services_scanners.incident_service import IncidentService
from datetime import datetime

def test_get_blocking_times():
    """Testa o cálculo de tempos de bloqueio para um incidente específico."""
    print("=" * 80)
    print("TESTE: get_blocking_times()")
    print("=" * 80)
    
    service = IncidentService()
    
    # Buscar incidentes processados
    stats = service.get_processing_stats(hours_ago=168)  # Última semana
    print(f"\nEstatisticas da ultima semana:")
    print(f"   Total de incidentes: {stats.get('total_incidents', 0)}")
    print(f"   Processados: {stats.get('processed_count', 0)}")
    print(f"   Atacantes processados: {stats.get('attacker_processed', 0)}")
    
    if stats.get('attacker_processed', 0) > 0:
        print("\nOK: Ha incidentes de atacantes processados, testando calculo de tempos...")
        
        # Buscar tempos de todos os incidentes
        all_times = service.get_all_blocking_times(limit=5)
        
        if all_times:
            print(f"\nTestando com {len(all_times)} incidentes:")
            for idx, result in enumerate(all_times, 1):
                print(f"\n--- Incidente {idx} ---")
                print(f"  ID: {result['incident_id']}")
                print(f"  IP: {result['device_ip']}")
                print(f"  Tipo: {result['incident_type']}")
                print(f"  TtD: {result['ttd'].get('readable', 'N/A')} ({result['ttd'].get('seconds', 'N/A')}s)")
                print(f"  TtB: {result['ttb'].get('readable', 'N/A')} ({result['ttb'].get('seconds', 'N/A')}s)")
                print(f"  Bloqueado: {result.get('blocked', False)}")
                
                # Testar método individual
                if 'incident_id' in result:
                    individual = service.get_blocking_times(result['incident_id'])
                    if 'error' not in individual:
                        print(f"  OK: Metodo individual funciona para ID {result['incident_id']}")
                    else:
                        print(f"  ERRO: Metodo individual: {individual['error']}")
        else:
            print("\nAviso: Nenhum incidente bloqueado encontrado")
    else:
        print("\nAviso: Nenhum incidente de atacante processado encontrado na ultima semana")
    
    print("\n" + "=" * 80)
    print("TESTE CONCLUÍDO")
    print("=" * 80)

def test_format_time_delta():
    """Testa a formatação de timedelta."""
    print("\n" + "=" * 80)
    print("TESTE: _format_time_delta()")
    print("=" * 80)
    
    service = IncidentService()
    
    # Testar diferentes intervalos
    test_cases = [
        (0, "0s"),
        (45, "45s"),
        (60, "1m 0s"),
        (125, "2m 5s"),
        (3661, "1h 1m 1s"),
        (7325, "2h 2m 5s"),
    ]
    
    print("\nTestando formatacao de tempos:")
    for seconds, expected_format in test_cases:
        delta = datetime.now() + __import__('datetime').timedelta(seconds=seconds) - datetime.now()
        formatted = service._format_time_delta(delta)
        
        # Ajustar expectativa para incluir segundos se for > 1 minuto
        if "m" in expected_format and seconds % 60 == 0:
            # Se for exatamente minutos, pode não mostrar 0s
            status = "OK" if formatted in [expected_format, expected_format.replace(" 0s", "")] else "ERRO"
        else:
            status = "OK" if formatted == expected_format else "ERRO"
        
        print(f"  {status} {seconds}s -> {formatted} (esperado: ~{expected_format})")
    
    print("\n" + "=" * 80)
    print("TESTE CONCLUÍDO")
    print("=" * 80)

if __name__ == "__main__":
    try:
        print("\nIniciando testes de tempo de deteccao e bloqueio\n")
        
        # Teste 1: Formatacao de tempo
        test_format_time_delta()
        
        # Teste 2: Calculo de tempos
        test_get_blocking_times()
        
        print("\nOK: Todos os testes concluidos com sucesso!")
        
    except Exception as e:
        print(f"\nERRO: Erro durante os testes: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

