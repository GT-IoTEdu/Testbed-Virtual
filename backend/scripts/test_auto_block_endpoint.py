#!/usr/bin/env python3
"""
Script de teste para o endpoint de bloqueio automático de incidentes.
"""

import requests
import json
import sys
from datetime import datetime

# Configuração
BASE_URL = "http://127.0.0.1:8000"
INCIDENTS_ENDPOINT = f"{BASE_URL}/api/incidents"
AUTO_BLOCK_ENDPOINT = f"{BASE_URL}/api/incidents/auto-block"

def test_auto_block_endpoint():
    """Testa o endpoint de bloqueio automático."""
    
    print("🧪 Testando endpoint de bloqueio automático de incidentes")
    print("=" * 60)
    
    # 1. Listar incidentes existentes
    print("\n1️⃣ Listando incidentes existentes...")
    try:
        response = requests.get(INCIDENTS_ENDPOINT, timeout=10)
        if response.status_code == 200:
            incidents = response.json()
            print(f"✅ Encontrados {len(incidents)} incidentes")
            
            if not incidents:
                print("❌ Nenhum incidente encontrado para teste")
                return False
            
            # Procurar por incidentes de atacante
            attacker_incidents = []
            victim_incidents = []
            
            for incident in incidents:
                incident_type = incident.get('incident_type', '')
                if 'Atacante' in incident_type:
                    attacker_incidents.append(incident)
                elif 'Vítima' in incident_type:
                    victim_incidents.append(incident)
            
            print(f"📊 Incidentes de atacante encontrados: {len(attacker_incidents)}")
            print(f"📊 Incidentes de vítima encontrados: {len(victim_incidents)}")
            
            # Testar com incidente de atacante se disponível
            if attacker_incidents:
                test_incident = attacker_incidents[0]
                incident_id = test_incident['id']
                device_ip = test_incident['device_ip']
                incident_type = test_incident['incident_type']
                
                print(f"📋 Testando com incidente de ATACANTE - ID {incident_id} (IP: {device_ip}, Tipo: {incident_type})")
                return test_block_attacker_incident(incident_id, device_ip, incident_type)
            
            # Se não há incidentes de atacante, testar com vítima para verificar filtro
            elif victim_incidents:
                test_incident = victim_incidents[0]
                incident_id = test_incident['id']
                device_ip = test_incident['device_ip']
                incident_type = test_incident['incident_type']
                
                print(f"📋 Testando com incidente de VÍTIMA - ID {incident_id} (IP: {device_ip}, Tipo: {incident_type})")
                return test_block_victim_incident(incident_id, device_ip, incident_type)
            
            else:
                print("❌ Nenhum incidente de atacante ou vítima encontrado para teste")
                return False
            
        else:
            print(f"❌ Erro ao listar incidentes: {response.status_code}")
            print(f"Resposta: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro de conexão: {e}")
        return False

def test_block_attacker_incident(incident_id, device_ip, incident_type):
    """Testa bloqueio com incidente de atacante."""
    
    print(f"\n2️⃣ Testando bloqueio automático para incidente de ATACANTE {incident_id}...")
    
    auto_block_data = {
        "incident_id": incident_id,
        "reason": "Teste de bloqueio automático - Atacante",
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
            
            # Verificar se o bloqueio foi aplicado
            if result.get('success') and not result.get('blocked', True):
                print(f"🔒 Dispositivo {device_ip} bloqueado automaticamente (atacante)")
                return True
            elif result.get('success') and result.get('blocked', False):
                print(f"⚠️ Dispositivo {device_ip} já estava bloqueado")
                return True
            else:
                print("❌ Bloqueio não foi aplicado para atacante")
                return False
                
        else:
            print(f"❌ Erro no bloqueio automático: {response.status_code}")
            print(f"Resposta: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro de conexão: {e}")
        return False

def test_block_victim_incident(incident_id, device_ip, incident_type):
    """Testa bloqueio com incidente de vítima (deve ser rejeitado)."""
    
    print(f"\n2️⃣ Testando bloqueio automático para incidente de VÍTIMA {incident_id}...")
    
    auto_block_data = {
        "incident_id": incident_id,
        "reason": "Teste de bloqueio automático - Vítima",
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
            print("✅ Resposta recebida!")
            print(f"📊 Resultado: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
            # Verificar se o bloqueio foi rejeitado corretamente
            if not result.get('success') and not result.get('blocked', True):
                print(f"✅ Bloqueio corretamente rejeitado para vítima {device_ip}")
                print(f"📝 Motivo: {result.get('reason', 'N/A')}")
                return True
            else:
                print("❌ Bloqueio foi aplicado incorretamente para vítima")
                return False
                
        else:
            print(f"❌ Erro inesperado: {response.status_code}")
            print(f"Resposta: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro de conexão: {e}")
        return False

def test_invalid_incident():
    """Testa com incidente inválido."""
    
    print(f"\n3️⃣ Testando com incidente inválido...")
    
    auto_block_data = {
        "incident_id": 99999,  # ID que não existe
        "reason": "Teste com incidente inválido",
        "admin_name": "Sistema de Teste"
    }
    
    try:
        response = requests.post(
            AUTO_BLOCK_ENDPOINT,
            json=auto_block_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 404:
            print("✅ Erro 404 retornado corretamente para incidente inválido")
            return True
        else:
            print(f"❌ Status inesperado: {response.status_code}")
            print(f"Resposta: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro de conexão: {e}")
        return False

def main():
    """Função principal."""
    
    print("🚀 Iniciando testes do endpoint de bloqueio automático")
    print(f"🌐 URL base: {BASE_URL}")
    print(f"⏰ Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Executar testes
    test1_success = test_auto_block_endpoint()
    test2_success = test_invalid_incident()
    
    # Resultado final
    print("\n" + "=" * 60)
    print("📊 RESUMO DOS TESTES")
    print("=" * 60)
    
    if test1_success:
        print("✅ Teste 1 (Bloqueio automático): PASSOU")
    else:
        print("❌ Teste 1 (Bloqueio automático): FALHOU")
    
    if test2_success:
        print("✅ Teste 2 (Incidente inválido): PASSOU")
    else:
        print("❌ Teste 2 (Incidente inválido): FALHOU")
    
    if test1_success and test2_success:
        print("\n🎉 TODOS OS TESTES PASSARAM!")
        sys.exit(0)
    else:
        print("\n💥 ALGUNS TESTES FALHARAM!")
        sys.exit(1)

if __name__ == "__main__":
    main()
