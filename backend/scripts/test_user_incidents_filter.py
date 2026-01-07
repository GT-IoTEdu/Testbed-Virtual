#!/usr/bin/env python3
"""
Script para testar o filtro de incidentes por dispositivos do usuário
"""

import requests
import json
from typing import List, Dict, Any

def test_user_incidents_filter():
    """Testa o filtro de incidentes para usuários comuns"""
    
    base_url = "http://127.0.0.1:8000"
    
    print("🧪 Testando filtro de incidentes por dispositivos do usuário")
    print("=" * 60)
    
    # 1. Buscar todos os incidentes (como gestor)
    print("\n1️⃣ Buscando todos os incidentes (visão de gestor)...")
    try:
        response = requests.get(f"{base_url}/api/scanners/zeek/incidents?hours_ago=24&maxlines=50")
        if response.status_code == 200:
            all_incidents = response.json()
            print(f"✅ Total de incidentes encontrados: {len(all_incidents)}")
            
            # Mostrar alguns incidentes
            if all_incidents:
                print("\n📋 Primeiros 3 incidentes:")
                for i, incident in enumerate(all_incidents[:3]):
                    print(f"   {i+1}. IP: {incident.get('device_ip', 'N/A')} - Tipo: {incident.get('incident_type', 'N/A')}")
        else:
            print(f"❌ Erro ao buscar incidentes: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")
        return
    
    # 2. Buscar dispositivos de um usuário específico
    print("\n2️⃣ Buscando dispositivos de usuários...")
    try:
        # Tentar buscar dispositivos de diferentes usuários
        user_ids = [1, 2, 3]  # IDs de usuários para testar
        
        for user_id in user_ids:
            print(f"\n   Testando usuário ID {user_id}...")
            response = requests.get(f"{base_url}/api/devices/users/{user_id}/devices?current_user_id={user_id}")
            
            if response.status_code == 200:
                data = response.json()
                devices = data if isinstance(data, list) else data.get('devices', [])
                print(f"   ✅ Usuário {user_id}: {len(devices)} dispositivos encontrados")
                
                # Mostrar IPs dos dispositivos
                device_ips = []
                for device in devices:
                    ip = device.get('ipaddr', device.get('ip', ''))
                    if ip and ip != "-":
                        device_ips.append(ip)
                        print(f"      📱 {device.get('cid', 'Sem nome')}: {ip}")
                
                if device_ips:
                    print(f"\n   🔍 Simulando filtro para usuário {user_id}...")
                    print(f"      IPs do usuário: {', '.join(device_ips)}")
                    
                    # Simular filtro no frontend
                    user_incidents = []
                    for incident in all_incidents:
                        incident_ip = incident.get('device_ip', '').lower()
                        if any(device_ip.lower() == incident_ip for device_ip in device_ips):
                            user_incidents.append(incident)
                    
                    print(f"      ✅ Incidentes filtrados: {len(user_incidents)}")
                    
                    if user_incidents:
                        print("      📋 Incidentes do usuário:")
                        for incident in user_incidents:
                            print(f"         • {incident.get('device_ip')} - {incident.get('incident_type')}")
                else:
                    print(f"   ⚠️ Usuário {user_id} não possui dispositivos com IPs válidos")
            else:
                print(f"   ❌ Erro ao buscar dispositivos do usuário {user_id}: {response.status_code}")
                
    except Exception as e:
        print(f"❌ Erro ao buscar dispositivos: {e}")
    
    # 3. Testar endpoint de IPs de dispositivos
    print("\n3️⃣ Testando endpoint de IPs de dispositivos...")
    try:
        response = requests.get(f"{base_url}/api/devices/devices/ips")
        if response.status_code == 200:
            data = response.json()
            device_ips = data.get('device_ips', [])
            print(f"✅ {len(device_ips)} dispositivos com IPs encontrados")
            
            if device_ips:
                print("\n📋 Dispositivos cadastrados:")
                for device in device_ips[:5]:  # Mostrar apenas os primeiros 5
                    print(f"   • {device.get('ip')} - {device.get('hostname')} ({device.get('mac')})")
        else:
            print(f"❌ Erro ao buscar IPs de dispositivos: {response.status_code}")
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 Teste concluído!")

if __name__ == "__main__":
    test_user_incidents_filter()
