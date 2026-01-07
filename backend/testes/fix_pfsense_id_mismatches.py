#!/usr/bin/env python3
"""
Script para corrigir automaticamente os mismatches de pf_id.
"""

from db.session import SessionLocal
from db.models import DhcpStaticMapping
from services_firewalls.pfsense_client import listar_clientes_dhcp_pfsense

def fix_pfsense_id_mismatches():
    """Corrige os mismatches de pf_id no banco de dados."""
    print("🔧 CORRIGINDO MISMATCHES DE pf_id AUTOMATICAMENTE")
    print("="*70)
    
    try:
        # Buscar dados do pfSense
        pfsense_data = listar_clientes_dhcp_pfsense()
        if not pfsense_data or pfsense_data.get('status') != 'ok':
            print("❌ Erro ao buscar dados do pfSense")
            return
        
        pfsense_servers = pfsense_data.get('data', [])
        
        # Mapear dispositivos do pfSense por MAC
        pfsense_devices = {}
        for server in pfsense_servers:
            for mapping in server.get('staticmap', []):
                mac = mapping.get('mac')
                pfsense_id = mapping.get('id')
                pfsense_devices[mac] = pfsense_id
        
        # Buscar dados do banco
        db = SessionLocal()
        db_devices = db.query(DhcpStaticMapping).all()
        
        print("📊 CORREÇÕES NECESSÁRIAS:")
        corrections_made = 0
        
        try:
            for device in db_devices:
                mac = device.mac
                pfsense_id = pfsense_devices.get(mac)
                
                if pfsense_id is not None and pfsense_id != device.pf_id:
                    old_pf_id = device.pf_id
                    device.pf_id = pfsense_id
                    corrections_made += 1
                    
                    print(f"✅ Corrigido: MAC {mac}")
                    print(f"   pf_id alterado de {old_pf_id} para {pfsense_id}")
                    print(f"   IP: {device.ipaddr}")
                    print(f"   Descrição: {device.descr}")
                    print()
            
            if corrections_made > 0:
                db.commit()
                print(f"🎉 {corrections_made} correções aplicadas com sucesso!")
            else:
                print("✅ Nenhuma correção necessária!")
                
        except Exception as e:
            print(f"❌ Erro ao aplicar correções: {e}")
            db.rollback()
        finally:
            db.close()
            
    except Exception as e:
        print(f"💥 Erro: {e}")

def show_final_comparison():
    """Mostra a comparação final após a correção."""
    print("\n" + "="*70)
    print("📊 COMPARAÇÃO FINAL")
    print("="*70)
    
    try:
        # Buscar dados do pfSense
        pfsense_data = listar_clientes_dhcp_pfsense()
        pfsense_servers = pfsense_data.get('data', [])
        
        # Buscar dados do banco
        db = SessionLocal()
        db_devices = db.query(DhcpStaticMapping).order_by(DhcpStaticMapping.pf_id).all()
        
        print("📊 COMPARAÇÃO FINAL:")
        print("pfSense ID | Banco pf_id | MAC | IP | Descrição | Status")
        print("-" * 80)
        
        # Mapear dispositivos do pfSense por MAC
        pfsense_devices = {}
        for server in pfsense_servers:
            for mapping in server.get('staticmap', []):
                mac = mapping.get('mac')
                pfsense_id = mapping.get('id')
                pfsense_devices[mac] = pfsense_id
        
        # Comparar com banco de dados
        mismatches = 0
        for device in db_devices:
            mac = device.mac
            pfsense_id = pfsense_devices.get(mac)
            
            if pfsense_id is not None:
                if pfsense_id != device.pf_id:
                    status = "❌ MISMATCH"
                    mismatches += 1
                else:
                    status = "✅ OK"
            else:
                status = "⚠️  Não no pfSense"
                pfsense_id = "N/A"
            
            print(f"{str(pfsense_id):>10s} | {device.pf_id:>10d} | {mac:17s} | {device.ipaddr:15s} | {device.descr[:20]:20s} | {status}")
        
        print(f"\n📈 RESUMO FINAL:")
        print(f"   - Total de dispositivos no banco: {len(db_devices)}")
        print(f"   - Total de dispositivos no pfSense: {len(pfsense_devices)}")
        print(f"   - Mismatches restantes: {mismatches}")
        
        if mismatches == 0:
            print("🎉 TODOS OS IDS ESTÃO SINCRONIZADOS!")
        else:
            print(f"⚠️  Ainda há {mismatches} mismatches")
        
        db.close()
        
    except Exception as e:
        print(f"💥 Erro na comparação final: {e}")

if __name__ == "__main__":
    print("🚀 INICIANDO CORREÇÃO AUTOMÁTICA DE MISMATCHES")
    print("="*70)
    
    # Aplicar correções
    fix_pfsense_id_mismatches()
    
    # Mostrar comparação final
    show_final_comparison()
    
    print("\n" + "="*70)
    print("🎯 CORREÇÃO AUTOMÁTICA CONCLUÍDA!")
    print("="*70)
