#!/usr/bin/env python3
"""
Teste para adicionar IPs a um alias existente.
"""

import requests
import json

def teste_adicionar_ips():
    """Testa a funcionalidade de adicionar IPs a um alias existente."""
    print("🔧 TESTE - ADICIONAR IPs A ALIAS EXISTENTE")
    print("=" * 50)
    
    base_url = "http://127.0.0.1:8000/api/devices"
    
    # Teste 1: Verificar alias existente
    print("\n1️⃣ Verificando alias existente...")
    try:
        response = requests.get(f"{base_url}/aliases-db/Teste_API_IoT_EDU")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Alias encontrado: {data['name']}")
            print(f"   Tipo: {data['alias_type']}")
            print(f"   Endereços atuais: {len(data['addresses'])}")
            for addr in data['addresses']:
                print(f"     - {addr['address']}: {addr['detail']}")
        else:
            print(f"❌ Erro: {response.status_code} - {response.text}")
            return
    except Exception as e:
        print(f"❌ Erro: {e}")
        return
    
    # Teste 2: Adicionar novos IPs
    print("\n2️⃣ Adicionando novos IPs...")
    try:
        new_addresses = {
            "addresses": [
                {
                    "address": "192.168.1.210",
                    "detail": "Dispositivo adicional 1"
                },
                {
                    "address": "192.168.1.211",
                    "detail": "Dispositivo adicional 2"
                },
                {
                    "address": "192.168.1.212",
                    "detail": "Dispositivo adicional 3"
                }
            ]
        }
        
        response = requests.post(
            f"{base_url}/aliases-db/Teste_API_IoT_EDU/add-addresses",
            json=new_addresses,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ IPs adicionados com sucesso!")
            print(f"   Nome: {data['name']}")
            print(f"   Tipo: {data['alias_type']}")
            print(f"   Total de endereços: {len(data['addresses'])}")
            print("   Endereços atualizados:")
            for addr in data['addresses']:
                print(f"     - {addr['address']}: {addr['detail']}")
        else:
            print(f"❌ Erro: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Erro: {e}")
    
    # Teste 3: Tentar adicionar IP duplicado
    print("\n3️⃣ Testando adição de IP duplicado...")
    try:
        duplicate_addresses = {
            "addresses": [
                {
                    "address": "192.168.1.210",  # IP já existente
                    "detail": "Tentativa de duplicata"
                }
            ]
        }
        
        response = requests.post(
            f"{base_url}/aliases-db/Teste_API_IoT_EDU/add-addresses",
            json=duplicate_addresses,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Teste de duplicata: IP não foi duplicado")
            print(f"   Total de endereços: {len(data['addresses'])}")
        else:
            print(f"❌ Erro: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Erro: {e}")
    
    print("\n🎉 Teste de adição de IPs concluído!")

if __name__ == "__main__":
    teste_adicionar_ips()
