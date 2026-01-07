#!/usr/bin/env python3
"""
Script de teste direto para a API do Zeek
Testa a conectividade e autenticação diretamente com a API
"""
import requests
import json
import sys


def test_zeek_api_direct():
    """Testa diretamente a API do Zeek"""
    
    # Configurações
    api_url = "http://192.168.100.1/zeek-api/alert_data.php"
    api_token = "y1X6Qn8PpV9jR4kM0wBz7Tf2GhUs3Lc8NrDq5Ke1HxYi0AzF7Gv9MbX2VwJoQp"
    
    print("🔍 Teste Direto da API Zeek")
    print("=" * 50)
    print(f"URL: {api_url}")
    print(f"Token: {api_token[:20]}...")
    print()
    
    # Headers de autenticação
    headers = {
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/json'
    }
    
    # Parâmetros de teste
    params = {
        'logfile': 'http.log',
        'maxlines': 5
    }
    
    try:
        print("📡 Fazendo requisição...")
        response = requests.get(api_url, params=params, headers=headers, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        print()
        
        if response.status_code == 200:
            print("✅ Resposta recebida com sucesso!")
            try:
                json_data = response.json()
                print("📋 Dados JSON:")
                print(json.dumps(json_data, indent=2, ensure_ascii=False))
                
                if json_data.get('success'):
                    print(f"\n🎉 API funcionando! Encontrados {json_data.get('total_lines', 0)} logs")
                else:
                    print(f"\n❌ API retornou erro: {json_data.get('error', 'Erro desconhecido')}")
                    
            except json.JSONDecodeError as e:
                print(f"❌ Erro ao decodificar JSON: {e}")
                print(f"Resposta bruta: {response.text[:500]}...")
                
        elif response.status_code == 401:
            print("❌ Erro de autenticação - Token inválido")
            print(f"Resposta: {response.text}")
            
        elif response.status_code == 404:
            print("❌ API não encontrada - Verifique a URL")
            print(f"Resposta: {response.text}")
            
        else:
            print(f"❌ Erro HTTP {response.status_code}")
            print(f"Resposta: {response.text[:200]}...")
            
    except requests.exceptions.ConnectionError:
        print("❌ Erro de conexão - Verifique se o servidor está acessível")
        print("   - Confirme que está na rede correta")
        print("   - Verifique se 192.168.100.1 é acessível")
        
    except requests.exceptions.Timeout:
        print("❌ Timeout - Servidor não respondeu a tempo")
        
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 50)
    print("Teste concluído!")


if __name__ == "__main__":
    test_zeek_api_direct()
