#!/usr/bin/env python3
"""
Script para testar os endpoints de aliases.
"""

import requests
import json

def test_aliases():
    """Testa os endpoints de aliases."""
    print("🧪 TESTANDO ENDPOINTS DE ALIASES")
    print("="*50)
    
    base_url = "http://127.0.0.1:8000/api/devices"
    
    # Teste 1: Salvar aliases do pfSense no banco
    print("\n📥 1. SALVANDO ALIASES DO PFSENSE NO BANCO")
    print("-" * 40)
    
    try:
        response = requests.post(f"{base_url}/aliases-db/save")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Aliases salvos com sucesso!")
            print(f"   - Aliases salvos: {data['aliases_saved']}")
            print(f"   - Aliases atualizados: {data['aliases_updated']}")
            print(f"   - Endereços salvos: {data['addresses_saved']}")
            print(f"   - Endereços atualizados: {data['addresses_updated']}")
            print(f"   - pfSense: {data['pfsense_message']}")
        else:
            print(f"❌ Erro: {response.status_code} - {response.text}")
            return
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")
        return
    
    # Teste 2: Listar aliases do banco
    print("\n📋 2. LISTANDO ALIASES DO BANCO")
    print("-" * 40)
    
    try:
        response = requests.get(f"{base_url}/aliases-db")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Aliases listados com sucesso!")
            print(f"   - Total de aliases: {data['total']}")
            print(f"   - Página: {data['page']}/{data['total'] // data['per_page'] + 1}")
            print(f"   - Aliases nesta página: {len(data['aliases'])}")
            
            # Mostrar alguns aliases
            for i, alias in enumerate(data['aliases'][:3]):
                print(f"   {i+1}. {alias['name']} ({alias['alias_type']})")
                print(f"      Descrição: {alias['descr']}")
                print(f"      Endereços: {len(alias['addresses'])}")
                for addr in alias['addresses'][:2]:
                    print(f"        - {addr['address']}: {addr['detail']}")
                if len(alias['addresses']) > 2:
                    print(f"        ... e mais {len(alias['addresses']) - 2} endereços")
        else:
            print(f"❌ Erro: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")
    
    # Teste 3: Estatísticas de aliases
    print("\n📊 3. ESTATÍSTICAS DE ALIASES")
    print("-" * 40)
    
    try:
        response = requests.get(f"{base_url}/aliases-db/statistics")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Estatísticas obtidas com sucesso!")
            print(f"   - Total de aliases: {data['total_aliases']}")
            print(f"   - Total de endereços: {data['total_addresses']}")
            print(f"   - Criados hoje: {data['created_today']}")
            print(f"   - Atualizados hoje: {data['updated_today']}")
            print(f"   - Por tipo:")
            for alias_type, count in data['aliases_by_type'].items():
                print(f"     * {alias_type}: {count}")
        else:
            print(f"❌ Erro: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")
    
    # Teste 4: Buscar aliases
    print("\n🔍 4. BUSCANDO ALIASES")
    print("-" * 40)
    
    try:
        response = requests.get(f"{base_url}/aliases-db/search?query=Teste")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Busca realizada com sucesso!")
            print(f"   - Termo buscado: {data['query']}")
            print(f"   - Resultados encontrados: {data['total_found']}")
            
            for alias in data['aliases']:
                print(f"   - {alias['name']} ({alias['alias_type']}): {alias['descr']}")
        else:
            print(f"❌ Erro: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")
    
    # Teste 5: Criar novo alias
    print("\n➕ 5. CRIANDO NOVO ALIAS")
    print("-" * 40)
    
    try:
        new_alias = {
            "name": "teste_api_iot_edu_v3",
            "alias_type": "host",
            "descr": "Alias de teste criado via API v3",
            "addresses": [
                {
                    "address": "192.168.1.202",
                    "detail": "Dispositivo de teste 3"
                },
                {
                    "address": "192.168.1.203",
                    "detail": "Dispositivo de teste 4"
                }
            ]
        }
        
        response = requests.post(
            f"{base_url}/aliases-db/create",
            json=new_alias,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Alias criado com sucesso!")
            print(f"   - Nome: {data['name']}")
            print(f"   - Tipo: {data['alias_type']}")
            print(f"   - Descrição: {data['descr']}")
            print(f"   - Endereços: {len(data['addresses'])}")
        else:
            print(f"❌ Erro: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")
    
    # Teste 6: Atualizar alias existente
    print("\n✏️ 6. ATUALIZANDO ALIAS EXISTENTE")
    print("-" * 40)
    
    try:
        update_data = {
            "descr": "Alias atualizado via API - nova descrição",
            "addresses": [
                {
                    "address": "192.168.1.204",
                    "detail": "Dispositivo atualizado 1"
                },
                {
                    "address": "192.168.1.205",
                    "detail": "Dispositivo atualizado 2"
                },
                {
                    "address": "192.168.1.206",
                    "detail": "Dispositivo atualizado 3"
                }
            ]
        }
        
        response = requests.patch(
            f"{base_url}/aliases-db/teste_api_iot_edu_v3",
            json=update_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Alias atualizado com sucesso!")
            print(f"   - Nome: {data['name']}")
            print(f"   - Tipo: {data['alias_type']}")
            print(f"   - Nova descrição: {data['descr']}")
            print(f"   - Novos endereços: {len(data['addresses'])}")
            for i, addr in enumerate(data['addresses']):
                print(f"     {i+1}. {addr['address']}: {addr['detail']}")
        else:
            print(f"❌ Erro: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")
    
    print("\n🎉 TESTES CONCLUÍDOS!")

if __name__ == "__main__":
    test_aliases()
