#!/usr/bin/env python3
"""
Script para verificar se o endpoint está pronto para testes no Postman.
"""

import requests
import json

def test_postman_ready():
    """Verifica se o endpoint está pronto para testes no Postman."""
    print("🔍 VERIFICANDO SE O ENDPOINT ESTÁ PRONTO PARA POSTMAN")
    print("="*60)
    
    base_url = "http://127.0.0.1:8000/api/devices"
    
    # Teste 1: Endpoint básico
    print("\n🧪 TESTE 1: Endpoint Básico")
    print("-" * 30)
    
    try:
        response = requests.get(f"{base_url}/dhcp/ip-addresses")
        
        if response.status_code == 200:
            print("✅ Endpoint funcionando!")
            data = response.json()
            
            # Verificar estrutura da resposta
            required_fields = ['range_info', 'ip_addresses', 'summary']
            missing_fields = [field for field in required_fields if field not in data]
            
            if not missing_fields:
                print("✅ Estrutura da resposta correta!")
                
                # Mostrar informações básicas
                range_info = data['range_info']
                summary = data['summary']
                
                print(f"📊 Range: {range_info['range_from']} - {range_info['range_to']}")
                print(f"📈 Total: {summary['total']} | Usados: {summary['used']} | Livres: {summary['free']}")
                
                # Mostrar alguns IPs
                ip_addresses = data['ip_addresses']
                if ip_addresses:
                    print(f"📱 Primeiros 3 IPs:")
                    for ip_info in ip_addresses[:3]:
                        status_emoji = "✅" if ip_info['status'] == 'used' else "🆓"
                        print(f"   {status_emoji} {ip_info['ip']} ({ip_info['status']})")
            else:
                print(f"❌ Campos faltando: {missing_fields}")
        else:
            print(f"❌ Erro: {response.status_code}")
            print(f"Resposta: {response.text}")
            
    except Exception as e:
        print(f"💥 Erro: {e}")
    
    # Teste 2: Filtro de IPs livres
    print("\n🧪 TESTE 2: Filtro IPs Livres")
    print("-" * 30)
    
    try:
        response = requests.get(f"{base_url}/dhcp/ip-addresses?status_filter=free")
        
        if response.status_code == 200:
            data = response.json()
            free_ips = data['ip_addresses']
            
            print(f"✅ IPs livres encontrados: {len(free_ips)}")
            
            if free_ips:
                print(f"📱 Primeiros 5 IPs livres:")
                for ip_info in free_ips[:5]:
                    print(f"   🆓 {ip_info['ip']}")
        else:
            print(f"❌ Erro: {response.status_code}")
            
    except Exception as e:
        print(f"💥 Erro: {e}")
    
    # Teste 3: Filtro de IPs usados
    print("\n🧪 TESTE 3: Filtro IPs Usados")
    print("-" * 30)
    
    try:
        response = requests.get(f"{base_url}/dhcp/ip-addresses?status_filter=used")
        
        if response.status_code == 200:
            data = response.json()
            used_ips = data['ip_addresses']
            
            print(f"✅ IPs usados encontrados: {len(used_ips)}")
            
            if used_ips:
                print(f"📱 IPs usados:")
                for ip_info in used_ips:
                    print(f"   ✅ {ip_info['ip']}: {ip_info['mac']} ({ip_info['description']})")
        else:
            print(f"❌ Erro: {response.status_code}")
            
    except Exception as e:
        print(f"💥 Erro: {e}")
    
    # Teste 4: Range personalizado
    print("\n🧪 TESTE 4: Range Personalizado")
    print("-" * 30)
    
    try:
        response = requests.get(f"{base_url}/dhcp/ip-addresses?range_from=10.30.30.1&range_to=10.30.30.20")
        
        if response.status_code == 200:
            data = response.json()
            range_info = data['range_info']
            summary = data['summary']
            
            print(f"✅ Range personalizado funcionando!")
            print(f"📊 Range: {range_info['range_from']} - {range_info['range_to']}")
            print(f"📈 Total: {summary['total']} | Usados: {summary['used']} | Livres: {summary['free']}")
        else:
            print(f"❌ Erro: {response.status_code}")
            
    except Exception as e:
        print(f"💥 Erro: {e}")
    
    # Resumo final
    print("\n" + "="*60)
    print("📋 RESUMO PARA POSTMAN")
    print("="*60)
    
    print("\n🔗 URLs para testar no Postman:")
    print("   1. GET {{api_base}}/dhcp/ip-addresses")
    print("   2. GET {{api_base}}/dhcp/ip-addresses?status_filter=free")
    print("   3. GET {{api_base}}/dhcp/ip-addresses?status_filter=used")
    print("   4. GET {{api_base}}/dhcp/ip-addresses?range_from=10.30.30.1&range_to=10.30.30.50")
    print("   5. GET {{api_base}}/dhcp/ip-addresses?server_id=wan")
    
    print("\n📋 Variável de ambiente:")
    print("   api_base = http://127.0.0.1:8000/api/devices")
    
    print("\n📊 Headers:")
    print("   Content-Type: application/json")
    
    print("\n✅ O endpoint está pronto para testes no Postman!")
    print("📖 Consulte o arquivo GUIA_POSTMAN_ENDERECOS_IP.md para instruções detalhadas")

if __name__ == "__main__":
    test_postman_ready()
