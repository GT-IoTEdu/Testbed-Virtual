#!/usr/bin/env python3
"""
SIMIR - Sistema Inteligente de Monitoramento de Rede
Monitor avançado de port scan com alertas por email e detecção inteligente
"""

import json
import time
import smtplib
import os
import sys
import signal
import threading
import subprocess
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
import logging
import argparse
import hashlib
from collections import defaultdict, deque
import re

# Configurações padrão
DEFAULT_CONFIG = {
    'email': {
        'smtp_server': 'smtp.gmail.com',
        'smtp_port': 587,
        'sender_email': 'simir.alerts@gmail.com',
        'sender_password': '',
        'recipient_email': 'rafaelbartorres@gmail.com'
    },
    'monitoring': {
        'zeek_log_dir': '/usr/local/zeek/spool/zeek',
        'check_interval': 5,
        'max_alerts_per_hour': 10,
        'alert_cooldown': 300,  # 5 minutos entre alertas similares
        'log_retention_days': 7
    },
    'detection': {
        'port_scan_threshold': 10,
        'time_window_minutes': 5,
        'suspicious_ports': [22, 23, 80, 443, 3389, 445, 135, 139],
        'whitelist_ips': ['127.0.0.1', '::1']
    }
}

# Configurar logging avançado
def setup_logging():
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Logger principal
    logger = logging.getLogger('SIMIR')
    logger.setLevel(logging.INFO)
    
    # Handler para arquivo
    file_handler = logging.FileHandler('/tmp/simir_monitor.log')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter(log_format))
    
    # Handler para console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(log_format))
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

logger = setup_logging()

class ThreatIntelligence:
    """Sistema básico de threat intelligence"""
    
    def __init__(self):
        self.scan_patterns = deque(maxlen=1000)
        self.ip_reputation = defaultdict(lambda: {'score': 0, 'events': []})
        
    def analyze_scan_pattern(self, src_ip, dest_ports, timestamp):
        """Analisa padrões de scan para determinar severidade"""
        severity = 'LOW'
        
        # Fatores de risco
        risk_score = 0
        
        # Número de portas
        if len(dest_ports) > 50:
            risk_score += 3
        elif len(dest_ports) > 20:
            risk_score += 2
        elif len(dest_ports) > 10:
            risk_score += 1
            
        # Portas suspeitas
        suspicious_count = sum(1 for port in dest_ports if port in DEFAULT_CONFIG['detection']['suspicious_ports'])
        risk_score += suspicious_count
        
        # Histórico do IP
        ip_history = self.ip_reputation[src_ip]
        if len(ip_history['events']) > 5:
            risk_score += 2
            
        # Determina severidade
        if risk_score >= 8:
            severity = 'CRITICAL'
        elif risk_score >= 5:
            severity = 'HIGH'
        elif risk_score >= 3:
            severity = 'MEDIUM'
            
        # Atualiza reputação do IP
        ip_history['score'] = risk_score
        ip_history['events'].append({
            'timestamp': timestamp,
            'ports': list(dest_ports),
            'severity': severity
        })
        
        return severity, risk_score
        
    def get_ip_summary(self, ip):
        """Retorna resumo da atividade de um IP"""
        history = self.ip_reputation[ip]
        total_events = len(history['events'])
        
        if total_events == 0:
            return "Primeiro evento registrado"
            
        recent_events = sum(1 for event in history['events'] 
                          if datetime.fromisoformat(event['timestamp']) > datetime.now() - timedelta(hours=24))
        
        return f"Total de eventos: {total_events}, Últimas 24h: {recent_events}, Score atual: {history['score']}"

class AlertManager:
    """Gerenciador de alertas com rate limiting e deduplicação"""
    
    def __init__(self, config):
        self.config = config
        self.sent_alerts = defaultdict(list)
        self.alert_history = deque(maxlen=1000)
        self.state_file = '/tmp/simir_alerts_state.json'
        self.load_state()
        
    def load_state(self):
        """Carrega estado dos alertas"""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                    # Reconstrói histórico de alertas
                    for alert_id, timestamps in state.get('sent_alerts', {}).items():
                        self.sent_alerts[alert_id] = [datetime.fromisoformat(ts) for ts in timestamps]
                    logger.info(f"Estado de alertas carregado: {len(self.sent_alerts)} tipos de alerta")
        except Exception as e:
            logger.error(f"Erro ao carregar estado de alertas: {e}")
            
    def save_state(self):
        """Salva estado dos alertas"""
        try:
            state = {
                'sent_alerts': {
                    alert_id: [ts.isoformat() for ts in timestamps]
                    for alert_id, timestamps in self.sent_alerts.items()
                },
                'last_update': datetime.now().isoformat()
            }
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            logger.error(f"Erro ao salvar estado de alertas: {e}")
            
    def should_send_alert(self, alert_id, severity='MEDIUM'):
        """Verifica se deve enviar alerta baseado em rate limiting"""
        now = datetime.now()
        cooldown = self.config['monitoring']['alert_cooldown']
        max_per_hour = self.config['monitoring']['max_alerts_per_hour']
        
        # Limpa alertas antigos
        if alert_id in self.sent_alerts:
            self.sent_alerts[alert_id] = [
                ts for ts in self.sent_alerts[alert_id]
                if now - ts < timedelta(seconds=cooldown * 3)
            ]
            
        # Verifica cooldown
        if alert_id in self.sent_alerts:
            last_sent = max(self.sent_alerts[alert_id]) if self.sent_alerts[alert_id] else None
            if last_sent and now - last_sent < timedelta(seconds=cooldown):
                logger.debug(f"Alerta {alert_id} em cooldown")
                return False
                
        # Verifica limite por hora
        recent_alerts = sum(1 for ts in self.sent_alerts[alert_id] 
                          if now - ts < timedelta(hours=1))
        if recent_alerts >= max_per_hour:
            logger.warning(f"Limite de alertas por hora atingido para {alert_id}")
            return False
            
        # Severidade crítica ignora alguns limites
        if severity == 'CRITICAL':
            return True
            
        return True
        
    def register_alert_sent(self, alert_id):
        """Registra que um alerta foi enviado"""
        self.sent_alerts[alert_id].append(datetime.now())
        self.save_state()

class SimirMonitor:
    """Monitor principal do SIMIR"""
    
    def __init__(self, config_file=None):
        self.config = self.load_config(config_file)
        self.threat_intel = ThreatIntelligence()
        self.alert_manager = AlertManager(self.config)
        self.running = True
        self.last_position = 0
        self.state_file = '/tmp/simir_monitor_state.json'
        self.load_state()
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGTERM, self.shutdown)
        
    def load_config(self, config_file):
        """Carrega configuração do arquivo ou usa padrões"""
        config = DEFAULT_CONFIG.copy()
        
        if config_file and os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    user_config = json.load(f)
                    # Merge configs recursivamente
                    for section, values in user_config.items():
                        if section in config:
                            config[section].update(values)
                        else:
                            config[section] = values
                logger.info(f"Configuração carregada de {config_file}")
            except Exception as e:
                logger.error(f"Erro ao carregar configuração: {e}")
                
        # Carrega variáveis de ambiente
        if 'SIMIR_EMAIL_PASSWORD' in os.environ:
            config['email']['sender_password'] = os.environ['SIMIR_EMAIL_PASSWORD']
        if 'SIMIR_SENDER_EMAIL' in os.environ:
            config['email']['sender_email'] = os.environ['SIMIR_SENDER_EMAIL']
        if 'SIMIR_RECIPIENT_EMAIL' in os.environ:
            config['email']['recipient_email'] = os.environ['SIMIR_RECIPIENT_EMAIL']
            
        return config
        
    def load_state(self):
        """Carrega estado do monitor"""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                    self.last_position = state.get('last_position', 0)
                    logger.info(f"Estado carregado: posição {self.last_position}")
        except Exception as e:
            logger.error(f"Erro ao carregar estado: {e}")
            
    def save_state(self):
        """Salva estado do monitor"""
        try:
            state = {
                'last_position': self.last_position,
                'last_update': datetime.now().isoformat()
            }
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            logger.error(f"Erro ao salvar estado: {e}")
            
    def shutdown(self, signum, frame):
        """Graceful shutdown"""
        logger.info(f"Recebido sinal {signum}, iniciando shutdown...")
        self.running = False
        
    def send_email_alert(self, subject, body, severity='MEDIUM'):
        """Envia alerta por email"""
        try:
            if not self.config['email']['sender_password']:
                logger.warning("Email não configurado, apenas logando alerta")
                logger.warning(f"ALERTA [{severity}]: {subject}")
                return False
                
            msg = MIMEMultipart()
            msg['From'] = self.config['email']['sender_email']
            msg['To'] = self.config['email']['recipient_email']
            msg['Subject'] = f"[SIMIR {severity}] {subject}"
            
            # Corpo do email com HTML
            html_body = f"""
            <html>
            <body>
            <h2 style="color: {'#d32f2f' if severity == 'CRITICAL' else '#f57c00' if severity == 'HIGH' else '#1976d2'};">
                🚨 ALERTA DE SEGURANÇA SIMIR
            </h2>
            
            <div style="background: #f5f5f5; padding: 15px; border-radius: 5px; margin: 10px 0;">
                <strong>Severidade:</strong> {severity}<br>
                <strong>Timestamp:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br>
                <strong>Sistema:</strong> SIMIR - Sonda Inteligente de Monitoramento
            </div>
            
            <h3>Detalhes do Alerta:</h3>
            <div style="background: #fff; padding: 15px; border-left: 4px solid #2196F3;">
                {body.replace('\n', '<br>')}
            </div>
            
            <hr>
            <p style="font-size: 12px; color: #666;">
                Este é um alerta automático do sistema SIMIR.<br>
                Para mais informações, verifique os logs do sistema.
            </p>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(html_body, 'html'))
            
            # Conectar e enviar
            server = smtplib.SMTP(self.config['email']['smtp_server'], self.config['email']['smtp_port'])
            server.starttls()
            server.login(self.config['email']['sender_email'], self.config['email']['sender_password'])
            
            text = msg.as_string()
            server.sendmail(self.config['email']['sender_email'], self.config['email']['recipient_email'], text)
            server.quit()
            
            logger.info(f"Email [{severity}] enviado com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao enviar email: {e}")
            return False
            
    def parse_zeek_notice(self, line):
        """Parse avançado de logs do Zeek"""
        try:
            # Skip comentários e linhas vazias
            if not line.strip() or line.startswith('#'):
                return None
                
            # Detecta formato JSON ou TSV
            if line.strip().startswith('{'):
                data = json.loads(line)
            else:
                # TSV parsing
                fields = line.strip().split('\t')
                if len(fields) < 6:
                    return None
                    
                data = {
                    'ts': fields[0],
                    'uid': fields[1] if len(fields) > 1 else '',
                    'src': fields[2] if len(fields) > 2 else '',
                    'dst': fields[3] if len(fields) > 3 else '',
                    'note': fields[4] if len(fields) > 4 else '',
                    'msg': fields[5] if len(fields) > 5 else '',
                    'actions': fields[6] if len(fields) > 6 else ''
                }
                
            return data
        except Exception as e:
            logger.debug(f"Erro ao parsear linha: {e}")
            return None
            
    def analyze_port_scan(self, notice_data):
        """Análise avançada de port scan"""
        try:
            note_type = notice_data.get('note', '')
            message = notice_data.get('msg', '')
            src_ip = notice_data.get('src', '')
            dst_ip = notice_data.get('dst', '')
            timestamp = notice_data.get('ts', str(time.time()))
            
            # Verifica se é realmente um port scan
            port_scan_indicators = [
                'PortScan::Port_Scan',
                'Scan::Port_Scan', 
                'Port_Scan',
                'Address_Scan'
            ]
            
            is_port_scan = any(indicator in note_type for indicator in port_scan_indicators)
            
            if not is_port_scan:
                return None
                
            # Skip IPs na whitelist
            if src_ip in self.config['detection']['whitelist_ips']:
                logger.debug(f"IP {src_ip} está na whitelist, ignorando")
                return None
                
            # Extrai informações do scan
            ports_scanned = self.extract_ports_from_message(message)
            
            # Análise de threat intelligence
            severity, risk_score = self.threat_intel.analyze_scan_pattern(
                src_ip, ports_scanned, datetime.now().isoformat()
            )
            
            ip_summary = self.threat_intel.get_ip_summary(src_ip)
            
            # Monta alerta
            alert_data = {
                'severity': severity,
                'src_ip': src_ip,
                'dst_ip': dst_ip,
                'ports_scanned': ports_scanned,
                'message': message,
                'timestamp': timestamp,
                'risk_score': risk_score,
                'ip_summary': ip_summary
            }
            
            return alert_data
            
        except Exception as e:
            logger.error(f"Erro na análise de port scan: {e}")
            return None
            
    def extract_ports_from_message(self, message):
        """Extrai portas da mensagem do Zeek"""
        ports = set()
        
        # Regex para encontrar portas
        port_patterns = [
            r'(\d+) ports',
            r'port (\d+)',
            r':(\d+)/',
            r'ports: ([\d,\s]+)'
        ]
        
        for pattern in port_patterns:
            matches = re.findall(pattern, message)
            for match in matches:
                if ',' in match:
                    # Lista de portas
                    for port_str in match.split(','):
                        try:
                            ports.add(int(port_str.strip()))
                        except ValueError:
                            pass
                else:
                    try:
                        ports.add(int(match))
                    except ValueError:
                        pass
                        
        return ports
        
    def create_alert_message(self, alert_data):
        """Cria mensagem de alerta formatada"""
        severity = alert_data['severity']
        src_ip = alert_data['src_ip']
        ports = alert_data['ports_scanned']
        risk_score = alert_data['risk_score']
        ip_summary = alert_data['ip_summary']
        
        subject = f"Port Scan {severity} detectado - {src_ip}"
        
        body = f"""
DETECÇÃO DE PORT SCAN - SEVERIDADE {severity}
{'=' * 50}

🎯 IP de Origem: {src_ip}
🎯 IP de Destino: {alert_data['dst_ip']}
📊 Risk Score: {risk_score}/10
⏰ Timestamp: {datetime.fromtimestamp(float(alert_data['timestamp'])).strftime('%Y-%m-%d %H:%M:%S')}

📈 ANÁLISE DO SCAN:
- Número de portas escaneadas: {len(ports)}
- Portas detectadas: {', '.join(map(str, sorted(ports))) if ports else 'N/A'}

🔍 HISTÓRICO DO IP:
{ip_summary}

📋 DETALHES TÉCNICOS:
{alert_data['message']}

🚨 AÇÕES RECOMENDADAS:
{'🔴 CRÍTICO: Bloqueio imediato recomendado' if severity == 'CRITICAL' else ''}
{'🟠 ALTO: Investigação urgente necessária' if severity == 'HIGH' else ''}
{'🟡 MÉDIO: Monitoramento contínuo recomendado' if severity == 'MEDIUM' else ''}

- Verificar se o IP {src_ip} é legítimo
- Analisar logs detalhados no sistema  
- Considerar bloqueio de firewall se malicioso
- Verificar outros sistemas na rede
"""
        
        return subject, body
        
    def monitor_zeek_logs(self):
        """Monitora logs do Zeek continuamente"""
        notice_log = os.path.join(self.config['monitoring']['zeek_log_dir'], 'notice.log')
        
        logger.info(f"Iniciando monitoramento de {notice_log}")
        
        while self.running:
            try:
                if not os.path.exists(notice_log):
                    logger.debug(f"Aguardando criação do arquivo {notice_log}")
                    time.sleep(self.config['monitoring']['check_interval'])
                    continue
                    
                with open(notice_log, 'r') as f:
                    f.seek(self.last_position)
                    
                    new_lines = 0
                    for line in f:
                        if not self.running:
                            break
                            
                        notice_data = self.parse_zeek_notice(line)
                        if notice_data:
                            alert_data = self.analyze_port_scan(notice_data)
                            if alert_data:
                                self.handle_port_scan_alert(alert_data)
                                
                        new_lines += 1
                        
                    self.last_position = f.tell()
                    
                    if new_lines > 0:
                        logger.debug(f"Processadas {new_lines} novas linhas")
                        self.save_state()
                        
            except FileNotFoundError:
                logger.debug("Arquivo de log não encontrado")
            except Exception as e:
                logger.error(f"Erro no monitoramento: {e}")
                
            time.sleep(self.config['monitoring']['check_interval'])
            
    def handle_port_scan_alert(self, alert_data):
        """Processa alerta de port scan"""
        try:
            alert_id = f"portscan_{alert_data['src_ip']}"
            
            # Verifica se deve enviar alerta
            if not self.alert_manager.should_send_alert(alert_id, alert_data['severity']):
                return
                
            # Cria mensagem
            subject, body = self.create_alert_message(alert_data)
            
            # Envia alerta
            success = self.send_email_alert(subject, body, alert_data['severity'])
            
            if success:
                self.alert_manager.register_alert_sent(alert_id)
                logger.info(f"Alerta enviado para port scan de {alert_data['src_ip']} (severidade: {alert_data['severity']})")
            else:
                logger.warning(f"Falha ao enviar alerta para port scan de {alert_data['src_ip']}")
                
        except Exception as e:
            logger.error(f"Erro ao processar alerta: {e}")
            
    def run(self):
        """Executa o monitor principal"""
        logger.info("🚀 SIMIR Monitor iniciado")
        logger.info(f"📧 Email configurado: {'✓' if self.config['email']['sender_password'] else '✗'}")
        logger.info(f"📁 Monitorando: {self.config['monitoring']['zeek_log_dir']}")
        
        try:
            self.monitor_zeek_logs()
        except KeyboardInterrupt:
            logger.info("Monitor interrompido pelo usuário")
        finally:
            self.save_state()
            logger.info("🛑 SIMIR Monitor finalizado")

def main():
    parser = argparse.ArgumentParser(description='SIMIR - Monitor Avançado de Port Scan')
    parser.add_argument('--config', help='Arquivo de configuração JSON')
    parser.add_argument('--email-password', help='Senha do email para alertas')
    parser.add_argument('--test-email', action='store_true', help='Envia email de teste')
    parser.add_argument('--daemon', action='store_true', help='Executa como daemon')
    parser.add_argument('--verbose', '-v', action='store_true', help='Log verbose')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger('SIMIR').setLevel(logging.DEBUG)
        
    # Configura senha se fornecida
    if args.email_password:
        os.environ['SIMIR_EMAIL_PASSWORD'] = args.email_password
        
    monitor = SimirMonitor(args.config)
    
    if args.test_email:
        logger.info("Enviando email de teste...")
        success = monitor.send_email_alert(
            "Teste do Sistema SIMIR",
            """
Este é um teste do sistema de monitoramento SIMIR.

🔧 Configurações testadas:
- Conexão SMTP: ✓
- Formatação de email: ✓  
- Sistema de alertas: ✓

Se você recebeu este email, o sistema está funcionando corretamente!
""",
            "TEST"
        )
        print("✓ Email de teste enviado!" if success else "✗ Falha no envio do email")
        return
        
    if args.daemon:
        logger.info("Executando como daemon...")
        
    monitor.run()

if __name__ == "__main__":
    main()
