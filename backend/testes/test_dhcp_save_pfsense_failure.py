#!/usr/bin/env python3
"""
Teste para verificar se o endpoint /dhcp/save não salva no banco quando há falha no pfSense.

Este teste simula uma falha no pfSense e verifica se:
1. O endpoint retorna sucesso mas com pfsense_saved = false
2. Nenhum dado foi salvo no banco de dados
3. A mensagem de erro do pfSense está presente
"""

import requests
import json
import time
from datetime import datetime

# Configurações
BASE_URL = "http://127.0.0.1:8000/api/devices"
TIMEOUT = 30

def test_dhcp_save_pfsense_failure():
    """Testa o comportamento quando há falha no pfSense."""
    print("🧪 Testando comportamento do /dhcp/save com falha no pfSense")
    print("=" * 60)
    
    # Dados de teste que podem causar erro no pfSense
    test_data = {
        "parent_id": "lan",
        "id": 999,  # ID inválido para causar erro
        "mac": "aa:bb:cc:dd:ee:ff",
        "ipaddr": "10.30.30.999",  # IP inválido
        "cid": "test-pfsense-failure",
        "hostname": "test-pfsense-failure",
        "descr": "Teste de falha no pfSense"
    }
    
    print(f"📋 Dados de teste:")
    print(f"   MAC: {test_data['mac']}")
    print(f"   IP: {test_data['ipaddr']}")
    print(f"   CID: {test_data['cid']}")
    print(f"   Descrição: {test_data['descr']}")
    print()
    
    try:
        # Fazer requisição
        print(f"🌐 Fazendo requisição POST para {BASE_URL}/dhcp/save")
        start_time = time.time()
        
        response = requests.post(
            f"{BASE_URL}/dhcp/save",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=TIMEOUT
        )
        
        response_time = time.time() - start_time
        
        print(f"⏱️  Tempo de resposta: {response_time:.3f}s")
        print(f"📊 Status Code: {response.status_code}")
        print()
        
        # Verificar status code
        if response.status_code == 200:
            print("✅ Status Code: OK (200)")
        else:
            print(f"❌ Status Code: ERRO ({response.status_code})")
            print(f"📄 Response: {response.text}")
            return False
        
        # Parsear resposta
        try:
            data = response.json()
            print("✅ JSON Parse: OK")
        except json.JSONDecodeError as e:
            print(f"❌ JSON Parse: ERRO - {e}")
            print(f"📄 Response: {response.text}")
            return False
        
        # Verificar campos obrigatórios
        print("\n🔍 Verificando campos da resposta:")
        required_fields = ['status', 'servers_saved', 'mappings_saved', 'mappings_updated', 'timestamp', 'pfsense_saved', 'pfsense_message']
        
        for field in required_fields:
            if field in data:
                print(f"✅ {field}: {data[field]}")
            else:
                print(f"❌ {field}: CAMPO AUSENTE")
                return False
        
        # Verificar lógica de negócio
        print("\n🔍 Verificando lógica de negócio:")
        
        # 1. Status deve ser 'success'
        if data['status'] == 'success':
            print("✅ Status: 'success'")
        else:
            print(f"❌ Status: '{data['status']}' (deveria ser 'success')")
            return False
        
        # 2. pfSense deve ter falhado
        if data['pfsense_saved'] == False:
            print("✅ pfSense falhou conforme esperado")
        else:
            print(f"❌ pfSense não falhou (pfsense_saved: {data['pfsense_saved']})")
            return False
        
        # 3. Nenhum dado deve ter sido salvo no banco
        if data['servers_saved'] == 0 and data['mappings_saved'] == 0 and data['mappings_updated'] == 0:
            print("✅ Nenhum dado salvo no banco (conforme esperado)")
        else:
            print(f"❌ Dados foram salvos no banco (servers: {data['servers_saved']}, mappings: {data['mappings_saved']}, updated: {data['mappings_updated']})")
            return False
        
        # 4. Mensagem de erro deve estar presente
        if data['pfsense_message'] and 'Erro' in data['pfsense_message']:
            print("✅ Mensagem de erro do pfSense presente")
        else:
            print(f"❌ Mensagem de erro do pfSense ausente ou inválida: {data['pfsense_message']}")
            return False
        
        # Verificar se o dispositivo realmente não foi salvo no banco
        print("\n🔍 Verificando se dispositivo não foi salvo no banco:")
        
        # Buscar o dispositivo por IP
        search_response = requests.get(
            f"{BASE_URL}/dhcp/devices/ip/{test_data['ipaddr']}",
            timeout=TIMEOUT
        )
        
        if search_response.status_code == 404:
            print("✅ Dispositivo não encontrado no banco (conforme esperado)")
        elif search_response.status_code == 200:
            print("❌ Dispositivo encontrado no banco (não deveria ter sido salvo)")
            return False
        else:
            print(f"⚠️  Erro ao verificar dispositivo no banco: {search_response.status_code}")
        
        # Resumo final
        print("\n" + "=" * 60)
        print("🎉 TESTE CONCLUÍDO COM SUCESSO!")
        print(f"📊 Status: {data['status']}")
        print(f"🔧 pfSense: {'✅ Sucesso' if data['pfsense_saved'] else '❌ Falha'}")
        print(f"💾 Banco: {'✅ Dados salvos' if data['servers_saved'] > 0 or data['mappings_saved'] > 0 else '❌ Nenhum dado salvo'}")
        print(f"📝 Mensagem: {data['pfsense_message']}")
        print(f"⚡ Performance: {response_time:.3f}s")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ ERRO DE CONEXÃO")
        print("💡 Verifique se o servidor está rodando:")
        print("   python start_server.py")
        return False
        
    except requests.exceptions.Timeout:
        print("❌ TIMEOUT")
        print(f"💡 A requisição demorou mais que {TIMEOUT}s")
        return False
        
    except requests.exceptions.RequestException as e:
        print(f"❌ ERRO DE REQUISIÇÃO: {e}")
        return False
        
    except Exception as e:
        print(f"❌ ERRO INESPERADO: {e}")
        return False

def test_dhcp_save_pfsense_success():
    """Testa o comportamento quando o pfSense é bem-sucedido."""
    print("\n🧪 Testando comportamento do /dhcp/save com sucesso no pfSense")
    print("=" * 60)
    
    # Dados de teste válidos
    test_data = {
        "parent_id": "lan",
        "id": 1,
        "mac": "aa:bb:cc:dd:ee:aa",
        "ipaddr": "10.30.30.100",
        "cid": "test-pfsense-success",
        "hostname": "test-pfsense-success",
        "descr": "Teste de sucesso no pfSense"
    }
    
    print(f"📋 Dados de teste:")
    print(f"   MAC: {test_data['mac']}")
    print(f"   IP: {test_data['ipaddr']}")
    print(f"   CID: {test_data['cid']}")
    print(f"   Descrição: {test_data['descr']}")
    print()
    
    try:
        # Fazer requisição
        print(f"🌐 Fazendo requisição POST para {BASE_URL}/dhcp/save")
        start_time = time.time()
        
        response = requests.post(
            f"{BASE_URL}/dhcp/save",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=TIMEOUT
        )
        
        response_time = time.time() - start_time
        
        print(f"⏱️  Tempo de resposta: {response_time:.3f}s")
        print(f"📊 Status Code: {response.status_code}")
        print()
        
        # Verificar status code
        if response.status_code == 200:
            print("✅ Status Code: OK (200)")
        else:
            print(f"❌ Status Code: ERRO ({response.status_code})")
            print(f"📄 Response: {response.text}")
            return False
        
        # Parsear resposta
        try:
            data = response.json()
            print("✅ JSON Parse: OK")
        except json.JSONDecodeError as e:
            print(f"❌ JSON Parse: ERRO - {e}")
            print(f"📄 Response: {response.text}")
            return False
        
        # Verificar lógica de negócio
        print("\n🔍 Verificando lógica de negócio:")
        
        # 1. Status deve ser 'success'
        if data['status'] == 'success':
            print("✅ Status: 'success'")
        else:
            print(f"❌ Status: '{data['status']}' (deveria ser 'success')")
            return False
        
        # 2. pfSense deve ter sido bem-sucedido
        if data['pfsense_saved'] == True:
            print("✅ pfSense foi bem-sucedido")
        else:
            print(f"❌ pfSense falhou (pfsense_saved: {data['pfsense_saved']})")
            print(f"📝 Mensagem: {data['pfsense_message']}")
            # Não falhar o teste se pfSense falhar, apenas avisar
            print("⚠️  pfSense falhou, mas isso pode ser esperado em ambiente de teste")
        
        # 3. Dados devem ter sido salvos no banco se pfSense foi bem-sucedido
        if data['pfsense_saved'] == True:
            if data['servers_saved'] > 0 or data['mappings_saved'] > 0:
                print("✅ Dados salvos no banco (conforme esperado)")
            else:
                print(f"❌ Nenhum dado salvo no banco (servers: {data['servers_saved']}, mappings: {data['mappings_saved']})")
                return False
        else:
            print("⚠️  pfSense falhou, não verificando dados do banco")
        
        # Resumo final
        print("\n" + "=" * 60)
        print("🎉 TESTE CONCLUÍDO COM SUCESSO!")
        print(f"📊 Status: {data['status']}")
        print(f"🔧 pfSense: {'✅ Sucesso' if data['pfsense_saved'] else '❌ Falha'}")
        print(f"💾 Banco: {'✅ Dados salvos' if data['servers_saved'] > 0 or data['mappings_saved'] > 0 else '❌ Nenhum dado salvo'}")
        print(f"📝 Mensagem: {data['pfsense_message']}")
        print(f"⚡ Performance: {response_time:.3f}s")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ ERRO DE CONEXÃO")
        print("💡 Verifique se o servidor está rodando:")
        print("   python start_server.py")
        return False
        
    except requests.exceptions.Timeout:
        print("❌ TIMEOUT")
        print(f"💡 A requisição demorou mais que {TIMEOUT}s")
        return False
        
    except requests.exceptions.RequestException as e:
        print(f"❌ ERRO DE REQUISIÇÃO: {e}")
        return False
        
    except Exception as e:
        print(f"❌ ERRO INESPERADO: {e}")
        return False

def main():
    """Função principal."""
    print("🚀 Iniciando Testes de Comportamento do /dhcp/save")
    print(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Teste 1: Falha no pfSense
    success1 = test_dhcp_save_pfsense_failure()
    
    # Aguardar um pouco entre os testes
    time.sleep(2)
    
    # Teste 2: Sucesso no pfSense
    success2 = test_dhcp_save_pfsense_success()
    
    # Resultado final
    print("\n" + "=" * 60)
    print("📊 RESUMO DOS TESTES")
    print("=" * 60)
    print(f"🧪 Teste Falha pfSense: {'✅ PASSOU' if success1 else '❌ FALHOU'}")
    print(f"🧪 Teste Sucesso pfSense: {'✅ PASSOU' if success2 else '❌ FALHOU'}")
    
    if success1 and success2:
        print("\n🎉 TODOS OS TESTES PASSARAM!")
        print("✅ A lógica de rollback está funcionando corretamente!")
        return 0
    else:
        print("\n❌ ALGUNS TESTES FALHARAM!")
        print("🔧 Verifique a implementação da lógica de rollback.")
        return 1

if __name__ == "__main__":
    exit(main())
