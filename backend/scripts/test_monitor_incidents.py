"""
Script para testar se o monitor está salvando incidentes corretamente.
"""
import sys
import os
import time
import logging

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services_scanners.zeek_monitor import start_zeek_monitor, get_zeek_monitor
from services_scanners.zeek_service import ZeekService
from services_scanners.zeek_models import ZeekLogType, ZeekLogRequest
from db.models import ZeekIncident
from db.session import SessionLocal
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_monitor():
    """Testa o monitor manualmente."""
    
    print("=" * 60)
    print("🧪 TESTE DO MONITOR DE INCIDENTES")
    print("=" * 60)
    
    # 1. Verificar incidentes antes
    print("\n1️⃣ Incidentes antes do teste...")
    db = SessionLocal()
    try:
        before_count = db.query(ZeekIncident).count()
        before_recent = db.query(ZeekIncident).filter(
            ZeekIncident.detected_at >= datetime.now() - timedelta(minutes=5)
        ).count()
        print(f"   Total: {before_count}")
        print(f"   Últimos 5 minutos: {before_recent}")
    finally:
        db.close()
    
    # 2. Iniciar monitor manualmente
    print("\n2️⃣ Iniciando monitor...")
    try:
        monitor = start_zeek_monitor(
            check_interval_seconds=3,
            hours_ago=1,
            maxlines=500
        )
        print(f"   ✅ Monitor iniciado")
        print(f"   Status: {monitor.get_status()}")
    except Exception as e:
        print(f"   ❌ Erro ao iniciar monitor: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 3. Aguardar algumas verificações
    print("\n3️⃣ Aguardando processamento (15 segundos)...")
    for i in range(5):
        time.sleep(3)
        status = monitor.get_status()
        print(f"   Verificação {i+1}/5 - Stats: {status.get('stats')}")
    
    # 4. Verificar incidentes depois
    print("\n4️⃣ Incidentes depois do teste...")
    db = SessionLocal()
    try:
        after_count = db.query(ZeekIncident).count()
        after_recent = db.query(ZeekIncident).filter(
            ZeekIncident.detected_at >= datetime.now() - timedelta(minutes=5)
        ).count()
        print(f"   Total: {after_count}")
        print(f"   Últimos 5 minutos: {after_recent}")
        
        if after_recent > before_recent:
            print(f"   ✅ {after_recent - before_recent} novo(s) incidente(s) detectado(s)!")
            latest = db.query(ZeekIncident).order_by(ZeekIncident.detected_at.desc()).first()
            print(f"   Último: ID={latest.id}, Tipo={latest.incident_type}, IP={latest.device_ip}")
        else:
            print(f"   ⚠️ Nenhum novo incidente detectado")
    finally:
        db.close()
    
    # 5. Parar monitor
    print("\n5️⃣ Parando monitor...")
    try:
        monitor.stop()
        print("   ✅ Monitor parado")
    except Exception as e:
        print(f"   ⚠️ Erro ao parar monitor: {e}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_monitor()

