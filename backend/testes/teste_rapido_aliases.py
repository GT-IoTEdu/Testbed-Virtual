#!/usr/bin/env python3
"""
Teste rápido dos endpoints de aliases.
"""

import requests
import json

def teste_rapido():
    """Teste rápido dos endpoints principais."""
    print("🚀 TESTE RÁPIDO - ENDPOINTS DE ALIASES")
    print("=" * 50)
    
    base_url = "http://127.0.0.1:8000/api/devices"
    
    # Teste 1: Listar aliases
    print("\n1️⃣ Listando aliases...")
    try:
        response = requests.get(f"{base_url}/aliases-db")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Total de aliases: {data['total']}")
            print(f"   Primeiro alias: {data['aliases'][0]['name']}")
        else:
            print(f"❌ Erro: {response.status_code}")
    except Exception as e:
        print(f"❌ Erro: {e}")
    
    # Teste 2: Estatísticas
    print("\n2️⃣ Verificando estatísticas...")
    try:
        response = requests.get(f"{base_url}/aliases-db/statistics")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Total de aliases: {data['total_aliases']}")
            print(f"   Total de endereços: {data['total_addresses']}")
        else:
            print(f"❌ Erro: {response.status_code}")
    except Exception as e:
        print(f"❌ Erro: {e}")
    
    # Teste 3: Buscar aliases
    print("\n3️⃣ Buscando aliases...")
    try:
        response = requests.get(f"{base_url}/aliases-db/search?query=Teste")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Encontrados: {data['total_found']} aliases")
        else:
            print(f"❌ Erro: {response.status_code}")
    except Exception as e:
        print(f"❌ Erro: {e}")
    
    # Teste 4: Atualizar alias (se existir)
    print("\n4️⃣ Testando atualização...")
    try:
        update_data = {
            "descr": "Teste de atualização rápida"
        }
        response = requests.patch(
            f"{base_url}/aliases-db/Teste_API_IoT_EDU",
            json=update_data,
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Alias atualizado: {data['name']}")
            print(f"   Nova descrição: {data['descr']}")
        else:
            print(f"❌ Erro: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Erro: {e}")
    
    print("\n🎉 Teste rápido concluído!")

if __name__ == "__main__":
    teste_rapido()
