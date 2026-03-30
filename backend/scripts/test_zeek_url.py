"""
Script para testar a URL da API do Zeek e verificar conectividade.
"""
import sys
import os
import requests

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services_firewalls.institution_config_service import InstitutionConfigService
import config

def test_zeek_url():
    """Testa a URL da API do Zeek."""
    
    print("=" * 60)
    print("🔍 TESTE DE CONECTIVIDADE COM API DO ZEEK")
    print("=" * 60)
    
    # Testar URLs possíveis
    test_urls = [
        "http://192.168.59.2/zeek-api/alert_data.php",
        "http://192.168.59.2/zeek-api",
        "http://192.168.100.1/zeek-api/alert_data.php",
        "http://192.168.100.1/zeek-api",
    ]
    
    # Token de teste
    test_token = "y1X6Qn8PpV9jR4kM0wBz7Tf2GhUs3Lc8NrDq5Ke1HxYi0AzF7Gv9MbX2VwJoQp"
    
    print("\n📋 Configurações do .env:")
    print(f"   ZEEK_API_URL: {config.ZEEK_API_URL}")
    print(f"   ZEEK_API_TOKEN: {'***' if config.ZEEK_API_TOKEN else 'NÃO CONFIGURADO'}")
    
    print("\n📋 Configurações do banco de dados:")
    institutions = InstitutionConfigService.get_all_institutions()
    for inst in institutions:
        config_db = InstitutionConfigService.get_institution_config(inst['id'])
        if config_db:
            print(f"   Instituição {inst['nome']} (ID: {inst['id']}):")
            print(f"      zeek_base_url: {config_db.get('zeek_base_url')}")
            print(f"      zeek_key: {'***' if config_db.get('zeek_key') else 'NÃO CONFIGURADO'}")
    
    print("\n🌐 Testando URLs...")
    print("-" * 60)
    
    for url in test_urls:
        print(f"\n🔍 Testando: {url}")
        try:
            headers = {
                'Authorization': f'Bearer {test_token}',
                'Content-Type': 'application/json'
            }
            params = {
                'logfile': 'notice.log',
                'maxlines': 1
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=5)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                print(f"   ✅ SUCESSO! URL está acessível")
                try:
                    data = response.json()
                    print(f"   Resposta: {str(data)[:100]}...")
                except:
                    print(f"   Resposta (texto): {response.text[:100]}...")
            elif response.status_code == 401:
                print(f"   ⚠️ Erro 401: Token inválido (mas a URL existe!)")
            elif response.status_code == 404:
                print(f"   ❌ Erro 404: URL não encontrada")
                print(f"   Resposta: {response.text[:200]}")
            else:
                print(f"   ⚠️ Status {response.status_code}: {response.text[:100]}")
                
        except requests.exceptions.ConnectionError:
            print(f"   ❌ Erro de conexão: Não foi possível conectar")
        except requests.exceptions.Timeout:
            print(f"   ❌ Timeout: Servidor não respondeu em 5 segundos")
        except Exception as e:
            print(f"   ❌ Erro: {e}")
    
    print("\n" + "=" * 60)
    print("💡 DICAS:")
    print("   1. Verifique se o pfSense está acessível")
    print("   2. Verifique se o arquivo alert_data.php existe no servidor")
    print("   3. Verifique se o servidor web está configurado corretamente")
    print("   4. Teste manualmente no navegador (com autenticação)")
    print("=" * 60)

if __name__ == "__main__":
    test_zeek_url()

