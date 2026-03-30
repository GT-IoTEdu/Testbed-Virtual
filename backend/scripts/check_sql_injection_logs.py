"""
Script para verificar logs de SQL Injection no Zeek.
"""
import sys
import os
import requests
import json

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services_firewalls.institution_config_service import InstitutionConfigService

def check_sql_injection_logs():
    """Verifica logs de SQL Injection no Zeek."""
    
    print("=" * 60)
    print("🔍 VERIFICANDO LOGS DE SQL INJECTION NO ZEEK")
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
    
    # Testar endpoint
    test_url = f"{base_url}/alert_data.php"
    params = {
        'logfile': 'notice.log',
        'maxlines': 500
    }
    headers = {
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/json'
    }
    
    print(f"\n🌐 Buscando logs de notice.log...")
    print("-" * 60)
    
    try:
        response = requests.get(test_url, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Total de logs: {data.get('total_lines', 0)}")
            
            # Filtrar logs de SQL Injection
            sql_logs = []
            for log in data.get('data', []):
                note = str(log.get('note', '')).lower()
                if 'sql' in note and 'injection' in note:
                    sql_logs.append(log)
            
            print(f"\n🔍 Logs de SQL Injection encontrados: {len(sql_logs)}")
            print("-" * 60)
            
            for idx, log in enumerate(sql_logs, 1):
                print(f"\n📋 Log {idx}:")
                print(f"   Note: {log.get('note')}")
                print(f"   Msg: {log.get('msg')}")
                print(f"   Src: {log.get('src')}")
                print(f"   Dst: {log.get('dst')}")
                print(f"   TS: {log.get('ts')}")
                print(f"   Campos disponíveis: {list(log.keys())[:10]}...")
        elif response.status_code == 404:
            content_type = response.headers.get('Content-Type', '').lower()
            if 'application/json' in content_type:
                try:
                    error_data = response.json()
                    print(f"⚠️ {error_data.get('error', 'Arquivo não encontrado')}")
                    print(f"   O arquivo notice.log ainda não existe (normal se o Zeek ainda não criou)")
                except:
                    print(f"❌ Erro 404 mas não conseguiu parsear JSON")
            else:
                print(f"❌ Erro 404 - Endpoint não encontrado (retornou HTML)")
                print(f"   Resposta: {response.text[:200]}")
        else:
            print(f"❌ Erro {response.status_code}: {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ Erro: {e}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    check_sql_injection_logs()

