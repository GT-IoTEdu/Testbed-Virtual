#!/usr/bin/env python3
"""
Teste para o endpoint de listagem de todos os dispositivos do sistema.
Este endpoint é acessível apenas para gestores (MANAGER).
"""

import requests
import json
from datetime import datetime

# Configurações
BASE_URL = "http://127.0.0.1:8000/api/devices"
MANAGER_ID = 2  # ID do gestor
USER_ID = 1     # ID do usuário comum

def test_all_devices_endpoint():
    """Testa o endpoint de listagem de todos os dispositivos."""
    
    print("🧪 Testando endpoint de listagem de todos os dispositivos")
    print("=" * 60)
    
    # Teste 1: Gestor acessando todos os dispositivos
    print("\n1️⃣ Teste 1: Gestor acessando todos os dispositivos")
    print("-" * 40)
    
    try:
        response = requests.get(f"{BASE_URL}/devices", params={"current_user_id": MANAGER_ID})
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Sucesso! Resposta:")
            print(f"   Total de dispositivos: {data['total_devices']}")
            print(f"   Dispositivos online: {data['online_devices']}")
            print(f"   Dispositivos offline: {data['offline_devices']}")
            print(f"   Dispositivos atribuídos: {data['assigned_devices']}")
            print(f"   Dispositivos não atribuídos: {data['unassigned_devices']}")
            
            print(f"\n📋 Lista de dispositivos ({len(data['devices'])} encontrados):")
            for i, device in enumerate(data['devices'][:5], 1):  # Mostrar apenas os primeiros 5
                print(f"   {i}. {device['descr']} - {device['ipaddr']} ({device['mac']})")
            
            if len(data['devices']) > 5:
                print(f"   ... e mais {len(data['devices']) - 5} dispositivos")
                
        else:
            print(f"❌ Erro: {response.status_code}")
            print(f"Resposta: {response.text}")
            
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")
    
    # Teste 2: Usuário comum tentando acessar (deve ser negado)
    print("\n2️⃣ Teste 2: Usuário comum tentando acessar (deve ser negado)")
    print("-" * 40)
    
    try:
        response = requests.get(f"{BASE_URL}/devices", params={"current_user_id": USER_ID})
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 403:
            data = response.json()
            print("✅ Sucesso! Acesso negado corretamente:")
            print(f"   Erro: {data['detail']}")
        else:
            print(f"❌ Erro: Deveria ter retornado 403, mas retornou {response.status_code}")
            print(f"Resposta: {response.text}")
            
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")
    
    # Teste 3: Comparação com endpoint de dispositivos de usuário específico
    print("\n3️⃣ Teste 3: Comparação com endpoint de dispositivos de usuário específico")
    print("-" * 40)
    
    try:
        # Dispositivos do gestor
        response_manager = requests.get(f"{BASE_URL}/users/{MANAGER_ID}/devices", 
                                     params={"current_user_id": MANAGER_ID})
        
        # Dispositivos do usuário comum
        response_user = requests.get(f"{BASE_URL}/users/{USER_ID}/devices", 
                                   params={"current_user_id": MANAGER_ID})
        
        print("Dispositivos do gestor:")
        if response_manager.status_code == 200:
            data_manager = response_manager.json()
            print(f"   Total: {data_manager['total_devices']}")
            print(f"   Atribuições ativas: {data_manager['active_assignments']}")
        else:
            print(f"   Erro: {response_manager.status_code}")
        
        print("Dispositivos do usuário comum:")
        if response_user.status_code == 200:
            data_user = response_user.json()
            print(f"   Total: {data_user['total_devices']}")
            print(f"   Atribuições ativas: {data_user['active_assignments']}")
        else:
            print(f"   Erro: {response_user.status_code}")
            
    except Exception as e:
        print(f"❌ Erro na comparação: {e}")

def test_endpoint_structure():
    """Testa a estrutura da resposta do endpoint."""
    
    print("\n🔍 Teste de Estrutura da Resposta")
    print("=" * 60)
    
    try:
        response = requests.get(f"{BASE_URL}/devices", params={"current_user_id": MANAGER_ID})
        
        if response.status_code == 200:
            data = response.json()
            
            # Verificar campos obrigatórios
            required_fields = ['devices', 'total_devices', 'online_devices', 'offline_devices', 
                              'assigned_devices', 'unassigned_devices']
            
            print("Verificando campos obrigatórios:")
            for field in required_fields:
                if field in data:
                    print(f"   ✅ {field}: {data[field]}")
                else:
                    print(f"   ❌ {field}: Campo ausente")
            
            # Verificar estrutura dos dispositivos
            if 'devices' in data and len(data['devices']) > 0:
                device = data['devices'][0]
                device_fields = ['id', 'server_id', 'pf_id', 'mac', 'ipaddr', 'cid', 
                               'hostname', 'descr', 'created_at', 'updated_at']
                
                print("\nVerificando estrutura do primeiro dispositivo:")
                for field in device_fields:
                    if field in device:
                        print(f"   ✅ {field}: {device[field]}")
                    else:
                        print(f"   ❌ {field}: Campo ausente")
            else:
                print("   ⚠️ Nenhum dispositivo encontrado para verificar estrutura")
                
    except Exception as e:
        print(f"❌ Erro no teste de estrutura: {e}")

if __name__ == "__main__":
    print("🚀 Iniciando testes do endpoint de listagem de todos os dispositivos")
    print(f"📅 Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 Base URL: {BASE_URL}")
    print(f"👤 Gestor ID: {MANAGER_ID}")
    print(f"👤 Usuário ID: {USER_ID}")
    
    test_all_devices_endpoint()
    test_endpoint_structure()
    
    print("\n✅ Testes concluídos!")
