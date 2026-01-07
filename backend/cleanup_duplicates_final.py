#!/usr/bin/env python3
"""
Script final para limpar duplicatas na tabela dhcp_static_mappings.
Remove registros duplicados mantendo o mais recente baseado em MAC e IP.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from config import DATABASE_URL

def cleanup_duplicates():
    """Remove duplicatas da tabela dhcp_static_mappings."""
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        print("🧹 Iniciando limpeza final de duplicatas...")
        
        # Query para encontrar duplicatas
        query = text("""
            SELECT mac, ipaddr, COUNT(*) as count, MAX(id) as max_id, 
                   GROUP_CONCAT(id ORDER BY id) as all_ids,
                   GROUP_CONCAT(pf_id ORDER BY id) as all_pf_ids
            FROM dhcp_static_mappings 
            GROUP BY mac, ipaddr 
            HAVING COUNT(*) > 1
            ORDER BY mac, ipaddr
        """)
        
        result = session.execute(query).fetchall()
        
        if not result:
            print("✅ Nenhuma duplicata encontrada!")
            return
        
        print(f"📊 Encontradas {len(result)} duplicatas:")
        
        total_removed = 0
        
        for row in result:
            mac = row[0]
            ipaddr = row[1]
            count = row[2]
            max_id = row[3]
            all_ids = row[4]
            all_pf_ids = row[5]
            
            print(f"\n🔸 MAC: {mac}, IP: {ipaddr}")
            print(f"   📊 {count} registros (IDs: {all_ids})")
            print(f"   🆔 pf_ids: {all_pf_ids}")
            print(f"   ✅ Manter ID: {max_id}")
            
            # Remover duplicatas mantendo o mais recente (maior ID)
            delete_query = text("""
                DELETE FROM dhcp_static_mappings 
                WHERE mac = :mac AND ipaddr = :ipaddr AND id != :max_id
            """)
            
            result_delete = session.execute(delete_query, {
                'mac': mac, 
                'ipaddr': ipaddr, 
                'max_id': max_id
            })
            
            removed = result_delete.rowcount
            total_removed += removed
            print(f"   🗑️  Removidos {removed} registros duplicados")
        
        # Commit das alterações
        session.commit()
        
        print(f"\n✅ Limpeza concluída! {total_removed} registros duplicados removidos.")
        
        # Verificar se ainda há duplicatas
        remaining_query = text("""
            SELECT COUNT(*) as count
            FROM (
                SELECT mac, ipaddr, COUNT(*) as cnt
                FROM dhcp_static_mappings 
                GROUP BY mac, ipaddr 
                HAVING COUNT(*) > 1
            ) as duplicates
        """)
        
        remaining = session.execute(remaining_query).scalar()
        
        if remaining == 0:
            print("✅ Confirmação: Nenhuma duplicata restante!")
        else:
            print(f"⚠️  Ainda há {remaining} duplicatas restantes.")
            
        # Mostrar estatísticas finais
        stats_query = text("""
            SELECT 
                COUNT(*) as total_devices,
                COUNT(DISTINCT mac) as unique_macs,
                COUNT(DISTINCT ipaddr) as unique_ips
            FROM dhcp_static_mappings
        """)
        
        stats = session.execute(stats_query).fetchone()
        print(f"\n📈 Estatísticas finais:")
        print(f"   📱 Total de dispositivos: {stats[0]}")
        print(f"   🔗 MACs únicos: {stats[1]}")
        print(f"   🌐 IPs únicos: {stats[2]}")
        
    except Exception as e:
        print(f"❌ Erro durante a limpeza: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    cleanup_duplicates()
    print("🏁 Limpeza finalizada!")
