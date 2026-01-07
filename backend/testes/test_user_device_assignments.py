#!/usr/bin/env python3
"""
Script de teste para os endpoints de atribuição de usuários a dispositivos DHCP.

Este script demonstra como:
1. Atribuir usuários a dispositivos DHCP
2. Consultar dispositivos por usuário
3. Consultar usuários por dispositivo
4. Buscar atribuições
5. Ver estatísticas de atribuições
"""
import requests
import json
import time

# Configuração
BASE_URL = "http://127.0.0.1:8000/api/devices"

def test_assign_device_to_user():
    """Testa o endpoint de atribuição de dispositivo a usuário."""
    print("🔗 Testando atribuição de dispositivo a usuário...")
    
    # Dados de exemplo baseados nos dados fornecidos
    assignment_data = {
        "user_id": 1,  # jomermello@hotmail.com
        "device_id": 1,  # openvas - 10.30.30.3
        "notes": "Dispositivo de monitoramento de segurança atribuído ao administrador",
        "assigned_by": 1
    }
    
    try:
        response = requests.post(f"{BASE_URL}/assignments", json=assignment_data)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Dispositivo atribuído com sucesso!")
            print(f"   - ID da atribuição: {data['id']}")
            print(f"   - Usuário: {data['user']['nome']} ({data['user']['email']})")
            print(f"   - Dispositivo: {data['device']['descr']} - {data['device']['ipaddr']}")
            print(f"   - Atribuído em: {data['assigned_at']}")
            print(f"   - Observações: {data['notes']}")
        else:
            print(f"❌ Erro ao atribuir dispositivo: {response.status_code}")
            print(f"   Resposta: {response.text}")
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")

def test_assign_second_device():
    """Testa atribuição de um segundo dispositivo ao mesmo usuário."""
    print("\n🔗 Testando atribuição de segundo dispositivo...")
    
    assignment_data = {
        "user_id": 1,  # jomermello@hotmail.com
        "device_id": 2,  # lubuntu-live - 10.30.30.10
        "notes": "Máquina de desenvolvimento atribuída ao administrador",
        "assigned_by": 1
    }
    
    try:
        response = requests.post(f"{BASE_URL}/assignments", json=assignment_data)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Segundo dispositivo atribuído com sucesso!")
            print(f"   - Dispositivo: {data['device']['descr']} - {data['device']['ipaddr']}")
        else:
            print(f"❌ Erro ao atribuir segundo dispositivo: {response.status_code}")
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")

def test_get_user_devices():
    """Testa o endpoint de listagem de dispositivos de um usuário."""
    print("\n📋 Testando listagem de dispositivos do usuário...")
    
    try:
        response = requests.get(f"{BASE_URL}/users/1/devices")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Dispositivos do usuário listados!")
            print(f"   - Usuário: {data['user']['nome']} ({data['user']['email']})")
            print(f"   - Instituição: {data['user']['instituicao']}")
            print(f"   - Total de dispositivos: {data['total_devices']}")
            print(f"   - Atribuições ativas: {data['active_assignments']}")
            
            if data['devices']:
                print(f"   - Dispositivos atribuídos:")
                for i, device in enumerate(data['devices'], 1):
                    print(f"     {i}. {device['descr']} - {device['ipaddr']} ({device['mac']})")
        else:
            print(f"❌ Erro ao listar dispositivos: {response.status_code}")
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")

def test_get_device_users():
    """Testa o endpoint de listagem de usuários de um dispositivo."""
    print("\n👥 Testando listagem de usuários do dispositivo...")
    
    try:
        response = requests.get(f"{BASE_URL}/devices/1/users")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Usuários do dispositivo listados!")
            print(f"   - Dispositivo: {data['device']['descr']} - {data['device']['ipaddr']}")
            print(f"   - Total de usuários: {data['total_users']}")
            print(f"   - Atribuições ativas: {data['active_assignments']}")
            
            if data['users']:
                print(f"   - Usuários atribuídos:")
                for i, user in enumerate(data['users'], 1):
                    print(f"     {i}. {user['nome']} ({user['email']}) - {user['instituicao']}")
        else:
            print(f"❌ Erro ao listar usuários: {response.status_code}")
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")

def test_search_assignments():
    """Testa o endpoint de busca de atribuições."""
    print("\n🔍 Testando busca de atribuições...")
    
    try:
        # Buscar por nome do usuário
        response = requests.get(f"{BASE_URL}/assignments/search?query=joner")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Busca por 'joner' realizada!")
            print(f"   - Total encontrado: {data['total_found']}")
            print(f"   - Query: {data['query']}")
            
            if data['assignments']:
                print(f"   - Atribuições encontradas:")
                for assignment in data['assignments']:
                    print(f"     - {assignment.user.nome} -> {assignment.device.descr}")
        else:
            print(f"❌ Erro na busca: {response.status_code}")
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")

def test_assignment_statistics():
    """Testa o endpoint de estatísticas de atribuições."""
    print("\n📊 Testando estatísticas de atribuições...")
    
    try:
        response = requests.get(f"{BASE_URL}/assignments/statistics")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Estatísticas obtidas!")
            print(f"   - Total de atribuições: {data['total_assignments']}")
            print(f"   - Atribuições ativas: {data['active_assignments']}")
            print(f"   - Atribuições inativas: {data['inactive_assignments']}")
            print(f"   - Usuários com dispositivos: {data['users_with_devices']}")
            print(f"   - Dispositivos com usuários: {data['devices_with_users']}")
            print(f"   - Atribuições por instituição: {data['assignments_by_institution']}")
        else:
            print(f"❌ Erro ao obter estatísticas: {response.status_code}")
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")

def test_remove_assignment():
    """Testa o endpoint de remoção de atribuição."""
    print("\n🗑️ Testando remoção de atribuição...")
    
    try:
        response = requests.delete(f"{BASE_URL}/assignments/1/2")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Atribuição removida com sucesso!")
            print(f"   - Status: {data['status']}")
            print(f"   - Mensagem: {data['message']}")
        else:
            print(f"❌ Erro ao remover atribuição: {response.status_code}")
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")

def main():
    """Executa todos os testes."""
    print("🚀 Iniciando testes dos endpoints de atribuição usuário-dispositivo...")
    print("=" * 70)
    
    # Aguardar um pouco para garantir que o servidor está rodando
    time.sleep(2)
    
    # Executar testes
    test_assign_device_to_user()
    test_assign_second_device()
    test_get_user_devices()
    test_get_device_users()
    test_search_assignments()
    test_assignment_statistics()
    test_remove_assignment()
    
    print("\n" + "=" * 70)
    print("✅ Testes concluídos!")

if __name__ == "__main__":
    main()
