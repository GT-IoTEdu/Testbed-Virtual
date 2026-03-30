#!/usr/bin/env python3
"""
Script para testar a conexão com o endpoint do Zeek e diagnosticar problemas
"""

import requests
import sys
import os
from dotenv import load_dotenv

# Adicionar o diretório pai ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

def test_zeek_endpoint(base_url: str, token: str):
    """Testa a conexão com o endpoint do Zeek"""
    print("=" * 70)
    print("TESTE DE CONEXÃO COM ENDPOINT DO ZEEK")
    print("=" * 70)
    print(f"\n📡 URL Base: {base_url}")
    print(f"🔑 Token: {token[:20]}... (primeiros 20 caracteres)")
    
    # Testar diferentes variações da URL
    urls_to_test = [
        f"{base_url.rstrip('/')}/alert_data.php",
        f"{base_url}/alert_data.php",
        f"{base_url.rstrip('/')}/zeek-api/alert_data.php",
        f"{base_url}/zeek-api/alert_data.php",
    ]
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    params = {
        'logfile': 'notice.log',
        'maxlines': 1
    }
    
    print("\n🔍 Testando diferentes variações da URL...\n")
    
    for url in urls_to_test:
        print(f"Testando: {url}")
        try:
            response = requests.get(url, params=params, headers=headers, timeout=10)
            
            print(f"  Status Code: {response.status_code}")
            print(f"  Content-Type: {response.headers.get('Content-Type', 'N/A')}")
            print(f"  Content-Length: {len(response.text)} bytes")
            
            if response.status_code == 200:
                print(f"  ✅ SUCESSO! Endpoint encontrado e funcionando!")
                try:
                    json_data = response.json()
                    print(f"  📦 Resposta JSON válida: {json_data.get('success', False)}")
                    if json_data.get('success'):
                        print(f"  📊 Total de linhas: {json_data.get('total_lines', 0)}")
                except:
                    print(f"  ⚠️ Resposta não é JSON válido")
                    print(f"  Primeiros 200 chars: {response.text[:200]}")
                print()
                return True
            elif response.status_code == 404:
                if 'text/html' in response.headers.get('Content-Type', ''):
                    print(f"  ❌ Endpoint não encontrado (servidor retornou HTML)")
                    print(f"  Primeiros 200 chars da resposta: {response.text[:200]}")
                else:
                    print(f"  ℹ️ 404 - Pode ser que o arquivo notice.log não exista ainda")
                    try:
                        json_data = response.json()
                        print(f"  📦 Resposta JSON: {json_data}")
                    except:
                        print(f"  ⚠️ Resposta não é JSON")
            elif response.status_code == 401:
                print(f"  ❌ Não autorizado - verifique o token")
            else:
                print(f"  ⚠️ Status inesperado: {response.status_code}")
                print(f"  Primeiros 200 chars: {response.text[:200]}")
        except requests.exceptions.ConnectionError as e:
            print(f"  ❌ Erro de conexão: {e}")
        except requests.exceptions.Timeout:
            print(f"  ❌ Timeout - servidor não respondeu em 10 segundos")
        except Exception as e:
            print(f"  ❌ Erro: {e}")
        
        print()
    
    print("=" * 70)
    print("DIAGNÓSTICO:")
    print("=" * 70)
    print("\nSe nenhuma URL funcionou, verifique:")
    print("1. O arquivo alert_data.php existe no servidor Zeek?")
    print("2. O servidor web está configurado para executar PHP?")
    print("3. A URL base está correta?")
    print("4. O token está correto?")
    print("\nNo servidor Zeek, o arquivo deve estar em:")
    print("  /usr/local/www/zeek-api/alert_data.php")
    print("\nE o servidor web deve estar configurado para servir esse diretório.")
    
    return False

if __name__ == "__main__":
    # Buscar configurações do banco ou .env
    from services_firewalls.institution_config_service import InstitutionConfigService
    
    # Tentar buscar do banco primeiro
    institutions = InstitutionConfigService.get_all_institutions()
    
    if institutions:
        institution = institutions[0]
        base_url = institution.get('zeek_base_url', '').strip()
        token = institution.get('zeek_key', '').strip()
        
        if base_url and token:
            print(f"📋 Usando configurações da instituição: {institution.get('nome')} (ID: {institution.get('id')})")
            test_zeek_endpoint(base_url, token)
        else:
            print("⚠️ Instituição não tem configurações do Zeek, usando .env...")
            base_url = os.getenv("ZEEK_API_URL", "")
            token = os.getenv("ZEEK_API_TOKEN", "")
            if base_url and token:
                test_zeek_endpoint(base_url, token)
            else:
                print("❌ Nenhuma configuração encontrada!")
    else:
        print("⚠️ Nenhuma instituição encontrada, usando .env...")
        base_url = os.getenv("ZEEK_API_URL", "")
        token = os.getenv("ZEEK_API_TOKEN", "")
        if base_url and token:
            test_zeek_endpoint(base_url, token)
        else:
            print("❌ Nenhuma configuração encontrada!")

