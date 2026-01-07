"""
Serviço para integração com Zeek Network Security Monitor
"""
import json
import logging
import requests
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from urllib.parse import urlencode
import config

from .zeek_models import (
    ZeekLogType, ZeekSeverity, ZeekIncidentStatus, ZeekIncident,
    ZeekLogRequest, ZeekLogResponse, ZeekHttpLog, ZeekDnsLog, ZeekConnLog
)
from .incident_service import IncidentService

logger = logging.getLogger(__name__)


class ZeekService:
    """Serviço para comunicação com API do Zeek"""
    
    def __init__(self, zeek_api_base_url: Optional[str] = None, api_token: Optional[str] = None):
        """
        Inicializa o serviço Zeek
        
        Args:
            zeek_api_base_url: URL base da API do Zeek (usa config se não especificado)
            api_token: Token de autenticação (usa config se não especificado)
        """
        self.base_url = (zeek_api_base_url or config.ZEEK_API_URL or "http://192.168.100.1/zeek-api").rstrip('/')
        self.api_token = api_token or config.ZEEK_API_TOKEN
        self.timeout = 30
        self.incident_service = IncidentService()
        
        if not self.api_token:
            logger.warning("Token de autenticação do Zeek não configurado. Configure ZEEK_API_TOKEN no .env")
        
    def get_logs(self, request: ZeekLogRequest) -> ZeekLogResponse:
        """
        Busca logs do Zeek
        
        Args:
            request: Parâmetros da requisição
            
        Returns:
            Resposta com os logs e incidentes detectados
        """
        try:
            # Verifica se o token está configurado
            if not self.api_token:
                return ZeekLogResponse(
                    success=False,
                    message="Token de autenticação não configurado",
                    log_type=request.logfile,
                    total_lines=0,
                    logs=[],
                    incidents=[]
                )
            
            # Monta os parâmetros da URL
            params = {
                'logfile': request.logfile.value,
                'maxlines': request.maxlines
            }
            
            # Configura headers de autenticação
            headers = {
                'Authorization': f'Bearer {self.api_token}',
                'Content-Type': 'application/json'
            }
            
            # Faz a requisição para a API do Zeek
            url = f"{self.base_url}/alert_data.php"
            logger.info(f"Fazendo requisição para Zeek API: {url} com params: {params}")
            
            response = requests.get(url, params=params, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            
            # Processa a resposta JSON
            try:
                json_data = response.json()
            except json.JSONDecodeError as e:
                logger.error(f"Erro ao decodificar JSON da resposta Zeek: {e}")
                return ZeekLogResponse(
                    success=False,
                    message=f"Erro ao decodificar resposta JSON: {str(e)}",
                    log_type=request.logfile,
                    total_lines=0,
                    logs=[],
                    incidents=[]
                )
            
            # Verifica se a API retornou erro
            if not json_data.get('success', False):
                error_msg = json_data.get('error', 'Erro desconhecido da API Zeek')
                return ZeekLogResponse(
                    success=False,
                    message=error_msg,
                    log_type=request.logfile,
                    total_lines=0,
                    logs=[],
                    incidents=[]
                )
            
            # Extrai os dados dos logs
            logs = json_data.get('data', [])
            
            # Filtra por IP se especificado
            if request.filter_ip:
                logs = self._filter_logs_by_ip(logs, request.filter_ip)
            
            # Filtra por tempo se especificado
            if request.start_time or request.end_time:
                logs = self._filter_logs_by_time(logs, request.start_time, request.end_time)
            
            # Analisa logs para detectar incidentes
            incidents = self._analyze_logs_for_incidents(logs, request.logfile)
            
            return ZeekLogResponse(
                success=True,
                message=f"Logs recuperados com sucesso ({len(logs)} registros)",
                log_type=request.logfile,
                total_lines=len(logs),
                logs=logs,
                incidents=incidents
            )
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao buscar logs do Zeek: {e}")
            return ZeekLogResponse(
                success=False,
                message=f"Erro de comunicação com Zeek API: {str(e)}",
                log_type=request.logfile,
                total_lines=0,
                logs=[],
                incidents=[]
            )
        except Exception as e:
            logger.error(f"Erro inesperado ao processar logs do Zeek: {e}")
            return ZeekLogResponse(
                success=False,
                message=f"Erro interno: {str(e)}",
                log_type=request.logfile,
                total_lines=0,
                logs=[],
                incidents=[]
            )
    
    def _normalize_log_fields(self, log: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normaliza campos do log para formato consistente
        
        Args:
            log: Log bruto da API
            
        Returns:
            Log normalizado
        """
        normalized = {}
        
        for key, value in log.items():
            # Normaliza nomes de campos com pontos para underscores
            normalized_key = key.replace('.', '_')
            
            # Processa valores especiais do Zeek
            if isinstance(value, dict) and 'raw' in value and 'iso' in value:
                # Campo de tempo com formato especial da API
                normalized[normalized_key] = value['raw']
                normalized[f"{normalized_key}_iso"] = value['iso']
            elif isinstance(value, list):
                # Arrays (como tags, interfaces, etc.)
                normalized[normalized_key] = value
            else:
                # Valores simples
                normalized[normalized_key] = value
                
        return normalized
    
    def _filter_logs_by_ip(self, logs: List[Dict[str, Any]], filter_ip: str) -> List[Dict[str, Any]]:
        """
        Filtra logs por IP
        
        Args:
            logs: Lista de logs
            filter_ip: IP para filtrar
            
        Returns:
            Logs filtrados
        """
        filtered_logs = []
        for log in logs:
            normalized = self._normalize_log_fields(log)
            
            # Verifica se o IP está em qualquer campo relevante
            if (normalized.get('id_orig_h') == filter_ip or 
                normalized.get('id_resp_h') == filter_ip or
                str(normalized.get('id_orig_h', '')).startswith(filter_ip) or
                str(normalized.get('id_resp_h', '')).startswith(filter_ip)):
                filtered_logs.append(log)
        return filtered_logs
    
    def _filter_logs_by_time(self, logs: List[Dict[str, Any]], 
                           start_time: Optional[datetime], 
                           end_time: Optional[datetime]) -> List[Dict[str, Any]]:
        """
        Filtra logs por período de tempo
        
        Args:
            logs: Lista de logs
            start_time: Timestamp inicial
            end_time: Timestamp final
            
        Returns:
            Logs filtrados
        """
        if not start_time and not end_time:
            return logs
            
        filtered_logs = []
        for log in logs:
            normalized = self._normalize_log_fields(log)
            ts = normalized.get('ts')
            
            if ts is None:
                continue
                
            try:
                log_time = datetime.fromtimestamp(float(ts))
                
                if start_time and log_time < start_time:
                    continue
                if end_time and log_time > end_time:
                    continue
                    
                filtered_logs.append(log)
            except (ValueError, TypeError):
                # Se não conseguir converter timestamp, inclui o log
                filtered_logs.append(log)
        
        return filtered_logs
    
    def _analyze_logs_for_incidents(self, logs: List[Dict[str, Any]], 
                                  log_type: ZeekLogType) -> List[ZeekIncident]:
        """
        Analisa logs para detectar possíveis incidentes de segurança
        
        Args:
            logs: Lista de logs
            log_type: Tipo de log
            
        Returns:
            Lista de incidentes detectados
        """
        incidents = []
        
        for log in logs:
            normalized = self._normalize_log_fields(log)
            incident = self._detect_incident_in_log(normalized, log_type)
            if incident:
                incidents.append(incident)
                # Salva automaticamente no banco de dados
                try:
                    self._save_incident_to_database(incident, normalized)
                except Exception as e:
                    logger.error(f"Erro ao salvar incidente no banco de dados: {e}")
                    # Continua o processamento mesmo se houver erro ao salvar
        
        return incidents
    
    def _detect_incident_in_log(self, log: Dict[str, Any], 
                              log_type: ZeekLogType) -> Optional[ZeekIncident]:
        """
        Detecta incidentes em um log específico
        
        Args:
            log: Dados do log
            log_type: Tipo de log
            
        Returns:
            Incidente detectado ou None
        """
        if log_type == ZeekLogType.HTTP:
            return self._detect_http_incident(log)
        elif log_type == ZeekLogType.DNS:
            return self._detect_dns_incident(log)
        elif log_type == ZeekLogType.CONN:
            return self._detect_conn_incident(log)
        elif log_type == ZeekLogType.NOTICE:
            return self._detect_notice_incident(log)
        
        return None
    
    def _detect_http_incident(self, log: Dict[str, Any]) -> Optional[ZeekIncident]:
        """
        Detecta incidentes em logs HTTP
        
        Args:
            log: Log HTTP
            
        Returns:
            Incidente ou None
        """
        incident_type = None
        severity = None
        description = None
        
        # Verifica códigos de status suspeitos
        status_code = log.get('status_code')
        if status_code:
            if status_code >= 400:
                severity = ZeekSeverity.MEDIUM if status_code < 500 else ZeekSeverity.HIGH
                incident_type = f"HTTP Error {status_code}"
                description = f"Erro HTTP {status_code}: {log.get('status_msg', 'Unknown error')}"
            elif status_code in [301, 302, 303, 307, 308]:
                severity = ZeekSeverity.LOW
                incident_type = "HTTP Redirect"
                description = f"Redirecionamento HTTP {status_code} para {log.get('host', 'unknown host')}"
        
        # Verifica user agents suspeitos (mesmo sem status_code)
        user_agent = log.get('user_agent', '')
        if user_agent and not incident_type:
            suspicious_agents = ['curl', 'wget', 'python-requests', 'scanner', 'bot', 'sqlmap', 'nikto']
            if any(agent.lower() in user_agent.lower() for agent in suspicious_agents):
                severity = ZeekSeverity.MEDIUM
                incident_type = "Suspicious User Agent"
                description = f"User agent suspeito detectado: {user_agent}"
        
        # Verifica URIs suspeitas (mesmo sem status_code)
        uri = log.get('uri', '')
        if uri and not incident_type:
            suspicious_patterns = ['/admin', '/.env', '/wp-admin', '/phpmyadmin', '../', '/api/', '/config']
            if any(pattern in uri.lower() for pattern in suspicious_patterns):
                severity = ZeekSeverity.MEDIUM
                incident_type = "Suspicious URI Access"
                description = f"Acesso a URI suspeita: {uri}"
        
        # Verifica métodos HTTP suspeitos
        method = log.get('method', '')
        if method and not incident_type:
            if method.upper() in ['PUT', 'DELETE', 'PATCH', 'TRACE', 'OPTIONS']:
                severity = ZeekSeverity.LOW
                incident_type = f"Unusual HTTP Method"
                description = f"Método HTTP incomum detectado: {method}"
        
        # Verifica tamanho de requisição suspeito
        request_body_len = log.get('request_body_len', 0) or 0
        if request_body_len > 10000 and not incident_type:  # > 10KB
            severity = ZeekSeverity.LOW
            incident_type = "Large HTTP Request"
            description = f"Requisição HTTP grande detectada: {request_body_len} bytes"
        
        if incident_type:
            ts = log.get('ts')
            if isinstance(ts, dict) and 'raw' in ts:
                ts = ts['raw']
            elif ts is None:
                ts = datetime.now().timestamp()
                
            device_ip = log.get('id_orig_h', 'unknown')
            
            return ZeekIncident(
                device_ip=device_ip,
                incident_type=incident_type,
                severity=severity,
                description=description,
                detected_at=datetime.fromtimestamp(float(ts)) if isinstance(ts, (int, float)) else datetime.now(),
                status=ZeekIncidentStatus.NEW,
                raw_log_data=log,
                zeek_log_type=ZeekLogType.HTTP
            )
        
        return None
    
    def _detect_dns_incident(self, log: Dict[str, Any]) -> Optional[ZeekIncident]:
        """
        Detecta incidentes em logs DNS
        
        Args:
            log: Log DNS
            
        Returns:
            Incidente ou None
        """
        query = log.get('query', '').lower()
        if not query:
            return None
        
        # Domínios suspeitos
        suspicious_domains = [
            'malware.com', 'phishing.net', 'suspicious.org',
            # Adicione mais domínios conhecidamente maliciosos
        ]
        
        # Verifica DGA (Domain Generation Algorithm) patterns
        if len(query) > 20 and query.count('.') > 3:
            severity = ZeekSeverity.MEDIUM
            incident_type = "Possible DGA Domain"
            description = f"Possível domínio gerado algoritmicamente: {query}"
        elif any(domain in query for domain in suspicious_domains):
            severity = ZeekSeverity.HIGH
            incident_type = "Malicious Domain Query"
            description = f"Query para domínio malicioso: {query}"
        else:
            return None
        
        ts = log.get('ts', datetime.now().timestamp())
        device_ip = log.get('id_orig_h', 'unknown')
        
        return ZeekIncident(
            device_ip=device_ip,
            incident_type=incident_type,
            severity=severity,
            description=description,
            detected_at=datetime.fromtimestamp(ts) if isinstance(ts, (int, float)) else datetime.now(),
            status=ZeekIncidentStatus.NEW,
            raw_log_data=log,
            zeek_log_type=ZeekLogType.DNS
        )
    
    def _detect_conn_incident(self, log: Dict[str, Any]) -> Optional[ZeekIncident]:
        """
        Detecta incidentes em logs de conexão
        
        Args:
            log: Log de conexão
            
        Returns:
            Incidente ou None
        """
        # Verifica conexões com volumes anômalos de dados
        orig_bytes = log.get('orig_bytes', 0) or 0
        resp_bytes = log.get('resp_bytes', 0) or 0
        total_bytes = orig_bytes + resp_bytes
        
        # Limiar para considerar tráfego suspeito (100MB)
        if total_bytes > 100 * 1024 * 1024:
            severity = ZeekSeverity.MEDIUM
            incident_type = "High Volume Traffic"
            description = f"Alto volume de tráfego detectado: {total_bytes / (1024*1024):.2f} MB"
        
        # Verifica conexões falhadas
        conn_state = log.get('conn_state', '')
        if conn_state in ['REJ', 'RSTO', 'RSTR']:
            severity = ZeekSeverity.LOW
            incident_type = "Connection Failed"
            description = f"Conexão falhada com estado: {conn_state}"
        else:
            return None
        
        ts = log.get('ts', datetime.now().timestamp())
        device_ip = log.get('id_orig_h', 'unknown')
        
        return ZeekIncident(
            device_ip=device_ip,
            incident_type=incident_type,
            severity=severity,
            description=description,
            detected_at=datetime.fromtimestamp(ts) if isinstance(ts, (int, float)) else datetime.now(),
            status=ZeekIncidentStatus.NEW,
            raw_log_data=log,
            zeek_log_type=ZeekLogType.CONN
        )
    
    def _detect_notice_incident(self, log: Dict[str, Any]) -> Optional[ZeekIncident]:
        """
        Detecta incidentes em logs notice (alertas de segurança)
        
        Args:
            log: Log notice
            
        Returns:
            Incidente ou None
        """
        note = log.get('note', '')
        msg = log.get('msg', '')
        
        if not note:
            return None
        
        # Determina severidade baseada no tipo de nota
        severity = ZeekSeverity.MEDIUM  # Padrão
        incident_type = f"Security Notice: {note}"
        description = msg or f"Alerta de segurança detectado: {note}"
        
        # Ajusta severidade baseada em padrões conhecidos
        if any(keyword in note.lower() for keyword in ['sql_injection', 'xss', 'malware', 'botnet']):
            severity = ZeekSeverity.HIGH
        elif any(keyword in note.lower() for keyword in ['suspicious', 'anomaly', 'scan']):
            severity = ZeekSeverity.MEDIUM
        elif any(keyword in note.lower() for keyword in ['info', 'notice']):
            severity = ZeekSeverity.LOW
        
        # Para SQL Injection, classifica como crítico e diferencia atacante/vítima
        if 'sql_injection' in note.lower():
            severity = ZeekSeverity.CRITICAL
            if 'victim' in note.lower():
                incident_type = "SQL Injection - Vítima"
                description = f"Vítima de SQL Injection detectada: {msg}"
            elif 'attacker' in note.lower():
                incident_type = "SQL Injection - Atacante"
                description = f"Atacante de SQL Injection detectado: {msg}"
            else:
                incident_type = "SQL Injection Attack"
                description = f"Ataque de SQL Injection detectado: {msg}"
        
        ts = log.get('ts')
        if isinstance(ts, dict) and 'raw' in ts:
            ts = ts['raw']
        elif ts is None:
            ts = datetime.now().timestamp()
            
        # Para logs notice, verifica campos específicos que podem conter IPs
        # No notice.log, os IPs estão em 'src' e 'dst', não em 'id_orig_h' e 'id_resp_h'
        device_ip = (log.get('src') or 
                    log.get('id_orig_h') or 
                    log.get('dst') or 
                    log.get('id_resp_h') or 
                    '192.168.100.1')  # IP padrão do pfSense
        
        return ZeekIncident(
            device_ip=device_ip,
            incident_type=incident_type,
            severity=severity,
            description=description,
            detected_at=datetime.fromtimestamp(float(ts)) if isinstance(ts, (int, float)) else datetime.now(),
            status=ZeekIncidentStatus.NEW,
            raw_log_data=log,
            zeek_log_type=ZeekLogType.NOTICE
        )
    
    def get_available_log_types(self) -> List[str]:
        """
        Retorna os tipos de logs disponíveis
        
        Returns:
            Lista de tipos de logs
        """
        return [log_type.value for log_type in ZeekLogType]
    
    def test_connection(self) -> Tuple[bool, str]:
        """
        Testa a conectividade com a API do Zeek
        
        Returns:
            Tupla (sucesso, mensagem)
        """
        try:
            if not self.api_token:
                return False, "Token de autenticação não configurado"
                
            url = f"{self.base_url}/alert_data.php"
            params = {'logfile': 'http.log', 'maxlines': 1}
            headers = {
                'Authorization': f'Bearer {self.api_token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                try:
                    json_data = response.json()
                    if json_data.get('success', False):
                        return True, "Conexão com Zeek API estabelecida com sucesso"
                    else:
                        error_msg = json_data.get('error', 'Erro desconhecido')
                        return False, f"API retornou erro: {error_msg}"
                except json.JSONDecodeError:
                    return False, "Resposta da API não é um JSON válido"
            elif response.status_code == 401:
                return False, "Token de autenticação inválido"
            else:
                return False, f"Erro HTTP {response.status_code}: {response.text[:100]}"
                
        except requests.exceptions.ConnectionError:
            return False, "Não foi possível conectar com a API do Zeek"
        except requests.exceptions.Timeout:
            return False, "Timeout na conexão com a API do Zeek"
        except Exception as e:
            return False, f"Erro inesperado: {str(e)}"
    
    def _save_incident_to_database(self, incident: ZeekIncident, raw_log: Dict[str, Any]):
        """
        Salva um incidente detectado no banco de dados MySQL
        
        Args:
            incident: Incidente detectado pelo Zeek
            raw_log: Log original para armazenar como dados brutos
        """
        try:
            # Converte o modelo Pydantic para o modelo SQLAlchemy
            incident_data = {
                'device_ip': incident.device_ip,
                'device_name': incident.device_name,
                'incident_type': incident.incident_type,
                'severity': incident.severity.value.lower(),  # Converte para lowercase
                'status': incident.status.value.lower(),      # Converte para lowercase
                'description': incident.description,
                'detected_at': incident.detected_at,
                'zeek_log_type': incident.zeek_log_type.value.lower(),  # Converte para lowercase
                'raw_log_data': json.dumps(raw_log, default=str),
                'action_taken': incident.action_taken,
                'assigned_to': None,  # Campo não existe no modelo Pydantic
                'notes': None         # Campo não existe no modelo Pydantic
            }
            
            # Cria o incidente no banco de dados
            created_incident = self.incident_service.save_incident(incident_data)
            
            if created_incident:
                logger.info(f"Incidente salvo no banco de dados - ID: {created_incident.id}, Tipo: {incident.incident_type}, IP: {incident.device_ip}")
            else:
                logger.warning(f"Falha ao salvar incidente no banco - Tipo: {incident.incident_type}, IP: {incident.device_ip}")
                
        except Exception as e:
            logger.error(f"Erro ao salvar incidente no banco de dados: {e}")
            raise
