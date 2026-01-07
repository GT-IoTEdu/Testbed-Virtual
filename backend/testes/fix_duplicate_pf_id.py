#!/usr/bin/env python3
"""
Script para corrigir pf_id duplicado no banco de dados.
"""

from db.session import SessionLocal
from db.models import DhcpStaticMapping
from sqlalchemy import func

def fix_duplicate_pf_id():
    """Corrige pf_id duplicados no banco de dados."""
    db = SessionLocal()
    
    try:
        print("🔧 Corrigindo pf_id duplicados...")
        
        # Encontrar registros com pf_id duplicado
        duplicates = db.query(DhcpStaticMapping.pf_id, func.count(DhcpStaticMapping.id)).filter(
            DhcpStaticMapping.pf_id == 0
        ).group_by(DhcpStaticMapping.pf_id).having(
            func.count(DhcpStaticMapping.id) > 1
        ).all()
        
        if duplicates:
            print(f"Encontrados {len(duplicates)} pf_id duplicados")
            
            # Pegar o registro mais recente com pf_id = 0
            latest_duplicate = db.query(DhcpStaticMapping).filter(
                DhcpStaticMapping.pf_id == 0
            ).order_by(DhcpStaticMapping.created_at.desc()).first()
            
            if latest_duplicate:
                print(f"Registro mais recente com pf_id=0: ID={latest_duplicate.id}, MAC={latest_duplicate.mac}")
                
                # Encontrar o próximo pf_id disponível
                max_pf_id = db.query(DhcpStaticMapping.pf_id).order_by(
                    DhcpStaticMapping.pf_id.desc()
                ).first()
                
                new_pf_id = (max_pf_id[0] if max_pf_id else -1) + 1
                print(f"Atribuindo pf_id={new_pf_id} ao registro ID={latest_duplicate.id}")
                
                # Atualizar o pf_id
                latest_duplicate.pf_id = new_pf_id
                db.commit()
                
                print(f"✅ pf_id atualizado com sucesso para {new_pf_id}")
        else:
            print("✅ Nenhum pf_id duplicado encontrado")
            
    except Exception as e:
        print(f"❌ Erro ao corrigir pf_id: {e}")
        db.rollback()
    finally:
        db.close()

def list_devices():
    """Lista todos os dispositivos para verificar."""
    db = SessionLocal()
    
    try:
        devices = db.query(DhcpStaticMapping).order_by(DhcpStaticMapping.pf_id).all()
        
        print("\n📱 Lista de dispositivos (ordenados por pf_id):")
        print("ID | pf_id | MAC | IP | Descrição")
        print("-" * 60)
        
        for device in devices:
            print(f"{device.id:2d} | {device.pf_id:5d} | {device.mac:17s} | {device.ipaddr:15s} | {device.descr}")
            
    except Exception as e:
        print(f"❌ Erro ao listar dispositivos: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 INICIANDO CORREÇÃO DE pf_id DUPLICADOS")
    print("="*60)
    
    # Listar dispositivos antes da correção
    print("📋 ANTES DA CORREÇÃO:")
    list_devices()
    
    # Corrigir pf_id duplicados
    fix_duplicate_pf_id()
    
    # Listar dispositivos após a correção
    print("\n📋 APÓS A CORREÇÃO:")
    list_devices()
    
    print("\n" + "="*60)
    print("🎯 CORREÇÃO CONCLUÍDA!")
    print("="*60)
