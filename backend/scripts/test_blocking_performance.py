#!/usr/bin/env python3
"""
Script de Teste de Performance - Sistema de Detecção e Bloqueio Automático

Este script monitora e mede:
- Tempo de execução de cada endpoint/operação envolvida
- Consumo de CPU e RAM em cada etapa
- Timestamp de cada operação
- Gera relatório detalhado de performance
"""

import sys
import os
import time
import psutil
import requests
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

# Adicionar o diretório backend ao path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from dotenv import load_dotenv
load_dotenv()

@dataclass
class PerformanceMetric:
    """Métrica de performance de uma operação"""
    timestamp: str
    function_name: str
    endpoint: str
    route: str
    duration_seconds: float
    cpu_percent: float
    cpu_system_percent: float
    ram_mb: float
    ram_percent: float
    ram_system_percent: float
    ram_system_available_mb: float
    success: bool
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class PerformanceMonitor:
    """Monitor de performance do sistema"""
    
    def __init__(self):
        self.process = psutil.Process(os.getpid())
        self.metrics: List[PerformanceMetric] = []
        self.base_url = os.getenv("API_URL", "http://localhost:8000")
        self.api_token = os.getenv("API_TOKEN", "")
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
        
    def get_system_metrics(self) -> Dict[str, Any]:
        """Obtém métricas atuais do sistema"""
        try:
            # Métricas do processo
            cpu_percent = self.process.cpu_percent(interval=0.1)
            ram_info = self.process.memory_info()
            ram_mb = ram_info.rss / (1024 * 1024)
            ram_percent = self.process.memory_percent()
            
            # Métricas do sistema
            cpu_system = psutil.cpu_percent(interval=0.1)
            ram_system = psutil.virtual_memory()
            ram_system_percent = ram_system.percent
            ram_system_available_mb = ram_system.available / (1024 * 1024)
            
            return {
                "cpu_percent": cpu_percent,
                "cpu_system_percent": cpu_system,
                "ram_mb": ram_mb,
                "ram_percent": ram_percent,
                "ram_system_percent": ram_system_percent,
                "ram_system_available_mb": ram_system_available_mb
            }
        except Exception as e:
            print(f"⚠️ Erro ao obter métricas: {e}")
            return {
                "cpu_percent": 0.0,
                "cpu_system_percent": 0.0,
                "ram_mb": 0.0,
                "ram_percent": 0.0,
                "ram_system_percent": 0.0,
                "ram_system_available_mb": 0.0
            }
    
    def measure_operation(self, function_name: str, endpoint: str, route: str, 
                         operation_func, *args, **kwargs) -> PerformanceMetric:
        """Mede o tempo e recursos de uma operação"""
        timestamp_start = datetime.now()
        start_metrics = self.get_system_metrics()
        
        success = False
        error = None
        metadata = {}
        
        try:
            # Executar operação
            result = operation_func(*args, **kwargs)
            
            timestamp_end = datetime.now()
            duration = (timestamp_end - timestamp_start).total_seconds()
            
            end_metrics = self.get_system_metrics()
            
            # Usar métricas do final (mais representativas)
            success = True
            if isinstance(result, dict):
                metadata = result
            elif result is not None:
                metadata = {"result": str(result)}
                
        except Exception as e:
            timestamp_end = datetime.now()
            duration = (timestamp_end - timestamp_start).total_seconds()
            end_metrics = self.get_system_metrics()
            error = str(e)
            success = False
        
        metric = PerformanceMetric(
            timestamp=timestamp_start.isoformat(),
            function_name=function_name,
            endpoint=endpoint,
            route=route,
            duration_seconds=duration,
            cpu_percent=end_metrics["cpu_percent"],
            cpu_system_percent=end_metrics["cpu_system_percent"],
            ram_mb=end_metrics["ram_mb"],
            ram_percent=end_metrics["ram_percent"],
            ram_system_percent=end_metrics["ram_system_percent"],
            ram_system_available_mb=end_metrics["ram_system_available_mb"],
            success=success,
            error=error,
            metadata=metadata
        )
        
        self.metrics.append(metric)
        return metric
    
    def test_zeek_logs(self):
        """Testa busca de logs do Zeek"""
        def operation():
            url = f"{self.base_url}/api/scanners/zeek/logs"
            params = {
                "logfile": "notice.log",
                "maxlines": 100
            }
            response = requests.get(url, params=params, headers=self.headers, timeout=30)
            response.raise_for_status()
            return response.json()
        
        return self.measure_operation(
            "ZeekService.get_logs",
            "GET /api/scanners/zeek/logs",
            "/api/scanners/zeek/logs?logfile=notice.log&maxlines=100",
            operation
        )
    
    def test_save_incident(self, incident_data: Dict[str, Any]):
        """Testa salvamento de incidente"""
        def operation():
            url = f"{self.base_url}/api/incidents/"
            response = requests.post(url, json=incident_data, headers=self.headers, timeout=30)
            response.raise_for_status()
            return response.json()
        
        return self.measure_operation(
            "IncidentService.save_incident",
            "POST /api/incidents/",
            "/api/incidents/",
            operation
        )
    
    def test_process_batch(self, limit: int = 10):
        """Testa processamento em lote"""
        def operation():
            url = f"{self.base_url}/api/incidents/process-batch"
            params = {"limit": limit}
            response = requests.post(url, params=params, headers=self.headers, timeout=60)
            response.raise_for_status()
            return response.json()
        
        return self.measure_operation(
            "IncidentService.process_incidents_for_auto_blocking",
            "POST /api/incidents/process-batch",
            f"/api/incidents/process-batch?limit={limit}",
            operation
        )
    
    def test_get_alias(self, alias_name: str):
        """Testa busca de alias"""
        def operation():
            url = f"{self.base_url}/api/devices/aliases-db/{alias_name}"
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            return response.json()
        
        return self.measure_operation(
            "AliasService.get_alias_by_name",
            f"GET /api/devices/aliases-db/{alias_name}",
            f"/api/devices/aliases-db/{alias_name}",
            operation
        )
    
    def test_update_alias(self, alias_name: str, update_data: Dict[str, Any]):
        """Testa atualização de alias"""
        def operation():
            url = f"{self.base_url}/api/devices/aliases-db/{alias_name}"
            response = requests.patch(url, json=update_data, headers=self.headers, timeout=30)
            response.raise_for_status()
            return response.json()
        
        return self.measure_operation(
            "AliasService.update_alias",
            f"PATCH /api/devices/aliases-db/{alias_name}",
            f"/api/devices/aliases-db/{alias_name}",
            operation
        )
    
    def test_add_addresses_to_alias(self, alias_name: str, addresses: List[Dict[str, Any]]):
        """Testa adição de endereços ao alias"""
        def operation():
            url = f"{self.base_url}/api/devices/aliases-db/{alias_name}/add-addresses"
            response = requests.post(url, json={"addresses": addresses}, headers=self.headers, timeout=30)
            response.raise_for_status()
            return response.json()
        
        return self.measure_operation(
            "AliasService.add_addresses_to_alias",
            f"POST /api/devices/aliases-db/{alias_name}/add-addresses",
            f"/api/devices/aliases-db/{alias_name}/add-addresses",
            operation
        )
    
    def test_apply_firewall(self):
        """Testa aplicação de mudanças no firewall"""
        def operation():
            url = f"{self.base_url}/api/devices/firewall/apply"
            response = requests.post(url, headers=self.headers, timeout=60)
            response.raise_for_status()
            return response.json()
        
        return self.measure_operation(
            "pfsense_client.aplicar_mudancas_firewall_pfsense",
            "POST /api/devices/firewall/apply",
            "/api/devices/firewall/apply",
            operation
        )
    
    def test_auto_block(self, incident_id: int):
        """Testa bloqueio automático direto"""
        def operation():
            url = f"{self.base_url}/api/incidents/auto-block"
            data = {"incident_id": incident_id}
            response = requests.post(url, json=data, headers=self.headers, timeout=60)
            response.raise_for_status()
            return response.json()
        
        return self.measure_operation(
            "IncidentService._apply_auto_block",
            "POST /api/incidents/auto-block",
            "/api/incidents/auto-block",
            operation
        )
    
    def run_full_blocking_test(self, test_ip: str = "192.168.59.4"):
        """Executa teste completo do processo de bloqueio automático"""
        print("\n" + "=" * 80)
        print("🚀 INICIANDO TESTE DE PERFORMANCE - BLOQUEIO AUTOMÁTICO")
        print("=" * 80)
        print(f"Timestamp Início: {datetime.now().isoformat()}")
        print(f"IP de Teste: {test_ip}")
        print(f"Base URL: {self.base_url}")
        print()
        
        total_start = datetime.now()
        
        # 1. Buscar logs do Zeek (simula monitor)
        print("📋 [1/6] Buscando logs do Zeek...")
        zeek_metric = self.test_zeek_logs()
        self.print_metric(zeek_metric)
        
        # 2. Criar incidente de teste
        print("\n📋 [2/6] Criando incidente de teste...")
        incident_data = {
            "device_ip": test_ip,
            "device_name": "Dispositivo de Teste",
            "incident_type": "SQL Injection - Atacante",
            "severity": "critical",
            "status": "new",
            "description": "Teste de performance - Bloqueio automático",
            "detected_at": datetime.now().isoformat(),
            "zeek_log_type": "notice.log"
        }
        incident_metric = self.test_save_incident(incident_data)
        self.print_metric(incident_metric)
        
        # Obter ID do incidente criado
        incident_id = None
        if incident_metric.success and incident_metric.metadata:
            incident_id = incident_metric.metadata.get("id")
            print(f"   ✅ Incidente criado com ID: {incident_id}")
        
        # Aguardar processamento automático (se houver)
        if incident_id:
            print("\n⏳ Aguardando processamento automático em background (5s)...")
            time.sleep(5)
        
        # 3. Processar incidente em lote (caso não tenha sido processado automaticamente)
        print("\n📋 [3/6] Processando incidentes em lote...")
        batch_metric = self.test_process_batch(limit=10)
        self.print_metric(batch_metric)
        
        # 4. Verificar alias Bloqueados
        print("\n📋 [4/6] Verificando alias Bloqueados...")
        blocked_metric = self.test_get_alias("Bloqueados")
        self.print_metric(blocked_metric)
        
        # 5. Se necessário, adicionar IP ao alias Bloqueados manualmente
        if blocked_metric.success:
            print("\n📋 [5/6] Adicionando IP ao alias Bloqueados...")
            addresses = [{"address": test_ip, "detail": "Teste de performance"}]
            add_metric = self.test_add_addresses_to_alias("Bloqueados", addresses)
            self.print_metric(add_metric)
        else:
            print("   ⚠️ Não foi possível verificar alias Bloqueados")
            add_metric = None
        
        # 6. Aplicar mudanças no firewall
        print("\n📋 [6/6] Aplicando mudanças no firewall...")
        apply_metric = self.test_apply_firewall()
        self.print_metric(apply_metric)
        
        total_end = datetime.now()
        total_duration = (total_end - total_start).total_seconds()
        
        # Relatório final
        self.print_final_report(total_duration)
        
        return self.metrics
    
    def print_metric(self, metric: PerformanceMetric):
        """Imprime métrica formatada"""
        status = "✅" if metric.success else "❌"
        print(f"   {status} {metric.function_name}")
        print(f"      Endpoint: {metric.endpoint}")
        print(f"      Rota: {metric.route}")
        print(f"      Tempo: {metric.duration_seconds:.3f}s")
        print(f"      CPU (Processo): {metric.cpu_percent:.2f}%")
        print(f"      CPU (Sistema): {metric.cpu_system_percent:.2f}%")
        print(f"      RAM (Processo): {metric.ram_mb:.2f} MB ({metric.ram_percent:.2f}%)")
        print(f"      RAM (Sistema): {metric.ram_system_percent:.2f}% ({metric.ram_system_available_mb:.0f} MB disponíveis)")
        if metric.error:
            print(f"      ❌ Erro: {metric.error}")
        if metric.metadata:
            print(f"      📊 Resultado: {json.dumps(metric.metadata, indent=8, default=str)[:200]}...")
    
    def print_final_report(self, total_duration: float):
        """Imprime relatório final"""
        print("\n" + "=" * 120)
        print("📊 RELATÓRIO FINAL DE PERFORMANCE - SISTEMA DE DETECÇÃO E BLOQUEIO AUTOMÁTICO")
        print("=" * 120)
        
        print(f"\n⏱️ TEMPO TOTAL DE EXECUÇÃO: {total_duration:.3f} segundos")
        print(f"📅 Timestamp Início: {self.metrics[0].timestamp if self.metrics else 'N/A'}")
        print(f"📅 Timestamp Fim: {datetime.now().isoformat()}")
        
        print("\n" + "=" * 120)
        print("📋 ENDPOINTS ENVOLVIDOS NO PROCESSO DE DETECÇÃO E BLOQUEIO AUTOMÁTICO")
        print("=" * 120)
        
        total_cpu = 0.0
        total_ram = 0.0
        max_cpu = 0.0
        max_ram = 0.0
        total_time = sum(m.duration_seconds for m in self.metrics)
        
        # Tabela formatada
        print(f"\n{'Nº':<4} {'Função':<45} {'Endpoint':<35} {'Rota':<40} {'Tempo (s)':<12} {'CPU%':<8} {'RAM (MB)':<12} {'Status':<10}")
        print("-" * 120)
        
        for i, metric in enumerate(self.metrics, 1):
            status = "✅ OK" if metric.success else "❌ ERRO"
            print(f"{i:<4} {metric.function_name[:43]:<45} {metric.endpoint[:33]:<35} {metric.route[:38]:<40} "
                  f"{metric.duration_seconds:>10.3f} {metric.cpu_percent:>7.2f} {metric.ram_mb:>11.2f} {status:<10}")
            
            total_cpu += metric.cpu_percent
            total_ram += metric.ram_mb
            max_cpu = max(max_cpu, metric.cpu_percent)
            max_ram = max(max_ram, metric.ram_mb)
        
        print("-" * 120)
        print(f"{'TOTAL':<4} {'':<45} {'':<35} {'':<40} "
              f"{total_time:>10.3f} {max_cpu:>7.2f} {max_ram:>11.2f} {'':<10}")
        
        # Detalhes de cada endpoint
        print("\n" + "=" * 120)
        print("📋 DETALHES DE CADA ENDPOINT")
        print("=" * 120)
        
        for i, metric in enumerate(self.metrics, 1):
            print(f"\n[{i}] {metric.function_name}")
            print(f"    📍 Endpoint: {metric.endpoint}")
            print(f"    🛣️  Rota: {metric.route}")
            print(f"    ⏰ Timestamp: {metric.timestamp}")
            print(f"    ⏱️  Tempo de Execução: {metric.duration_seconds:.3f} segundos")
            print(f"    💻 CPU (Processo): {metric.cpu_percent:.2f}%")
            print(f"    💻 CPU (Sistema): {metric.cpu_system_percent:.2f}%")
            print(f"    🧠 RAM (Processo): {metric.ram_mb:.2f} MB ({metric.ram_percent:.2f}%)")
            print(f"    🧠 RAM (Sistema): {metric.ram_system_percent:.2f}% ({metric.ram_system_available_mb:.0f} MB disponíveis)")
            print(f"    ✅ Status: {'Sucesso' if metric.success else 'Falha'}")
            if metric.error:
                print(f"    ❌ Erro: {metric.error}")
            if metric.metadata:
                metadata_str = json.dumps(metric.metadata, indent=6, default=str)
                if len(metadata_str) > 200:
                    metadata_str = metadata_str[:200] + "..."
                print(f"    📊 Resultado: {metadata_str}")
        
        print("\n" + "=" * 120)
        print("📊 RESUMO DE RECURSOS DO SISTEMA")
        print("=" * 120)
        
        if self.metrics:
            avg_cpu = total_cpu / len(self.metrics)
            avg_ram = total_ram / len(self.metrics)
            last_metric = self.metrics[-1]
            
            print(f"\n💻 CPU (Processo):")
            print(f"    - Média: {avg_cpu:.2f}%")
            print(f"    - Máximo: {max_cpu:.2f}%")
            print(f"    - Final: {last_metric.cpu_percent:.2f}%")
            
            print(f"\n💻 CPU (Sistema):")
            print(f"    - Final: {last_metric.cpu_system_percent:.2f}%")
            
            print(f"\n🧠 RAM (Processo):")
            print(f"    - Média: {avg_ram:.2f} MB")
            print(f"    - Máximo: {max_ram:.2f} MB")
            print(f"    - Final: {last_metric.ram_mb:.2f} MB ({last_metric.ram_percent:.2f}%)")
            
            print(f"\n🧠 RAM (Sistema):")
            print(f"    - Final: {last_metric.ram_system_percent:.2f}%")
            print(f"    - Disponível: {last_metric.ram_system_available_mb:.0f} MB")
        
        print("\n" + "=" * 120)
        print("⏱️ DISTRIBUIÇÃO DE TEMPO POR ETAPA")
        print("=" * 120)
        
        for metric in self.metrics:
            percentage = (metric.duration_seconds / total_time * 100) if total_time > 0 else 0
            bar_length = int(percentage / 2)
            bar = "█" * bar_length
            print(f"{metric.function_name[:50]:<50} {metric.duration_seconds:>7.3f}s ({percentage:>5.1f}%) {bar}")
        
        print("\n" + "=" * 120)
        print(f"⏱️ TEMPO TOTAL: {total_duration:.3f} segundos")
        print(f"📊 Total de Endpoints: {len(self.metrics)}")
        print(f"✅ Endpoints Bem-sucedidos: {sum(1 for m in self.metrics if m.success)}")
        print(f"❌ Endpoints com Falha: {sum(1 for m in self.metrics if not m.success)}")
        print("=" * 120)
        
        # Salvar relatório em arquivo
        self.save_report_to_file(total_duration)
    
    def save_report_to_file(self, total_duration: float):
        """Salva relatório em arquivo JSON"""
        report = {
            "test_timestamp": datetime.now().isoformat(),
            "total_duration_seconds": total_duration,
            "metrics": [asdict(m) for m in self.metrics],
            "summary": {
                "total_operations": len(self.metrics),
                "successful_operations": sum(1 for m in self.metrics if m.success),
                "failed_operations": sum(1 for m in self.metrics if not m.success),
                "total_time": sum(m.duration_seconds for m in self.metrics),
                "avg_cpu_percent": sum(m.cpu_percent for m in self.metrics) / len(self.metrics) if self.metrics else 0,
                "max_cpu_percent": max((m.cpu_percent for m in self.metrics), default=0),
                "avg_ram_mb": sum(m.ram_mb for m in self.metrics) / len(self.metrics) if self.metrics else 0,
                "max_ram_mb": max((m.ram_mb for m in self.metrics), default=0),
            }
        }
        
        report_file = backend_dir / "performance_test_report.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"💾 Relatório salvo em: {report_file}")

def main():
    """Função principal"""
    print("\n" + "=" * 80)
    print("🔧 TESTE DE PERFORMANCE - SISTEMA DE DETECÇÃO E BLOQUEIO AUTOMÁTICO")
    print("=" * 80)
    
    # Verificar variáveis de ambiente
    api_url = os.getenv("API_URL", "http://localhost:8000")
    api_token = os.getenv("API_TOKEN", "")
    
    if not api_token:
        print("⚠️ ATENÇÃO: API_TOKEN não configurado no .env")
        print("   O script tentará executar sem autenticação")
        print()
    
    # Criar monitor
    monitor = PerformanceMonitor()
    
    # IP de teste (pode ser passado como argumento)
    test_ip = sys.argv[1] if len(sys.argv) > 1 else "192.168.59.4"
    
    try:
        # Executar teste completo
        metrics = monitor.run_full_blocking_test(test_ip=test_ip)
        
        print("\n✅ Teste concluído com sucesso!")
        print(f"   Total de operações: {len(metrics)}")
        print(f"   Operações bem-sucedidas: {sum(1 for m in metrics if m.success)}")
        print(f"   Operações com falha: {sum(1 for m in metrics if not m.success)}")
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Teste interrompido pelo usuário")
    except Exception as e:
        print(f"\n\n❌ Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

