#!/usr/bin/env python3
"""
Script para limpar duplicatas na tabela dhcp_static_mappings.
Remove registros duplicados mantendo o mais recente baseado em MAC e IP.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from .db.session import SessionLocal
from .db.models import DhcpStaticMapping
from sqlalchemy import func
from datetime import datetime

def cleanup_duplicates():
    """Remove duplicatas da tabela dhcp_static_mappings."""
    db = SessionLocal()
    
    try:
        print("🔍 Procurando duplicatas na tabela dhcp_static_mappings...")
        
        # Encontrar duplicatas por MAC e IP
        duplicates = db.query(
            DhcpStaticMapping.mac,
            DhcpStaticMapping.ipaddr,
            func.count(DhcpStaticMapping.id).label('count'),
            func.max(DhcpStaticMapping.id).label('max_id')
        ).group_by(
            DhcpStaticMapping.mac,
            DhcpStaticMapping.ipaddr
        ).having(
            func.count(DhcpStaticMapping.id) > 1
        ).all()
        
        if not duplicates:
            print("✅ Nenhuma duplicata encontrada!")
            return
        
        print(f"📊 Encontradas {len(duplicates)} duplicatas:")
        
        total_removed = 0
        
        for dup in duplicates:
            mac = dup.mac
            ipaddr = dup.ipaddr
            count = dup.count
            max_id = dup.max_id
            
            print(f"  🔸 MAC: {mac}, IP: {ipaddr} - {count} registros (manter ID: {max_id})")
            
            # Buscar todos os registros duplicados
            records = db.query(DhcpStaticMapping).filter(
                DhcpStaticMapping.mac == mac,
                DhcpStaticMapping.ipaddr == ipaddr
            ).order_by(DhcpStaticMapping.id).all()
            
            # Manter o mais recente (maior ID) e remover os outros
            for record in records:
                if record.id != max_id:
                    print(f"    🗑️  Removendo ID: {record.id} (pf_id: {record.pf_id})")
                    db.delete(record)
                    total_removed += 1
        
        # Commit das alterações
        db.commit()
        
        print(f"✅ Limpeza concluída! {total_removed} registros duplicados removidos.")
        
        # Verificar se ainda há duplicatas
        remaining_duplicates = db.query(
            DhcpStaticMapping.mac,
            DhcpStaticMapping.ipaddr,
            func.count(DhcpStaticMapping.id).label('count')
        ).group_by(
            DhcpStaticMapping.mac,
            DhcpStaticMapping.ipaddr
        ).having(
            func.count(DhcpStaticMapping.id) > 1
        ).count()
        
        if remaining_duplicates == 0:
            print("✅ Confirmação: Nenhuma duplicata restante!")
        else:
            print(f"⚠️  Ainda há {remaining_duplicates} duplicatas restantes.")
            
    except Exception as e:
        print(f"❌ Erro durante a limpeza: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("🧹 Iniciando limpeza de duplicatas...")
    cleanup_duplicates()
    print("🏁 Limpeza finalizada!")
