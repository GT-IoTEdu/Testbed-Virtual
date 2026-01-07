#!/usr/bin/env python3
"""
Script para testar o bloqueio automático quando um incidente é criado.
"""

import requests
import json
import sys
from datetime import datetime

# Configuração
BASE_URL = "http://127.0.0.1:8000"
INCIDENTS_ENDPOINT = f"{BASE_URL}/api/incidents"
ALIASES_ENDPOINT = f"{BASE_URL}/api/devices/aliases-db"

def test_auto_block_on_incident_creation():
    """Testa se o bloqueio automático é aplicado quando um incidente de atacante é criado."""
    
    print("🧪 Testando bloqueio automático na criação de incidente")
    print("=" * 60)
    
    # 1. Verificar estado inicial do alias Bloqueados
    print("\n1️⃣ Verificando estado inicial do alias Bloqueados...")
    try:
        response = requests.get(f"{ALIASES_ENDPOINT}/Bloqueados", timeout=10)
        if response.status_code == 200:
            initial_alias = response.json()
            initial_addresses = [addr['address'] for addr in initial_alias.get('addresses', [])]
            print(f"📊 Endereços bloqueados inicialmente: {len(initial_addresses)}")
            print(f"📋 IPs bloqueados: {initial_addresses}")
        else:
            print("❌ Alias Bloqueados não encontrado inicialmente")
            initial_addresses = []
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro de conexão: {e}")
        return False
    
    # 2. Criar um novo incidente de atacante
    print(f"\n2️⃣ Criando incidente de atacante...")
    
    # Usar um IP de teste único
    test_ip = "192.168.100.99"  # IP de teste
    test_incident_data = {
        "device_ip": test_ip,
        "device_name": "Dispositivo de Teste",
        "incident_type": "SQL Injection - Atacante",
        "severity": "critical",
        "description": "Teste de bloqueio automático - Atacante detectado",
        "zeek_log_type": "notice.log",
        "raw_log_data": {
            "test": True,
            "auto_block_test": True
        },
        "action_taken": None,
        "notes": "Incidente criado para teste de bloqueio automático"
    }
    
    try:
        response = requests.post(
            INCIDENTS_ENDPOINT,
            json=test_incident_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            incident_result = response.json()
            incident_id = incident_result['id']
            print(f"✅ Incidente criado com ID: {incident_id}")
            print(f"📊 Tipo: {incident_result['incident_type']}")
            print(f"📊 IP: {incident_result['device_ip']}")
            print(f"📊 Status: {incident_result['status']}")
            
        else:
            print(f"❌ Erro ao criar incidente: {response.status_code}")
            print(f"Resposta: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro de conexão: {e}")
        return False
    
    # 3. Aguardar um pouco para o processamento
    print(f"\n3️⃣ Aguardando processamento do bloqueio automático...")
    import time
    time.sleep(2)  # Aguardar 2 segundos
    
    # 4. Verificar se o IP foi adicionado ao alias Bloqueados
    print(f"\n4️⃣ Verificando se IP {test_ip} foi bloqueado automaticamente...")
    
    try:
        response = requests.get(f"{ALIASES_ENDPOINT}/Bloqueados", timeout=10)
        if response.status_code == 200:
            updated_alias = response.json()
            updated_addresses = [addr['address'] for addr in updated_alias.get('addresses', [])]
            
            print(f"📊 Endereços bloqueados após incidente: {len(updated_addresses)}")
            print(f"📋 IPs bloqueados: {updated_addresses}")
            
            if test_ip in updated_addresses:
                print(f"✅ IP {test_ip} foi bloqueado automaticamente!")
                
                # Mostrar detalhes do bloqueio
                for addr in updated_alias.get('addresses', []):
                    if addr['address'] == test_ip:
                        print(f"📝 Detalhes do bloqueio: {addr.get('detail', 'Sem detalhes')}")
                        break
                
                return True
            else:
                print(f"❌ IP {test_ip} NÃO foi bloqueado automaticamente")
                print(f"🔍 Diferença: {set(updated_addresses) - set(initial_addresses)}")
                return False
                
        else:
            print(f"❌ Erro ao verificar alias: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro de conexão: {e}")
        return False

def test_victim_incident_no_block():
    """Testa que incidentes de vítima não são bloqueados automaticamente."""
    
    print(f"\n5️⃣ Testando que incidentes de vítima NÃO são bloqueados...")
    
    # Usar um IP de teste diferente
    test_ip = "192.168.100.98"  # IP de teste para vítima
    
    # Verificar estado inicial
    try:
        response = requests.get(f"{ALIASES_ENDPOINT}/Bloqueados", timeout=10)
        if response.status_code == 200:
            initial_alias = response.json()
            initial_addresses = [addr['address'] for addr in initial_alias.get('addresses', [])]
        else:
            initial_addresses = []
    except:
        initial_addresses = []
    
    # Criar incidente de vítima
    victim_incident_data = {
        "device_ip": test_ip,
        "device_name": "Vítima de Teste",
        "incident_type": "SQL Injection - Vítima",
        "severity": "high",
        "description": "Teste de bloqueio automático - Vítima detectada",
        "zeek_log_type": "notice.log",
        "raw_log_data": {"test": True, "victim_test": True},
        "action_taken": None,
        "notes": "Incidente de vítima para teste"
    }
    
    try:
        response = requests.post(
            INCIDENTS_ENDPOINT,
            json=victim_incident_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            incident_result = response.json()
            print(f"✅ Incidente de vítima criado com ID: {incident_result['id']}")
            
            # Aguardar processamento
            import time
            time.sleep(2)
            
            # Verificar que não foi bloqueado
            response = requests.get(f"{ALIASES_ENDPOINT}/Bloqueados", timeout=10)
            if response.status_code == 200:
                updated_alias = response.json()
                updated_addresses = [addr['address'] for addr in updated_alias.get('addresses', [])]
                
                if test_ip not in updated_addresses:
                    print(f"✅ IP {test_ip} (vítima) NÃO foi bloqueado automaticamente - correto!")
                    return True
                else:
                    print(f"❌ IP {test_ip} (vítima) foi bloqueado incorretamente!")
                    return False
            else:
                print(f"❌ Erro ao verificar alias: {response.status_code}")
                return False
        else:
            print(f"❌ Erro ao criar incidente de vítima: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro de conexão: {e}")
        return False

def main():
    """Função principal."""
    
    print("🚀 Teste de Bloqueio Automático na Criação de Incidentes")
    print(f"🌐 URL base: {BASE_URL}")
    print(f"⏰ Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Executar testes
    test1_success = test_auto_block_on_incident_creation()
    test2_success = test_victim_incident_no_block()
    
    # Resultado final
    print("\n" + "=" * 60)
    print("📊 RESULTADO DOS TESTES")
    print("=" * 60)
    
    if test1_success:
        print("✅ Teste 1 (Bloqueio automático para atacante): PASSOU")
    else:
        print("❌ Teste 1 (Bloqueio automático para atacante): FALHOU")
    
    if test2_success:
        print("✅ Teste 2 (Não bloquear vítima): PASSOU")
    else:
        print("❌ Teste 2 (Não bloquear vítima): FALHOU")
    
    if test1_success and test2_success:
        print("\n🎉 TODOS OS TESTES PASSARAM!")
        print("🔒 Bloqueio automático está funcionando corretamente!")
        print("⚠️  IMPORTANTE: Verifique manualmente no pfSense se os aliases foram sincronizados")
        sys.exit(0)
    else:
        print("\n💥 ALGUNS TESTES FALHARAM!")
        print("🔍 Verifique os logs do servidor para mais detalhes")
        sys.exit(1)

if __name__ == "__main__":
    main()
