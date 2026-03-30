"""
Script para validar os tempos de bloqueio calculando a média entre múltiplas execuções.
"""
import sys
import os
from pathlib import Path

# Adicionar o diretório backend ao path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from services_scanners.incident_service import IncidentService
from statistics import mean, median, stdev

def calculate_averages(times_list):
    """Calcula estatisticas de uma lista de tempos."""
    if not times_list:
        return None
    
    return {
        'count': len(times_list),
        'mean': mean(times_list),
        'median': median(times_list),
        'stdev': stdev(times_list) if len(times_list) > 1 else 0,
        'min': min(times_list),
        'max': max(times_list)
    }

def format_statistics(stats):
    """Formata estatisticas para exibicao."""
    if not stats:
        return "N/A"
    
    return (
        f"n={stats['count']}, "
        f"media={stats['mean']:.3f}s, "
        f"mediana={stats['median']:.3f}s, "
        f"desvio={stats['stdev']:.3f}s, "
        f"min={stats['min']:.3f}s, "
        f"max={stats['max']:.3f}s"
    )

def test_average_blocking_times(num_executions=10):
    """
    Executa multiplas vezes o calculo de tempos e calcula as medias.
    
    Args:
        num_executions: Numero de execucoes para calcular a media
    """
    print("=" * 80)
    print(f"VALIDACAO: Media entre {num_executions} execucoes")
    print("=" * 80)
    
    service = IncidentService()
    
    # Listas para armazenar resultados de cada execucao
    all_ttd_times = []
    all_ttb_times = []
    all_counts = []
    
    print(f"\nExecutando {num_executions} vezes o calculo de tempos de bloqueio...")
    
    for execution in range(1, num_executions + 1):
        print(f"\nExecucao {execution}/{num_executions}...")
        
        try:
            # Buscar tempos de todos os incidentes
            results = service.get_all_blocking_times(limit=100)
            
            if results:
                # Filtrar apenas os que tem bloqueio e tempos validos
                blocked = [inc for inc in results if inc.get('blocked')]
                ttd_valid = [inc['ttd']['seconds'] for inc in blocked 
                            if inc.get('ttd') and inc['ttd'].get('seconds') is not None]
                ttb_valid = [inc['ttb']['seconds'] for inc in blocked 
                            if inc.get('ttb') and inc['ttb'].get('seconds') is not None]
                
                all_ttd_times.extend(ttd_valid)
                all_ttb_times.extend(ttb_valid)
                all_counts.append(len(blocked))
                
                print(f"  - Incidentes bloqueados: {len(blocked)}")
                print(f"  - TtD validos: {len(ttd_valid)}")
                print(f"  - TtB validos: {len(ttb_valid)}")
                
                if ttd_valid:
                    print(f"  - TtD nesta execucao: media={mean(ttd_valid):.3f}s, "
                          f"min={min(ttd_valid):.3f}s, max={max(ttd_valid):.3f}s")
                if ttb_valid:
                    print(f"  - TtB nesta execucao: media={mean(ttb_valid):.3f}s, "
                          f"min={min(ttb_valid):.3f}s, max={max(ttb_valid):.3f}s")
            else:
                print("  - Nenhum incidente encontrado")
                all_counts.append(0)
                
        except Exception as e:
            print(f"  ERRO na execucao {execution}: {e}")
            all_counts.append(0)
    
    # Calcular estatisticas agregadas
    print("\n" + "=" * 80)
    print("ESTATISTICAS FINAIS (Todas as execucoes combinadas)")
    print("=" * 80)
    
    if all_ttd_times:
        ttd_stats = calculate_averages(all_ttd_times)
        print(f"\nTtD (Time to Detection):")
        print(f"  {format_statistics(ttd_stats)}")
    else:
        print("\nTtD: Nenhum dado valido encontrado")
    
    if all_ttb_times:
        ttb_stats = calculate_averages(all_ttb_times)
        print(f"\nTtB (Time to Block):")
        print(f"  {format_statistics(ttb_stats)}")
    else:
        print("\nTtB: Nenhum dado valido encontrado")
    
    if all_counts:
        count_stats = calculate_averages(all_counts)
        print(f"\nNumero de incidentes por execucao:")
        print(f"  {format_statistics(count_stats)}")
    
    print("\n" + "=" * 80)
    
    # Avaliacao de performance
    print("\nAVALIACAO DE PERFORMANCE:")
    print("=" * 80)
    
    if all_ttd_times:
        avg_ttd = mean(all_ttd_times)
        if avg_ttd < 5:
            status = "EXCELENTE"
        elif avg_ttd < 30:
            status = "BOA"
        else:
            status = "NECESSITA OTIMIZACAO"
        
        print(f"\nTtD medio: {avg_ttd:.3f}s - Status: {status}")
    
    if all_ttb_times:
        avg_ttb = mean(all_ttb_times)
        if avg_ttb < 10:
            status = "EXCELENTE"
        elif avg_ttb < 60:
            status = "BOA"
        else:
            status = "NECESSITA OTIMIZACAO"
        
        print(f"\nTtB medio: {avg_ttb:.3f}s - Status: {status}")
    
    print("\n" + "=" * 80)
    print("VALIDACAO CONCLUIDA")
    print("=" * 80)
    
    return {
        'ttd_stats': calculate_averages(all_ttd_times) if all_ttd_times else None,
        'ttb_stats': calculate_averages(all_ttb_times) if all_ttb_times else None,
        'count_stats': calculate_averages(all_counts) if all_counts else None
    }

def compare_executions(num_executions=5):
    """
    Compara cada execucao individualmente para verificar consistencia.
    
    Args:
        num_executions: Numero de execucoes para comparar
    """
    print("\n" + "=" * 80)
    print(f"COMPARACAO INDIVIDUAL: {num_executions} execucoes")
    print("=" * 80)
    
    service = IncidentService()
    
    execution_stats = []
    
    for execution in range(1, num_executions + 1):
        print(f"\nExecucao {execution}:")
        
        try:
            results = service.get_all_blocking_times(limit=100)
            
            if results:
                blocked = [inc for inc in results if inc.get('blocked')]
                ttd_times = [inc['ttd']['seconds'] for inc in blocked 
                            if inc.get('ttd') and inc['ttd'].get('seconds') is not None]
                ttb_times = [inc['ttb']['seconds'] for inc in blocked 
                            if inc.get('ttb') and inc['ttb'].get('seconds') is not None]
                
                stats = {
                    'execution': execution,
                    'count': len(blocked),
                    'ttd_mean': mean(ttd_times) if ttd_times else None,
                    'ttb_mean': mean(ttb_times) if ttb_times else None,
                    'ttd_count': len(ttd_times),
                    'ttb_count': len(ttb_times)
                }
                
                execution_stats.append(stats)
                
                print(f"  Incidentes: {stats['count']}")
                if stats['ttd_mean']:
                    print(f"  TtD medio: {stats['ttd_mean']:.3f}s (n={stats['ttd_count']})")
                if stats['ttb_mean']:
                    print(f"  TtB medio: {stats['ttb_mean']:.3f}s (n={stats['ttb_count']})")
            else:
                print("  Nenhum dado encontrado")
                
        except Exception as e:
            print(f"  ERRO: {e}")
    
    # Mostrar variacao entre execucoes
    if execution_stats:
        print("\n" + "=" * 80)
        print("VARIACAO ENTRE EXECUCOES:")
        print("=" * 80)
        
        ttd_means = [s['ttd_mean'] for s in execution_stats if s['ttd_mean'] is not None]
        ttb_means = [s['ttb_mean'] for s in execution_stats if s['ttb_mean'] is not None]
        
        if ttd_means:
            print(f"\nTtD medio varia de {min(ttd_means):.3f}s ate {max(ttd_means):.3f}s")
            if len(ttd_means) > 1:
                print(f"  Desvio padrao: {stdev(ttd_means):.3f}s")
        
        if ttb_means:
            print(f"\nTtB medio varia de {min(ttb_means):.3f}s ate {max(ttb_means):.3f}s")
            if len(ttb_means) > 1:
                print(f"  Desvio padrao: {stdev(ttb_means):.3f}s")

if __name__ == "__main__":
    try:
        print("\n" + "=" * 80)
        print("VALIDACAO DE TEMPOS DE BLOQUEIO")
        print("=" * 80)
        
        # Teste 1: Media entre 10 execucoes
        test_average_blocking_times(num_executions=10)
        
        # Teste 2: Comparacao individual entre 5 execucoes
        compare_executions(num_executions=5)
        
        print("\n" + "=" * 80)
        print("TODOS OS TESTES CONCLUIDOS COM SUCESSO!")
        print("=" * 80 + "\n")
        
    except Exception as e:
        print(f"\nERRO: Erro durante os testes: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

