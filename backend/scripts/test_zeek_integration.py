#!/usr/bin/env python3
"""
Script de teste para a integração com Zeek Network Security Monitor
"""
import asyncio
import json
import sys
import os
from pathlib import Path

# Adiciona o diretório backend ao path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from services_scanners.zeek_service import ZeekService
from services_scanners.zeek_models import ZeekLogRequest, ZeekLogType


async def test_zeek_integration():
    """Testa a integração com Zeek"""
    print("🔍 Testando integração com Zeek Network Security Monitor")
    print("=" * 60)
    
    # Inicializa o serviço
    zeek_service = ZeekService()
    
    # 1. Teste de conectividade
    print("\n1. 🌐 Testando conectividade...")
    success, message = zeek_service.test_connection()
    print(f"   Status: {'✅ OK' if success else '❌ FALHA'}")
    print(f"   Mensagem: {message}")
    
    if not success:
        print("\n⚠️  Não foi possível conectar com a API do Zeek.")
        print("   Verifique se o Zeek está rodando em 192.168.100.1")
        return
    
    # 2. Teste de busca de logs HTTP
    print("\n2. 📊 Testando busca de logs HTTP...")
    try:
        request = ZeekLogRequest(
            logfile=ZeekLogType.HTTP,
            maxlines=5
        )
        response = zeek_service.get_logs(request)
        
        print(f"   Status: {'✅ OK' if response.success else '❌ FALHA'}")
        print(f"   Logs encontrados: {response.total_lines}")
        print(f"   Incidentes detectados: {len(response.incidents)}")
        
        if response.logs:
            print("   📋 Exemplo de log:")
            log_sample = response.logs[0]
            for key, value in list(log_sample.items())[:5]:
                print(f"      {key}: {value}")
        
        if response.incidents:
            print("   🚨 Exemplo de incidente:")
            incident = response.incidents[0]
            print(f"      IP: {incident.device_ip}")
            print(f"      Tipo: {incident.incident_type}")
            print(f"      Severidade: {incident.severity}")
            print(f"      Descrição: {incident.description}")
            
    except Exception as e:
        print(f"   ❌ ERRO: {e}")
    
    # 3. Teste de busca de logs DNS
    print("\n3. 🌐 Testando busca de logs DNS...")
    try:
        request = ZeekLogRequest(
            logfile=ZeekLogType.DNS,
            maxlines=5
        )
        response = zeek_service.get_logs(request)
        
        print(f"   Status: {'✅ OK' if response.success else '❌ FALHA'}")
        print(f"   Logs encontrados: {response.total_lines}")
        print(f"   Incidentes detectados: {len(response.incidents)}")
        
    except Exception as e:
        print(f"   ❌ ERRO: {e}")
    
    # 4. Teste de busca de logs de conexão
    print("\n4. 🔗 Testando busca de logs de conexão...")
    try:
        request = ZeekLogRequest(
            logfile=ZeekLogType.CONN,
            maxlines=5
        )
        response = zeek_service.get_logs(request)
        
        print(f"   Status: {'✅ OK' if response.success else '❌ FALHA'}")
        print(f"   Logs encontrados: {response.total_lines}")
        print(f"   Incidentes detectados: {len(response.incidents)}")
        
    except Exception as e:
        print(f"   ❌ ERRO: {e}")
    
    # 5. Teste com filtro por IP
    print("\n5. 🎯 Testando filtro por IP...")
    try:
        request = ZeekLogRequest(
            logfile=ZeekLogType.HTTP,
            maxlines=10,
            filter_ip="192.168.1.100"  # IP de exemplo
        )
        response = zeek_service.get_logs(request)
        
        print(f"   Status: {'✅ OK' if response.success else '❌ FALHA'}")
        print(f"   Logs filtrados: {response.total_lines}")
        
    except Exception as e:
        print(f"   ❌ ERRO: {e}")
    
    # 6. Teste de tipos de logs disponíveis
    print("\n6. 📝 Testando tipos de logs disponíveis...")
    try:
        log_types = zeek_service.get_available_log_types()
        print(f"   Tipos disponíveis: {', '.join(log_types)}")
        
    except Exception as e:
        print(f"   ❌ ERRO: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Teste de integração concluído!")
    
    # Instruções para o usuário
    print("\n📋 Próximos passos:")
    print("1. Acesse o dashboard da aplicação")
    print("2. Clique na aba 'Ocorrências'")
    print("3. Verifique se os dados do Zeek aparecem")
    print("4. Teste os filtros de severidade, status e tipo de log")
    
    print("\n🔗 Endpoints da API:")
    print("- GET /api/scanners/zeek/health")
    print("- GET /api/scanners/zeek/logs")
    print("- GET /api/scanners/zeek/incidents")
    print("- GET /api/scanners/zeek/stats")


def main():
    """Função principal"""
    try:
        asyncio.run(test_zeek_integration())
    except KeyboardInterrupt:
        print("\n\n⚠️  Teste interrompido pelo usuário")
    except Exception as e:
        print(f"\n\n❌ ERRO INESPERADO: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
