#!/usr/bin/env python3
"""
Script simples para limpar duplicatas na tabela dhcp_static_mappings.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Imports diretos para evitar problemas de módulo
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from config import DATABASE_URL

def cleanup_duplicates():
    """Remove duplicatas da tabela dhcp_static_mappings."""
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        print("🔍 Procurando duplicatas...")
        
        # Query para encontrar duplicatas
        query = text("""
            SELECT mac, ipaddr, COUNT(*) as count, MAX(id) as max_id
            FROM dhcp_static_mappings 
            GROUP BY mac, ipaddr 
            HAVING COUNT(*) > 1
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
            
            print(f"  🔸 MAC: {mac}, IP: {ipaddr} - {count} registros (manter ID: {max_id})")
            
            # Remover duplicatas mantendo o mais recente
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
            print(f"    🗑️  Removidos {removed} registros duplicados")
        
        # Commit das alterações
        session.commit()
        
        print(f"✅ Limpeza concluída! {total_removed} registros duplicados removidos.")
        
    except Exception as e:
        print(f"❌ Erro durante a limpeza: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    print("🧹 Iniciando limpeza de duplicatas...")
    cleanup_duplicates()
    print("🏁 Limpeza finalizada!")
