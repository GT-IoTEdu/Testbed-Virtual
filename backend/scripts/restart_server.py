#!/usr/bin/env python3
"""
Script para reiniciar o servidor e testar os endpoints de aliases.
"""

import subprocess
import time
import requests
import json

def restart_server():
    """Reinicia o servidor FastAPI."""
    print("🔄 REINICIANDO O SERVIDOR")
    print("="*40)
    
    try:
        # Parar o servidor atual (se estiver rodando)
        print("1. Parando servidor atual...")
        subprocess.run(["taskkill", "/f", "/im", "python.exe"], capture_output=True)
        time.sleep(2)
        
        # Iniciar novo servidor
        print("2. Iniciando novo servidor...")
        process = subprocess.Popen(
            ["python", "main.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Aguardar o servidor inicializar
        print("3. Aguardando inicialização...")
        time.sleep(5)
        
        # Verificar se está rodando
        try:
            response = requests.get("http://127.0.0.1:8000/docs", timeout=10)
            if response.status_code == 200:
                print("✅ Servidor reiniciado com sucesso!")
                return process
            else:
                print("❌ Servidor não respondeu corretamente")
                return None
        except requests.exceptions.RequestException:
            print("❌ Servidor não está respondendo")
            return None
            
    except Exception as e:
        print(f"❌ Erro ao reiniciar servidor: {e}")
        return None

def test_endpoints():
    """Testa os endpoints de aliases."""
    print("\n🧪 TESTANDO ENDPOINTS")
    print("="*40)
    
    base_url = "http://127.0.0.1:8000/api/devices"
    
    # Teste 1: Verificar se o endpoint POST existe
    print("\n1. Verificando endpoint POST /aliases/save")
    try:
        response = requests.post(f"{base_url}/aliases/save")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Endpoint funcionando!")
            data = response.json()
            print(f"   - Aliases salvos: {data['aliases_saved']}")
            print(f"   - Aliases atualizados: {data['aliases_updated']}")
        else:
            print(f"❌ Erro: {response.text}")
    except Exception as e:
        print(f"❌ Erro AQUI: {e}")
    
    # Teste 2: Verificar endpoint GET /aliases
    print("\n2. Verificando endpoint GET /aliases")
    try:
        response = requests.get(f"{base_url}/aliases")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Endpoint funcionando!")
            data = response.json()
            print(f"   - Total de aliases: {data['total']}")
        else:
            print(f"❌ Erro: {response.text}")
    except Exception as e:
        print(f"❌ Erro: {e}")
    
    # Teste 3: Verificar endpoint GET /aliases/statistics
    print("\n3. Verificando endpoint GET /aliases/statistics")
    try:
        response = requests.get(f"{base_url}/aliases/statistics")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Endpoint funcionando!")
            data = response.json()
            print(f"   - Total de aliases: {data['total_aliases']}")
        else:
            print(f"❌ Erro: {response.text}")
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    # Reiniciar servidor
    process = restart_server()
    
    if process:
        # Testar endpoints
        test_endpoints()
        
        # Parar servidor
        print("\n🛑 Parando servidor...")
        process.terminate()
        process.wait()
        print("✅ Servidor parado")
    else:
        print("❌ Não foi possível reiniciar o servidor")
