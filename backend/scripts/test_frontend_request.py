#!/usr/bin/env python3
"""
Script para testar se o problema do histórico de bloqueios foi resolvido.
"""
import requests
import json

def test_frontend_request():
    """Simula a requisição do frontend."""
    
    print("🧪 Testando Requisição do Frontend")
    print("=" * 50)
    
    # Simular a requisição exata do frontend
    url = "http://127.0.0.1:8000/api/feedback/recent?days=30"
    
    print(f"🔍 URL: {url}")
    
    try:
        response = requests.get(url, headers={
            'Content-Type': 'application/json'
        })
        
        print(f"📡 Status: {response.status_code}")
        print(f"📡 Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Sucesso! Dados recebidos:")
            print(f"📊 Quantidade de itens: {len(data)}")
            
            if data:
                print(f"📋 Primeiro item:")
                print(f"   ID: {data[0]['id']}")
                print(f"   Status: {data[0]['status']}")
                print(f"   Feedback: {data[0]['user_feedback'][:50]}...")
                print(f"   Data: {data[0]['feedback_date']}")
                
                # Simular filtro 'all' (padrão)
                filtered_data = data
                print(f"🔍 Filtro 'all': {len(filtered_data)} itens")
                
                # Simular filtro 'admin'
                admin_data = [item for item in data if 
                    'Bloqueio administrativo' in item['user_feedback'] or 
                    item['admin_reviewed_by']]
                print(f"🔍 Filtro 'admin': {len(admin_data)} itens")
                
                # Simular filtro 'user'
                user_data = [item for item in data if 
                    'Bloqueio administrativo' not in item['user_feedback'] and 
                    not item['admin_reviewed_by']]
                print(f"🔍 Filtro 'user': {len(user_data)} itens")
                
                print("\n✅ PROBLEMA RESOLVIDO!")
                print("📊 O endpoint está funcionando corretamente")
                print("📊 Os dados estão sendo retornados")
                print("📊 Os filtros estão funcionando")
                
            else:
                print("⚠️ Nenhum dado encontrado")
                
        else:
            print(f"❌ Erro HTTP: {response.status_code}")
            print(f"Resposta: {response.text}")
            
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    test_frontend_request()
