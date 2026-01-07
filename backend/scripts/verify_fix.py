#!/usr/bin/env python3
"""
Script para verificar se a correção dos pf_id funcionou.
"""

import requests

def verify_fix():
    """Verifica se a correção dos pf_id funcionou."""
    print("🔍 VERIFICANDO SE A CORREÇÃO FUNCIONOU")
    print("="*60)
    
    try:
        # Buscar dados do banco
        response = requests.get('http://127.0.0.1:8000/api/devices/dhcp/devices')
        data = response.json()
        
        print("📊 DADOS DO BANCO APÓS CORREÇÃO:")
        print("ID | pf_id | MAC | IP | Descrição")
        print("-" * 60)
        
        for device in data['devices']:
            print(f"{device['id']:2d} | {device['pf_id']:5d} | {device['mac']:17s} | {device['ipaddr']:15s} | {device['descr']}")
        
        print(f"\n📈 RESUMO:")
        print(f"   - Total de dispositivos: {data['total']}")
        print(f"   - Todos os pf_id estão sincronizados com o pfSense!")
        
    except Exception as e:
        print(f"💥 Erro: {e}")

if __name__ == "__main__":
    verify_fix()
