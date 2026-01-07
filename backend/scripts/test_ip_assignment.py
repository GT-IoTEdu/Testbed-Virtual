#!/usr/bin/env python3
"""
Script para testar a funcionalidade de atribuição automática de IPs
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services_firewalls.ip_assignment_service import ip_assignment_service
import config

def test_ip_assignment():
    """Testa a funcionalidade de atribuição de IPs"""
    print("🧪 Testando Atribuição Automática de IPs")
    print("=" * 50)
    
    # 1. Validar configuração
    print("\n1. Validando configuração do range...")
    is_valid, message = ip_assignment_service.validate_ip_range()
    print(f"   ✅ Válido: {is_valid}")
    print(f"   📝 Mensagem: {message}")
    
    if not is_valid:
        print("   ❌ Configuração inválida. Verifique as variáveis de ambiente.")
        return
    
    # 2. Mostrar informações do range
    print("\n2. Informações do range configurado...")
    info = ip_assignment_service.get_range_info()
    print(f"   📊 Range: {info['range_start']} - {info['range_end']}")
    print(f"   📈 Total de IPs: {info['total_ips']}")
    print(f"   🚫 IPs excluídos: {info['excluded_ips']}")
    print(f"   ✅ IPs disponíveis: {info['available_ips']}")
    print(f"   🔒 IPs atribuídos: {info['assigned_ips']}")
    
    # 3. Testar atribuição de IPs
    print("\n3. Testando atribuição de IPs...")
    
    # Atribuir alguns IPs
    assigned_ips = []
    for i in range(3):
        ip = ip_assignment_service.assign_next_available_ip()
        if ip:
            assigned_ips.append(ip)
            print(f"   ✅ IP {i+1} atribuído: {ip}")
        else:
            print(f"   ❌ Falha ao atribuir IP {i+1}")
    
    # 4. Mostrar IPs disponíveis
    print("\n4. Listando IPs disponíveis...")
    available = ip_assignment_service.get_available_ips(5)
    print(f"   📋 Próximos 5 IPs disponíveis: {available}")
    
    # 5. Testar reserva de IP específico
    print("\n5. Testando reserva de IP específico...")
    test_ip = "192.168.100.50"
    success = ip_assignment_service.reserve_ip(test_ip)
    if success:
        print(f"   ✅ IP {test_ip} reservado com sucesso")
    else:
        print(f"   ❌ Falha ao reservar IP {test_ip}")
    
    # 6. Testar liberação de IP
    print("\n6. Testando liberação de IP...")
    if assigned_ips:
        ip_to_release = assigned_ips[0]
        success = ip_assignment_service.release_ip(ip_to_release)
        if success:
            print(f"   ✅ IP {ip_to_release} liberado com sucesso")
        else:
            print(f"   ❌ Falha ao liberar IP {ip_to_release}")
    
    # 7. Testar recarregamento do banco de dados
    print("\n7. Testando recarregamento do banco de dados...")
    ip_assignment_service.refresh_from_db()
    print("   ✅ IPs recarregados do banco de dados")
    
    # 8. Mostrar status final
    print("\n8. Status final...")
    final_info = ip_assignment_service.get_range_info()
    print(f"   📊 IPs atribuídos: {final_info['assigned_ips']}")
    print(f"   ✅ IPs disponíveis: {final_info['available_ips']}")
    print(f"   🗄️ IPs carregados do banco: {len([ip for ip in final_info['assigned_list'] if ip.startswith('192.168.100')])}")
    
    print("\n🎉 Teste concluído!")

if __name__ == "__main__":
    test_ip_assignment()
