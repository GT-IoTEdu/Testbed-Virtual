"""
Script para testar tempos de detecção e bloqueio em cenário real de ataque SQL Injection.

Este script monitora o seguinte cenário:
1. Atacante executa sqlmap (geração do log notice.log com tag "atacante" pelo Zeek)
2. API detecta o log e salva como incidente
3. API processa o incidente e aplica bloqueio automático

Métricas medidas:
- TtD (Time to Detection): Tempo desde geração do log do Zeek até salvamento no banco
- TtP (Time to Processing): Tempo desde salvamento até processamento
- TtB (Time to Block): Tempo desde detecção até bloqueio efetivo
"""
import sys
import os
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

# Adicionar o diretório backend ao path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from services_scanners.zeek_service import ZeekService
from services_scanners.incident_service import IncidentService
from services_scanners.zeek_models import ZeekLogType
from db.models import ZeekIncident
from db.session import get_db_session
from sqlalchemy import desc

class DetectionBlockingTester:
    """Classe para testar tempos de detecção e bloqueio"""
    
    def __init__(self):
        self.zeek_service = ZeekService()
        self.incident_service = IncidentService()
        self.test_results = []
        
        # Verificar configuração do Zeek
        print(f"\n🔧 Configuração do Zeek Service:")
        print(f"  - URL Base: {self.zeek_service.base_url}")
        print(f"  - Token: {'Configurado' if self.zeek_service.api_token else 'NÃO CONFIGURADO'}")
        print(f"  - Timeout: {self.zeek_service.timeout}s")
    
    def find_zeek_log_timestamp(self, log: Dict[str, Any]) -> Optional[datetime]:
        """
        Extrai o timestamp do log do Zeek.
        
        Args:
            log: Log do Zeek
            
        Returns:
            Timestamp do log ou None
        """
        ts = log.get('ts')
        
        # Tenta diferentes formatos de timestamp
        if isinstance(ts, dict):
            if 'raw' in ts:
                ts = ts['raw']
            elif 'iso' in ts:
                try:
                    return datetime.fromisoformat(ts['iso'].replace('Z', '+00:00'))
                except:
                    pass
        
        if ts is None:
            return None
            
        try:
            if isinstance(ts, (int, float)):
                return datetime.fromtimestamp(ts)
            elif isinstance(ts, str):
                # Tenta converter string para float/int
                return datetime.fromtimestamp(float(ts))
        except (ValueError, TypeError):
            pass
        
        return None
    
    def monitor_zeek_logs(self, target_ip: Optional[str] = None, 
                         max_wait_minutes: int = 10) -> Optional[Dict[str, Any]]:
        """
        Monitora logs notice.log do Zeek procurando por incidentes de SQL Injection com tag "atacante".
        
        Args:
            target_ip: IP específico para monitorar (opcional)
            max_wait_minutes: Tempo máximo de espera em minutos
            
        Returns:
            Dicionário com informações do log detectado
        """
        print("\n" + "=" * 80)
        print("MONITORAMENTO: Procurando por logs notice.log com SQL Injection - Atacante")
        print("=" * 80)
        print(f"🔍 Buscando logs do Zeek (tipo: notice.log)")
        if target_ip:
            print(f"🎯 Filtrando por IP: {target_ip}")
        print(f"⏱️  Timeout: {max_wait_minutes} minutos")
        print("=" * 80)
        
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=max_wait_minutes)
        
        last_checked_logs = set()  # Para evitar duplicatas
        check_count = 0
        
        while datetime.now() < end_time:
            try:
                check_count += 1
                elapsed = (datetime.now() - start_time).total_seconds()
                print(f"\n🔄 Verificação #{check_count} (tempo decorrido: {elapsed:.0f}s)")
                
                # Buscar logs notice do Zeek
                from services_scanners.zeek_models import ZeekLogRequest
                
                request = ZeekLogRequest(
                    logfile=ZeekLogType.NOTICE,
                    maxlines=100,  # Aumentado para pegar mais logs
                    filter_ip=target_ip
                )
                
                response = self.zeek_service.get_logs(request)
                
                if not response.success:
                    print(f"⚠️  Resposta não foi bem-sucedida: {response.message}")
                    time.sleep(5)
                    continue
                
                if response.logs:
                    print(f"📊 Total de {len(response.logs)} log(s) recebido(s) do Zeek")
                    
                    # Procurar por logs de SQL Injection com tag "atacante"
                    for log in response.logs:
                        # Criar hash único do log para evitar reprocessamento
                        log_hash = hash(str(log.get('ts', '')) + str(log.get('note', '')) + 
                                      str(log.get('src', '')))
                        
                        if log_hash in last_checked_logs:
                            continue
                        
                        last_checked_logs.add(log_hash)
                        
                        # Debug: mostrar informações do log
                        note_raw = log.get('note', '')
                        note = note_raw.lower()
                        msg = log.get('msg', '')
                        src = log.get('src') or log.get('id_orig_h', 'unknown')
                        
                        # Debug: mostrar logs que contêm SQL ou injection
                        if 'sql' in note or 'injection' in note:
                            print(f"  🔍 Log encontrado: note='{note_raw}', src='{src}', msg='{msg[:50]}...'")
                        
                        # Verificar se é SQL Injection com tag atacante
                        # Aceita formatos: "SQL_Injection_Attacker", "HTTP::SQL_Injection_Attacker", etc.
                        # Remove "::" e espaços para comparação mais flexível
                        note_clean = note.replace('::', '_').replace(':', '_')
                        is_sql_injection = ('sql' in note_clean and 'injection' in note_clean)
                        is_attacker = 'attacker' in note_clean
                        
                        if is_sql_injection and is_attacker:
                            log_timestamp = self.find_zeek_log_timestamp(log)
                            device_ip = log.get('src') or log.get('id_orig_h') or 'unknown'
                            
                            # Filtrar por IP se target_ip foi especificado
                            if target_ip and device_ip != target_ip:
                                print(f"  ⏭️  Pulando log do IP {device_ip} (esperado: {target_ip})")
                                continue
                            
                            result = {
                                'zeek_log_time': log_timestamp.isoformat() if log_timestamp else None,
                                'device_ip': device_ip,
                                'log_data': log,
                                'note': log.get('note', ''),
                                'msg': log.get('msg', '')
                            }
                            
                            print(f"\n✅ LOG DETECTADO:")
                            print(f"  - IP do atacante: {device_ip}")
                            print(f"  - Tipo: {log.get('note', 'N/A')}")
                            print(f"  - Mensagem: {log.get('msg', 'N/A')[:100]}")
                            print(f"  - Timestamp Zeek: {log_timestamp}")
                            
                            return result
                
                else:
                    print(f"ℹ️  Nenhum log recebido nesta verificação")
                
                # Aguardar antes de verificar novamente
                print(f"⏳ Aguardando 5 segundos antes da próxima verificação...")
                time.sleep(5)
                
            except Exception as e:
                print(f"⚠️  Erro ao buscar logs: {e}")
                import traceback
                traceback.print_exc()
                time.sleep(5)
        
        print(f"\n⏱️  Timeout após {max_wait_minutes} minutos")
        print(f"📊 Total de logs únicos verificados: {len(last_checked_logs)}")
        return None
    
    def monitor_incident_creation(self, device_ip: str, 
                                 zeek_log_time: datetime,
                                 max_wait_minutes: int = 5) -> Optional[ZeekIncident]:
        """
        Monitora a criação de incidente no banco de dados.
        
        Args:
            device_ip: IP do dispositivo
            zeek_log_time: Timestamp do log do Zeek
            max_wait_minutes: Tempo máximo de espera
            
        Returns:
            Incidente criado ou None
        """
        print("\n" + "=" * 80)
        print("MONITORAMENTO: Aguardando criação do incidente no banco de dados")
        print("=" * 80)
        
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=max_wait_minutes)
        
        while datetime.now() < end_time:
            try:
                with get_db_session() as db:
                    # Buscar incidente mais recente do IP
                    incident = db.query(ZeekIncident).filter(
                        ZeekIncident.device_ip == device_ip,
                        ZeekIncident.incident_type.like('%SQL Injection%'),
                        ZeekIncident.incident_type.like('%Atacante%')
                    ).order_by(desc(ZeekIncident.detected_at)).first()
                    
                    if incident:
                        # Verificar se o incidente foi criado após o log do Zeek
                        if incident.detected_at >= zeek_log_time - timedelta(minutes=1):
                            print(f"\n✅ INCIDENTE CRIADO:")
                            print(f"  - ID: {incident.id}")
                            print(f"  - IP: {incident.device_ip}")
                            print(f"  - Tipo: {incident.incident_type}")
                            print(f"  - Detectado em: {incident.detected_at}")
                            print(f"  - Processado em: {incident.processed_at}")
                            
                            return incident
                    
                    time.sleep(2)
                    
            except Exception as e:
                print(f"⚠️  Erro ao buscar incidente: {e}")
                time.sleep(2)
        
        print(f"\n⏱️  Timeout após {max_wait_minutes} minutos")
        return None
    
    def trigger_incident_processing(self) -> Dict[str, Any]:
        """
        Dispara o processamento de incidentes pendentes.
        
        Returns:
            Resultado do processamento
        """
        print("\n" + "=" * 80)
        print("PROCESSAMENTO: Disparando processamento de incidentes pendentes")
        print("=" * 80)
        
        try:
            result = self.incident_service.process_incidents_for_auto_blocking(limit=50)
            
            print(f"\n📊 RESULTADO DO PROCESSAMENTO:")
            print(f"  - Processados: {result.get('processed_count', 0)}")
            print(f"  - Bloqueados: {result.get('blocked_count', 0)}")
            print(f"  - Ignorados: {result.get('skipped_count', 0)}")
            print(f"  - Erros: {result.get('error_count', 0)}")
            
            return result
            
        except Exception as e:
            print(f"❌ Erro ao processar incidentes: {e}")
            return {'success': False, 'error': str(e)}
    
    def monitor_blocking(self, incident: ZeekIncident, 
                        max_wait_minutes: int = 5) -> Optional[datetime]:
        """
        Monitora quando o bloqueio é efetivamente aplicado.
        
        Args:
            incident: Incidente para monitorar
            max_wait_minutes: Tempo máximo de espera
            
        Returns:
            Timestamp do bloqueio ou None
        """
        print("\n" + "=" * 80)
        print("MONITORAMENTO: Aguardando bloqueio efetivo")
        print("=" * 80)
        
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=max_wait_minutes)
        
        while datetime.now() < end_time:
            try:
                with get_db_session() as db:
                    from db.models import DhcpStaticMapping, BlockingFeedbackHistory
                    
                    device = db.query(DhcpStaticMapping).filter(
                        DhcpStaticMapping.ipaddr == incident.device_ip
                    ).first()
                    
                    if device:
                        feedback = db.query(BlockingFeedbackHistory).filter(
                            BlockingFeedbackHistory.dhcp_mapping_id == device.id,
                            BlockingFeedbackHistory.feedback_by == "Sistema Automático"
                        ).order_by(desc(BlockingFeedbackHistory.created_at)).first()
                        
                        if feedback:
                            print(f"\n✅ BLOQUEIO EFETIVADO:")
                            print(f"  - Feedback ID: {feedback.id}")
                            print(f"  - Criado em: {feedback.created_at}")
                            print(f"  - Motivo: {feedback.admin_reason[:100] if feedback.admin_reason else 'N/A'}")
                            
                            return feedback.created_at
                    
                    time.sleep(2)
                    
            except Exception as e:
                print(f"⚠️  Erro ao verificar bloqueio: {e}")
                time.sleep(2)
        
        print(f"\n⏱️  Timeout após {max_wait_minutes} minutos")
        return None
    
    def calculate_times(self, zeek_log_time: datetime,
                       incident: ZeekIncident,
                       blocked_time: Optional[datetime]) -> Dict[str, Any]:
        """
        Calcula todos os tempos de detecção e bloqueio.
        
        Args:
            zeek_log_time: Timestamp do log do Zeek
            incident: Incidente criado
            blocked_time: Timestamp do bloqueio
            
        Returns:
            Dicionário com todos os tempos calculados
        """
        times = {}
        
        # TtD (Time to Detection): Zeek log -> Incidente salvo
        if incident.detected_at and zeek_log_time:
            ttd_delta = incident.detected_at - zeek_log_time
            times['ttd'] = {
                'seconds': ttd_delta.total_seconds(),
                'readable': self._format_time_delta(ttd_delta),
                'zeek_log_time': zeek_log_time.isoformat(),
                'detected_at': incident.detected_at.isoformat()
            }
        
        # TtP (Time to Processing): Incidente salvo -> Processado
        if incident.processed_at and incident.detected_at:
            ttp_delta = incident.processed_at - incident.detected_at
            times['ttp'] = {
                'seconds': ttp_delta.total_seconds(),
                'readable': self._format_time_delta(ttp_delta),
                'detected_at': incident.detected_at.isoformat(),
                'processed_at': incident.processed_at.isoformat()
            }
        
        # TtB (Time to Block): Detecção -> Bloqueio
        if blocked_time and incident.detected_at:
            ttb_delta = blocked_time - incident.detected_at
            times['ttb'] = {
                'seconds': ttb_delta.total_seconds(),
                'readable': self._format_time_delta(ttb_delta),
                'detected_at': incident.detected_at.isoformat(),
                'blocked_at': blocked_time.isoformat()
            }
        
        # TtB desde log do Zeek: Zeek log -> Bloqueio
        if blocked_time and zeek_log_time:
            ttb_from_zeek_delta = blocked_time - zeek_log_time
            times['ttb_from_zeek'] = {
                'seconds': ttb_from_zeek_delta.total_seconds(),
                'readable': self._format_time_delta(ttb_from_zeek_delta),
                'zeek_log_time': zeek_log_time.isoformat(),
                'blocked_at': blocked_time.isoformat()
            }
        
        return times
    
    def _format_time_delta(self, delta: timedelta) -> str:
        """Formata timedelta para string legível"""
        total_seconds = int(delta.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        milliseconds = int((delta.total_seconds() - total_seconds) * 1000)
        
        parts = []
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0:
            parts.append(f"{minutes}m")
        if seconds > 0 or len(parts) == 0:
            parts.append(f"{seconds}s")
        if milliseconds > 0 and len(parts) < 3:
            parts.append(f"{milliseconds}ms")
        
        return " ".join(parts) if parts else "0s"
    
    def run_test(self, target_ip: Optional[str] = None, 
                auto_trigger_processing: bool = True) -> Dict[str, Any]:
        """
        Executa o teste completo de detecção e bloqueio.
        
        Args:
            target_ip: IP específico para monitorar
            auto_trigger_processing: Se True, dispara processamento automaticamente
            
        Returns:
            Resultado completo do teste
        """
        print("\n" + "=" * 80)
        print("INÍCIO DO TESTE: Detecção e Bloqueio Automático")
        print("=" * 80)
        print(f"\n📋 Instruções:")
        print(f"1. Execute um ataque sqlmap contra o servidor alvo")
        if target_ip:
            print(f"2. Certifique-se de que o ataque está sendo executado do IP: {target_ip}")
        print(f"3. O script irá monitorar a detecção e bloqueio automático")
        print(f"\n⏳ Aguardando ataque sqlmap...\n")
        
        if target_ip:
            print(f"💡 Dica: Execute o sqlmap da máquina {target_ip}")
            print(f"   Exemplo: sqlmap -u 'http://<servidor_alvo>/vulnerable.php?id=1' --batch\n")
        
        # Passo 1: Monitorar log do Zeek
        zeek_log = self.monitor_zeek_logs(target_ip, max_wait_minutes=10)
        
        if not zeek_log:
            return {
                'success': False,
                'message': 'Nenhum log de SQL Injection - Atacante detectado no período de monitoramento'
            }
        
        zeek_log_time = datetime.fromisoformat(zeek_log['zeek_log_time']) if zeek_log['zeek_log_time'] else None
        if not zeek_log_time:
            zeek_log_time = datetime.now()
        
        # Passo 2: Monitorar criação do incidente
        incident = self.monitor_incident_creation(
            zeek_log['device_ip'],
            zeek_log_time,
            max_wait_minutes=5
        )
        
        if not incident:
            return {
                'success': False,
                'message': 'Incidente não foi criado no banco de dados',
                'zeek_log': zeek_log
            }
        
        # Passo 3: Disparar processamento (se necessário)
        if auto_trigger_processing and not incident.processed_at:
            processing_result = self.trigger_incident_processing()
            
            # Aguardar um pouco para o processamento completar
            time.sleep(3)
            
            # Atualizar incidente
            incident = self.incident_service.get_incident_by_id(incident.id)
        
        # Passo 4: Monitorar bloqueio
        blocked_time = None
        if incident.processed_at:
            blocked_time = self.monitor_blocking(incident, max_wait_minutes=5)
        
        # Passo 5: Calcular tempos
        times = self.calculate_times(zeek_log_time, incident, blocked_time)
        
        # Resultado final
        result = {
            'success': True,
            'zeek_log': zeek_log,
            'incident': {
                'id': incident.id,
                'device_ip': incident.device_ip,
                'incident_type': incident.incident_type,
                'detected_at': incident.detected_at.isoformat() if incident.detected_at else None,
                'processed_at': incident.processed_at.isoformat() if incident.processed_at else None
            },
            'times': times,
            'blocked': blocked_time is not None,
            'blocked_at': blocked_time.isoformat() if blocked_time else None
        }
        
        # Exibir resultados
        print("\n" + "=" * 80)
        print("RESULTADOS DO TESTE")
        print("=" * 80)
        print(f"\n📊 TEMPOS CALCULADOS:")
        
        if 'ttd' in times:
            print(f"\n⏱️  TtD (Time to Detection):")
            print(f"  - Tempo: {times['ttd']['readable']} ({times['ttd']['seconds']:.3f}s)")
            print(f"  - Zeek log: {times['ttd']['zeek_log_time']}")
            print(f"  - Detectado: {times['ttd']['detected_at']}")
        
        if 'ttp' in times:
            print(f"\n⏱️  TtP (Time to Processing):")
            print(f"  - Tempo: {times['ttp']['readable']} ({times['ttp']['seconds']:.3f}s)")
            print(f"  - Detectado: {times['ttp']['detected_at']}")
            print(f"  - Processado: {times['ttp']['processed_at']}")
        
        if 'ttb' in times:
            print(f"\n⏱️  TtB (Time to Block):")
            print(f"  - Tempo: {times['ttb']['readable']} ({times['ttb']['seconds']:.3f}s)")
            print(f"  - Detectado: {times['ttb']['detected_at']}")
            print(f"  - Bloqueado: {times['ttb']['blocked_at']}")
        
        if 'ttb_from_zeek' in times:
            print(f"\n⏱️  TtB (desde log Zeek):")
            print(f"  - Tempo: {times['ttb_from_zeek']['readable']} ({times['ttb_from_zeek']['seconds']:.3f}s)")
            print(f"  - Zeek log: {times['ttb_from_zeek']['zeek_log_time']}")
            print(f"  - Bloqueado: {times['ttb_from_zeek']['blocked_at']}")
        
        print("\n" + "=" * 80)
        
        return result


def main():
    """Função principal"""
    import argparse
    
    # IP padrão do atacante de teste
    DEFAULT_ATTACKER_IP = "192.168.59.4"
    DEFAULT_ATTACKER_MAC = "24:0a:64:1c:73:44"
    
    parser = argparse.ArgumentParser(
        description='Testa tempos de detecção e bloqueio automático',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Exemplo de uso:
  # Usar IP padrão do atacante ({DEFAULT_ATTACKER_IP})
  python test_detection_blocking_times.py
  
  # Monitorar IP específico
  python test_detection_blocking_times.py --target-ip 192.168.100.10
  
  # Não disparar processamento automaticamente
  python test_detection_blocking_times.py --no-auto-process

Informações do atacante de teste:
  IP: {DEFAULT_ATTACKER_IP}
  MAC: {DEFAULT_ATTACKER_MAC}
        """
    )
    parser.add_argument(
        '--target-ip',
        type=str,
        default=None,
        help=f'IP específico para monitorar (padrão: {DEFAULT_ATTACKER_IP} se não especificado)'
    )
    parser.add_argument(
        '--no-auto-process',
        action='store_true',
        help='Não dispara processamento automaticamente'
    )
    parser.add_argument(
        '--attacker-ip',
        type=str,
        default=DEFAULT_ATTACKER_IP,
        help=f'IP do atacante para usar como padrão (padrão: {DEFAULT_ATTACKER_IP})'
    )
    
    args = parser.parse_args()
    
    # Usar IP do atacante como padrão se target-ip não foi especificado
    target_ip = args.target_ip or args.attacker_ip
    
    print(f"\n📌 Configuração do teste:")
    print(f"  - IP do atacante: {args.attacker_ip}")
    print(f"  - MAC do atacante: {DEFAULT_ATTACKER_MAC}")
    print(f"  - IP monitorado: {target_ip}")
    print(f"  - Processamento automático: {'Desativado' if args.no_auto_process else 'Ativado'}")
    
    try:
        tester = DetectionBlockingTester()
        result = tester.run_test(
            target_ip=target_ip,
            auto_trigger_processing=not args.no_auto_process
        )
        
        if result.get('success'):
            print("\n✅ TESTE CONCLUÍDO COM SUCESSO!")
        else:
            print(f"\n❌ TESTE FALHOU: {result.get('message', 'Erro desconhecido')}")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Teste interrompido pelo usuário")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

