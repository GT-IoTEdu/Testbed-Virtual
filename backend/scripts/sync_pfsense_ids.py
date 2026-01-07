#!/usr/bin/env python3
"""
Script para comparar e sincronizar IDs do pfSense com pf_id do banco de dados.
"""

from db.session import SessionLocal
from db.models import DhcpStaticMapping
from services_firewalls.pfsense_client import listar_clientes_dhcp_pfsense
import json

def compare_pfsense_and_database():
    """Compara IDs do pfSense com pf_id do banco de dados."""
    print("🔍 COMPARANDO IDS DO PFSENSE COM BANCO DE DADOS")
    print("="*70)
    
    # Buscar dados do pfSense
    try:
        pfsense_data = listar_clientes_dhcp_pfsense()
        if not pfsense_data or pfsense_data.get('status') != 'ok':
            print("❌ Erro ao buscar dados do pfSense")
            return
        
        pfsense_servers = pfsense_data.get('result', {}).get('data', [])
        
        # Buscar dados do banco
        db = SessionLocal()
        db_devices = db.query(DhcpStaticMapping).order_by(DhcpStaticMapping.pf_id).all()
        
        print("📊 COMPARAÇÃO:")
        print("pfSense ID | Banco pf_id | MAC | IP | Descrição | Status")
        print("-" * 80)
        
        # Mapear dispositivos do pfSense por MAC
        pfsense_devices = {}
        for server in pfsense_servers:
            for mapping in server.get('staticmap', []):
                mac = mapping.get('mac')
                pfsense_id = mapping.get('id')
                pfsense_devices[mac] = {
                    'pfsense_id': pfsense_id,
                    'ipaddr': mapping.get('ipaddr'),
                    'cid': mapping.get('cid'),
                    'descr': mapping.get('descr')
                }
        
        # Comparar com banco de dados
        mismatches = []
        for device in db_devices:
            mac = device.mac
            pfsense_device = pfsense_devices.get(mac)
            
            if pfsense_device:
                pfsense_id = pfsense_device['pfsense_id']
                if pfsense_id != device.pf_id:
                    status = f"❌ MISMATCH (pfSense:{pfsense_id} vs Banco:{device.pf_id})"
                    mismatches.append({
                        'device_id': device.id,
                        'mac': mac,
                        'pfsense_id': pfsense_id,
                        'db_pf_id': device.pf_id,
                        'ipaddr': device.ipaddr,
                        'descr': device.descr
                    })
                else:
                    status = "✅ OK"
            else:
                status = "⚠️  Não encontrado no pfSense"
                pfsense_id = "N/A"
            
            print(f"{pfsense_id:10d} | {device.pf_id:10d} | {mac:17s} | {device.ipaddr:15s} | {device.descr[:20]:20s} | {status}")
        
        print(f"\n📈 RESUMO:")
        print(f"   - Total de dispositivos no banco: {len(db_devices)}")
        print(f"   - Total de dispositivos no pfSense: {len(pfsense_devices)}")
        print(f"   - Mismatches encontrados: {len(mismatches)}")
        
        if mismatches:
            print(f"\n🔧 DISPOSITIVOS COM MISMATCH:")
            for mismatch in mismatches:
                print(f"   - MAC: {mismatch['mac']}")
                print(f"     pfSense ID: {mismatch['pfsense_id']}")
                print(f"     Banco pf_id: {mismatch['db_pf_id']}")
                print(f"     IP: {mismatch['ipaddr']}")
                print(f"     Descrição: {mismatch['descr']}")
                print()
        
        db.close()
        
        return mismatches
        
    except Exception as e:
        print(f"💥 Erro: {e}")
        return None

def fix_pfsense_id_mismatches():
    """Corrige os mismatches de pf_id no banco de dados."""
    print("\n" + "="*70)
    print("🔧 CORRIGINDO MISMATCHES DE pf_id")
    print("="*70)
    
    mismatches = compare_pfsense_and_database()
    
    if not mismatches:
        print("✅ Nenhum mismatch encontrado!")
        return
    
    # Buscar dados do pfSense novamente
    try:
        pfsense_data = listar_clientes_dhcp_pfsense()
        pfsense_servers = pfsense_data.get('result', {}).get('data', [])
        
        # Mapear dispositivos do pfSense por MAC
        pfsense_devices = {}
        for server in pfsense_servers:
            for mapping in server.get('staticmap', []):
                mac = mapping.get('mac')
                pfsense_id = mapping.get('id')
                pfsense_devices[mac] = pfsense_id
        
        # Corrigir no banco de dados
        db = SessionLocal()
        
        try:
            for mismatch in mismatches:
                mac = mismatch['mac']
                pfsense_id = pfsense_devices.get(mac)
                
                if pfsense_id is not None:
                    # Atualizar pf_id no banco
                    device = db.query(DhcpStaticMapping).filter(
                        DhcpStaticMapping.id == mismatch['device_id']
                    ).first()
                    
                    if device:
                        old_pf_id = device.pf_id
                        device.pf_id = pfsense_id
                        db.commit()
                        
                        print(f"✅ Corrigido: MAC {mac}")
                        print(f"   pf_id alterado de {old_pf_id} para {pfsense_id}")
                else:
                    print(f"⚠️  Dispositivo {mac} não encontrado no pfSense")
            
            print("\n🎉 Correção concluída!")
            
        except Exception as e:
            print(f"❌ Erro ao corrigir: {e}")
            db.rollback()
        finally:
            db.close()
            
    except Exception as e:
        print(f"💥 Erro ao buscar dados do pfSense: {e}")

def show_final_comparison():
    """Mostra a comparação final após a correção."""
    print("\n" + "="*70)
    print("📊 COMPARAÇÃO FINAL")
    print("="*70)
    
    compare_pfsense_and_database()

if __name__ == "__main__":
    print("🚀 INICIANDO SINCRONIZAÇÃO DE IDS")
    print("="*70)
    
    # Mostrar comparação inicial
    compare_pfsense_and_database()
    
    # Perguntar se deve corrigir
    print("\n" + "="*70)
    response = input("Deseja corrigir os mismatches? (s/n): ").lower().strip()
    
    if response in ['s', 'sim', 'y', 'yes']:
        fix_pfsense_id_mismatches()
        show_final_comparison()
    else:
        print("❌ Correção cancelada pelo usuário")
    
    print("\n" + "="*70)
    print("🎯 SINCRONIZAÇÃO CONCLUÍDA!")
    print("="*70)
