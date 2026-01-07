#!/usr/bin/env python3
"""
Script para testar e verificar o bloqueio automático no pfSense.
"""

import requests
import json
import sys
from datetime import datetime

# Configuração
BASE_URL = "http://127.0.0.1:8000"
INCIDENTS_ENDPOINT = f"{BASE_URL}/api/incidents"
AUTO_BLOCK_ENDPOINT = f"{BASE_URL}/api/incidents/auto-block"
ALIASES_ENDPOINT = f"{BASE_URL}/api/devices/aliases-db"

def check_blocked_alias():
    """Verifica se o alias Bloqueados existe e contém IPs."""
    
    print("🔍 Verificando alias Bloqueados...")
    
    try:
        response = requests.get(f"{ALIASES_ENDPOINT}/Bloqueados", timeout=10)
        if response.status_code == 200:
            alias_data = response.json()
            print("✅ Alias Bloqueados encontrado no banco de dados")
            print(f"📊 Endereços no alias: {len(alias_data.get('addresses', []))}")
            
            for addr in alias_data.get('addresses', []):
                print(f"   - {addr['address']}: {addr.get('detail', 'Sem detalhes')}")
            
            return alias_data
        elif response.status_code == 404:
            print("❌ Alias Bloqueados não encontrado no banco de dados")
            return None
        else:
            print(f"❌ Erro ao verificar alias: {response.status_code}")
            print(f"Resposta: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro de conexão: {e}")
        return None

def test_auto_block_with_verification():
    """Testa bloqueio automático e verifica se funcionou."""
    
    print("🧪 Testando bloqueio automático com verificação")
    print("=" * 60)
    
    # 1. Listar incidentes de atacante
    print("\n1️⃣ Buscando incidentes de atacante...")
    try:
        response = requests.get(INCIDENTS_ENDPOINT, timeout=10)
        if response.status_code == 200:
            incidents = response.json()
            
            # Procurar por incidentes de atacante
            attacker_incidents = []
            for incident in incidents:
                incident_type = incident.get('incident_type', '')
                if 'Atacante' in incident_type:
                    attacker_incidents.append(incident)
            
            if not attacker_incidents:
                print("❌ Nenhum incidente de atacante encontrado")
                return False
            
            # Usar o primeiro incidente de atacante
            test_incident = attacker_incidents[0]
            incident_id = test_incident['id']
            device_ip = test_incident['device_ip']
            incident_type = test_incident['incident_type']
            
            print(f"📋 Usando incidente: ID {incident_id}, IP {device_ip}, Tipo: {incident_type}")
            
        else:
            print(f"❌ Erro ao listar incidentes: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro de conexão: {e}")
        return False
    
    # 2. Verificar estado inicial do alias Bloqueados
    print(f"\n2️⃣ Verificando estado inicial do alias Bloqueados...")
    initial_alias = check_blocked_alias()
    
    # 3. Executar bloqueio automático
    print(f"\n3️⃣ Executando bloqueio automático...")
    auto_block_data = {
        "incident_id": incident_id,
        "reason": "Teste de verificação de bloqueio no pfSense",
        "admin_name": "Sistema de Teste"
    }
    
    try:
        response = requests.post(
            AUTO_BLOCK_ENDPOINT,
            json=auto_block_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Bloqueio automático executado!")
            print(f"📊 Resultado: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
            if not result.get('success'):
                print("❌ Bloqueio falhou")
                return False
                
        else:
            print(f"❌ Erro no bloqueio automático: {response.status_code}")
            print(f"Resposta: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro de conexão: {e}")
        return False
    
    # 4. Verificar se o IP foi adicionado ao alias Bloqueados
    print(f"\n4️⃣ Verificando se IP {device_ip} foi adicionado ao alias Bloqueados...")
    
    try:
        response = requests.get(f"{ALIASES_ENDPOINT}/Bloqueados", timeout=10)
        if response.status_code == 200:
            updated_alias = response.json()
            addresses = [addr['address'] for addr in updated_alias.get('addresses', [])]
            
            if device_ip in addresses:
                print(f"✅ IP {device_ip} encontrado no alias Bloqueados!")
                print(f"📊 Total de endereços bloqueados: {len(addresses)}")
                
                # Mostrar detalhes do IP bloqueado
                for addr in updated_alias.get('addresses', []):
                    if addr['address'] == device_ip:
                        print(f"📝 Detalhes: {addr.get('detail', 'Sem detalhes')}")
                        break
                
                return True
            else:
                print(f"❌ IP {device_ip} NÃO encontrado no alias Bloqueados")
                print(f"📊 Endereços atuais: {addresses}")
                return False
                
        else:
            print(f"❌ Erro ao verificar alias: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro de conexão: {e}")
        return False

def main():
    """Função principal."""
    
    print("🚀 Teste de Verificação de Bloqueio Automático no pfSense")
    print(f"🌐 URL base: {BASE_URL}")
    print(f"⏰ Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Executar teste
    success = test_auto_block_with_verification()
    
    # Resultado final
    print("\n" + "=" * 60)
    print("📊 RESULTADO DO TESTE")
    print("=" * 60)
    
    if success:
        print("✅ TESTE PASSOU - Bloqueio automático funcionando corretamente!")
        print("🔒 IP foi adicionado ao alias Bloqueados no banco de dados")
        print("⚠️  IMPORTANTE: Verifique manualmente no pfSense se o alias foi sincronizado")
        sys.exit(0)
    else:
        print("❌ TESTE FALHOU - Problema no bloqueio automático!")
        print("🔍 Verifique os logs do servidor para mais detalhes")
        sys.exit(1)

if __name__ == "__main__":
    main()
