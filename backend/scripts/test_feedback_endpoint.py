#!/usr/bin/env python3
"""
Script para testar o endpoint de feedback de bloqueio.
"""
import requests
import json
import sys
import os

# Adicionar o diretório backend ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Configuração
BASE_URL = "http://127.0.0.1:8000"
FEEDBACK_RECENT_ENDPOINT = f"{BASE_URL}/api/feedback/recent"
FEEDBACK_STATS_ENDPOINT = f"{BASE_URL}/api/feedback/stats"

def test_feedback_endpoints():
    """Testa os endpoints de feedback."""
    
    print("🧪 Testando Endpoints de Feedback de Bloqueio")
    print("=" * 60)
    
    # 1. Testar endpoint de feedbacks recentes
    print("\n1️⃣ Testando endpoint /api/feedback/recent?days=30")
    try:
        response = requests.get(f"{FEEDBACK_RECENT_ENDPOINT}?days=30", timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Resposta: {json.dumps(data, indent=2, ensure_ascii=False)}")
            print(f"Tipo da resposta: {type(data)}")
            print(f"Quantidade de itens: {len(data) if isinstance(data, list) else 'N/A'}")
        else:
            print(f"Erro HTTP: {response.status_code}")
            print(f"Resposta: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro de conexão: {e}")
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
    
    # 2. Testar endpoint de estatísticas
    print("\n2️⃣ Testando endpoint /api/feedback/stats")
    try:
        response = requests.get(FEEDBACK_STATS_ENDPOINT, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Estatísticas: {json.dumps(data, indent=2, ensure_ascii=False)}")
        else:
            print(f"Erro HTTP: {response.status_code}")
            print(f"Resposta: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro de conexão: {e}")
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
    
    # 3. Testar diretamente o serviço
    print("\n3️⃣ Testando serviço diretamente")
    try:
        from services_firewalls.blocking_feedback_service import BlockingFeedbackService
        
        service = BlockingFeedbackService()
        
        # Testar get_recent_feedback
        feedbacks = service.get_recent_feedback(days=30)
        print(f"Feedbacks encontrados pelo serviço: {len(feedbacks)}")
        
        for i, feedback in enumerate(feedbacks[:3]):
            print(f"Feedback {i+1}:")
            print(f"  ID: {feedback.id}")
            print(f"  Status: {feedback.status}")
            print(f"  Feedback: {feedback.user_feedback[:50]}...")
            print(f"  Data: {feedback.feedback_date}")
            print(f"  to_dict(): {feedback.to_dict()}")
            print()
        
        # Testar get_feedback_stats
        stats = service.get_feedback_stats()
        print(f"Estatísticas do serviço: {stats}")
        
    except Exception as e:
        print(f"❌ Erro ao testar serviço: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_feedback_endpoints()
