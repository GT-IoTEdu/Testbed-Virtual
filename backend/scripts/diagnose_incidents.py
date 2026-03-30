"""
Script para diagnosticar por que os incidentes não estão sendo salvos.
"""
import sys
import os
import logging

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services_scanners.zeek_monitor import get_zeek_monitor
from services_scanners.zeek_service import ZeekService
from services_scanners.zeek_models import ZeekLogType, ZeekLogRequest
from db.models import ZeekIncident
from db.session import SessionLocal
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def diagnose():
    """Diagnostica problemas com incidentes."""
    
    print("=" * 60)
    print("🔍 DIAGNÓSTICO DE INCIDENTES")
    print("=" * 60)
    
    # 1. Verificar se o monitor está rodando
    print("\n1️⃣ Verificando monitor...")
    print("   ℹ️ Nota: O monitor só existe no processo do servidor.")
    print("   ℹ️ Para verificar se está rodando, acesse: GET /api/scanners/zeek/monitor/status")
    
    monitor = get_zeek_monitor()
    if monitor:
        status = monitor.get_status()
        print(f"   ✅ Monitor encontrado: {status.get('is_running')}")
        print(f"   Estatísticas: {status.get('stats')}")
        print(f"   Última verificação: {status.get('last_check_time')}")
    else:
        print("   ⚠️ Monitor não encontrado neste processo (normal se servidor não está rodando)")
        print("   💡 Para iniciar o monitor, inicie o servidor com: python start_server.py")
        print("   💡 O monitor será iniciado automaticamente no startup do servidor")
    
    # 2. Verificar incidentes no banco
    print("\n2️⃣ Verificando incidentes no banco...")
    db = SessionLocal()
    try:
        total = db.query(ZeekIncident).count()
        recent = db.query(ZeekIncident).filter(
            ZeekIncident.detected_at >= datetime.now() - timedelta(hours=1)
        ).count()
        print(f"   Total de incidentes: {total}")
        print(f"   Incidentes nas últimas 1 hora: {recent}")
        
        if recent > 0:
            latest = db.query(ZeekIncident).order_by(ZeekIncident.detected_at.desc()).first()
            print(f"   Último incidente: ID={latest.id}, Tipo={latest.incident_type}, IP={latest.device_ip}, Detectado={latest.detected_at}")
    finally:
        db.close()
    
    # 3. Testar busca de logs
    print("\n3️⃣ Testando busca de logs do Zeek...")
    try:
        zeek_service = ZeekService()
        request = ZeekLogRequest(
            logfile=ZeekLogType.NOTICE,
            maxlines=10,
            start_time=datetime.now() - timedelta(hours=1),
            end_time=datetime.now()
        )
        response = zeek_service.get_logs(request)
        
        if response.success:
            print(f"   ✅ Logs retornados: {len(response.logs)}")
            if response.logs:
                # Testar detecção de incidentes
                for log in response.logs[:3]:
                    normalized = zeek_service._normalize_log_fields(log)
                    incident = zeek_service._detect_incident_in_log(normalized, ZeekLogType.NOTICE)
                    if incident:
                        print(f"   ✅ Incidente detectado: {incident.incident_type} - IP: {incident.device_ip}")
                    else:
                        note = normalized.get('note', '')
                        if note:
                            print(f"   ⚠️ Log não gerou incidente - Note: {note}")
        else:
            print(f"   ❌ Erro ao buscar logs: {response.message}")
    except Exception as e:
        print(f"   ❌ Erro: {e}")
        import traceback
        traceback.print_exc()
    
    # 4. Verificar configuração do Zeek
    print("\n4️⃣ Verificando configuração do Zeek...")
    try:
        zeek_service = ZeekService()
        print(f"   URL: {zeek_service.base_url}")
        print(f"   Token configurado: {'Sim' if zeek_service.api_token else 'Não'}")
    except Exception as e:
        print(f"   ❌ Erro: {e}")
    
    print("\n" + "=" * 60)
    print("💡 DICAS:")
    print("   1. Verifique os logs do servidor para erros")
    print("   2. Verifique se o monitor está iniciando no startup")
    print("   3. Verifique se há logs do Zeek sendo retornados")
    print("   4. Verifique se os logs estão gerando incidentes")
    print("=" * 60)

if __name__ == "__main__":
    diagnose()

