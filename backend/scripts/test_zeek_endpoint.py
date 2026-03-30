"""
Script para testar o endpoint da API do Zeek e verificar se está retornando JSON ou HTML.
"""
import sys
import os
import requests
import json

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services_firewalls.institution_config_service import InstitutionConfigService

def test_zeek_endpoint():
    """Testa o endpoint da API do Zeek."""
    
    print("=" * 60)
    print("🔍 TESTE DO ENDPOINT DA API DO ZEEK")
    print("=" * 60)
    
    # Buscar configurações do banco
    institutions = InstitutionConfigService.get_all_institutions()
    if not institutions:
        print("❌ Nenhuma instituição encontrada")
        return
    
    inst = institutions[0]
    config_db = InstitutionConfigService.get_institution_config(inst['id'])
    
    if not config_db:
        print("❌ Configuração da instituição não encontrada")
        return
    
    base_url = config_db.get('zeek_base_url', '').rstrip('/')
    api_token = config_db.get('zeek_key', '')
    
    if not base_url or not api_token:
        print("❌ Configurações do Zeek não encontradas no banco")
        return
    
    print(f"\n📋 Configurações:")
    print(f"   Instituição: {inst['nome']}")
    print(f"   URL Base: {base_url}")
    print(f"   Token: {'***' if api_token else 'NÃO CONFIGURADO'}")
    
    # Testar endpoint
    test_url = f"{base_url}/alert_data.php"
    params = {
        'logfile': 'notice.log',
        'maxlines': 10
    }
    headers = {
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/json'
    }
    
    print(f"\n🌐 Testando endpoint: {test_url}")
    print(f"   Parâmetros: {params}")
    print("-" * 60)
    
    try:
        response = requests.get(test_url, params=params, headers=headers, timeout=10)
        
        print(f"✅ Status Code: {response.status_code}")
        print(f"   Content-Type: {response.headers.get('Content-Type', 'N/A')}")
        print(f"   Content-Length: {len(response.content)} bytes")
        
        # Verificar se é JSON ou HTML
        content_type = response.headers.get('Content-Type', '').lower()
        response_text = response.text[:500]
        
        print(f"\n📄 Resposta (primeiros 500 chars):")
        print("-" * 60)
        print(response_text)
        print("-" * 60)
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"\n✅ Resposta é JSON válido!")
                print(f"   success: {data.get('success', 'N/A')}")
                print(f"   logfile: {data.get('logfile', 'N/A')}")
                print(f"   total_lines: {data.get('total_lines', 'N/A')}")
                if data.get('data'):
                    print(f"   Primeiro log: {json.dumps(data['data'][0], indent=2)[:200]}...")
                else:
                    print(f"   Nenhum log retornado")
            except json.JSONDecodeError as e:
                print(f"\n❌ Resposta não é JSON válido: {e}")
                print(f"   A resposta parece ser: {'HTML' if '<html' in response_text.lower() else 'Texto'}")
        elif response.status_code == 404:
            if 'application/json' in content_type:
                try:
                    error_data = response.json()
                    print(f"\n⚠️ Erro 404 (JSON): {error_data.get('error', 'N/A')}")
                    if 'log file not found' in error_data.get('error', '').lower():
                        print(f"   ℹ️ O arquivo notice.log não existe ainda (normal se o Zeek ainda não criou)")
                except:
                    print(f"\n❌ Erro 404 mas não conseguiu parsear JSON")
            else:
                print(f"\n❌ Erro 404 - Endpoint não encontrado (retornou HTML, não JSON)")
                print(f"   O servidor web não encontrou o arquivo alert_data.php")
                print(f"   Verifique se o arquivo existe no servidor")
        elif response.status_code == 401:
            print(f"\n❌ Erro 401 - Não autorizado")
            print(f"   Verifique se o token está correto")
        else:
            print(f"\n⚠️ Status {response.status_code}")
            print(f"   Resposta: {response_text[:200]}")
            
    except requests.exceptions.ConnectionError:
        print(f"\n❌ Erro de conexão: Não foi possível conectar ao servidor")
        print(f"   Verifique se o pfSense está acessível em {base_url}")
    except requests.exceptions.Timeout:
        print(f"\n❌ Timeout: Servidor não respondeu em 10 segundos")
    except Exception as e:
        print(f"\n❌ Erro: {e}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_zeek_endpoint()

