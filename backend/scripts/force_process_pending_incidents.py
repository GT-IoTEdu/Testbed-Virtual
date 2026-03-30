"""
Script para processar manualmente incidentes pendentes do Zeek
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services_scanners.zeek_service import ZeekService
from services_scanners.zeek_models import ZeekLogType, ZeekLogRequest
from datetime import datetime, timedelta

def main():
    print("\n" + "="*60)
    print("🔄 PROCESSANDO MANUALMENTE INCIDENTES PENDENTES DO ZEEK")
    print("="*60)
    
    try:
        service = ZeekService()
        
        # Buscar logs das últimas 24 horas
        request = ZeekLogRequest(
            logfile=ZeekLogType.NOTICE,
            maxlines=500,
            hours_ago=24
        )
        
        print(f"\n📋 Buscando logs do Zeek...")
        response = service.get_logs(request)
        
        if not response.success:
            print(f"❌ Erro ao buscar logs: {response.message}")
            return
        
        print(f"✅ {len(response.logs)} log(s) encontrado(s)")
        
        # Processar cada log
        incidents_saved = 0
        incidents_skipped = 0
        errors = 0
        
        for i, log in enumerate(response.logs, 1):
            try:
                normalized = service._normalize_log_fields(log)
                incident = service._detect_incident_in_log(normalized, ZeekLogType.NOTICE)
                
                if incident:
                    print(f"\n🔍 [{i}/{len(response.logs)}] Incidente detectado:")
                    print(f"   Tipo: {incident.incident_type}")
                    print(f"   IP: {incident.device_ip}")
                    print(f"   Detectado: {incident.detected_at}")
                    
                    # Tentar salvar
                    try:
                        service._save_incident_to_database(incident, normalized)
                        incidents_saved += 1
                        print(f"   ✅ Salvo no banco de dados")
                    except Exception as e:
                        errors += 1
                        print(f"   ❌ Erro ao salvar: {e}")
                else:
                    incidents_skipped += 1
                    note = normalized.get('note', 'N/A')
                    if 'sql' in note.lower() or 'injection' in note.lower():
                        print(f"\n⚠️ [{i}/{len(response.logs)}] Log não gerou incidente: {note}")
            except Exception as e:
                errors += 1
                print(f"❌ Erro ao processar log {i}: {e}")
        
        print("\n" + "="*60)
        print("📊 RESUMO")
        print("="*60)
        print(f"   Logs processados: {len(response.logs)}")
        print(f"   Incidentes salvos: {incidents_saved}")
        print(f"   Incidentes ignorados: {incidents_skipped}")
        print(f"   Erros: {errors}")
        print("="*60)
        
    except Exception as e:
        print(f"❌ Erro geral: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

