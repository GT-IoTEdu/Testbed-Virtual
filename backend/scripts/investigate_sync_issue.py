"""
Script para investigar problemas de sincronização entre Zeek, Banco de Dados e View
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import json
from datetime import datetime, timedelta
from db.session import SessionLocal
from db.models import ZeekIncident
from services_scanners.zeek_service import ZeekService
from services_scanners.zeek_models import ZeekLogType, ZeekLogRequest

def check_monitor_status():
    """Verifica o status do monitor via API"""
    print("\n" + "="*60)
    print("1️⃣ VERIFICANDO STATUS DO MONITOR")
    print("="*60)
    
    try:
        base_url = "http://127.0.0.1:8000"
        response = requests.get(f"{base_url}/api/scanners/zeek/monitor/status", timeout=5)
        
        if response.status_code == 200:
            status = response.json()
            print(f"   ✅ Monitor está rodando: {status.get('is_running', False)}")
            print(f"   📊 Estatísticas:")
            stats = status.get('stats', {})
            print(f"      - Verificações: {stats.get('total_checks', 0)}")
            print(f"      - Logs processados: {stats.get('total_logs_processed', 0)}")
            print(f"      - Incidentes salvos: {stats.get('total_incidents', 0)}")
            print(f"      - Erros: {stats.get('errors', 0)}")
            print(f"      - Arquivo não encontrado: {stats.get('file_not_found_count', 0)}x")
            print(f"   ⏰ Última verificação: {status.get('last_check_time', 'N/A')}")
            return status
        else:
            print(f"   ❌ Erro ao verificar monitor: {response.status_code}")
            return None
    except Exception as e:
        print(f"   ❌ Erro ao conectar com servidor: {e}")
        print(f"   💡 Certifique-se de que o servidor está rodando")
        return None

def check_zeek_logs():
    """Verifica logs disponíveis no Zeek"""
    print("\n" + "="*60)
    print("2️⃣ VERIFICANDO LOGS DO ZEEK")
    print("="*60)
    
    try:
        service = ZeekService()
        request = ZeekLogRequest(
            logfile=ZeekLogType.NOTICE,
            maxlines=100,
            hours_ago=24
        )
        
        response = service.get_logs(request)
        
        if response.success:
            print(f"   ✅ Logs retornados: {len(response.logs)}")
            print(f"   📋 Últimos 5 logs:")
            for i, log in enumerate(response.logs[:5], 1):
                note = log.get('note', 'N/A')
                src = log.get('src', 'N/A')
                ts = log.get('ts', {})
                if isinstance(ts, dict):
                    ts_str = ts.get('iso', 'N/A')
                else:
                    ts_str = str(ts)
                print(f"      {i}. Note: {note}, Src: {src}, TS: {ts_str}")
            
            # Detectar incidentes
            incidents_detected = []
            for log in response.logs:
                normalized = service._normalize_log_fields(log)
                incident = service._detect_incident_in_log(normalized, ZeekLogType.NOTICE)
                if incident:
                    incidents_detected.append(incident)
            
            print(f"   🔍 Incidentes detectados nos logs: {len(incidents_detected)}")
            for i, incident in enumerate(incidents_detected[:5], 1):
                print(f"      {i}. {incident.incident_type} - IP: {incident.device_ip}")
            
            return response.logs, incidents_detected
        else:
            print(f"   ❌ Erro ao buscar logs: {response.message}")
            return [], []
    except Exception as e:
        print(f"   ❌ Erro ao verificar logs do Zeek: {e}")
        import traceback
        traceback.print_exc()
        return [], []

def check_database_incidents():
    """Verifica incidentes no banco de dados"""
    print("\n" + "="*60)
    print("3️⃣ VERIFICANDO INCIDENTES NO BANCO DE DADOS")
    print("="*60)
    
    try:
        db = SessionLocal()
        try:
            # Total de incidentes
            total = db.query(ZeekIncident).count()
            print(f"   📊 Total de incidentes: {total}")
            
            # Incidentes das últimas 24 horas
            since = datetime.now() - timedelta(hours=24)
            recent = db.query(ZeekIncident).filter(
                ZeekIncident.detected_at >= since
            ).order_by(ZeekIncident.detected_at.desc()).all()
            
            print(f"   📊 Incidentes nas últimas 24 horas: {len(recent)}")
            
            if recent:
                print(f"   📋 Últimos 5 incidentes:")
                for i, incident in enumerate(recent[:5], 1):
                    print(f"      {i}. ID={incident.id}, Tipo={incident.incident_type}, IP={incident.device_ip}, Detectado={incident.detected_at}")
            
            # Incidentes não processados
            unprocessed = db.query(ZeekIncident).filter(
                ZeekIncident.processed_at.is_(None)
            ).count()
            print(f"   ⚠️ Incidentes não processados: {unprocessed}")
            
            return recent
        finally:
            db.close()
    except Exception as e:
        print(f"   ❌ Erro ao verificar banco de dados: {e}")
        import traceback
        traceback.print_exc()
        return []

def compare_zeek_vs_database(zeek_incidents, db_incidents):
    """Compara incidentes do Zeek com os do banco"""
    print("\n" + "="*60)
    print("4️⃣ COMPARANDO ZEEK VS BANCO DE DADOS")
    print("="*60)
    
    if not zeek_incidents:
        print("   ⚠️ Nenhum incidente detectado no Zeek")
        return
    
    if not db_incidents:
        print("   ⚠️ Nenhum incidente no banco de dados")
        return
    
    # Criar conjunto de chaves dos incidentes do banco (IP + Tipo + Timestamp aproximado)
    db_keys = set()
    for incident in db_incidents:
        # Arredondar timestamp para minutos para comparação
        detected_minute = incident.detected_at.replace(second=0, microsecond=0)
        key = (incident.device_ip, incident.incident_type, detected_minute)
        db_keys.add(key)
    
    # Verificar quais incidentes do Zeek não estão no banco
    missing = []
    for zeek_incident in zeek_incidents:
        detected_minute = zeek_incident.detected_at.replace(second=0, microsecond=0)
        key = (zeek_incident.device_ip, zeek_incident.incident_type, detected_minute)
        
        if key not in db_keys:
            missing.append(zeek_incident)
    
    if missing:
        print(f"   ⚠️ {len(missing)} incidente(s) do Zeek não encontrado(s) no banco:")
        for i, incident in enumerate(missing[:10], 1):
            print(f"      {i}. {incident.incident_type} - IP: {incident.device_ip} - Detectado: {incident.detected_at}")
    else:
        print(f"   ✅ Todos os incidentes do Zeek estão no banco de dados")

def main():
    print("\n" + "="*60)
    print("🔍 INVESTIGAÇÃO DE SINCRONIZAÇÃO: ZEEK → BANCO → VIEW")
    print("="*60)
    
    # 1. Verificar monitor
    monitor_status = check_monitor_status()
    
    # 2. Verificar logs do Zeek
    zeek_logs, zeek_incidents = check_zeek_logs()
    
    # 3. Verificar banco de dados
    db_incidents = check_database_incidents()
    
    # 4. Comparar
    compare_zeek_vs_database(zeek_incidents, db_incidents)
    
    # 5. Resumo e recomendações
    print("\n" + "="*60)
    print("💡 RECOMENDAÇÕES")
    print("="*60)
    
    if not monitor_status or not monitor_status.get('is_running'):
        print("   ⚠️ Monitor não está rodando - reinicie o servidor")
    
    if zeek_incidents and not db_incidents:
        print("   ⚠️ Há incidentes no Zeek mas nenhum no banco - verifique logs do monitor")
    
    if zeek_logs and not zeek_incidents:
        print("   ⚠️ Há logs no Zeek mas nenhum incidente detectado - verifique detecção")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    main()

