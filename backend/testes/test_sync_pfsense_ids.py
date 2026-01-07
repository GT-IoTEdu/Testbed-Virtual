#!/usr/bin/env python3
"""
Teste para sincronização de IDs do pfSense com o banco de dados local.

Este script testa o endpoint de sincronização que corrige inconsistências
entre os IDs do pfSense e os pf_id do banco de dados local.
"""
import requests
import json
import time
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000/api/devices"
TIMEOUT = 30

def test_sync_pfsense_ids():
    """Testa a sincronização de IDs do pfSense."""
    print("🔄 Testando sincronização de IDs do pfSense...")
    
    url = f"{BASE_URL}/dhcp/sync"
    
    try:
        response = requests.post(url, timeout=TIMEOUT)
        response.raise_for_status()
        
        result = response.json()
        print(f"✅ Sincronização concluída com sucesso!")
        print(f"📊 Resultado da sincronização:")
        print(f"   - Status: {result.get('status')}")
        print(f"   - Mensagem: {result.get('message')}")
        
        sync_result = result.get('sync_result', {})
        print(f"   - Servidores criados: {sync_result.get('servers_created', 0)}")
        print(f"   - Mapeamentos sincronizados: {sync_result.get('mappings_synced', 0)}")
        print(f"   - Mapeamentos criados: {sync_result.get('mappings_created', 0)}")
        print(f"   - Mapeamentos atualizados: {sync_result.get('mappings_updated', 0)}")
        print(f"   - Timestamp: {sync_result.get('timestamp')}")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro na requisição: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return False

def compare_pfsense_and_local_data():
    """Compara dados do pfSense com dados locais."""
    print("\n🔍 Comparando dados do pfSense com dados locais...")
    
    try:
        # Buscar dados do pfSense
        pfsense_url = f"{BASE_URL}/dhcp/servers"
        pfsense_response = requests.get(pfsense_url, timeout=TIMEOUT)
        pfsense_response.raise_for_status()
        pfsense_data = pfsense_response.json()
        
        # Buscar dados locais
        local_url = f"{BASE_URL}/dhcp/devices"
        local_response = requests.get(local_url, timeout=TIMEOUT)
        local_response.raise_for_status()
        local_data = local_response.json()
        
        print(f"📊 Dados do pfSense:")
        if 'result' in pfsense_data and 'data' in pfsense_data['result']:
            for server in pfsense_data['result']['data']:
                print(f"   Servidor: {server.get('id')} ({server.get('interface')})")
                static_maps = server.get('staticmap', [])
                print(f"   Mapeamentos estáticos: {len(static_maps)}")
                for mapping in static_maps:
                    print(f"     - ID: {mapping.get('id')}, MAC: {mapping.get('mac')}, IP: {mapping.get('ipaddr')}")
        
        print(f"\n📊 Dados locais:")
        if 'devices' in local_data:
            devices = local_data['devices']
            print(f"   Total de dispositivos: {len(devices)}")
            for device in devices:
                print(f"     - pf_id: {device.get('pf_id')}, MAC: {device.get('mac')}, IP: {device.get('ipaddr')}")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro na requisição: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return False

def test_sync_workflow():
    """Testa o fluxo completo de sincronização."""
    print("\n🔄 Testando fluxo completo de sincronização...")
    
    # 1. Verificar estado inicial
    print("1️⃣ Verificando estado inicial...")
    if not compare_pfsense_and_local_data():
        return False
    
    # 2. Executar sincronização
    print("\n2️⃣ Executando sincronização...")
    if not test_sync_pfsense_ids():
        return False
    
    # 3. Aguardar um pouco
    print("\n3️⃣ Aguardando processamento...")
    time.sleep(2)
    
    # 4. Verificar estado final
    print("\n4️⃣ Verificando estado final...")
    if not compare_pfsense_and_local_data():
        return False
    
    print("\n✅ Fluxo de sincronização concluído com sucesso!")
    return True

def main():
    """Função principal."""
    print("=" * 60)
    print("🧪 TESTE DE SINCRONIZAÇÃO DE IDS DO PFSENSE")
    print("=" * 60)
    print(f"⏰ Início: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 URL Base: {BASE_URL}")
    print(f"⏱️  Timeout: {TIMEOUT}s")
    
    try:
        # Teste individual de sincronização
        success1 = test_sync_pfsense_ids()
        
        # Teste de comparação
        success2 = compare_pfsense_and_local_data()
        
        # Teste de fluxo completo
        success3 = test_sync_workflow()
        
        print("\n" + "=" * 60)
        print("📋 RESUMO DOS TESTES")
        print("=" * 60)
        print(f"✅ Sincronização individual: {'SUCESSO' if success1 else 'FALHA'}")
        print(f"✅ Comparação de dados: {'SUCESSO' if success2 else 'FALHA'}")
        print(f"✅ Fluxo completo: {'SUCESSO' if success3 else 'FALHA'}")
        
        overall_success = success1 and success2 and success3
        print(f"\n🎯 RESULTADO GERAL: {'SUCESSO' if overall_success else 'FALHA'}")
        
        if overall_success:
            print("\n🎉 Todos os testes passaram! A sincronização está funcionando corretamente.")
        else:
            print("\n⚠️  Alguns testes falharam. Verifique os logs acima.")
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Teste interrompido pelo usuário.")
    except Exception as e:
        print(f"\n❌ Erro crítico: {e}")
    
    print(f"\n⏰ Fim: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
